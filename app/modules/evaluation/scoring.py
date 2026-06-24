"""Deterministic scoring: dependency rules, word-count penalties, final score.

These are pure functions — the LLM never computes the final score (Writing §12, §17).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PenaltyOutcome:
    penalty: float
    zero_total: bool
    details: str


def apply_dependency_rules(
    criteria_scores: dict[str, int], dependency_rules: list[dict]
) -> dict[str, int]:
    """Apply criterion dependencies, e.g. task_achievement=0 -> all criteria 0."""
    scores = dict(criteria_scores)
    for rule in sorted(dependency_rules, key=lambda r: r.get("priority", 0)):
        cond = rule.get("condition", {})
        action = rule.get("action", {})
        criterion = cond.get("criterion")
        if criterion in scores and scores[criterion] == cond.get("equals"):
            if action.get("set_all_zero"):
                scores = {k: 0 for k in scores}
    return scores


def word_count_penalty(word_count: int, penalty_rule: dict | None) -> PenaltyOutcome:
    """Resolve the word-count band penalty (Writing §11)."""
    if not penalty_rule:
        return PenaltyOutcome(0.0, False, "no rule")
    for band in penalty_rule.get("condition", {}).get("bands", []):
        low = band.get("min", 0)
        high = band.get("max")
        if word_count >= low and (high is None or word_count <= high):
            if band.get("zero_total"):
                return PenaltyOutcome(0.0, True, f"{word_count} words → score 0")
            penalty = float(band.get("penalty") or 0)
            return PenaltyOutcome(penalty, False, f"{word_count} words → {penalty}")
    return PenaltyOutcome(0.0, False, f"{word_count} words → no band")


def compute_final_score(
    raw_score: float, penalty: float, zero_total: bool, max_score: float
) -> float:
    if zero_total:
        return 0.0
    return max(0.0, min(max_score, raw_score + penalty))
