"""Health endpoint tests."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_liveness_returns_200(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


async def test_readiness_returns_200_when_db_is_up(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
