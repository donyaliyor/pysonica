"""Global exception handlers — register once, catch everything.

Design:
    - ``DomainError`` → ``ExceptionMiddleware`` (Starlette's built-in handler routing).
    - ``StarletteHTTPException`` → ``ExceptionMiddleware`` (404, 405, etc.).
    - ``RequestValidationError`` → ``ExceptionMiddleware`` (422 with consistent shape).
    - Unhandled ``Exception`` → ``UnhandledExceptionMiddleware`` (pure ASGI middleware).

The catch-all uses a middleware instead of ``add_exception_handler(Exception, ...)``
because Starlette's routing of ``Exception`` handlers to ``ServerErrorMiddleware``
varies across versions. See ``errors/middleware.py`` for details.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.errors.exceptions import DomainError
from app.errors.middleware import UnhandledExceptionMiddleware
from app.errors.schemas import ErrorResponse

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app.

    Call once in ``create_app()`` / app factory::

        from app.errors import register_exception_handlers
        register_exception_handlers(app)

    Registers typed handlers on ``ExceptionMiddleware`` and adds
    ``UnhandledExceptionMiddleware`` for the catch-all 500 path.
    """
    app.add_exception_handler(DomainError, _handle_domain_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    # Catch-all for unhandled exceptions — added as middleware for
    # cross-version Starlette compatibility.
    app.add_middleware(UnhandledExceptionMiddleware)


def _get_request_id(request: Request) -> str:
    """Extract correlation ID from request headers."""
    return request.headers.get("x-request-id", "")


async def _handle_domain_error(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    """Map domain exceptions to structured HTTP responses."""
    logger.warning(
        "domain_error",
        error_type=type(exc).__name__,
        detail=exc.detail,
        status_code=exc.status_code,
        **exc.extra,
    )
    body = ErrorResponse(
        detail=exc.detail,
        status_code=exc.status_code,
        request_id=_get_request_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def _handle_http_error(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Catch-all for Starlette/FastAPI HTTP exceptions (404, 405, etc.)."""
    detail = str(exc.detail)
    body = ErrorResponse(
        detail=detail,
        status_code=exc.status_code,
        request_id=_get_request_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def _handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Pydantic request validation failures → 422 with structured response."""
    logger.warning("validation_error", errors=exc.errors())
    body = ErrorResponse(
        detail="Request validation failed",
        status_code=422,
        request_id=_get_request_id(request),
    )
    return JSONResponse(status_code=422, content=body.model_dump())
