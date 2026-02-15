"""Structured error response schema.

Every error — domain, HTTP, validation, unhandled — returns the same shape.
Clients parse one schema. Ops correlate via ``request_id``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Consistent error payload returned by all exception handlers.

    Simplified RFC 7807 — full spec adds ``type`` URI and ``instance``
    which most APIs don't need initially.
    """

    detail: str = Field(description="Human-readable error message.")
    status_code: int = Field(
        description="HTTP status code (mirrored in body for convenience).",
    )
    request_id: str = Field(
        default="",
        description="Correlation ID from X-Request-ID header.",
    )
