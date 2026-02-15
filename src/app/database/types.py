"""Database type aliases and declarative base.

Centralizes SQLAlchemy type imports so that application code doesn't need
direct SQLAlchemy dependencies for type annotations.

Usage in route code::

    from app.database import AsyncSessionDep

    @router.get("/items")
    async def list_items(db: AsyncSessionDep):
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.database.session import session_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session-per-request with auto-commit/rollback."""
    async with session_manager.session() as session:
        yield session


AsyncSessionDep = Annotated[AsyncSession, Depends(get_db)]


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy declarative base for all domain models.

    Includes ``AsyncAttrs`` mixin so that lazy-loaded relationships and
    deferred columns can be accessed as awaitables in async code::

        # Instead of triggering MissingGreenlet:
        children = await parent.awaitable_attrs.children
    """
