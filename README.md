# pysonica

Production-ready Python infrastructure boilerplate. Clone, rename `app/`, start building.

Every module is independently extractable — copy `logging/` into an existing Django monolith and have structured logging running in an afternoon.

## Modules

| Module | Purpose | Key Deps |
|---|---|---|
| `config/` | Pydantic Settings, env vars, `.env` | pydantic-settings |
| `logging/` | Structured logging, correlation IDs, access logs | structlog, asgi-correlation-id |
| `database/` | Async SQLAlchemy 2.0, session management, migrations | SQLAlchemy, asyncpg, Alembic |
| `errors/` | Exception hierarchy, global handlers, ErrorResponse | FastAPI |
| `health/` | `/health/live` + `/health/ready` with composable checks | FastAPI |
| `security/` | OWASP security headers middleware | Starlette |
| `resilience/` | Retry with exponential backoff + full jitter | tenacity |

**Not included** (by design): auth, rate limiting, pagination, caching, background jobs, K8s manifests.

## Quickstart

```bash
git clone <repo-url> my-project && cd my-project
cp .env.example .env
make install
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
make db-up && make db-migrate
make dev        # → http://localhost:8000/docs
make test       # → run tests
make ci         # → full CI pipeline locally
```

## Architecture

```
src/app/
├── config/       ─┐
├── logging/       │
├── database/      ├── Independent modules (zero sibling imports)
├── errors/        │
├── health/        │
├── security/      │
├── resilience/   ─┘
├── main.py        ← Only file that wires modules together
├── api/           ← Route skeleton
└── cli/           ← CLI entry point
```

**Core rule: no cross-module imports.** Modules accept configuration as parameters, not by importing siblings. Enforced by `import-linter` in CI. See [ADR-001](docs/adr/001-no-cross-module-imports.md).

## Extracting a Module

1. Copy `src/app/<module>/` into your project.
2. Install deps listed in the module's `README.md`.
3. Call the setup function with your config values.

No other modules required. No surgery.

## Commands

```
make help           # Show all targets
make dev            # Dev server with auto-reload
make fmt            # Auto-format
make check          # Lint + type check + import-linter
make test           # Tests (excludes slow)
make ci             # Full CI pipeline locally
make db-up          # Start PostgreSQL
make db-migrate     # Run migrations
make clean          # Remove all generated files
```

## Testing

Real PostgreSQL with rollback isolation — each test runs in a transaction that rolls back. Fast, realistic, no cleanup.

Marks: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`.

## Deployment

```bash
docker build -t app --build-arg BUILD_VERSION=$(git describe --tags) .
docker compose up          # Full stack
```

Multi-stage build, non-root user, exec form CMD, health check included. See [Dockerfile](Dockerfile).

## Quality Gates

| When | What | Tools |
|---|---|---|
| Seconds (pre-commit) | Format, lint, types, secrets, commit msg | ruff, pyright, detect-secrets, commitizen |
| Minutes (CI) | Tests, coverage, types, architecture, CVEs | pytest, import-linter, pip-audit, trivy |
| Hours (review) | PR template, CODEOWNERS | GitHub |

## Stack

Python 3.12+ · FastAPI · Uvicorn · SQLAlchemy 2.0 (async) · asyncpg · Alembic · Pydantic v2 · structlog · tenacity · typer · uv · ruff · pyright · mypy · pytest · Docker · GitHub Actions