"""Resilience module unit tests."""

from __future__ import annotations

import pytest

from app.resilience import TransientError, retry_on_transient

pytestmark = pytest.mark.unit


async def test_retry_succeeds_on_first_attempt() -> None:
    call_count = 0

    @retry_on_transient()
    async def succeeds() -> str:
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await succeeds()
    assert result == "ok"
    assert call_count == 1


async def test_retry_retries_on_transient_error() -> None:
    call_count = 0

    @retry_on_transient(max_attempts=3)
    async def fails_then_succeeds() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("transient")
        return "ok"

    result = await fails_then_succeeds()
    assert result == "ok"
    assert call_count == 3


async def test_retry_raises_after_max_attempts() -> None:
    @retry_on_transient(max_attempts=2, wait_max=0.01)
    async def always_fails() -> None:
        raise TransientError("permanent transient")

    with pytest.raises(TransientError, match="permanent transient"):
        await always_fails()


async def test_retry_does_not_retry_non_transient() -> None:
    call_count = 0

    @retry_on_transient()
    async def raises_value_error() -> None:
        nonlocal call_count
        call_count += 1
        msg = "not transient"
        raise ValueError(msg)

    with pytest.raises(ValueError, match="not transient"):
        await raises_value_error()
    assert call_count == 1


async def test_retry_custom_exception_type() -> None:
    call_count = 0

    @retry_on_transient(max_attempts=3, retry_on=ConnectionError)
    async def fails_with_connection_error() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError
        return "ok"

    result = await fails_with_connection_error()
    assert result == "ok"
    assert call_count == 2
