# Compatibility alias for library_service.py
from app.services.library_service import (
    LibraryService,
    LibraryServiceException,
    BookNotFoundError,
    DuplicateBookError,
    BookUnavailableError,
    ActiveLoanConflictError,
    InvalidOperationError,
)

__all__ = [
    "LibraryService",
    "LibraryServiceException",
    "BookNotFoundError",
    "DuplicateBookError",
    "BookUnavailableError",
    "ActiveLoanConflictError",
    "InvalidOperationError",
]
