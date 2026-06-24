"""Statistics aggregation and the versioned weakness-score policy (ТЗ §20)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.statistics import repository as repo

WEAKNESS_POLICY_VERSION = "weakness_v1"


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
