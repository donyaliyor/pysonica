# Contributing

## Setup

```bash
git clone <repo-url> && cd <repo>
cp .env.example .env
make install
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
make db-up && make db-migrate
make ci
```

## Workflow

1. Branch from `main`.
2. Make changes. Pre-commit hooks run on `git commit`.
3. Run `make ci` before pushing.
4. Open a PR. Fill in the template.
5. CI must pass. Get a review. Squash-merge.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) enforced by commitizen.

```
feat: add user registration endpoint
fix: handle null email in profile update
refactor: extract retry logic to resilience module
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`, `style`, `build`.

## Code Standards

- **Type hints on everything.** No `Any` unless unavoidable.
- **Tests required.** Business logic → unit tests. Endpoints → integration tests. 80%+ coverage.
- **No cross-module imports.** See [ADR-001](docs/adr/001-no-cross-module-imports.md). `import-linter` enforces this.

## Adding a New Module

1. Create `src/app/<module>/` with `__init__.py`, implementation, `README.md`.
2. Accept configuration as **parameters** — no sibling imports.
3. Wire in `src/app/main.py`.
4. Add to import-linter contract in `pyproject.toml`.
5. Run `make lint-imports`.

## Migrations

```bash
make db-revision MSG="add orders table"   # Create
make db-migrate                           # Apply
make db-rollback                          # Rollback one
```

Every migration must have a working `downgrade()`. The stairway test verifies upgrade→downgrade→upgrade for every revision.

## Commands

| Command | What |
|---|---|
| `make dev` | Dev server with auto-reload |
| `make fmt` | Auto-format |
| `make check` | Lint + types + import-linter |
| `make test` | Tests (excludes slow) |
| `make ci` | Full CI pipeline locally |
| `make clean` | Remove all generated files |