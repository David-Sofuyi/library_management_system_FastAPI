# Freshie LMS (FastAPI + Frontend)

A complete, full-stack Library Management System featuring:
- **FastAPI backend** with SQLite & SQLAlchemy ORM
- **Interactive Single-Page Application (SPA) Frontend** served directly from the application
- **RESTful API** with auto-generated Swagger and ReDoc documentation
- **Automated Pytest Suite**

---

## 🎨 Features & Capabilities

### 🖥️ Interactive Web UI
- **Dashboard Stats**: Real-time counter of total book titles, total physical copies, available copies, and active loans.
- **Book Catalog**:
  - Search filter (by Title, Author, or ISBN).
  - Add New Book with validation.
  - Edit Book metadata and inventory counts.
  - Delete Book with safety checks (blocked if copies are on loan).
- **Lending & Return Flow**:
  - One-click **Borrow** from any book card or via quick action button.
  - Active loans tracker with Borrower ID filter.
  - Quick **Return Book** action with instant inventory restoration.
- **Audit History**: Complete transaction log of active and historical returns.
- **Instant Feedback**: Toast notifications for successful operations and error prevention.

### ⚙️ REST API Endpoints
- `GET /`: Serves the interactive SPA frontend dashboard.
- `GET /health`: System health status.
- `GET /docs`: Interactive Swagger API documentation.
- `GET /redoc`: ReDoc API documentation.
- `POST /books/`: Add book.
- `GET /books/`: Search/list catalog.
- `GET /books/{book_id}`: Book details.
- `PUT /books/{book_id}`: Update book.
- `DELETE /books/{book_id}`: Delete book.
- `POST /books/borrow`: Borrow a book copy.
- `POST /books/return`: Return a borrowed copy.
- `GET /books/loans/active`: List current active loans.
- `GET /books/loans`: List all historical loans.

---

## 📁 Project Structure

```text
library_management_system_FastAPI/
│
├── app/
│   ├── __init__.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py        # SQLAlchemy engine, session maker, get_db & init_db
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── book.py              # SQLAlchemy Book model
│   │   └── loan.py              # SQLAlchemy Loan model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── book_schema.py       # Pydantic v2 schemas for Book CRUD & responses
│   │   └── loan_schema.py       # Pydantic v2 schemas for borrow/return requests
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── library_service.py   # Business logic and exception management
│   │   └── library_services.py  # Compatibility alias
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── book_routes.py       # FastAPI endpoints for books & loans
│   │
│   ├── static/                  # Frontend UI Assets
│   │   ├── css/
│   │   │   └── style.css        # Responsive dashboard styling
│   │   ├── js/
│   │   │   └── app.js           # Frontend state, API integration, and DOM logic
│   │   └── index.html           # Single-page application HTML
│   │
│   └── main.py                  # FastAPI application with static mount and lifespan
│
├── tests/
│   └── test_api.py              # Automated Pytest suite
│
├── .env                         # Environment variables configuration
├── .gitignore                   # Ignored files (venv, db, pycache)
├── requirements.txt             # Project dependencies
├── pytest.ini                   # Pytest configuration
└── main.py                      # Root launcher script
```

---

## 🚀 Running the Application

### 1. Start the Server

```powershell
python main.py
```
*Or run directly with Uvicorn:*
```powershell
uvicorn app.main:app --reload --port 8000
```

### 2. Access the Application
- **Frontend Dashboard**: Open your browser to [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 3. Run Automated Tests

```powershell
python -m pytest -v
```
