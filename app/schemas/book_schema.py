from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BookBase(BaseModel):
    isbn: str = Field(..., min_length=1, max_length=64, description="ISBN identifier of the book")
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    total_copies: int = Field(default=1, gt=0, description="Total number of copies owned")


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    total_copies: Optional[int] = Field(None, gt=0)


class BookResponse(BookBase):
    id: int
    available_copies: int

    model_config = ConfigDict(from_attributes=True)
