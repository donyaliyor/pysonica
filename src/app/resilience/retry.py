"""Retry with exponential backoff and full jitter.

Defaults follow AWS best practices for contention avoidance:
    - Full Jitter outperforms equal jitter and decorrelated jitter.
    - Stop after 3 attempts OR 60 seconds (whichever comes first).
    - Only retry explicitly transient errors.
    - Log each retry via stdlib logger (routed through structlog if configured).

References:
    - https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    - https://tenacity.readthedocs.io/
"""

from __future__ import annotations

import logging
from typing import Any

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Base for errors that should trigger a retry.

    Raise from infrastructure code, or pass concrete exception types
    via ``retry_on`` to skip the wrapping step.
    """


def retry_on_transient(
    *,
    max_attempts: int = 3,
    max_delay_seconds: float = 60,
    wait_multiplier: float = 1,
    wait_max: float = 10,
    retry_on: type[Exception] | tuple[type[Exception], ...] = TransientError,
    **tenacity_kwargs: Any,
) -> Any:
    """Pre-configured retry decorator for external service calls.

    Args:
        max_attempts: Give up after this many tries (including the first).
        max_delay_seconds: Give up after this total elapsed time.
        wait_multiplier: Multiplier for exponential backoff base.
        wait_max: Cap on any single wait interval (seconds).
        retry_on: Exception types to retry on.
        **tenacity_kwargs: Passed through to ``tenacity.retry()``.
    """
    return retry(
        wait=wait_random_exponential(multiplier=wait_multiplier, max=wait_max),
        stop=stop_after_attempt(max_attempts) | stop_after_delay(max_delay_seconds),
        retry=retry_if_exception_type(retry_on),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
        **tenacity_kwargs,
    )
