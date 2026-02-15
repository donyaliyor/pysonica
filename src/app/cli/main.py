"""CLI entry point — batch processing, admin tasks, health checks.

Exit codes:
    0 — Success.
    1 — Application error (bad input, domain logic failure).
    2 — Infrastructure error (DB down, network timeout). Retryable.
"""

from __future__ import annotations

import signal
from types import FrameType

import structlog
import typer

from app.config import get_settings
from app.logging import setup_logging

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

cli = typer.Typer(
    name="app-cli",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

EXIT_SUCCESS = 0
EXIT_APP_ERROR = 1
EXIT_INFRA_ERROR = 2


def _handle_sigterm(_signum: int, _frame: FrameType | None) -> None:
    """Raise SystemExit on SIGTERM for clean shutdown.

    Signal handlers must be reentrant — only async-signal-safe operations
    are permitted. Logging here risks deadlock if the handler fires while
    the logger holds its lock. ``raise SystemExit`` is safe.
    """
    raise SystemExit(EXIT_INFRA_ERROR)


@cli.callback()
def _setup(ctx: typer.Context) -> None:  # pyright: ignore[reportUnusedFunction]
    """Shared setup for all CLI commands."""
    signal.signal(signal.SIGTERM, _handle_sigterm)

    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        json_format=settings.log_json_format,
    )

    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


@cli.command()
def db_check(ctx: typer.Context) -> None:
    """Verify database connectivity."""
    import asyncio

    from sqlalchemy import text

    from app.database import session_manager

    settings = ctx.obj["settings"]

    async def _check() -> None:
        session_manager.init(url=settings.database_url.get_secret_value())
        try:
            async with session_manager.session() as db:
                await db.execute(text("SELECT 1"))
            logger.info("db_check_ok")
        finally:
            await session_manager.close()

    try:
        asyncio.run(_check())
    except Exception as exc:
        logger.exception("db_check_failed")
        typer.echo(f"Database check failed: {exc}", err=True)
        raise SystemExit(EXIT_INFRA_ERROR) from exc
