# database/

Async SQLAlchemy 2.0 session management with lifecycle control and FastAPI integration.

## Dependencies

```
sqlalchemy[asyncio]>=2.0
asyncpg>=0.30
alembic>=1.14
fastapi>=0.115        # for Depends() in get_db / AsyncSessionDep
```

## Public API

| Symbol | Description |
|---|---|
| `DatabaseSessionManager` | Manages async engine + session factory. Init at startup, close at shutdown. |
| `session_manager` | Module-level singleton instance. |
| `get_db()` | FastAPI dependency — yields session-per-request with auto-commit/rollback. |
| `AsyncSessionDep` | `Annotated[AsyncSession, Depends(get_db)]` — use in route signatures. |
| `Base` | SQLAlchemy `DeclarativeBase` with `AsyncAttrs` — extend for domain models. |

## Integration

**FastAPI lifespan**:

```python
from app.database import session_manager

async def lifespan(app):
    session_manager.init(url="postgresql+asyncpg://...", pool_size=5)
    yield
    await session_manager.close()
```

**Route code**:

```python
from app.database import AsyncSessionDep
from sqlalchemy import select

@router.get("/items")
async def list_items(db: AsyncSessionDep):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

**Batch/CLI** (no FastAPI):

```python
from app.database import session_manager

session_manager.init(url="postgresql+asyncpg://...")
async with session_manager.session() as db:
    await db.execute(...)
await session_manager.close()
```

## Test Isolation

The rollback pattern (implemented in `tests/integration/conftest.py`):

1. Begin an outer transaction on the real connection.
2. Bind the session to that connection.
3. Route code calls `commit()` — commits the inner savepoint, not the outer txn.
4. Fixture teardown rolls back the outer transaction — nothing persists.

Full-speed integration tests with real PostgreSQL and zero cleanup.

## Extraction

Copy `database/` into your project. Install the four dependencies. Call `session_manager.init(url=...)` at startup. If not using FastAPI, ignore `get_db` and `AsyncSessionDep` — use `session_manager.session()` directly.

## Design Notes

- `DatabaseSessionManager.init()` takes a **URL string**, not a Settings object — Goal B extraction-friendly.
- `expire_on_commit=False` — prevents lazy-load exceptions after commit in async code.
- `pool_pre_ping=True` — detects stale connections before queries fail.
- `pool_recycle=3600` — recycles connections hourly, preventing server-side timeout errors (e.g., AWS RDS 8-hour default).
- `Base` includes `AsyncAttrs` mixin — enables `await model.awaitable_attrs.relationship` for lazy-loaded attributes in async context.
- Module-level `session_manager` singleton is initialized explicitly in lifespan, not at import time — fail-fast, testable.