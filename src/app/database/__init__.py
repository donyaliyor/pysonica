"""Database module — independently extractable.

Public API:
    DatabaseSessionManager  — Async engine + session factory lifecycle manager.
    session_manager         — Module-level singleton instance.
    get_db                  — FastAPI dependency yielding session-per-request.
    AsyncSessionDep         — Annotated type for route signatures.
    Base                    — SQLAlchemy declarative base (with AsyncAttrs).
"""

from app.database.session import DatabaseSessionManager, session_manager
from app.database.types import AsyncSessionDep, Base, get_db

__all__ = [
    "AsyncSessionDep",
    "Base",
    "DatabaseSessionManager",
    "get_db",
    "session_manager",
]
