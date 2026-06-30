"""Admin CRUD for the academic catalog (ТЗ §26).

Create/update + deactivate (via is_active). Hard delete is intentionally omitted
in this phase to avoid breaking historical references; use the admin panel for
exceptional manual deletes.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalog_schemas import (
    BlueprintCreate,
    BlueprintUpdate,
    ExamProfileCreate,
    ExamProfileUpdate,
    SkillCreate,
    SkillUpdate,
    SubjectCreate,
    SubjectUpdate,
    TaskFamilyCreate,
    TaskFamilyUpdate,
)
from app.api.dependencies.admin import require_admin
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import TaskNotFound
from app.modules.access.models import User
from app.modules.catalog import service as catalog_service
from app.modules.catalog.models import (
    ExamProfile,
    Skill,
    Subject,
    TaskBlueprint,
    TaskFamily,
)
from app.modules.catalog.schemas import (
    ExamProfileOut,
    SkillOut,
    SubjectOut,
    TaskBlueprintOut,
    TaskFamilyOut,
)
from app.modules.system.audit import record_audit

router = APIRouter(prefix="/admin", tags=["admin:catalog"], route_class=EnvelopeRoute)


async def _get_or_404(db: AsyncSession, model, entity_id: uuid.UUID):
    obj = await db.get(model, entity_id)
    if obj is None:
        raise TaskNotFound(f"{model.__name__} not found.")
    return obj


async def _apply(db, obj, changes: dict, *, admin: User, action: str, entity_type: str):
    before = {k: getattr(obj, k) for k in changes}
    for key, value in changes.items():
        setattr(obj, key, value)
    await db.flush()
    await record_audit(
        db, actor_user_id=admin.id, action=action, entity_type=entity_type,
        entity_id=str(obj.id), before=before, after=changes,
    )
    return obj


# --- Subjects ---
@router.post("/subjects", response_model=SubjectOut)
async def create_subject(
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> SubjectOut:
    subject = Subject(**payload.model_dump())
    db.add(subject)
    await db.flush()
    await record_audit(db, actor_user_id=admin.id, action="subject_create",
                       entity_type="subject", entity_id=str(subject.id),
                       after=payload.model_dump())
    return SubjectOut.model_validate(subject)


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> SubjectOut:
    subject = await _get_or_404(db, Subject, subject_id)
    await _apply(db, subject, payload.model_dump(exclude_none=True),
                 admin=admin, action="subject_update", entity_type="subject")
    return SubjectOut.model_validate(subject)


# --- Exam profiles ---
@router.post("/exam-profiles", response_model=ExamProfileOut)
async def create_exam_profile(
    payload: ExamProfileCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ExamProfileOut:
    subject = await catalog_service.get_subject_by_code(db, payload.subject_code)
    data = payload.model_dump(exclude={"subject_code"})
    exam = ExamProfile(subject_id=subject.id, **data)
    db.add(exam)
    await db.flush()
    await record_audit(db, actor_user_id=admin.id, action="exam_profile_create",
                       entity_type="exam_profile", entity_id=str(exam.id), after=data)
    return ExamProfileOut.model_validate(exam)


@router.patch("/exam-profiles/{exam_id}", response_model=ExamProfileOut)
async def update_exam_profile(
    exam_id: uuid.UUID,
    payload: ExamProfileUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ExamProfileOut:
    exam = await _get_or_404(db, ExamProfile, exam_id)
    await _apply(db, exam, payload.model_dump(exclude_none=True),
                 admin=admin, action="exam_profile_update", entity_type="exam_profile")
    return ExamProfileOut.model_validate(exam)


# --- Skills ---
@router.post("/skills", response_model=SkillOut)
async def create_skill(
    payload: SkillCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> SkillOut:
    exam = await catalog_service.get_exam_by_code(db, payload.exam_profile_code)
    data = payload.model_dump(exclude={"exam_profile_code"})
    skill = Skill(exam_profile_id=exam.id, **data)
    db.add(skill)
    await db.flush()
    await record_audit(db, actor_user_id=admin.id, action="skill_create",
                       entity_type="skill", entity_id=str(skill.id), after=data)
    return SkillOut.model_validate(skill)


@router.patch("/skills/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> SkillOut:
    skill = await _get_or_404(db, Skill, skill_id)
    await _apply(db, skill, payload.model_dump(exclude_none=True),
                 admin=admin, action="skill_update", entity_type="skill")
    return SkillOut.model_validate(skill)


# --- Task families ---
@router.post("/task-families", response_model=TaskFamilyOut)
async def create_task_family(
    payload: TaskFamilyCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TaskFamilyOut:
    family = TaskFamily(**payload.model_dump())
    db.add(family)
    await db.flush()
    await record_audit(db, actor_user_id=admin.id, action="task_family_create",
                       entity_type="task_family", entity_id=str(family.id),
                       after={"code": payload.code})
    return TaskFamilyOut.model_validate(family)


@router.patch("/task-families/{family_id}", response_model=TaskFamilyOut)
async def update_task_family(
    family_id: uuid.UUID,
    payload: TaskFamilyUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TaskFamilyOut:
    family = await _get_or_404(db, TaskFamily, family_id)
    await _apply(db, family, payload.model_dump(exclude_none=True),
                 admin=admin, action="task_family_update", entity_type="task_family")
    return TaskFamilyOut.model_validate(family)


# --- Blueprints ---
@router.post("/task-blueprints", response_model=TaskBlueprintOut)
async def create_blueprint(
    payload: BlueprintCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TaskBlueprintOut:
    blueprint = TaskBlueprint(**payload.model_dump())
    db.add(blueprint)
    await db.flush()
    await record_audit(db, actor_user_id=admin.id, action="blueprint_create",
                       entity_type="task_blueprint", entity_id=str(blueprint.id),
                       after={"code": payload.code})
    return TaskBlueprintOut.model_validate(blueprint)


@router.patch("/task-blueprints/{blueprint_id}", response_model=TaskBlueprintOut)
async def update_blueprint(
    blueprint_id: uuid.UUID,
    payload: BlueprintUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TaskBlueprintOut:
    blueprint = await _get_or_404(db, TaskBlueprint, blueprint_id)
    await _apply(db, blueprint, payload.model_dump(exclude_none=True),
                 admin=admin, action="blueprint_update", entity_type="task_blueprint")
    return TaskBlueprintOut.model_validate(blueprint)
