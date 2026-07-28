"""Admin API for role-based Markdown guidelines."""

from __future__ import annotations

import hashlib
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    GuidelineCreateRequest,
    GuidelineLinkRequest,
    GuidelineOut,
    LinkedGuidelineOut,
)
from app.api.dependencies.admin import require_admin
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import TaskNotFound
from app.modules.access.models import User
from app.modules.catalog.models import (
    Guideline,
    TaskBlueprint,
    TaskBlueprintGuideline,
    TaskInstanceGuideline,
)
from app.modules.system.audit import record_audit
from app.modules.tasks.models import TaskInstance

router = APIRouter(
    prefix="/admin/guidelines", tags=["admin:guidelines"], route_class=EnvelopeRoute
)


def _checksum(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


async def _linked_rows(db: AsyncSession, model, owner_field, owner_id: uuid.UUID) -> list[dict]:
    rows = await db.execute(
        select(model, Guideline)
        .join(Guideline, model.guideline_id == Guideline.id)
        .where(owner_field == owner_id)
        .order_by(model.position, Guideline.code)
    )
    return [
        {
            "id": link.id,
            "guideline_id": guideline.id,
            "code": guideline.code,
            "version": guideline.version,
            "role": link.role,
            "position": link.position,
            "include_in_generation": link.include_in_generation,
            "include_in_evaluation": link.include_in_evaluation,
        }
        for link, guideline in rows.all()
    ]


@router.post("", response_model=GuidelineOut)
async def create_guideline(
    payload: GuidelineCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> GuidelineOut:
    guideline = Guideline(
        code=payload.code,
        version=payload.version,
        default_role=payload.role,
        subject_id=payload.subject_id,
        subject_task_id=payload.subject_task_id,
        exam_profile_id=payload.exam_profile_id,
        skill_id=payload.skill_id,
        task_family_id=payload.task_family_id,
        frontmatter=payload.frontmatter or {},
        body_markdown=payload.body_markdown,
        checksum=_checksum(payload.body_markdown),
        status=payload.status,
    )
    db.add(guideline)
    await db.flush()
    await record_audit(
        db,
        actor_user_id=admin.id,
        action="guideline_create",
        entity_type="guideline",
        entity_id=str(guideline.id),
        after={
            "code": guideline.code,
            "version": guideline.version,
            "role": guideline.default_role,
        },
    )
    return GuidelineOut.model_validate(guideline)


@router.post("/blueprints/{blueprint_id}", response_model=LinkedGuidelineOut)
async def link_blueprint_guideline(
    blueprint_id: uuid.UUID,
    payload: GuidelineLinkRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> LinkedGuidelineOut:
    blueprint = await db.get(TaskBlueprint, blueprint_id)
    guideline = await db.get(Guideline, payload.guideline_id)
    if blueprint is None or guideline is None:
        raise TaskNotFound("Blueprint or guideline not found.")
    link = TaskBlueprintGuideline(blueprint_id=blueprint.id, **payload.model_dump())
    db.add(link)
    await db.flush()
    await record_audit(
        db,
        actor_user_id=admin.id,
        action="blueprint_guideline_link",
        entity_type="task_blueprint",
        entity_id=str(blueprint.id),
        after={"guideline_id": str(guideline.id), "role": link.role},
    )
    return LinkedGuidelineOut.model_validate(
        {
            "id": link.id,
            "guideline_id": guideline.id,
            "code": guideline.code,
            "version": guideline.version,
            "role": link.role,
            "position": link.position,
            "include_in_generation": link.include_in_generation,
            "include_in_evaluation": link.include_in_evaluation,
        }
    )


@router.get("/blueprints/{blueprint_id}", response_model=list[LinkedGuidelineOut])
async def list_blueprint_guidelines(
    blueprint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[LinkedGuidelineOut]:
    return [
        LinkedGuidelineOut.model_validate(row)
        for row in await _linked_rows(
            db, TaskBlueprintGuideline, TaskBlueprintGuideline.blueprint_id, blueprint_id
        )
    ]


@router.post("/tasks/{task_id}", response_model=LinkedGuidelineOut)
async def link_task_guideline(
    task_id: uuid.UUID,
    payload: GuidelineLinkRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> LinkedGuidelineOut:
    task = await db.get(TaskInstance, task_id)
    guideline = await db.get(Guideline, payload.guideline_id)
    if task is None or guideline is None:
        raise TaskNotFound("Task or guideline not found.")
    link = TaskInstanceGuideline(task_id=task.id, **payload.model_dump())
    db.add(link)
    await db.flush()
    await record_audit(
        db,
        actor_user_id=admin.id,
        action="task_guideline_link",
        entity_type="task",
        entity_id=str(task.id),
        after={"guideline_id": str(guideline.id), "role": link.role},
    )
    return LinkedGuidelineOut.model_validate(
        {
            "id": link.id,
            "guideline_id": guideline.id,
            "code": guideline.code,
            "version": guideline.version,
            "role": link.role,
            "position": link.position,
            "include_in_generation": link.include_in_generation,
            "include_in_evaluation": link.include_in_evaluation,
        }
    )


@router.get("/tasks/{task_id}", response_model=list[LinkedGuidelineOut])
async def list_task_guidelines(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[LinkedGuidelineOut]:
    return [
        LinkedGuidelineOut.model_validate(row)
        for row in await _linked_rows(
            db, TaskInstanceGuideline, TaskInstanceGuideline.task_id, task_id
        )
    ]
