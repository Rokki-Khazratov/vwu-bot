"""Health endpoints (ТЗ §35)."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute

router = APIRouter(prefix="/health", tags=["health"], route_class=EnvelopeRoute)


@router.get("/live")
async def live() -> dict:
    return {"status": "alive"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}
