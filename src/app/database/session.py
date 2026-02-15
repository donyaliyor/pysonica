"""Async database session management.

Based on: https://github.com/rhoboro/async-fastapi-sqlalchemy
Adapted: parameterized init (Goal B), explicit pool config, type hints.

Usage:
    # Lifespan
    session_manager = DatabaseSessionManager()
    session_manager.init(url="postgresql+asyncpg://...", pool_size=5)
    yield
    await session_manager.close()

    # Per-request (FastAPI Depends)
    async def get_db():
        async with session_manager.session() as session:
            yield session
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseSessionManager:
    """Manages async engine and session factory lifecycle.

    Designed for two contexts:
        - **Web**: session-per-request via :meth:`session` + ``Depends(get_db)``
        - **Batch/CLI**: session-per-task via :meth:`session` in a context manager

    The manager must be initialized before use and closed on shutdown.
    Calling :meth:`session` or :meth:`connect` before :meth:`init` raises
    :class:`RuntimeError`.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(
        self,
        url: str,
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        echo: bool = False,
        pool_class: type[Any] | None = None,
    ) -> None:
        """Create the async engine and session factory.

        Args:
            url: Database URL (``postgresql+asyncpg://...``).
            pool_size: Number of persistent connections in the pool.
            max_overflow: Additional connections allowed above pool_size.
            pool_pre_ping: Test connections before use (detects stale connections).
            echo: Log all SQL statements (noisy — use for debugging only).
            pool_class: SQLAlchemy pool class override (e.g., ``NullPool`` for tests).
                When set, ``pool_size`` and ``max_overflow`` are ignored.
        """
        engine_kwargs: dict[str, Any] = {
            "pool_pre_ping": pool_pre_ping,
            "echo": echo,
        }
        if pool_class is not None:
            engine_kwargs["poolclass"] = pool_class
        else:
            engine_kwargs["pool_size"] = pool_size
            engine_kwargs["max_overflow"] = max_overflow

        self._engine = create_async_engine(url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Dispose of the connection pool. Call in lifespan shutdown."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    def _check_init(self) -> None:
        if self._engine is None or self._sessionmaker is None:
            msg = "DatabaseSessionManager is not initialized. Call init() first."
            raise RuntimeError(msg)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield an async session. Commits on success, rolls back on exception."""
        self._check_init()
        assert self._sessionmaker is not None  # noqa: S101 — guarded by _check_init

        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Yield a raw async connection. For migrations and admin operations."""
        self._check_init()
        assert self._engine is not None  # noqa: S101 — guarded by _check_init

        async with self._engine.begin() as conn:
            yield conn

    @property
    def engine(self) -> AsyncEngine:
        """Access the engine directly. Raises RuntimeError if not initialized."""
        self._check_init()
        assert self._engine is not None  # noqa: S101 — guarded by _check_init
        return self._engine


# Module-level singleton — initialized in lifespan, used by get_db.
session_manager = DatabaseSessionManager()
