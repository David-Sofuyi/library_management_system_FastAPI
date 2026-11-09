from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.book import Book
from app.models.loan import Loan
from app.schemas.book_schema import BookCreate, BookUpdate


class LibraryServiceException(Exception):
    """Base exception for library service errors."""
    pass


class BookNotFoundError(LibraryServiceException):
    pass


class DuplicateBookError(LibraryServiceException):
    pass


class BookUnavailableError(LibraryServiceException):
    pass


class ActiveLoanConflictError(LibraryServiceException):
    pass


class InvalidOperationError(LibraryServiceException):
    pass


class LibraryService:

    @staticmethod
    def add_book(db: Session, book_in: BookCreate) -> Book:
        isbn = book_in.isbn.strip()
        existing = db.query(Book).filter(Book.isbn == isbn).first()
        if existing:
            raise DuplicateBookError(f"A book with ISBN '{isbn}' already exists.")

        book = Book(
            isbn=isbn,
            title=book_in.title.strip(),
            author=book_in.author.strip(),
            total_copies=book_in.total_copies,
            available_copies=book_in.total_copies,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def get_book_by_id(db: Session, book_id: int) -> Book:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise BookNotFoundError(f"Book with ID {book_id} not found.")
        return book

    @staticmethod
    def get_book_by_isbn(db: Session, isbn: str) -> Book:
        book = db.query(Book).filter(Book.isbn == isbn.strip()).first()
        if not book:
            raise BookNotFoundError(f"Book with ISBN '{isbn.strip()}' not found.")
        return book

    @staticmethod
    def get_books(
        db: Session,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Book]:
        stmt = db.query(Book)
        if query and query.strip():
            search = f"%{query.strip()}%"
            stmt = stmt.filter(
                or_(
                    Book.isbn.ilike(search),
                    Book.title.ilike(search),
                    Book.author.ilike(search),
                )
            )
        return stmt.offset(skip).limit(limit).all()

    @staticmethod
    def update_book(db: Session, book_id: int, book_in: BookUpdate) -> Book:
        book = LibraryService.get_book_by_id(db, book_id)

        if book_in.title is not None:
            book.title = book_in.title.strip()
        if book_in.author is not None:
            book.author = book_in.author.strip()

        if book_in.total_copies is not None:
            currently_borrowed = book.total_copies - book.available_copies
            if book_in.total_copies < currently_borrowed:
                raise InvalidOperationError(
                    f"Cannot reduce total copies to {book_in.total_copies}. "
                    f"There are currently {currently_borrowed} copies on loan."
                )
            book.available_copies = book_in.total_copies - currently_borrowed
            book.total_copies = book_in.total_copies

        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def delete_book(db: Session, book_id: int) -> Book:
        book = LibraryService.get_book_by_id(db, book_id)

        # Check if active loans exist for this book
        active_loans_count = (
            db.query(Loan)
            .filter(Loan.book_id == book.id, Loan.is_active.is_(True))
            .count()
        )
        if active_loans_count > 0:
            raise InvalidOperationError(
                f"Cannot delete book '{book.title}' because {active_loans_count} "
                "borrowed copies have not been returned."
            )

        db.delete(book)
        db.commit()
        return book

    @staticmethod
    def borrow_book(db: Session, isbn: str, borrower_id: str) -> Loan:
        isbn = isbn.strip()
        borrower_id = borrower_id.strip()

        book = LibraryService.get_book_by_isbn(db, isbn)

        # Verify borrower doesn't already hold an active copy of this book
        existing_loan = (
            db.query(Loan)
            .filter(
                Loan.book_id == book.id,
                Loan.borrower_id == borrower_id,
                Loan.is_active.is_(True),
            )
            .first()
        )
        if existing_loan:
            raise ActiveLoanConflictError(
                f"Borrower '{borrower_id}' already has an active loan for this book."
            )

        if book.available_copies <= 0:
            raise BookUnavailableError(
                f"No copies of '{book.title}' are currently available for borrowing."
            )

        book.available_copies -= 1

        loan = Loan(
            book_id=book.id,
            borrower_id=borrower_id,
            is_active=True,
            borrowed_at=datetime.now(timezone.utc),
        )
        db.add(loan)
        db.commit()
        db.refresh(loan)
        return loan

    @staticmethod
    def return_book(db: Session, isbn: str, borrower_id: str) -> Loan:
        isbn = isbn.strip()
        borrower_id = borrower_id.strip()

        book = LibraryService.get_book_by_isbn(db, isbn)

        loan = (
            db.query(Loan)
            .filter(
                Loan.book_id == book.id,
                Loan.borrower_id == borrower_id,
                Loan.is_active.is_(True),
            )
            .first()
        )
        if not loan:
            raise InvalidOperationError(
                f"No active loan found for borrower '{borrower_id}' and book '{book.title}'."
            )

        loan.is_active = False
        loan.returned_at = datetime.now(timezone.utc)

        if book.available_copies < book.total_copies:
            book.available_copies += 1

        db.commit()
        db.refresh(loan)
        return loan

    @staticmethod
    def get_loans(
        db: Session,
        borrower_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Loan]:
        stmt = db.query(Loan).options(joinedload(Loan.book))
        if borrower_id:
            stmt = stmt.filter(Loan.borrower_id == borrower_id.strip())
        if is_active is not None:
            stmt = stmt.filter(Loan.is_active == is_active)

        return stmt.order_by(Loan.borrowed_at.desc()).offset(skip).limit(limit).all()
