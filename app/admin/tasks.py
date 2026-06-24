"""Admin task endpoints (ТЗ §26).

Phase 1 reuses the allowlist auth dependency; a dedicated admin credential is
added in Phase 6.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import TaskNotFound
from app.modules.access.models import User
from app.modules.llm.factory import get_llm_provider
from app.modules.llm.provider import LLMProvider
from app.modules.tasks import repository as repo
from app.modules.tasks.generation import generate_tasks
from app.modules.tasks.schemas import ActivateResponse, BatchGenerateRequest, TaskInstanceOut

router = APIRouter(prefix="/admin/tasks", tags=["admin:tasks"], route_class=EnvelopeRoute)


@router.post("/batch-generate", response_model=list[TaskInstanceOut])
async def batch_generate(
    payload: BatchGenerateRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    _: User = Depends(get_current_user),
) -> list[TaskInstanceOut]:
    tasks = await generate_tasks(
        db, provider,
        blueprint_code=payload.blueprint_code,
        count=payload.count,
        difficulty=payload.difficulty,
    )
    return [TaskInstanceOut.model_validate(t) for t in tasks]


@router.get("", response_model=list[TaskInstanceOut])
async def list_tasks(
    blueprint_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TaskInstanceOut]:
    tasks = await repo.list_tasks(db, blueprint_code=blueprint_code, status=status)
    return [TaskInstanceOut.model_validate(t) for t in tasks]


@router.post("/{task_id}/activate", response_model=ActivateResponse)
async def activate(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ActivateResponse:
    task = await repo.get_task(db, task_id)
    if task is None:
        raise TaskNotFound()
    task.status = "active"
    await db.flush()
    return ActivateResponse(id=task.id, status=task.status)
