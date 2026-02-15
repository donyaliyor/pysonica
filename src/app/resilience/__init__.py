"""Resilience module — independently extractable.

Public API:
    retry_on_transient — Pre-configured retry decorator for external calls.
    TransientError     — Base exception class for retryable errors.
"""

from app.resilience.retry import TransientError, retry_on_transient

__all__ = ["TransientError", "retry_on_transient"]
