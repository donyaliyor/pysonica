# resilience/

Retry with exponential backoff and full jitter for external service calls.

## Dependencies

```
tenacity>=9.0
```

## Public API

| Symbol | Description |
|---|---|
| `retry_on_transient()` | Decorator factory. Full jitter, 3 attempts, 60s max. All params overridable. |
| `TransientError` | Base exception — raise from infra code to trigger retries. |

## Integration

```python
from app.resilience import retry_on_transient, TransientError

@retry_on_transient()
async def call_payment_api(order_id: str) -> dict:
    try:
        resp = await client.post(url, json={"order_id": order_id})
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError as exc:
        raise TransientError("payment service unavailable") from exc
```

Skip the `TransientError` wrapping by passing exception types directly:

```python
@retry_on_transient(retry_on=(httpx.ConnectError, httpx.TimeoutException))
async def call_external_api() -> dict:
    ...
```

Error classification — what to retry vs. what to fail immediately:

| Retry (transient) | Don't retry (permanent) |
|---|---|
| Connection refused / reset | 400 Bad Request |
| Timeout | 401 Unauthorized |
| 429 Too Many Requests | 403 Forbidden |
| 500, 502, 503, 504 | 404 Not Found |
| DNS resolution failure | 409 Conflict |

## Extraction

Copy `resilience/` into your project. Single dependency: `tenacity`. Logging uses stdlib `logging.getLogger()` — automatically routed through structlog if `setup_logging()` has been called, works standalone otherwise.