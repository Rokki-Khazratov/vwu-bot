"""FSM states (ТЗ §7). Store only UI-state + backend IDs — never rubric/answers/scoring."""

from aiogram.fsm.state import State, StatesGroup


class Training(StatesGroup):
    select_subject = State()
    select_exam = State()
    select_skill = State()
    select_task_family = State()
    select_mode = State()
    session_created = State()
    waiting_text_answer = State()
    submitting = State()
    evaluating = State()
    result_ready = State()


class Dictionary(StatesGroup):
    waiting_word = State()


class Flashcards(StatesGroup):
    reviewing = State()
