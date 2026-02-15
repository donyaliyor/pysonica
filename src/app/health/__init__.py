"""Health check module — independently extractable.

Public API:
    create_health_router  — Factory returning an APIRouter with
                            /health/live and /health/ready.
    HealthCondition       — Type alias for async check callables.
"""

from app.health.routes import HealthCondition, create_health_router

__all__ = ["HealthCondition", "create_health_router"]
