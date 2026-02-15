"""Version endpoint tests."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_version_endpoint(client: httpx.AsyncClient) -> None:
    response = await client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "pysonica"
    assert "version" in data
    assert "environment" in data
