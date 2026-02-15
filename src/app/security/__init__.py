"""Security module — independently extractable.

Public API:
    SecurityHeadersMiddleware — Pure ASGI middleware adding OWASP security headers.
"""

from app.security.middleware import SecurityHeadersMiddleware

__all__ = ["SecurityHeadersMiddleware"]
