import pytest

from app.modules.evaluation.scoring import (
    apply_dependency_rules,
    compute_final_score,
    word_count_penalty,
)

WORD_COUNT_RULE = {
    "condition": {
        "bands": [
            {"min": 476, "max": None, "penalty": -3},
            {"min": 376, "max": 475, "penalty": -2},
            {"min": 276, "max": 375, "penalty": -1},
            {"min": 225, "max": 275, "penalty": 0},
            {"min": 210, "max": 224, "penalty": -1},
            {"min": 111, "max": 129, "penalty": -6},
            {"min": 0, "max": 110, "penalty": None, "zero_total": True},
        ]
    }
}

DEP_RULE = [{"condition": {"criterion": "task_achievement", "equals": 0},
             "action": {"set_all_zero": True}, "priority": 1}]


def test_dependency_zeroes_all_when_ta_zero():
    scores = {"task_achievement": 0, "organisation_coherence": 4,
              "range_vocabulary_grammar": 3, "accuracy_vocabulary_grammar": 5}
    assert apply_dependency_rules(scores, DEP_RULE) == {
        "task_achievement": 0, "organisation_coherence": 0,
        "range_vocabulary_grammar": 0, "accuracy_vocabulary_grammar": 0,
    }


def test_dependency_no_effect_when_ta_nonzero():
    scores = {"task_achievement": 3, "organisation_coherence": 4,
              "range_vocabulary_grammar": 3, "accuracy_vocabulary_grammar": 5}
    assert apply_dependency_rules(scores, DEP_RULE) == scores


@pytest.mark.parametrize(
    "wc,penalty,zero",
    [
        (250, 0.0, False),
        (300, -1.0, False),
        (500, -3.0, False),
        (220, -1.0, False),
        (120, -6.0, False),
        (90, 0.0, True),
    ],
)
def test_word_count_penalty(wc, penalty, zero):
    outcome = word_count_penalty(wc, WORD_COUNT_RULE)
    assert outcome.penalty == penalty
    assert outcome.zero_total == zero


def test_compute_final_clamps_and_applies_penalty():
    assert compute_final_score(14, -1, False, 20) == 13
    assert compute_final_score(14, 0, True, 20) == 0  # zero_total wins
    assert compute_final_score(2, -5, False, 20) == 0  # clamp at 0
    assert compute_final_score(22, 0, False, 20) == 20  # clamp at max
