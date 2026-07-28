"""Aggregate queries for user statistics (ТЗ §20).

All queries are scoped to a single user and read from evaluated attempts.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Subject, SubjectTask
from app.modules.evaluation.models import (
    Attempt,
    ContentPointAssessment,
    CriterionScore,
    ErrorEvent,
    EvaluationResult,
)
from app.modules.tasks.models import TaskInstance
from app.modules.training.models import SessionTask, TrainingSession


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


async def error_patterns(db: AsyncSession, user_id: uuid.UUID, limit: int = 10) -> list[dict]:
    signature = func.lower(
        func.coalesce(ErrorEvent.category, "")
        + "|"
        + func.coalesce(ErrorEvent.subcategory, "")
        + "|"
        + func.coalesce(ErrorEvent.source_fragment, "")
        + "|"
        + func.coalesce(ErrorEvent.corrected_fragment, "")
    )
    rows = await db.execute(
        select(
            ErrorEvent.category,
            ErrorEvent.subcategory,
            ErrorEvent.source_fragment,
            ErrorEvent.corrected_fragment,
            ErrorEvent.criterion_code,
            func.count().label("count"),
            func.max(Attempt.created_at).label("last_seen"),
        )
        .join(Attempt, Attempt.id == ErrorEvent.attempt_id)
        .where(Attempt.user_id == user_id)
        .group_by(
            signature,
            ErrorEvent.category,
            ErrorEvent.subcategory,
            ErrorEvent.source_fragment,
            ErrorEvent.corrected_fragment,
            ErrorEvent.criterion_code,
        )
        .order_by(func.count().desc(), func.max(Attempt.created_at).desc())
        .limit(limit)
    )
    return [
        {
            "category": category,
            "subcategory": subcategory,
            "source_fragment": source,
            "corrected_fragment": corrected,
            "criterion_code": criterion,
            "count": int(count),
            "last_seen": last_seen,
        }
        for category, subcategory, source, corrected, criterion, count, last_seen in rows.all()
    ]


async def weak_content_points(db: AsyncSession, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
    rows = await db.execute(
        select(
            ContentPointAssessment.status,
            func.count(),
            func.max(Attempt.created_at),
        )
        .join(EvaluationResult, EvaluationResult.id == ContentPointAssessment.evaluation_result_id)
        .join(Attempt, Attempt.id == EvaluationResult.attempt_id)
        .where(
            Attempt.user_id == user_id,
            ContentPointAssessment.status.in_(["missing", "mentioned", "partly_developed"]),
        )
        .group_by(ContentPointAssessment.status)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [
        {"status": status, "count": int(count), "last_seen": last_seen}
        for status, count, last_seen in rows.all()
    ]


async def affected_task_codes_for_criterion(
    db: AsyncSession, user_id: uuid.UUID, criterion_code: str, limit: int = 5
) -> list[str]:
    rows = await db.execute(
        select(SubjectTask.code, func.count())
        .select_from(CriterionScore)
        .join(EvaluationResult, EvaluationResult.id == CriterionScore.evaluation_result_id)
        .join(Attempt, Attempt.id == EvaluationResult.attempt_id)
        .join(TrainingSession, TrainingSession.id == Attempt.session_id)
        .outerjoin(SubjectTask, TrainingSession.subject_task_id == SubjectTask.id)
        .where(Attempt.user_id == user_id, CriterionScore.criterion_code == criterion_code)
        .group_by(SubjectTask.code)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [code for code, _ in rows.all() if code]


async def affected_task_codes_for_error(
    db: AsyncSession, user_id: uuid.UUID, category: str, limit: int = 5
) -> list[str]:
    rows = await db.execute(
        select(SubjectTask.code, func.count())
        .select_from(ErrorEvent)
        .join(Attempt, Attempt.id == ErrorEvent.attempt_id)
        .join(TrainingSession, TrainingSession.id == Attempt.session_id)
        .outerjoin(SubjectTask, TrainingSession.subject_task_id == SubjectTask.id)
        .where(Attempt.user_id == user_id, ErrorEvent.category == category)
        .group_by(SubjectTask.code)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [code for code, _ in rows.all() if code]


async def history_annotations(db: AsyncSession, attempt_id: uuid.UUID) -> dict:
    error_rows = await db.execute(
        select(ErrorEvent.category, func.count())
        .where(ErrorEvent.attempt_id == attempt_id)
        .group_by(ErrorEvent.category)
        .order_by(func.count().desc())
        .limit(3)
    )
    weakest = (
        await db.execute(
            select(CriterionScore.criterion_code, CriterionScore.score, CriterionScore.max_score)
            .join(EvaluationResult, EvaluationResult.id == CriterionScore.evaluation_result_id)
            .where(EvaluationResult.attempt_id == attempt_id)
            .order_by((cast(CriterionScore.score, Float) / CriterionScore.max_score).asc())
            .limit(1)
        )
    ).first()
    return {
        "top_errors": [
            {"category": category, "count": int(count)}
            for category, count in error_rows.all()
        ],
        "weakest_criterion": {
            "criterion_code": weakest[0],
            "score": int(weakest[1]),
            "max_score": int(weakest[2]),
        }
        if weakest
        else None,
    }


async def filtered_session_ids(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    subject_code: str | None = None,
    task_code: str | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    error_category: str | None = None,
    criterion_code: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[uuid.UUID]:
    stmt = (
        select(TrainingSession.id)
        .join(Subject, TrainingSession.subject_id == Subject.id)
        .outerjoin(SubjectTask, TrainingSession.subject_task_id == SubjectTask.id)
        .outerjoin(SessionTask, SessionTask.session_id == TrainingSession.id)
        .outerjoin(TaskInstance, SessionTask.task_id == TaskInstance.id)
        .outerjoin(
            Attempt,
            (Attempt.session_id == TrainingSession.id) & (Attempt.task_id == TaskInstance.id),
        )
        .where(TrainingSession.user_id == user_id)
    )
    if subject_code:
        stmt = stmt.where(Subject.code == subject_code)
    if task_code:
        stmt = stmt.where(SubjectTask.code == task_code)
    if status:
        stmt = stmt.where(TrainingSession.status == status)
    if date_from:
        stmt = stmt.where(TrainingSession.created_at >= date_from)
    if date_to:
        stmt = stmt.where(TrainingSession.created_at <= date_to)
    if min_score is not None:
        stmt = stmt.where(TrainingSession.score_earned >= min_score)
    if max_score is not None:
        stmt = stmt.where(TrainingSession.score_earned <= max_score)
    if error_category or criterion_code:
        stmt = stmt.join(EvaluationResult, EvaluationResult.attempt_id == Attempt.id)
    if error_category:
        stmt = stmt.join(ErrorEvent, ErrorEvent.evaluation_result_id == EvaluationResult.id)
        stmt = stmt.where(ErrorEvent.category == error_category)
    if criterion_code:
        stmt = stmt.join(CriterionScore, CriterionScore.evaluation_result_id == EvaluationResult.id)
        stmt = stmt.where(CriterionScore.criterion_code == criterion_code)
    rows = await db.execute(
        stmt.distinct()
        .order_by(TrainingSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows.scalars())
