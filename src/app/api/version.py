"""/version endpoint — ops can verify what's deployed."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SettingsDep

router = APIRouter(tags=["ops"])


@router.get("/version")
async def version(settings: SettingsDep) -> dict[str, str]:
    """Return application version and environment."""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }
