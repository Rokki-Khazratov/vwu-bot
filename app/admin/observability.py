"""Admin observability endpoints (ТЗ §26)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import AuditLogOut, LLMCallOut
from app.api.dependencies.admin import require_admin
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.modules.access.models import User
from app.modules.llm.models import LLMCall
from app.modules.system.audit import list_audit_logs

router = APIRouter(prefix="/admin", tags=["admin:observability"], route_class=EnvelopeRoute)


@router.get("/llm-calls", response_model=list[LLMCallOut])
async def llm_calls(
    purpose: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[LLMCallOut]:
    stmt = select(LLMCall).order_by(LLMCall.created_at.desc()).limit(limit)
    if purpose:
        stmt = stmt.where(LLMCall.purpose == purpose)
    rows = (await db.execute(stmt)).scalars().all()
    return [LLMCallOut.model_validate(c) for c in rows]


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def audit_logs(
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AuditLogOut]:
    rows = await list_audit_logs(db, entity_type=entity_type, limit=limit)
    return [AuditLogOut.model_validate(a) for a in rows]
