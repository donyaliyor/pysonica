"""Domain exception hierarchy.

All domain exceptions carry a ``status_code`` so the global handler can map
them to HTTP responses without the domain layer knowing about HTTP.

Usage::

    from app.errors import NotFoundError, ConflictError

    raise NotFoundError("Order", order_id="abc-123")
    raise ConflictError("Email already registered")
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for all domain exceptions.

    Attributes:
        status_code: HTTP status code the global handler maps this to.
        detail: Human-readable message for the API response.
        extra: Structured context for logging (never sent to client).
    """

    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(
        self,
        detail: str | None = None,
        *,
        status_code: int | None = None,
        **extra: object,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra
        super().__init__(self.detail)


class NotFoundError(DomainError):
    """Resource not found (404)."""

    status_code = 404

    def __init__(self, resource: str = "Resource", **extra: object) -> None:
        super().__init__(detail=f"{resource} not found")
        self.extra = extra


class ConflictError(DomainError):
    """Conflicting state (409)."""

    status_code = 409


class ValidationError(DomainError):
    """Domain validation failure (422).

    Distinct from Pydantic's RequestValidationError.
    """

    status_code = 422


class PermissionDeniedError(DomainError):
    """Caller lacks permission (403)."""

    status_code = 403


class AuthenticationError(DomainError):
    """Missing or invalid credentials (401)."""

    status_code = 401
