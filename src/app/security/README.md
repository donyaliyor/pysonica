# security/

Pure ASGI middleware adding OWASP-recommended security headers to every response.

## Dependencies

```
starlette>=0.27       # or fastapi (includes starlette)
```

## Public API

| Symbol | Description |
|---|---|
| `SecurityHeadersMiddleware` | Pure ASGI middleware. Configurable via constructor kwargs. |

## Default Headers

| Header | Value | Prevents |
|---|---|---|
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME-type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` | Unnecessary browser features |
| `X-XSS-Protection` | `0` | Disable broken XSS auditor (OWASP recommendation) |
| `Cache-Control` | `no-store` | Cached sensitive data |
| `Content-Security-Policy` | `default-src 'self'` | XSS, injection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Downgrade attacks |

## Integration

```python
from app.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

Customize:

```python
app.add_middleware(
    SecurityHeadersMiddleware,
    strict_transport_security="",  # disable HSTS in local dev
    custom_headers={"Permissions-Policy": "camera=(self)"},
)
```

Remove a default header — pass empty string:

```python
app.add_middleware(
    SecurityHeadersMiddleware,
    custom_headers={"Cache-Control": ""},
)
```

## Extraction

Copy `security/` into any Starlette or FastAPI project. Single dependency: `starlette`.