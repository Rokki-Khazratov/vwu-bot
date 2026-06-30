"""Spaced-repetition scheduling — SM-2 variant (versioned strategy, ТЗ §22.2).

Grades map to SM-2 quality: no->2 (lapse), maybe->3, yes->5.
Pure functions over scheduling state so they are unit-testable without a DB.
"""

from __future__ import annotations

from dataclasses import dataclass

ALGORITHM_VERSION = "sm2_v1"

_GRADE_QUALITY = {"no": 2, "maybe": 3, "yes": 5}
_MIN_EASE = 1.3


@dataclass
class ScheduleState:
    ease_factor: float
    repetitions: int
    interval_days: int


def schedule(state: ScheduleState, grade: str) -> ScheduleState:
    quality = _GRADE_QUALITY.get(grade)
    if quality is None:
        raise ValueError(f"Invalid grade '{grade}'.")

    if quality < 3:
        # Lapse: relearn from the start.
        repetitions = 0
        interval = 1
    else:
        if state.repetitions == 0:
            interval = 1
        elif state.repetitions == 1:
            interval = 6
        else:
            interval = round(state.interval_days * state.ease_factor)
        repetitions = state.repetitions + 1

    ease = state.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease = max(_MIN_EASE, round(ease, 3))
    return ScheduleState(ease_factor=ease, repetitions=repetitions, interval_days=interval)


def knowledge_level_for(repetitions: int, grade: str) -> str:
    if grade == "no":
        return "learning"
    if repetitions >= 3:
        return "known"
    return "learning"
