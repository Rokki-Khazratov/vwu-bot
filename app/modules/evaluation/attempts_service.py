from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_model import ensure_aware
from app.core.exceptions import (
    AttemptDuplicate,
    AttemptNotFound,
    InvalidAnswerFormat,
    SessionInvalidState,
    SessionNotFound,
    TaskNotFound,
)
from app.modules.evaluation.models import Attempt
from app.modules.evaluation.payload import build_attempt_payload
from app.modules.evaluation.router import route_and_evaluate
from app.modules.llm.provider import LLMProvider
from app.modules.tasks import repository as task_repo
from app.modules.training import repository as training_repo
from app.modules.training import service as training_service
from app.modules.writing.word_count import count_words, normalize_text


def _now() -> datetime:
    return datetime.now(UTC)


async def create_attempt(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    task_id: uuid.UUID,
    answer_type: str,
    answer_text: str | None,
) -> Attempt:
    """Validate and persist a pending attempt (no evaluation yet)."""
    session = await training_repo.get_session(db, session_id)
    if session is None or session.user_id != user_id:
        raise SessionNotFound()
    if session.status not in {"started", "in_progress"}:
        raise SessionInvalidState(
            f"Cannot submit an answer for a session in state '{session.status}'."
        )

    session_task = await training_repo.get_session_task(db, session.id)
    if session_task is None or session_task.task_id != task_id:
        raise TaskNotFound("Task does not belong to this session.")

    task = await task_repo.get_task(db, task_id)
    if task is None:
        raise TaskNotFound()

    # One active attempt per session task (ТЗ §30).
    existing = (await db.execute(
        select(Attempt).where(Attempt.session_id == session.id, Attempt.task_id == task_id)
    )).scalars().first()
    if existing is not None:
        raise AttemptDuplicate()

    if answer_type != "text" or not answer_text or not answer_text.strip():
        raise InvalidAnswerFormat("A non-empty text answer is required.")

    normalized = normalize_text(answer_text)
    started_at = ensure_aware(session.started_at) if session.started_at else _now()
    attempt = Attempt(
        user_id=user_id,
        session_id=session.id,
        task_id=task.id,
        raw_answer={"type": "text", "text": answer_text},
        normalized_answer=normalized,
        word_count=count_words(normalized),
        started_at=started_at,
        submitted_at=_now(),
        duration_seconds=int((_now() - started_at).total_seconds()),
        status="evaluating",
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def evaluate_attempt(db: AsyncSession, provider: LLMProvider, attempt: Attempt) -> dict:
    """Run evaluation for a persisted attempt and finalize its session."""
    task = await task_repo.get_task(db, attempt.task_id)
    if task is None:
        raise TaskNotFound()
    evaluation = await route_and_evaluate(db, provider, task=task, attempt=attempt)

    if attempt.session_id is not None:
        session = await training_repo.get_session(db, attempt.session_id)
        if session is not None:
            await training_service.finalize_session(
                db, session,
                score_earned=float(evaluation.result.final_score or 0),
                score_max=float(evaluation.result.max_score or 0),
            )
    return await build_attempt_payload(db, attempt, evaluation.result, evaluation.semantic_blocks)


async def evaluate_attempt_by_id(
    db: AsyncSession, provider: LLMProvider, attempt_id: uuid.UUID
) -> dict:
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise AttemptNotFound()
    return await evaluate_attempt(db, provider, attempt)


async def submit_attempt(
    db: AsyncSession,
    provider: LLMProvider,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    task_id: uuid.UUID,
    answer_type: str,
    answer_text: str | None,
) -> dict:
    """Synchronous submit + evaluate (Phase 1 behaviour)."""
    attempt = await create_attempt(
        db, user_id=user_id, session_id=session_id, task_id=task_id,
        answer_type=answer_type, answer_text=answer_text,
    )
    return await evaluate_attempt(db, provider, attempt)
