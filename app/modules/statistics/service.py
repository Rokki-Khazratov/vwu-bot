"""Statistics aggregation and the versioned weakness-score policy (ТЗ §20)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.statistics import repository as repo

WEAKNESS_POLICY_VERSION = "weakness_v1"
DIAGNOSIS_POLICY_VERSION = "diagnosis_v1"


async def overview(db: AsyncSession, user_id: uuid.UUID) -> dict:
    counts = await repo.overview_counts(db, user_id)
    sessions = await repo.recent_sessions(db, user_id)
    avg_pct = None
    if counts["avg_max"]:
        avg_pct = round(counts["avg_score"] / counts["avg_max"] * 100, 1)
    return {
        **counts,
        "average_percent": avg_pct,
        "recent_sessions": [
            {
                "id": str(s.id),
                "mode": s.mode,
                "score_earned": float(s.score_earned) if s.score_earned is not None else None,
                "score_max": float(s.score_max) if s.score_max is not None else None,
                "completed_at": s.completed_at,
            }
            for s in sessions
        ],
    }


async def criterion_trends(db: AsyncSession, user_id: uuid.UUID) -> dict:
    aggregates = await repo.criterion_aggregates(db, user_id)
    trends = []
    for agg in aggregates:
        recent = await repo.recent_criterion_scores(db, user_id, agg["criterion_code"])
        recent_avg = round(sum(recent) / len(recent), 2) if recent else None
        delta = round(recent_avg - agg["avg_score"], 2) if recent_avg is not None else None
        trends.append({**agg, "recent_avg": recent_avg, "delta": delta})
    return {"criteria": trends}


async def error_trends(db: AsyncSession, user_id: uuid.UUID) -> dict:
    categories = await repo.error_aggregates(db, user_id)
    return {
        "categories": categories,
        "repeated": [c for c in categories if c["count"] > 1],
        "severity": await repo.severity_counts(db, user_id),
    }


async def weaknesses(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Rank criteria by a transparent, versioned weakness score.

    weakness = (0.8 * deficit + 0.2 * recent_drop) * 100
      deficit     = (max - avg) / max            # overall shortfall
      recent_drop = max(0, avg - recent_avg)/max  # recent regression
    """
    aggregates = await repo.criterion_aggregates(db, user_id)
    items = []
    for agg in aggregates:
        mx = agg["max_score"] or 5.0
        avg = agg["avg_score"]
        deficit = (mx - avg) / mx if mx else 0.0
        recent = await repo.recent_criterion_scores(db, user_id, agg["criterion_code"])
        recent_avg = sum(recent) / len(recent) if recent else avg
        recent_drop = max(0.0, (avg - recent_avg) / mx) if mx else 0.0
        score = round((0.8 * deficit + 0.2 * recent_drop) * 100, 1)
        items.append({
            "criterion_code": agg["criterion_code"],
            "avg_score": avg,
            "max_score": mx,
            "samples": agg["count"],
            "weakness_score": score,
            "components": {"deficit": round(deficit, 3), "recent_drop": round(recent_drop, 3)},
        })
    items.sort(key=lambda x: x["weakness_score"], reverse=True)
    return {"policy_version": WEAKNESS_POLICY_VERSION, "weaknesses": items}


def _severity(score: float) -> str:
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


async def diagnosis(db: AsyncSession, user_id: uuid.UUID) -> dict:
    counts = await overview(db, user_id)
    weak = (await weaknesses(db, user_id))["weaknesses"]
    errors = await repo.error_patterns(db, user_id)
    content_gaps = await repo.weak_content_points(db, user_id)
    focus_items: list[dict] = []

    for item in weak[:3]:
        criterion = item["criterion_code"]
        affected = await repo.affected_task_codes_for_criterion(db, user_id, criterion)
        focus_items.append(
            {
                "type": "weak_criterion",
                "title": f"Критерий: {criterion}",
                "severity": _severity(item["weakness_score"]),
                "evidence": {
                    "avg_score": item["avg_score"],
                    "max_score": item["max_score"],
                    "samples": item["samples"],
                    "weakness_score": item["weakness_score"],
                    "components": item["components"],
                    "affected_tasks": affected,
                },
                "sample_errors": [],
                "recommended_action": {
                    "type": "train",
                    "label": "Тренировать этот критерий",
                    "task_code": "writing",
                },
                "filters": {"criterion_code": criterion},
            }
        )

    for pattern in errors[:3]:
        category = pattern["category"]
        count = pattern["count"]
        affected = await repo.affected_task_codes_for_error(db, user_id, category)
        focus_items.append(
            {
                "type": "repeated_error",
                "title": f"Повторяется ошибка: {category}",
                "severity": "high" if count >= 3 else "medium",
                "evidence": {
                    "category": category,
                    "subcategory": pattern["subcategory"],
                    "count": count,
                    "last_seen": pattern["last_seen"],
                    "affected_tasks": affected,
                },
                "sample_errors": [
                    {
                        "source_fragment": pattern["source_fragment"],
                        "corrected_fragment": pattern["corrected_fragment"],
                        "criterion_code": pattern["criterion_code"],
                    }
                ],
                "recommended_action": {
                    "type": "train",
                    "label": "Тренировать похожие ошибки",
                    "task_code": "writing",
                },
                "filters": {"error_category": category},
            }
        )

    for gap in content_gaps[:2]:
        focus_items.append(
            {
                "type": "content_point_gap",
                "title": f"Content points: {gap['status']}",
                "severity": "medium",
                "evidence": {
                    "status": gap["status"],
                    "count": gap["count"],
                    "last_seen": gap["last_seen"],
                    "affected_tasks": ["writing"],
                },
                "sample_errors": [],
                "recommended_action": {
                    "type": "train",
                    "label": "Тренировать раскрытие пунктов",
                    "task_code": "writing",
                },
                "filters": {"task_code": "writing"},
            }
        )

    focus_items.sort(
        key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}.get(x["severity"], 0),
            x["evidence"].get("weakness_score", x["evidence"].get("count", 0)),
        ),
        reverse=True,
    )
    return {
        "policy_version": DIAGNOSIS_POLICY_VERSION,
        "summary": {
            "tasks_evaluated": counts["tasks_evaluated"],
            "sessions_completed": counts["sessions_completed"],
            "average_percent": counts["average_percent"],
        },
        "focus_items": focus_items[:8],
    }
