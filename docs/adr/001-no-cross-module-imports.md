# ADR-001: No Cross-Module Imports

**Status:** Accepted
**Date:** 2025-01-01

## Context

This repo serves two goals:

- **Goal A** — standalone starter for new Python projects.
- **Goal B** — extraction kit where each module can be copied into an existing codebase independently.

Goal B requires that no infrastructure module depends on a sibling. If `logging/` imports from `config/`, extracting `logging/` forces you to also extract `config/`.

## Decision

**Infrastructure modules must not import from each other.** Only wiring files may import multiple modules.

### Rules

1. `config/`, `logging/`, `database/`, `errors/`, `health/`, `security/`, `resilience/` have zero sibling imports.
2. Only `main.py` and `tests/conftest.py` wire modules together.
3. Modules accept configuration as function parameters (strings, bools, callables), never by importing a Settings object.
4. `import-linter` enforces this in CI. Violations fail the build.

### Example

```python
# WRONG — logging/ imports config/
from app.config import get_settings
def setup_logging():
    settings = get_settings()

# RIGHT — logging/ accepts parameters
def setup_logging(*, log_level: str = "INFO", json_output: bool = False) -> None:
    ...

# Wiring in main.py
settings = get_settings()
setup_logging(log_level=settings.log_level, json_output=settings.log_json_format)
```

## Consequences

**Positive:** Any module extracts by copying its directory + installing listed deps. Flat dependency graph. Modules testable in isolation.

**Negative:** `main.py` has repetitive parameter passing (intentional — explicit > implicit). Some type duplication across modules.

## Enforcement

```toml
[tool.importlinter]
root_packages = ["app"]

[[tool.importlinter.contracts]]
name = "Infrastructure modules are independent"
type = "independence"
modules = [
    "app.config", "app.logging", "app.database", "app.errors",
    "app.health", "app.security", "app.resilience",
]
```