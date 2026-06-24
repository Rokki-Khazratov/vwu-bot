from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ExamProfileNotFound,
    SubjectNotFound,
)
from app.modules.catalog.models import (
    ExamProfile,
    Skill,
    Subject,
    TaskBlueprint,
    TaskFamily,
)


async def list_subjects(db: AsyncSession) -> list[Subject]:
    rows = await db.execute(
        select(Subject).where(Subject.is_active.is_(True)).order_by(Subject.code)
    )
    return list(rows.scalars())


async def get_subject_by_code(db: AsyncSession, code: str) -> Subject:
    subject = (
        await db.execute(select(Subject).where(Subject.code == code))
    ).scalar_one_or_none()
    if subject is None:
        raise SubjectNotFound()
    return subject


async def list_exams(db: AsyncSession, subject_code: str) -> list[ExamProfile]:
    subject = await get_subject_by_code(db, subject_code)
    rows = await db.execute(
        select(ExamProfile)
        .where(ExamProfile.subject_id == subject.id, ExamProfile.is_active.is_(True))
        .order_by(ExamProfile.code)
    )
    return list(rows.scalars())


async def get_exam_by_code(db: AsyncSession, exam_code: str) -> ExamProfile:
    exam = (
        await db.execute(select(ExamProfile).where(ExamProfile.code == exam_code))
    ).scalar_one_or_none()
    if exam is None:
        raise ExamProfileNotFound()
    return exam


async def list_skills(db: AsyncSession, exam_code: str) -> list[Skill]:
    exam = await get_exam_by_code(db, exam_code)
    rows = await db.execute(
        select(Skill)
        .where(Skill.exam_profile_id == exam.id, Skill.is_active.is_(True))
        .order_by(Skill.position)
    )
    return list(rows.scalars())


async def list_task_families(db: AsyncSession, skill_id: uuid.UUID) -> list[TaskFamily]:
    rows = await db.execute(
        select(TaskFamily)
        .where(TaskFamily.skill_id == skill_id, TaskFamily.is_active.is_(True))
        .order_by(TaskFamily.code)
    )
    return list(rows.scalars())


async def list_blueprints(db: AsyncSession, task_family_id: uuid.UUID) -> list[TaskBlueprint]:
    rows = await db.execute(
        select(TaskBlueprint)
        .where(
            TaskBlueprint.task_family_id == task_family_id,
            TaskBlueprint.is_active.is_(True),
        )
        .order_by(TaskBlueprint.code)
    )
    return list(rows.scalars())
