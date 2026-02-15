"""Structured logging module — independently extractable.

Public API:
    setup_logging        — Configure structlog + stdlib integration.
    AccessLogMiddleware  — Pure ASGI middleware for request timing and correlation.
"""

from app.logging.middleware import AccessLogMiddleware
from app.logging.setup import setup_logging

__all__ = ["AccessLogMiddleware", "setup_logging"]
