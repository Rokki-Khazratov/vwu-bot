"""Assemble the client-facing attempt-result payload from persisted rows."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.models import (
    Attempt,
    ContentPointAssessment,
    CriterionScore,
    ErrorEvent,
    EvaluationResult,
)


def _f(value: object) -> float | None:
    return float(value) if value is not None else None


async def build_attempt_payload(
    db: AsyncSession,
    attempt: Attempt,
    result: EvaluationResult,
    semantic_blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    criteria = (await db.execute(
        select(CriterionScore).where(CriterionScore.evaluation_result_id == result.id)
    )).scalars().all()
    content_points = (await db.execute(
        select(ContentPointAssessment).where(
            ContentPointAssessment.evaluation_result_id == result.id
        )
    )).scalars().all()
    errors = (await db.execute(
        select(ErrorEvent).where(ErrorEvent.evaluation_result_id == result.id)
    )).scalars().all()

    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "evaluation_status": result.status,
        "score": {
            "raw": _f(result.raw_score),
            "penalty_total": _f(result.penalty_total),
            "final": _f(result.final_score),
            "max": _f(result.max_score),
        },
        "criteria": [
            {
                "code": c.criterion_code,
                "score": c.score,
                "max_score": c.max_score,
                "selected_band": c.selected_band,
                "explanation": c.explanation,
                "evidence": c.evidence or [],
            }
            for c in criteria
        ],
        "content_points": [
            {"id": cp.content_point_id, "status": cp.status,
             "evidence": cp.evidence, "comment": cp.comment}
            for cp in content_points
        ],
        "errors": [
            {
                "category": e.category,
                "subcategory": e.subcategory,
                "severity": e.severity,
                "source_fragment": e.source_fragment,
                "corrected_fragment": e.corrected_fragment,
                "explanation": e.explanation,
                "criterion_code": e.criterion_code,
            }
            for e in errors
        ],
        "strengths": result.strengths or [],
        "recommendations": result.recommendations or [],
        "confidence": result.confidence,
        "semantic_blocks": semantic_blocks or [],
    }
