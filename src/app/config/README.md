# config/

Pydantic Settings with cached singleton, environment-based configuration, and `SecretStr` for sensitive values.

## Dependencies

```
pydantic>=2.10
pydantic-settings>=2.7
python-dotenv>=1.0
```

## Public API

| Symbol | Description |
|---|---|
| `Settings` | `BaseSettings` subclass. All fields have defaults — starts with zero config. |
| `get_settings()` | `@lru_cache` singleton. Returns the same `Settings` instance on every call. |

## Usage

**FastAPI dependency injection:**

```python
from app.config import Settings, get_settings
from fastapi import Depends

@router.get("/example")
async def example(settings: Settings = Depends(get_settings)):
    return {"app": settings.app_name}
```

**Lifespan (fail fast on bad config):**

```python
settings = get_settings()  # Raises ValidationError if env is invalid
```

**Tests — clear cache before overriding:**

```python
@pytest.fixture
def override_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

## Extraction

Copy `config/` into your project. Install the three dependencies. No other modules required.