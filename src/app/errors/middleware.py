"""Catch-all exception middleware — last line of defense.

Pure ASGI middleware that catches any exception not handled by FastAPI's
``ExceptionMiddleware`` (domain errors, HTTP errors, validation errors).

Why a middleware instead of ``add_exception_handler(Exception, handler)``?
Starlette's routing of ``Exception`` handlers to ``ServerErrorMiddleware``
varies across versions. A middleware in the user stack is reliable regardless
of Starlette internals.

Placement:
    Register via ``register_exception_handlers(app)`` — it adds this middleware
    automatically. In the middleware stack (bottom-to-top execution order), it
    sits just above ``ExceptionMiddleware`` and below user middleware like
    ``AccessLogMiddleware``.
"""

from __future__ import annotations

import structlog
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.errors.schemas import ErrorResponse

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class UnhandledExceptionMiddleware:
    """Pure ASGI middleware — catches unhandled exceptions and returns 500.

    Unlike ``BaseHTTPMiddleware``, this has no issues with ``StreamingResponse``
    or WebSocket connections — it only intercepts HTTP scope and passes
    everything else through unchanged.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            request = Request(scope)
            request_id = request.headers.get("x-request-id", "")

            # Defensive: the logger itself may be what's broken.
            # We can't log a logging failure — suppress and return 500.
            try:  # noqa: SIM105
                logger.exception(
                    "unhandled_error",
                    error_type=type(exc).__name__,
                    path=request.url.path,
                )
            except Exception:  # noqa: S110
                pass

            body = ErrorResponse(
                detail="Internal server error",
                status_code=500,
                request_id=request_id,
            )
            response = JSONResponse(
                status_code=500,
                content=body.model_dump(),
            )
            await response(scope, receive, send)
