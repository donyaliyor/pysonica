# errors/

Domain exception hierarchy, structured error responses, and global FastAPI exception handlers.

## Dependencies

```
fastapi>=0.115
pydantic>=2.10
structlog>=24.4       # for handler logging (optional — replace with stdlib logging)
```

## Public API

| Symbol | Description |
|---|---|
| `DomainError` | Base exception. Carries `status_code`, `detail`, `extra`. |
| `NotFoundError` | 404 — `raise NotFoundError("Order", order_id="abc")` |
| `ConflictError` | 409 |
| `ValidationError` | 422 (domain-level, not Pydantic) |
| `PermissionDeniedError` | 403 |
| `AuthenticationError` | 401 |
| `ErrorResponse` | Pydantic model: `{detail, status_code, request_id}` |
| `register_exception_handlers(app)` | Attach all handlers to FastAPI app. |

## Integration

**App factory**:

```python
from app.errors import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

**Domain code** (no HTTP imports needed):

```python
from app.errors import NotFoundError

async def get_order(order_id: str):
    order = await db.get(Order, order_id)
    if not order:
        raise NotFoundError("Order", order_id=order_id)
    return order
```

**Custom exceptions** — extend `DomainError`:

```python
class RateLimitExceeded(DomainError):
    status_code = 429
    detail = "Too many requests"
```

## Extraction

Copy `errors/` into your project. The only structlog dependency is in `handlers.py` — replace `structlog.get_logger()` with `logging.getLogger(__name__)` if not using structlog. Everything else is pure FastAPI + Pydantic.

## Design Notes

- `DomainError.extra` captures structured context for logging but is **never sent to clients**.
- Handler on `StarletteHTTPException` (parent class) catches all HTTP exceptions including FastAPI's `HTTPException`.
- `ErrorResponse.request_id` enables correlation between client error reports and server logs.
- `RequestValidationError` handler overrides FastAPI's default to return the same `ErrorResponse` shape.