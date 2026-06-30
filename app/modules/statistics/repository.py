"""Aggregate queries for user statistics (ТЗ §20).

All queries are scoped to a single user and read from evaluated attempts.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.models import (
    Attempt,
    CriterionScore,
    ErrorEvent,
    EvaluationResult,
)
from app.modules.training.models import TrainingSession


async def overview_counts(db: AsyncSession, user_id: uuid.UUID) -> dict:
    completed_sessions = (await db.execute(
        select(func.count())
        .select_from(TrainingSession)
        .where(TrainingSession.user_id == user_id, TrainingSession.status == "completed")
    )).scalar() or 0

    study_seconds = (await db.execute(
        select(func.coalesce(func.sum(TrainingSession.duration_seconds), 0))
        .where(TrainingSession.user_id == user_id)
    )).scalar() or 0

    attempts_row = (await db.execute(
        select(
            func.count(),
            func.coalesce(func.avg(cast(Attempt.score_final, Float)), 0.0),
            func.coalesce(func.avg(cast(Attempt.score_max, Float)), 0.0),
        ).where(Attempt.user_id == user_id, Attempt.status == "evaluated")
    )).one()

    return {
        "sessions_completed": int(completed_sessions),
        "tasks_evaluated": int(attempts_row[0]),
        "total_study_seconds": int(study_seconds),
        "avg_score": round(float(attempts_row[1]), 2),
        "avg_max": round(float(attempts_row[2]), 2),
    }


async def recent_sessions(db: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list:
    rows = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id, TrainingSession.status == "completed")
        .order_by(TrainingSession.completed_at.desc().nullslast())
        .limit(limit)
    )
    return list(rows.scalars())


async def criterion_aggregates(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    rows = await db.execute(
        select(
            CriterionScore.criterion_code,
            func.avg(cast(CriterionScore.score, Float)),
            func.avg(cast(CriterionScore.max_score, Float)),
            func.count(),
        )
        .join(EvaluationResult, EvaluationResult.id == CriterionScore.evaluation_result_id)
        .join(Attempt, Attempt.id == EvaluationResult.attempt_id)
        .where(Attempt.user_id == user_id)
        .group_by(CriterionScore.criterion_code)
    )
    return [
        {
            "criterion_code": code,
            "avg_score": round(float(avg or 0), 2),
            "max_score": round(float(mx or 0), 2),
            "count": int(cnt),
        }
        for code, avg, mx, cnt in rows.all()
    ]


async def recent_criterion_scores(
    db: AsyncSession, user_id: uuid.UUID, code: str, limit: int = 5
) -> list[int]:
    """Most recent scores for a criterion (newest first) for trend deltas."""
    rows = await db.execute(
        select(CriterionScore.score)
        .join(EvaluationResult, EvaluationResult.id == CriterionScore.evaluation_result_id)
        .join(Attempt, Attempt.id == EvaluationResult.attempt_id)
        .where(Attempt.user_id == user_id, CriterionScore.criterion_code == code)
        .order_by(Attempt.created_at.desc())
        .limit(limit)
    )
    return [int(s) for s in rows.scalars()]


async def error_aggregates(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    rows = await db.execute(
        select(
            ErrorEvent.category,
            func.count(),
            func.max(Attempt.created_at),
        )
        .join(Attempt, Attempt.id == ErrorEvent.attempt_id)
        .where(Attempt.user_id == user_id)
        .group_by(ErrorEvent.category)
        .order_by(func.count().desc())
    )
    return [
        {"category": cat, "count": int(cnt), "last_seen": last}
        for cat, cnt, last in rows.all()
    ]


async def severity_counts(db: AsyncSession, user_id: uuid.UUID) -> dict[str, int]:
    rows = await db.execute(
        select(ErrorEvent.severity, func.count())
        .join(Attempt, Attempt.id == ErrorEvent.attempt_id)
        .where(Attempt.user_id == user_id)
        .group_by(ErrorEvent.severity)
    )
    return {sev or "unknown": int(cnt) for sev, cnt in rows.all()}
