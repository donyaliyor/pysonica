# logging/

Structured logging via structlog with stdlib integration. All loggers (application, SQLAlchemy, httpx, uvicorn) emit structured output with correlation IDs.

## Dependencies

```
structlog>=24.4
starlette>=0.27          # or fastapi (includes starlette)
```

Optional (for correlation IDs):

```
asgi-correlation-id>=4.3
```

## Public API

| Symbol | Description |
|---|---|
| `setup_logging(*, log_level, json_format)` | Configure structlog + stdlib pipeline. Call once at startup. |
| `AccessLogMiddleware` | Pure ASGI middleware — logs method, path, status_code, duration_ms, request_id per request. |

## Integration

**FastAPI lifespan**:

```python
from app.logging import setup_logging, AccessLogMiddleware
from asgi_correlation_id import CorrelationIdMiddleware

async def lifespan(app):
    setup_logging(log_level="INFO", json_format=True)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(CorrelationIdMiddleware)  # must be outermost
```

**Using structlog in application code**:

```python
import structlog

logger = structlog.get_logger()

async def create_order(order_id: str):
    await logger.ainfo("order_created", order_id=order_id)
    # Output includes request_id automatically via contextvars
```

## Extraction

Copy `logging/` into your project. Install structlog and starlette. Call `setup_logging()` at startup. Add `AccessLogMiddleware` to your ASGI app.

No other modules required.

## Design Notes

- `setup_logging()` accepts **parameters**, not a Settings object — Goal B extraction-friendly.
- `AccessLogMiddleware` is **pure ASGI** (no `BaseHTTPMiddleware`) — no response buffering, correct contextvars propagation, no background task cancellation.
- `foreign_pre_chain` ensures third-party stdlib loggers get the same processors.
- Uvicorn handlers are cleared and propagation enabled so all uvicorn logs flow through the structlog pipeline.
- `uvicorn.access` is suppressed — `AccessLogMiddleware` replaces it with structured output.
- `drop_color_message_key` strips uvicorn's `color_message` extra that pollutes JSON output.
- Correlation IDs flow via `structlog.contextvars` — zero coupling to any specific correlation ID library.