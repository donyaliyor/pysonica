"""API v1 router — add your domain routes here.

Example::

    from fastapi import APIRouter
    from app.api.deps import AsyncSessionDep

    items_router = APIRouter(prefix="/items", tags=["items"])

    @items_router.get("/")
    async def list_items(db: AsyncSessionDep):
        ...

    # Then include in this router:
    router.include_router(items_router)
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# Include domain routers below:
# router.include_router(items_router)
# router.include_router(orders_router)
