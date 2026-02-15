"""Health check endpoints — K8s liveness and readiness probes.

- ``/health/live`` — always 200 if the process is running (liveness).
- ``/health/ready`` — 200 only if all conditions pass (readiness).

K8s usage::

    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import APIRouter, Response

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

HealthCondition = Callable[[], Awaitable[bool]]

_DEFAULT_CHECK_TIMEOUT: float = 5.0


def create_health_router(
    *,
    ready_conditions: list[HealthCondition] | None = None,
    check_timeout: float = _DEFAULT_CHECK_TIMEOUT,
) -> APIRouter:
    """Build a health router with the given readiness conditions.

    Args:
        ready_conditions: Async callables returning True if healthy.
            All must pass for ``/health/ready`` to return 200.
        check_timeout: Seconds before a single check is considered failed.
    """
    router = APIRouter(prefix="/health", tags=["health"])
    conditions = ready_conditions or []

    @router.get("/live", status_code=200)
    async def liveness() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        """Liveness probe — process is running."""
        return {"status": "alive"}

    @router.get("/ready", status_code=200)
    async def readiness(response: Response) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Readiness probe — all conditions must pass."""
        results: dict[str, bool] = {}
        for condition in conditions:
            name = condition.__name__
            try:
                results[name] = await asyncio.wait_for(
                    condition(),
                    timeout=check_timeout,
                )
            except TimeoutError:
                await logger.awarning(
                    "readiness_check_timeout",
                    check=name,
                    timeout=check_timeout,
                )
                results[name] = False
            except Exception:
                await logger.aexception("readiness_check_failed", check=name)
                results[name] = False

        healthy = all(results.values()) if results else True
        if not healthy:
            response.status_code = 503

        return {
            "status": "ready" if healthy else "not_ready",
            "checks": results,
        }

    return router
