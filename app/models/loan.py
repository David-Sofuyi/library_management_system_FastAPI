from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


def utc_now():
    return datetime.now(timezone.utc)


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    borrower_id = Column(String(100), index=True, nullable=False)
    borrowed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    book = relationship("Book", back_populates="loans")

    def __repr__(self):
        return f"<Loan(id={self.id}, book_id={self.book_id}, borrower='{self.borrower_id}', active={self.is_active})>"
