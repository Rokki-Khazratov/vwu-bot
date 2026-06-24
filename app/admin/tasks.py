"""Admin task endpoints (ТЗ §26).

Phase 2 reuses the allowlist auth dependency (require_admin); a dedicated admin
credential is added in Phase 6.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import TaskPatchRequest
from app.api.dependencies.admin import require_admin
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import TaskNotFound
from app.modules.access.models import User
from app.modules.llm.factory import get_llm_provider
from app.modules.llm.provider import LLMProvider
from app.modules.system.audit import record_audit
from app.modules.tasks import repository as repo
from app.modules.tasks.generation import generate_tasks
from app.modules.tasks.schemas import ActivateResponse, BatchGenerateRequest, TaskInstanceOut

router = APIRouter(prefix="/admin/tasks", tags=["admin:tasks"], route_class=EnvelopeRoute)


@router.post("/batch-generate", response_model=list[TaskInstanceOut])
async def batch_generate(
    payload: BatchGenerateRequest,
    db: AsyncSession = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    _: User = Depends(require_admin),
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
    _: User = Depends(require_admin),
) -> list[TaskInstanceOut]:
    tasks = await repo.list_tasks(db, blueprint_code=blueprint_code, status=status)
    return [TaskInstanceOut.model_validate(t) for t in tasks]


async def _set_status(
    db: AsyncSession, task_id: uuid.UUID, status: str, admin: User
) -> ActivateResponse:
    task = await repo.get_task(db, task_id)
    if task is None:
        raise TaskNotFound()
    before = task.status
    task.status = status
    await db.flush()
    await record_audit(
        db, actor_user_id=admin.id, action=f"task_{status}",
        entity_type="task", entity_id=str(task.id),
        before={"status": before}, after={"status": status},
    )
    return ActivateResponse(id=task.id, status=task.status)


@router.post("/{task_id}/activate", response_model=ActivateResponse)
async def activate(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ActivateResponse:
    return await _set_status(db, task_id, "active", admin)


@router.post("/{task_id}/reject", response_model=ActivateResponse)
async def reject(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ActivateResponse:
    return await _set_status(db, task_id, "rejected", admin)


@router.patch("/{task_id}", response_model=TaskInstanceOut)
async def patch_task(
    task_id: uuid.UUID,
    payload: TaskPatchRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TaskInstanceOut:
    task = await repo.get_task(db, task_id)
    if task is None:
        raise TaskNotFound()
    changes = payload.model_dump(exclude_none=True)
    before = {k: getattr(task, k) for k in changes}
    for key, value in changes.items():
        setattr(task, key, value)
    await db.flush()
    await record_audit(
        db, actor_user_id=admin.id, action="task_update",
        entity_type="task", entity_id=str(task.id), before=before, after=changes,
    )
    return TaskInstanceOut.model_validate(task)
