"""Root test configuration.

Hierarchy:
    tests/conftest.py              ← this file (engine, settings, session_manager)
    tests/unit/conftest.py         ← no fixtures needed
    tests/integration/conftest.py  ← real DB, rollback session, AsyncClient
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings
from app.database import session_manager
from app.logging import setup_logging


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    get_settings.cache_clear()
    settings = get_settings()
    return settings


@pytest.fixture(scope="session", autouse=True)
def _configure_logging(test_settings: Settings) -> None:
    setup_logging(log_level="DEBUG", json_format=False)


@pytest.fixture(scope="session")
def engine(test_settings: Settings) -> AsyncEngine:
    """Session-scoped async engine with NullPool.

    NullPool creates a fresh connection for each ``engine.connect()`` call
    in whatever event loop is current. This avoids cross-loop errors when
    a session-scoped engine is used by function-scoped async fixtures
    running in different event loops (pytest-asyncio 0.26+).
    """
    return create_async_engine(
        test_settings.database_url.get_secret_value(),
        poolclass=NullPool,
    )


@pytest.fixture(scope="session")
def async_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _init_session_manager(test_settings: Settings) -> None:
    """Initialize the global session_manager for health check conditions.

    Uses NullPool for the same cross-loop compatibility reason as the
    ``engine`` fixture. Integration tests override ``get_db`` via
    ``dependency_overrides``, but health check conditions (e.g.,
    ``_is_db_online``) use ``session_manager`` directly.
    """
    session_manager.init(
        url=test_settings.database_url.get_secret_value(),
        pool_class=NullPool,
    )
