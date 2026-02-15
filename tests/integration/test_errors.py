"""Error handler behavior tests.

Verifies that all exception types return the same ErrorResponse shape
and that stack traces are never exposed to clients.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import APIRouter, FastAPI

from app.errors import DomainError, NotFoundError
from app.errors.handlers import register_exception_handlers

pytestmark = pytest.mark.integration


def _create_error_app() -> FastAPI:
    """Minimal app with error handlers and routes that raise exceptions."""
    app = FastAPI()
    register_exception_handlers(app)

    router = APIRouter()

    @router.get("/raise-not-found")
    async def raise_not_found() -> None:
        raise NotFoundError("Order", order_id="abc-123")

    @router.get("/raise-domain")
    async def raise_domain() -> None:
        raise DomainError("Something went wrong", status_code=400)

    @router.get("/raise-unhandled")
    async def raise_unhandled() -> None:
        msg = "unexpected failure"
        raise RuntimeError(msg)

    @router.get("/raise-validation")
    async def raise_validation(required_param: int) -> dict[str, int]:
        return {"value": required_param}

    app.include_router(router)
    return app


@pytest.fixture
async def error_client() -> AsyncIterator[httpx.AsyncClient]:
    app = _create_error_app()
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as ac:
        yield ac


def _assert_error_response(data: dict[str, object], status_code: int) -> None:
    assert "detail" in data
    assert data["status_code"] == status_code
    assert "request_id" in data


async def test_not_found_error_returns_404(error_client: httpx.AsyncClient) -> None:
    response = await error_client.get("/raise-not-found")
    assert response.status_code == 404
    data = response.json()
    _assert_error_response(data, 404)
    assert "Order" in data["detail"]


async def test_domain_error_returns_custom_status(
    error_client: httpx.AsyncClient,
) -> None:
    response = await error_client.get("/raise-domain")
    assert response.status_code == 400
    _assert_error_response(data=response.json(), status_code=400)


async def test_unhandled_error_returns_500_without_traceback(
    error_client: httpx.AsyncClient,
) -> None:
    response = await error_client.get("/raise-unhandled")
    assert response.status_code == 500
    data = response.json()
    _assert_error_response(data, 500)
    assert "unexpected failure" not in data["detail"]
    assert "RuntimeError" not in data["detail"]
    assert "Traceback" not in data["detail"]


async def test_validation_error_returns_422(error_client: httpx.AsyncClient) -> None:
    response = await error_client.get("/raise-validation")
    assert response.status_code == 422
    data = response.json()
    _assert_error_response(data, 422)


async def test_404_for_nonexistent_route(error_client: httpx.AsyncClient) -> None:
    response = await error_client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    _assert_error_response(data, 404)
