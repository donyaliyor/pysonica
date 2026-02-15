"""Shared API dependencies.

Add cross-cutting dependencies here — auth, rate limiting, tenant resolution.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.database import AsyncSessionDep

SettingsDep = Annotated[Settings, Depends(get_settings)]

__all__ = ["AsyncSessionDep", "SettingsDep"]
