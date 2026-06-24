from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ExamProfileNotFound,
    SubjectNotFound,
    TaskNotFound,
)
from app.modules.catalog.models import ExamProfile, Skill, Subject, TaskBlueprint, TaskFamily
from app.modules.tasks.models import TaskInstance
from app.modules.training.models import SessionTask, TrainingSession


async def resolve_catalog(
    db: AsyncSession,
    subject_code: str,
    exam_code: str,
    skill_code: str | None,
    family_code: str | None,
) -> tuple[Subject, ExamProfile, Skill | None, TaskFamily | None]:
    subject = (
        await db.execute(select(Subject).where(Subject.code == subject_code))
    ).scalar_one_or_none()
    if subject is None:
        raise SubjectNotFound()

    exam = (
        await db.execute(
            select(ExamProfile).where(
                ExamProfile.subject_id == subject.id, ExamProfile.code == exam_code
            )
        )
    ).scalar_one_or_none()
    if exam is None:
        raise ExamProfileNotFound()

    skill = None
    if skill_code:
        skill = (
            await db.execute(
                select(Skill).where(
                    Skill.exam_profile_id == exam.id, Skill.code == skill_code
                )
            )
        ).scalar_one_or_none()

    family = None
    if family_code and skill is not None:
        family = (
            await db.execute(
                select(TaskFamily).where(
                    TaskFamily.skill_id == skill.id, TaskFamily.code == family_code
                )
            )
        ).scalar_one_or_none()

    return subject, exam, skill, family


async def pick_task_for_family(
    db: AsyncSession, family_id: uuid.UUID, prefer_new: bool = True
) -> TaskInstance:
    """Pick an active task from the family's blueprints (ТЗ §14, mode=single)."""
    blueprint_ids = (
        await db.execute(select(TaskBlueprint.id).where(TaskBlueprint.task_family_id == family_id))
    ).scalars().all()
    if not blueprint_ids:
        raise TaskNotFound("No blueprint for this task family.")

    stmt = (
        select(TaskInstance)
        .where(TaskInstance.blueprint_id.in_(blueprint_ids), TaskInstance.status == "active")
        .order_by(func.random())
        .limit(1)
    )
    task = (await db.execute(stmt)).scalars().first()
    if task is None:
        raise TaskNotFound("No active task available for this family.")
    return task


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> TrainingSession | None:
    return (
        await db.execute(select(TrainingSession).where(TrainingSession.id == session_id))
    ).scalar_one_or_none()


async def get_session_task(db: AsyncSession, session_id: uuid.UUID) -> SessionTask | None:
    return (
        await db.execute(
            select(SessionTask)
            .where(SessionTask.session_id == session_id)
            .order_by(SessionTask.position)
        )
    ).scalars().first()


async def list_sessions(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 20
) -> list[TrainingSession]:
    rows = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .order_by(TrainingSession.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars())
