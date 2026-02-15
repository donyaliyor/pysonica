"""Structlog pipeline configuration.

Routes ALL loggers (stdlib + third-party) through structlog processors so that
every log line — from SQLAlchemy, httpx, uvicorn, or application code — gets
consistent formatting and automatic correlation IDs.

Based on: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
Adapted: parameterized for Goal B extraction.
"""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import Processor


def setup_logging(
    *,
    log_level: str = "INFO",
    json_format: bool = False,
) -> None:
    """Configure structlog + stdlib logging integration.

    Args:
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: True → JSON lines (production). False → colored console (dev).

    This function is idempotent — safe to call in both lifespan and tests.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # format_exc_info converts exc_info tuples to strings. Only needed for
    # JSONRenderer — ConsoleRenderer handles exception rendering natively
    # with pretty printing and will warn if it receives pre-formatted strings.
    formatter_processors: list[Processor] = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
    ]
    if json_format:
        formatter_processors.append(structlog.processors.format_exc_info)
    formatter_processors.append(renderer)

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=formatter_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
