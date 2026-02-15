# =============================================================================
# Multi-stage Dockerfile — Python 3.12 + uv
#
# Build:  docker build -t app .
# Run:    docker run -p 8000:8000 --env-file .env app
#
# Pattern: astral-sh/uv-docker-example (multistage.Dockerfile)
#
# Key decisions:
#   - python:3.12-slim base (~150 MB vs ~1 GB full)
#   - Multi-stage: builder installs deps, runtime copies only .venv
#   - Bind mounts for lockfile/pyproject in builder (better layer caching
#     than COPY — files don't persist in builder layer)
#   - UV_PYTHON_DOWNLOADS=0: forces system interpreter in both stages,
#     preventing symlink-to-managed-Python breakage in runtime stage
#   - --no-editable: embeds project in .venv so source isn't needed at runtime
#   - Non-root user (appuser) for defense in depth
#   - Exec form CMD: SIGTERM reaches uvicorn directly
#   - Single process: K8s scales via pods, not Gunicorn workers
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — install dependencies with uv
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS builder

# Pin uv version for reproducible builds. Update via dependabot.
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_NO_DEV=1

WORKDIR /app

# Layer 1: Install dependencies only.
# Bind-mount lockfile + pyproject.toml instead of COPY — they don't persist
# in the builder layer, and changes to app code don't invalidate this layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Layer 2: Copy application source and install the project itself.
# --no-editable embeds the project into .venv/lib so source code
# is NOT needed in the runtime image.
COPY src/ src/
COPY pyproject.toml uv.lock README.md ./
COPY alembic.ini ./
COPY migrations/ migrations/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# ---------------------------------------------------------------------------
# Stage 2: Runtime — minimal image with .venv + migrations only
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS runtime

# Build-time metadata — set via: docker build --build-arg BUILD_VERSION=1.2.3
ARG BUILD_VERSION=0.1.0
ENV APP_VERSION=${BUILD_VERSION}

# Non-root user for defense in depth.
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/false --create-home appuser

WORKDIR /app

# Copy the virtual environment from builder (includes all deps + project).
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy Alembic config and migrations for runtime migration commands.
COPY --from=builder --chown=appuser:appuser /app/alembic.ini ./
COPY --from=builder --chown=appuser:appuser /app/migrations ./migrations/

# Ensure the venv's Python and scripts are on PATH.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

# Health check — uses the liveness endpoint.
# python -c with urllib is available in slim images without extra deps.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", \
         "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"]

# Exec form required: shell form wraps in /bin/sh, which swallows SIGTERM.
# Uvicorn single-process: K8s scales via pod replicas.
# --host 0.0.0.0: bind to all interfaces (required in containers).
# --port 8000: explicit (matches EXPOSE).
# --workers 1: single process (default, explicit for clarity).
#
# For Gunicorn + Uvicorn workers (VM deployments without K8s):
#   CMD ["gunicorn", "app.main:create_app()", "-k", "uvicorn.workers.UvicornWorker", \
#        "--bind", "0.0.0.0:8000", "--workers", "4"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]