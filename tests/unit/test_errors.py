"""Error hierarchy unit tests."""

from __future__ import annotations

import pytest

from app.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

pytestmark = pytest.mark.unit


def test_domain_error_defaults() -> None:
    exc = DomainError()
    assert exc.status_code == 500
    assert exc.detail == "An unexpected error occurred."
    assert exc.extra == {}


def test_domain_error_custom() -> None:
    exc = DomainError("bad thing", status_code=418, request_id="abc")
    assert exc.status_code == 418
    assert exc.detail == "bad thing"
    assert exc.extra == {"request_id": "abc"}


def test_not_found_error_includes_resource_name() -> None:
    exc = NotFoundError("Order", order_id="abc-123")
    assert exc.status_code == 404
    assert "Order" in exc.detail
    assert exc.extra == {"order_id": "abc-123"}


def test_not_found_error_default_resource() -> None:
    exc = NotFoundError()
    assert "Resource" in exc.detail


@pytest.mark.parametrize(
    ("cls", "expected_status"),
    [
        (ConflictError, 409),
        (ValidationError, 422),
        (PermissionDeniedError, 403),
        (AuthenticationError, 401),
    ],
)
def test_exception_status_codes(
    cls: type[DomainError],
    expected_status: int,
) -> None:
    exc = cls("test")
    assert exc.status_code == expected_status
    assert isinstance(exc, DomainError)
