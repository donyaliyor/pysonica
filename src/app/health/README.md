# health/

Kubernetes-style liveness and readiness probes with composable health conditions.

## Dependencies

```
fastapi>=0.115
structlog>=24.4       # for check failure logging (replace with stdlib if needed)
```

## Public API

| Symbol | Description |
|---|---|
| `create_health_router(*, ready_conditions, check_timeout)` | Factory returning `APIRouter` with `/health/live` and `/health/ready`. |
| `HealthCondition` | Type alias: `Callable[[], Awaitable[bool]]` |

## Integration

```python
from app.health import create_health_router
from sqlalchemy import text

async def is_db_online() -> bool:
    async with session_manager.session() as db:
        await db.execute(text("SELECT 1"))
    return True

health_router = create_health_router(
    ready_conditions=[is_db_online],
    check_timeout=5.0,  # seconds per check (default)
)
app.include_router(health_router)
```

Response shapes:

```
GET /health/live   → 200 {"status": "alive"}
GET /health/ready  → 200 {"status": "ready", "checks": {"is_db_online": true}}
GET /health/ready  → 503 {"status": "not_ready", "checks": {"is_db_online": false}}
```

## Extraction

Copy `health/` into your project. Replace `structlog.get_logger()` with `logging.getLogger(__name__)` if not using structlog. Conditions are plain async callables with no framework coupling.