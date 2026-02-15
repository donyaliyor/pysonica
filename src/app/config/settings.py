"""Application settings via pydantic-settings.

Resolution order (highest priority first):
    init kwargs → environment variables → .env file → secrets directory → field defaults
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        # Accept extra env vars injected by orchestrators (K8s, Docker, systemd).
        extra="ignore",
    )

    # App
    app_name: str = "pysonica"
    debug: bool = False
    version: str = "0.1.0"
    environment: Literal["local", "staging", "production"] = "local"

    # Database
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    )
    database_pool_size: int = 5
    database_pool_overflow: int = 10

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json_format: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton. In tests, call ``get_settings.cache_clear()`` first."""
    return Settings()
