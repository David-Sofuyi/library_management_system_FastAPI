from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.book_schema import BookResponse


class LoanBorrowRequest(BaseModel):
    isbn: str = Field(..., min_length=1, description="ISBN of the book to borrow")
    borrower_id: str = Field(..., min_length=1, max_length=100, description="Borrower identifier")


class LoanReturnRequest(BaseModel):
    isbn: str = Field(..., min_length=1, description="ISBN of the book to return")
    borrower_id: str = Field(..., min_length=1, max_length=100, description="Borrower identifier")


class LoanResponse(BaseModel):
    id: int
    book_id: int
    borrower_id: str
    borrowed_at: datetime
    returned_at: Optional[datetime] = None
    is_active: bool
    book: Optional[BookResponse] = None

    model_config = ConfigDict(from_attributes=True)
