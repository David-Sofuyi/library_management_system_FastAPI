from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.book_schema import BookCreate, BookResponse, BookUpdate
from app.schemas.loan_schema import LoanBorrowRequest, LoanResponse, LoanReturnRequest
from app.services.library_service import (
    ActiveLoanConflictError,
    BookNotFoundError,
    BookUnavailableError,
    DuplicateBookError,
    InvalidOperationError,
    LibraryService,
)

router = APIRouter(prefix="/books", tags=["Books & Loans"])


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new book",
)
def add_book(book_in: BookCreate, db: Session = Depends(get_db)):
    """Add a new book with its title, author, ISBN, and total copies."""
    try:
        return LibraryService.add_book(db, book_in)
    except DuplicateBookError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=List[BookResponse],
    summary="Search or list all books",
)
def list_books(
    query: Optional[str] = Query(
        None, description="Search term for title, author, or ISBN"
    ),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    db: Session = Depends(get_db),
):
    """Retrieve books with optional text search and pagination."""
    return LibraryService.get_books(db, query=query, skip=skip, limit=limit)


@router.post(
    "/borrow",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Borrow a book",
)
def borrow_book(request: LoanBorrowRequest, db: Session = Depends(get_db)):
    """Borrow a copy of a book by ISBN for a specific borrower."""
    try:
        return LibraryService.borrow_book(db, request.isbn, request.borrower_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ActiveLoanConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BookUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/return",
    response_model=LoanResponse,
    summary="Return a borrowed book",
)
def return_book(request: LoanReturnRequest, db: Session = Depends(get_db)):
    """Return a previously borrowed book by ISBN and borrower ID."""
    try:
        return LibraryService.return_book(db, request.isbn, request.borrower_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/loans/active",
    response_model=List[LoanResponse],
    summary="View active loans",
)
def get_active_loans(
    borrower_id: Optional[str] = Query(None, description="Filter by borrower ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all currently active (unreturned) loans."""
    return LibraryService.get_loans(
        db, borrower_id=borrower_id, is_active=True, skip=skip, limit=limit
    )


@router.get(
    "/loans",
    response_model=List[LoanResponse],
    summary="View loan history",
)
def get_all_loans(
    borrower_id: Optional[str] = Query(None, description="Filter by borrower ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve full loan history with optional filters."""
    return LibraryService.get_loans(
        db, borrower_id=borrower_id, is_active=is_active, skip=skip, limit=limit
    )


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get book by ID",
)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single book by its primary ID."""
    try:
        return LibraryService.get_book_by_id(db, book_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update book details",
)
def update_book(
    book_id: int,
    book_in: BookUpdate,
    db: Session = Depends(get_db),
):
    """Update title, author, or total copies of an existing book."""
    try:
        return LibraryService.update_book(db, book_id, book_in)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{book_id}",
    response_model=BookResponse,
    summary="Delete a book",
)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book from the system if no borrowed copies remain unreturned."""
    try:
        return LibraryService.delete_book(db, book_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
