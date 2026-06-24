from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_model import ensure_aware
from app.core.exceptions import (
    SessionInvalidState,
    SessionNotFound,
    ValidationError,
)
from app.modules.tasks.models import TaskInstance
from app.modules.training import repository as repo
from app.modules.training.models import SessionTask, TrainingSession


def _now() -> datetime:
    return datetime.now(UTC)


def available_actions(session: TrainingSession) -> list[str]:
    return {
        "created": ["start", "cancel"],
        "started": ["submit_answer", "cancel"],
        "in_progress": ["submit_answer", "cancel"],
        "completed": ["view_result", "repeat_errors"],
        "cancelled": [],
        "expired": [],
    }.get(session.status, [])


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    subject_code: str,
    exam_profile_code: str,
    skill_code: str,
    task_family_code: str,
    mode: str = "single",
    prefer_new_task: bool = True,
) -> tuple[TrainingSession, TaskInstance]:
    if mode != "single":
        raise ValidationError("Only 'single' mode is supported in this version.")

    subject, exam, skill, family = await repo.resolve_catalog(
        db, subject_code, exam_profile_code, skill_code, task_family_code
    )
    if skill is None or family is None:
        raise ValidationError("Unknown skill or task family for this exam profile.")

    task = await repo.pick_task_for_family(db, family.id, prefer_new=prefer_new_task)

    session = TrainingSession(
        user_id=user_id,
        subject_id=subject.id,
        exam_profile_id=exam.id,
        skill_id=skill.id,
        task_family_id=family.id,
        mode=mode,
        status="created",
        score_max=task.max_score,
    )
    db.add(session)
    await db.flush()

    db.add(SessionTask(session_id=session.id, task_id=task.id, position=0, status="pending"))
    await db.flush()
    return session, task


async def _owned_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> TrainingSession:
    session = await repo.get_session(db, session_id)
    if session is None or session.user_id != user_id:
        raise SessionNotFound()
    return session


async def start_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> TrainingSession:
    session = await _owned_session(db, session_id, user_id)
    if session.status != "created":
        raise SessionInvalidState(f"Cannot start a session in state '{session.status}'.")
    session.status = "in_progress"
    session.started_at = _now()
    session_task = await repo.get_session_task(db, session.id)
    if session_task is not None:
        session_task.started_at = _now()
        session_task.status = "in_progress"
    await db.flush()
    return session


async def cancel_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> TrainingSession:
    session = await _owned_session(db, session_id, user_id)
    if session.status in {"completed", "cancelled", "expired"}:
        raise SessionInvalidState(f"Cannot cancel a session in state '{session.status}'.")
    session.status = "cancelled"
    await db.flush()
    return session


async def get_session_with_task(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[TrainingSession, TaskInstance | None]:
    session = await _owned_session(db, session_id, user_id)
    session_task = await repo.get_session_task(db, session.id)
    task = None
    if session_task is not None:
        from app.modules.tasks import repository as task_repo

        task = await task_repo.get_task(db, session_task.task_id)
    return session, task


async def finalize_session(
    db: AsyncSession, session: TrainingSession, *, score_earned: float, score_max: float
) -> None:
    """Mark the (single-task) session completed after evaluation (ТЗ §14)."""
    session.status = "completed"
    session.completed_at = _now()
    session.submitted_at = _now()
    session.score_earned = score_earned
    session.score_max = score_max
    if session.started_at is not None:
        session.duration_seconds = int(
            (_now() - ensure_aware(session.started_at)).total_seconds()
        )
    session_task = await repo.get_session_task(db, session.id)
    if session_task is not None:
        session_task.status = "submitted"
        session_task.submitted_at = _now()
    await db.flush()
