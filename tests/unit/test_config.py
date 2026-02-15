"""Config module unit tests."""

from __future__ import annotations

import pytest

from app.config import Settings, get_settings

pytestmark = pytest.mark.unit


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "pysonica"
    assert settings.version == "0.1.0"
    assert settings.environment == "local"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.log_json_format is False
    assert settings.database_pool_size == 5
    assert settings.database_pool_overflow == 10


def test_is_production_false_by_default() -> None:
    settings = Settings()
    assert settings.is_production is False


def test_is_production_true_when_production() -> None:
    settings = Settings(environment="production")
    assert settings.is_production is True


def test_database_url_is_secret() -> None:
    settings = Settings()
    plain = str(settings.database_url)
    assert "postgres" not in plain
    assert "**" in plain


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()
    try:
        first = get_settings()
        second = get_settings()
        assert first is second
    finally:
        get_settings.cache_clear()
