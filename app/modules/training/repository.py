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
from app.modules.evaluation.models import Attempt
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


async def list_session_history(db: AsyncSession, user_id: uuid.UUID, limit: int = 20) -> list[dict]:
    rows = await db.execute(
        select(
            TrainingSession,
            Subject.code.label("subject_code"),
            ExamProfile.code.label("exam_profile_code"),
            Skill.code.label("skill_code"),
            TaskFamily.code.label("task_family_code"),
            TaskInstance.id.label("task_id"),
            TaskInstance.title.label("task_title"),
            Attempt.id.label("attempt_id"),
        )
        .join(Subject, TrainingSession.subject_id == Subject.id)
        .join(ExamProfile, TrainingSession.exam_profile_id == ExamProfile.id)
        .outerjoin(Skill, TrainingSession.skill_id == Skill.id)
        .outerjoin(TaskFamily, TrainingSession.task_family_id == TaskFamily.id)
        .outerjoin(SessionTask, SessionTask.session_id == TrainingSession.id)
        .outerjoin(TaskInstance, SessionTask.task_id == TaskInstance.id)
        .outerjoin(
            Attempt,
            (Attempt.session_id == TrainingSession.id) & (Attempt.task_id == TaskInstance.id),
        )
        .where(TrainingSession.user_id == user_id)
        .order_by(TrainingSession.created_at.desc())
        .limit(limit)
    )
    out: list[dict] = []
    for row in rows:
        session = row[0]
        out.append(
            {
                "id": session.id,
                "mode": session.mode,
                "status": session.status,
                "score_earned": float(session.score_earned)
                if session.score_earned is not None
                else None,
                "score_max": float(session.score_max) if session.score_max is not None else None,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "created_at": session.created_at,
                "duration_seconds": session.duration_seconds,
                "subject_code": row.subject_code,
                "exam_profile_code": row.exam_profile_code,
                "skill_code": row.skill_code,
                "task_family_code": row.task_family_code,
                "task_id": row.task_id,
                "task_title": row.task_title,
                "attempt_id": row.attempt_id,
            }
        )
    return out
