"""Admin human-correction of evaluations (Writing §23).

The original AI result is preserved: every correction snapshots the prior state
into a ScoreCorrection row and writes an audit-log entry. Completed history is
only ever mutated through this administrative path (ТЗ §4.10).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AttemptNotFound, ValidationError
from app.modules.evaluation.models import (
    Attempt,
    CriterionScore,
    EvaluationResult,
    ScoreCorrection,
)
from app.modules.system.audit import record_audit


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


async def _load(db: AsyncSession, attempt_id: uuid.UUID) -> tuple[Attempt, EvaluationResult]:
    attempt = (
        await db.execute(select(Attempt).where(Attempt.id == attempt_id))
    ).scalar_one_or_none()
    if attempt is None:
        raise AttemptNotFound()
    result = (
        await db.execute(
            select(EvaluationResult).where(EvaluationResult.attempt_id == attempt_id)
        )
    ).scalar_one_or_none()
    if result is None:
        raise ValidationError("Attempt has no evaluation result to correct.")
    return attempt, result


async def correct_score(
    db: AsyncSession,
    *,
    attempt_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    criteria_overrides: dict[str, int] | None,
    final_score: float | None,
    reason: str | None,
) -> tuple[Attempt, EvaluationResult]:
    attempt, result = await _load(db, attempt_id)
    criterion_rows = list((await db.execute(
        select(CriterionScore).where(CriterionScore.evaluation_result_id == result.id)
    )).scalars())

    original = {
        "raw_score": float(result.raw_score) if result.raw_score is not None else None,
        "final_score": float(result.final_score) if result.final_score is not None else None,
        "criteria": {c.criterion_code: c.score for c in criterion_rows},
    }

    if criteria_overrides:
        by_code = {c.criterion_code: c for c in criterion_rows}
        for code, score in criteria_overrides.items():
            if code not in by_code:
                raise ValidationError(f"Unknown criterion '{code}'.")
            row = by_code[code]
            if not (row.max_score >= score >= 0):
                raise ValidationError(f"Score for '{code}' out of range.")
            row.score = score
        raw_total = float(sum(c.score for c in criterion_rows))
        penalty = float(result.penalty_total or 0)
        max_score = float(result.max_score or 0)
        result.raw_score = raw_total
        result.final_score = _clamp(raw_total + penalty, 0, max_score)

    if final_score is not None:
        result.final_score = _clamp(
            float(final_score), 0, float(result.max_score or final_score)
        )

    attempt.score_raw = result.raw_score
    attempt.score_final = result.final_score

    corrected = {
        "raw_score": float(result.raw_score) if result.raw_score is not None else None,
        "final_score": float(result.final_score) if result.final_score is not None else None,
        "criteria": {c.criterion_code: c.score for c in criterion_rows},
    }
    db.add(ScoreCorrection(
        attempt_id=attempt.id, evaluation_result_id=result.id,
        actor_user_id=actor_user_id, kind="score",
        original=original, corrected=corrected, reason=reason,
    ))
    await record_audit(
        db, actor_user_id=actor_user_id, action="correct_score",
        entity_type="attempt", entity_id=str(attempt.id),
        before=original, after=corrected, reason=reason,
    )
    await db.flush()
    return attempt, result


async def correct_feedback(
    db: AsyncSession,
    *,
    attempt_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    summary: str | None,
    strengths: list[str] | None,
    recommendations: list[str] | None,
    reason: str | None,
) -> tuple[Attempt, EvaluationResult]:
    attempt, result = await _load(db, attempt_id)
    original = {
        "summary": result.summary,
        "strengths": result.strengths,
        "recommendations": result.recommendations,
    }
    if summary is not None:
        result.summary = summary
    if strengths is not None:
        result.strengths = strengths
    if recommendations is not None:
        result.recommendations = recommendations

    corrected = {
        "summary": result.summary,
        "strengths": result.strengths,
        "recommendations": result.recommendations,
    }
    db.add(ScoreCorrection(
        attempt_id=attempt.id, evaluation_result_id=result.id,
        actor_user_id=actor_user_id, kind="feedback",
        original=original, corrected=corrected, reason=reason,
    ))
    await record_audit(
        db, actor_user_id=actor_user_id, action="correct_feedback",
        entity_type="attempt", entity_id=str(attempt.id),
        before=original, after=corrected, reason=reason,
    )
    await db.flush()
    return attempt, result
