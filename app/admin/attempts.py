"""Admin attempt review + human correction (ТЗ §26, Writing §23)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    AttemptSummary,
    FeedbackCorrectionRequest,
    ScoreCorrectionRequest,
)
from app.api.dependencies.admin import require_admin
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import AttemptNotFound
from app.modules.access.models import User
from app.modules.evaluation import repository as eval_repo
from app.modules.evaluation.correction import correct_feedback, correct_score
from app.modules.evaluation.models import Attempt
from app.modules.evaluation.payload import build_attempt_payload

router = APIRouter(prefix="/admin/attempts", tags=["admin:attempts"], route_class=EnvelopeRoute)


@router.get("", response_model=list[AttemptSummary])
async def list_attempts(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AttemptSummary]:
    stmt = select(Attempt).order_by(Attempt.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Attempt.status == status)
    rows = (await db.execute(stmt)).scalars().all()
    return [AttemptSummary.model_validate(a) for a in rows]


@router.get("/{attempt_id}")
async def get_attempt_detail(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    attempt = await eval_repo.get_attempt(db, attempt_id)
    if attempt is None:
        raise AttemptNotFound()
    # Enrich with the candidate text + task title for the calibration dashboard.
    from app.modules.tasks import repository as task_repo

    task = await task_repo.get_task(db, attempt.task_id)
    extra = {
        "answer_text": attempt.normalized_answer,
        "word_count": attempt.word_count,
        "task_title": task.title if task else None,
    }
    result = await eval_repo.get_result_for_attempt(db, attempt.id)
    if result is None:
        return {"attempt_id": str(attempt.id), "status": attempt.status, **extra}
    payload = await build_attempt_payload(db, attempt, result)
    return {**payload, **extra}


@router.patch("/{attempt_id}/score")
async def patch_score(
    attempt_id: uuid.UUID,
    payload: ScoreCorrectionRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    attempt, result = await correct_score(
        db, attempt_id=attempt_id, actor_user_id=admin.id,
        criteria_overrides=payload.criteria, final_score=payload.final_score,
        reason=payload.reason,
    )
    return await build_attempt_payload(db, attempt, result)


@router.patch("/{attempt_id}/feedback")
async def patch_feedback(
    attempt_id: uuid.UUID,
    payload: FeedbackCorrectionRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    attempt, result = await correct_feedback(
        db, attempt_id=attempt_id, actor_user_id=admin.id,
        summary=payload.summary, strengths=payload.strengths,
        recommendations=payload.recommendations, reason=payload.reason,
    )
    return await build_attempt_payload(db, attempt, result)
