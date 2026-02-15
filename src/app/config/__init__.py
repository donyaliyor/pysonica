"""Configuration module — independently extractable.

Public API:
    Settings      — Pydantic BaseSettings with all app configuration.
    get_settings  — Cached factory returning the singleton Settings instance.
"""

from app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
