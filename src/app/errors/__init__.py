"""Error handling module — independently extractable.

Public API:
    DomainError                   — Base exception with status_code attribute.
    NotFoundError                 — 404.
    ConflictError                 — 409.
    ValidationError               — 422 (domain-level, not Pydantic).
    PermissionDeniedError         — 403.
    AuthenticationError           — 401.
    ErrorResponse                 — Pydantic model for all error payloads.
    UnhandledExceptionMiddleware  — Pure ASGI catch-all for unhandled exceptions.
    register_exception_handlers   — Attach handlers + middleware to FastAPI app.
"""

from app.errors.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.errors.handlers import register_exception_handlers
from app.errors.middleware import UnhandledExceptionMiddleware
from app.errors.schemas import ErrorResponse

__all__ = [
    "AuthenticationError",
    "ConflictError",
    "DomainError",
    "ErrorResponse",
    "NotFoundError",
    "PermissionDeniedError",
    "UnhandledExceptionMiddleware",
    "ValidationError",
    "register_exception_handlers",
]
