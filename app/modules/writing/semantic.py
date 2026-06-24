"""Client-neutral semantic feedback blocks (ТЗ §29, Writing §25).

The bot maps these to Telegram Rich Messages; the backend stays presentation-free.
"""

from __future__ import annotations

from typing import Any

from app.modules.evaluation.scoring import PenaltyOutcome

_CRITERION_NAMES = {
    "task_achievement": "Task Achievement",
    "organisation_coherence": "Organisation & Coherence",
    "range_vocabulary_grammar": "Range (Vocabulary & Grammar)",
    "accuracy_vocabulary_grammar": "Accuracy (Vocabulary & Grammar)",
}


def build_feedback_blocks(
    data: dict[str, Any],
    *,
    final_score: float,
    raw_score: float,
    max_score: float,
    penalty: PenaltyOutcome,
    adjusted_scores: dict[str, int],
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [
        {"type": "heading", "level": 1, "text": "Writing Result"},
        {
            "type": "status",
            "text": f"Final score: {final_score:g} / {max_score:g}",
        },
        {
            "type": "score_table",
            "headers": ["Criterion", "Score"],
            "rows": [
                [_CRITERION_NAMES.get(code, code), f"{adjusted_scores.get(code, 0)}/5"]
                for code in _CRITERION_NAMES
                if code in adjusted_scores
            ]
            + [["Raw total", f"{raw_score:g}/{max_score:g}"]],
        },
    ]

    if penalty.penalty or penalty.zero_total:
        blocks.append({
            "type": "paragraph",
            "role": "penalty_notice",
            "text": f"Word-count penalty: {penalty.details}.",
        })

    criteria_rows = []
    for c in data.get("criteria", []):
        criteria_rows.append({
            "criterion": _CRITERION_NAMES.get(c["code"], c["code"]),
            "score": adjusted_scores.get(c["code"], c["score"]),
            "explanation": c.get("explanation", ""),
        })
    if criteria_rows:
        blocks.append({"type": "criteria_table", "rows": criteria_rows})

    cps = data.get("content_points", [])
    if cps:
        blocks.append({
            "type": "content_point_list",
            "items": [{"id": c["id"], "status": c["status"], "comment": c.get("comment", "")}
                      for c in cps],
        })

    if data.get("strengths"):
        blocks.append({"type": "recommendation_list", "role": "strengths",
                       "items": data["strengths"]})

    if data.get("errors"):
        blocks.append({
            "type": "error_list",
            "items": [{
                "category": e.get("category"),
                "severity": e.get("severity"),
                "before": e.get("source_fragment"),
                "after": e.get("corrected_fragment"),
                "explanation": e.get("explanation"),
            } for e in data["errors"]],
        })

    if data.get("recommendations"):
        blocks.append({"type": "recommendation_list", "role": "recommendations",
                       "items": data["recommendations"]})

    return blocks
