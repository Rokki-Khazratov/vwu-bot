from app.modules.flashcards.scheduler import ScheduleState, schedule


def test_first_yes_sets_interval_1():
    out = schedule(ScheduleState(2.5, 0, 0), "yes")
    assert out.repetitions == 1
    assert out.interval_days == 1
    assert out.ease_factor >= 2.5


def test_second_yes_sets_interval_6():
    out = schedule(ScheduleState(2.5, 1, 1), "yes")
    assert out.repetitions == 2
    assert out.interval_days == 6


def test_third_yes_multiplies_by_ease():
    out = schedule(ScheduleState(2.5, 2, 6), "yes")
    assert out.repetitions == 3
    assert out.interval_days == round(6 * 2.5)


def test_no_resets_repetitions_and_interval():
    out = schedule(ScheduleState(2.6, 5, 40), "no")
    assert out.repetitions == 0
    assert out.interval_days == 1
    assert out.ease_factor < 2.6  # ease penalised


def test_maybe_grows_slowly_and_lowers_ease():
    out = schedule(ScheduleState(2.5, 2, 6), "maybe")
    assert out.repetitions == 3
    assert out.ease_factor < 2.5
