from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), index=True, nullable=False)
    author = Column(String(255), index=True, nullable=False)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)

    loans = relationship("Loan", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(isbn='{self.isbn}', title='{self.title}', available={self.available_copies}/{self.total_copies})>"
