from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.modules.access.models import User
from app.modules.catalog import service
from app.modules.catalog.schemas import (
    ExamProfileOut,
    SkillOut,
    SubjectOut,
    TaskBlueprintOut,
    TaskFamilyOut,
)

router = APIRouter(tags=["catalog"], route_class=EnvelopeRoute)


@router.get("/subjects", response_model=list[SubjectOut])
async def get_subjects(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SubjectOut]:
    return [SubjectOut.model_validate(s) for s in await service.list_subjects(db)]


@router.get("/subjects/{subject_code}/exams", response_model=list[ExamProfileOut])
async def get_exams(
    subject_code: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ExamProfileOut]:
    return [ExamProfileOut.model_validate(e) for e in await service.list_exams(db, subject_code)]


@router.get("/exam-profiles/{exam_code}/skills", response_model=list[SkillOut])
async def get_skills(
    exam_code: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SkillOut]:
    return [SkillOut.model_validate(s) for s in await service.list_skills(db, exam_code)]


@router.get("/skills/{skill_id}/task-families", response_model=list[TaskFamilyOut])
async def get_task_families(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TaskFamilyOut]:
    families = await service.list_task_families(db, skill_id)
    return [TaskFamilyOut.model_validate(f) for f in families]


@router.get("/task-families/{task_family_id}/blueprints", response_model=list[TaskBlueprintOut])
async def get_blueprints(
    task_family_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TaskBlueprintOut]:
    blueprints = await service.list_blueprints(db, task_family_id)
    return [TaskBlueprintOut.model_validate(b) for b in blueprints]
