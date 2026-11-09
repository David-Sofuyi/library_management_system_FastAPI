import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.main import app

# In-memory SQLite with StaticPool preserves the schema across connections
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint_serves_frontend(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Library Management System" in response.text
    assert "Freshie LMS" in response.text


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_add_and_get_book(client):
    book_payload = {
        "isbn": "978-0132350884",
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "total_copies": 3,
    }
    response = client.post("/books/", json=book_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["isbn"] == book_payload["isbn"]
    assert data["available_copies"] == 3
    assert data["id"] is not None

    book_id = data["id"]
    get_res = client.get(f"/books/{book_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Clean Code"


def test_duplicate_book_isbn(client):
    book_payload = {
        "isbn": "978-0132350884",
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "total_copies": 2,
    }
    res1 = client.post("/books/", json=book_payload)
    assert res1.status_code == 201

    res2 = client.post("/books/", json=book_payload)
    assert res2.status_code == 409


def test_search_books(client):
    client.post(
        "/books/",
        json={"isbn": "111", "title": "Fluent Python", "author": "Luciano Ramalho", "total_copies": 2},
    )
    client.post(
        "/books/",
        json={"isbn": "222", "title": "Design Patterns", "author": "Gang of Four", "total_copies": 1},
    )

    search_res = client.get("/books/?query=fluent")
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) == 1
    assert results[0]["title"] == "Fluent Python"


def test_update_book(client):
    res = client.post(
        "/books/",
        json={"isbn": "333", "title": "Original Title", "author": "Author", "total_copies": 2},
    )
    book_id = res.json()["id"]

    # Borrow 1 copy
    client.post("/books/borrow", json={"isbn": "333", "borrower_id": "member-1"})

    # Update title and total_copies
    up_res = client.put(f"/books/{book_id}", json={"title": "Updated Title", "total_copies": 5})
    assert up_res.status_code == 200
    assert up_res.json()["title"] == "Updated Title"
    assert up_res.json()["total_copies"] == 5
    assert up_res.json()["available_copies"] == 4  # 5 - 1 borrowed

    # Trying to reduce total copies below borrowed amount should fail
    fail_res = client.put(f"/books/{book_id}", json={"total_copies": 0})
    assert fail_res.status_code == 422  # pydantic gt=0 validation


def test_borrow_and_return_book(client):
    # Add book
    client.post(
        "/books/",
        json={"isbn": "978-TEST", "title": "Test Driven Development", "author": "Kent Beck", "total_copies": 1},
    )

    # Borrow book
    borrow_payload = {"isbn": "978-TEST", "borrower_id": "member-101"}
    borrow_res = client.post("/books/borrow", json=borrow_payload)
    assert borrow_res.status_code == 201
    loan_data = borrow_res.json()
    assert loan_data["is_active"] is True
    assert loan_data["borrower_id"] == "member-101"

    # Verify available copies decreased
    book_res = client.get("/books/?query=978-TEST")
    assert book_res.json()[0]["available_copies"] == 0

    # Try borrowing again when no copies available
    borrow_fail = client.post("/books/borrow", json={"isbn": "978-TEST", "borrower_id": "member-202"})
    assert borrow_fail.status_code == 400

    # Try borrowing when borrower already has active loan
    client.put(f"/books/{book_res.json()[0]['id']}", json={"total_copies": 2})
    borrow_duplicate_member = client.post("/books/borrow", json={"isbn": "978-TEST", "borrower_id": "member-101"})
    assert borrow_duplicate_member.status_code == 409

    # Check active loans endpoint
    active_loans = client.get("/books/loans/active?borrower_id=member-101")
    assert active_loans.status_code == 200
    assert len(active_loans.json()) == 1

    # Return book
    return_payload = {"isbn": "978-TEST", "borrower_id": "member-101"}
    return_res = client.post("/books/return", json=return_payload)
    assert return_res.status_code == 200
    assert return_res.json()["is_active"] is False

    # Check active loans endpoint again
    active_loans_after = client.get("/books/loans/active?borrower_id=member-101")
    assert active_loans_after.status_code == 200
    assert len(active_loans_after.json()) == 0

    # Check loan history
    all_loans = client.get("/books/loans")
    assert all_loans.status_code == 200
    assert len(all_loans.json()) == 1


def test_cannot_delete_book_with_active_loans(client):
    client.post(
        "/books/",
        json={"isbn": "978-DEL", "title": "Deletable Book", "author": "Author", "total_copies": 1},
    )
    book = client.get("/books/?query=978-DEL").json()[0]

    # Borrow
    client.post("/books/borrow", json={"isbn": "978-DEL", "borrower_id": "borrower-1"})

    # Attempt deletion
    del_res = client.delete(f"/books/{book['id']}")
    assert del_res.status_code == 400

    # Return and then delete
    client.post("/books/return", json={"isbn": "978-DEL", "borrower_id": "borrower-1"})
    del_ok = client.delete(f"/books/{book['id']}")
    assert del_ok.status_code == 200
