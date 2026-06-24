from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.modules.access.models import User
from app.modules.statistics import service

router = APIRouter(prefix="/statistics", tags=["statistics"], route_class=EnvelopeRoute)


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await service.overview(db, user.id)


@router.get("/criteria")
async def criteria(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await service.criterion_trends(db, user.id)


@router.get("/errors")
async def errors(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await service.error_trends(db, user.id)


@router.get("/weaknesses")
async def weaknesses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await service.weaknesses(db, user.id)
