"""Integration test fixtures — real DB with rollback isolation.

Rollback pattern:
    1. Begin an outer transaction on the real connection.
    2. Bind the test session to that connection.
    3. Route code calls commit() — commits the inner SAVEPOINT, not the outer txn.
    4. Fixture teardown rolls back the outer transaction — nothing persists.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.database import get_db
from app.main import create_app


@pytest.fixture
async def db_session(
    engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    """Yield a session wrapped in a transaction that rolls back at teardown."""
    async with engine.connect() as conn:
        txn = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        await conn.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await txn.rollback()


@pytest.fixture
async def db_session_with_savepoint_restart(
    engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    """Rollback session that restarts SAVEPOINTs after each commit.

    Use when route code under test calls session.commit() multiple times.
    """
    async with engine.connect() as conn:
        txn = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        await conn.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(
            sync_session: object,
            transaction: object,
        ) -> None:
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                conn.sync_connection.begin_nested()  # type: ignore[union-attr]

        try:
            yield session
        finally:
            await session.close()
            await txn.rollback()


@pytest.fixture
async def test_app(
    db_session: AsyncSession,
) -> AsyncIterator[FastAPI]:
    """FastAPI app with DB dependency overridden for rollback isolation."""
    app = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(
    test_app: FastAPI,
) -> AsyncIterator[httpx.AsyncClient]:
    """httpx.AsyncClient wired to the test app via ASGITransport."""
    transport = httpx.ASGITransport(app=test_app)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as ac:
        yield ac
