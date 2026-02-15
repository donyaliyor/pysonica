# =============================================================================
# Makefile — self-documenting developer interface
#
# Usage: make <target>
# Run `make` or `make help` to see all targets.
# =============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash
.ONESHELL:

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
PYTHON := uv run python
PYTEST := uv run pytest
APP_MODULE := app.main:create_app
SRC_DIRS := src tests

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

.PHONY: install
install: ## Install all dependencies (runtime + dev)
	uv sync

.PHONY: dev
dev: ## Run the dev server with auto-reload
	uv run uvicorn $(APP_MODULE) --factory --reload --host 0.0.0.0 --port 8000

.PHONY: cli
cli: ## Run the CLI (pass ARGS, e.g., make cli ARGS="db-check")
	uv run app-cli $(ARGS)

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

.PHONY: fmt
fmt: ## Format code (ruff format + isort)
	uv run ruff format $(SRC_DIRS)
	uv run ruff check --fix --select I $(SRC_DIRS)

.PHONY: lint
lint: ## Run all linters (ruff + pyright)
	uv run ruff check $(SRC_DIRS)
	uv run ruff format --check $(SRC_DIRS)
	uv run pyright src

.PHONY: typecheck
typecheck: ## Run both type checkers (pyright + mypy)
	uv run pyright src
	uv run mypy src

.PHONY: lint-imports
lint-imports: ## Check import-linter contracts (Goal B enforcement)
	uv run lint-imports

.PHONY: check
check: lint typecheck lint-imports ## Run all static checks

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

.PHONY: test
test: ## Run tests (excludes slow tests)
	$(PYTEST) -m "not slow"

.PHONY: test-all
test-all: ## Run all tests including slow ones
	$(PYTEST)

.PHONY: test-unit
test-unit: ## Run unit tests only
	$(PYTEST) -m unit

.PHONY: test-integration
test-integration: ## Run integration tests only
	$(PYTEST) -m integration

.PHONY: test-migrations
test-migrations: ## Run migration stairway test
	$(PYTEST) tests/migrations/ -m slow

.PHONY: coverage
coverage: ## Run tests with coverage report
	$(PYTEST) -m "not slow" --cov --cov-report=term-missing --cov-report=html

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

.PHONY: db-up
db-up: ## Start PostgreSQL via Docker Compose
	docker compose up -d postgres

.PHONY: db-down
db-down: ## Stop PostgreSQL
	docker compose down

.PHONY: db-reset
db-reset: ## Stop PostgreSQL and delete data volume
	docker compose down -v

.PHONY: db-migrate
db-migrate: ## Run all pending migrations
	uv run alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback one migration
	uv run alembic downgrade -1

.PHONY: db-revision
db-revision: ## Create a new migration (pass MSG, e.g., make db-revision MSG="add users table")
	uv run alembic revision --autogenerate -m "$(MSG)"

.PHONY: db-check
db-check: ## Verify database connectivity via CLI
	uv run app-cli db-check

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

.PHONY: docker-build
docker-build: ## Build the Docker image
	docker build -t pysonica .

.PHONY: docker-run
docker-run: ## Run the full stack (app + postgres)
	docker compose up --build

.PHONY: docker-down
docker-down: ## Tear down the full stack
	docker compose down

# ---------------------------------------------------------------------------
# CI (mirrors GitHub Actions pipeline)
# ---------------------------------------------------------------------------

.PHONY: ci
ci: check test ## Run the full CI pipeline locally (lint + typecheck + test)

.PHONY: ci-full
ci-full: check test-all ## Run extended CI (includes slow tests)

.PHONY: audit
audit: ## Audit dependencies for known vulnerabilities
	uv run pip-audit

# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------

.PHONY: bump
bump: ## Bump version (pass PART=patch|minor|major, default: patch)
	uv run cz bump --$(or $(PART),patch)

.PHONY: changelog
changelog: ## Generate CHANGELOG.md from conventional commits
	uv run cz changelog

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove ALL auto-generated files (.venv, caches, build artifacts)
	rm -rf .venv
	rm -rf .pytest_cache .mypy_cache .ruff_cache .pyright .import_linter_cache
	rm -rf htmlcov .coverage coverage.xml
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true