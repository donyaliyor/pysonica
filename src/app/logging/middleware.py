"""Pure ASGI access log middleware.

Logs method, path, status_code, duration_ms, and client_ip for every HTTP
request. Binds the correlation ID (from X-Request-ID header) into structlog
contextvars so all log lines within a request carry it automatically.

Pure ASGI implementation avoids BaseHTTPMiddleware limitations:
- contextvars propagate correctly in both directions
- streaming responses are not buffered in memory
- background tasks are not cancelled on client disconnect

References:
    - https://www.starlette.io/middleware/#pure-asgi-middleware
    - https://github.com/encode/starlette/discussions/2160
"""

from __future__ import annotations

import time

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class AccessLogMiddleware:
    """Log every HTTP request with method, path, status, and duration_ms.

    Binds ``request_id`` (from ``X-Request-ID`` / ``asgi-correlation-id``)
    into structlog contextvars for the duration of the request. All log
    lines emitted during request handling automatically include it.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=_extract_header(scope, b"x-request-id"),
        )

        status_code = 500
        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            await logger.ainfo(
                "request",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=_client_ip(scope),
            )


def _extract_header(scope: Scope, name: bytes) -> str:
    """Extract a single header value from ASGI scope."""
    headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
    for header_name, header_value in headers:
        if header_name == name:
            return header_value.decode("latin-1")
    return ""


def _client_ip(scope: Scope) -> str:
    """Resolve client IP, preferring X-Forwarded-For behind a reverse proxy."""
    forwarded = _extract_header(scope, b"x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client: tuple[str, int] | None = scope.get("client")
    if client:
        return client[0]
    return ""
