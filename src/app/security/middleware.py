"""Security headers middleware — OWASP Top 10 #5: Security Misconfiguration.

Adds standard security headers to every HTTP response. Sensible defaults
for JSON APIs. Override per-header via constructor kwargs.

References:
    - https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
    - https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
    - https://owasp.org/www-project-secure-headers/
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_DEFAULT_HEADERS: dict[str, str] = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "X-XSS-Protection": "0",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware:
    """Pure ASGI middleware that sets OWASP-recommended security headers.

    Args:
        app: The ASGI application.
        content_security_policy: CSP directive. Default ``"default-src 'self'"``
            is appropriate for APIs. Frontends will need to customize.
        strict_transport_security: HSTS directive. Set to ``""`` to disable
            (e.g. local dev where reverse proxy handles TLS).
        custom_headers: Override or remove defaults. Empty string removes a header.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        content_security_policy: str = "default-src 'self'",
        strict_transport_security: str = "max-age=31536000; includeSubDomains",
        custom_headers: dict[str, str] | None = None,
    ) -> None:
        self.app = app
        self._headers: dict[str, str] = {**_DEFAULT_HEADERS}

        if content_security_policy:
            self._headers["Content-Security-Policy"] = content_security_policy
        if strict_transport_security:
            self._headers["Strict-Transport-Security"] = strict_transport_security

        if custom_headers:
            for key, value in custom_headers.items():
                if value:
                    self._headers[key] = value
                else:
                    self._headers.pop(key, None)

        self._raw_headers: list[tuple[bytes, bytes]] = [
            (k.lower().encode(), v.encode()) for k, v in self._headers.items()
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self._raw_headers)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
