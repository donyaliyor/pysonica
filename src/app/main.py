"""Application factory and lifespan management.

This is the **only** file that imports multiple infrastructure modules.
It reads configuration and passes values to each module's setup function,
keeping modules independent of each other (Goal B).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import router as v1_router
from app.api.version import router as version_router
from app.config import get_settings
from app.database import session_manager
from app.errors import register_exception_handlers
from app.health import create_health_router
from app.logging import AccessLogMiddleware, setup_logging
from app.security import SecurityHeadersMiddleware

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.log_json_format,
    )

    session_manager.init(
        url=settings.database_url.get_secret_value(),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_pool_overflow,
        echo=settings.debug,
    )

    await logger.ainfo(
        "startup",
        app_name=settings.app_name,
        environment=settings.environment,
        version=settings.version,
    )

    yield

    await session_manager.close()
    await logger.ainfo("shutdown")


async def _is_db_online() -> bool:
    """Health check condition — verifies the DB connection pool works."""
    async with session_manager.session() as db:
        await db.execute(text("SELECT 1"))
    return True


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    register_exception_handlers(app)

    # Middleware executes bottom-to-top: CorrelationId → Security → AccessLog
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(
        SecurityHeadersMiddleware,
        strict_transport_security=(
            "max-age=31536000; includeSubDomains" if settings.is_production else ""
        ),
    )
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(create_health_router(ready_conditions=[_is_db_online]))
    app.include_router(version_router)
    app.include_router(v1_router, prefix="/api/v1")

    return app
