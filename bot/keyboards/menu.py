from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks.factories import AnalyticsCB, CatalogCB, MenuCB, SessionCB


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Профиль", callback_data=MenuCB(action="profile"))
    kb.button(text="🎯 Тренировка", callback_data=MenuCB(action="train"))
    kb.button(text="📊 Статистика", callback_data=MenuCB(action="stats"))
    kb.button(text="📚 Словарь", callback_data=MenuCB(action="dictionary"))
    kb.button(text="🗂 История", callback_data=MenuCB(action="history"))
    kb.button(text="🧠 Повторение слов", callback_data=MenuCB(action="review"))
    kb.adjust(1, 1, 2, 2)
    return kb.as_markup()


def subjects_menu(subjects: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for subject in subjects:
        kb.button(
            text=subject.get("name") or subject.get("code", "Subject"),
            callback_data=CatalogCB(level="subject", value=subject["code"]),
        )
    kb.adjust(1)
    return kb.as_markup()


def subject_actions_menu(subject_code: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Grammar", callback_data=CatalogCB(level="subject_action", value="grammar"))
    kb.button(text="Reading", callback_data=CatalogCB(level="subject_action", value="reading"))
    kb.button(text="Writing", callback_data=CatalogCB(level="subject_action", value="writing"))
    kb.button(text="Full Mock", callback_data=CatalogCB(level="subject_action", value="full_mock"))
    kb.button(text="Statistics", callback_data=MenuCB(action="stats"))
    kb.button(text="Dictionary", callback_data=MenuCB(action="dictionary"))
    kb.button(text="Back", callback_data=MenuCB(action="train"))
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def submit_confirmation(session_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Final submit",
        callback_data=SessionCB(action="final_submit", session_id=session_id),
    )
    kb.button(
        text="Continue/Edit",
        callback_data=SessionCB(action="continue", session_id=session_id),
    )
    kb.button(text="Cancel", callback_data=SessionCB(action="cancel", session_id=session_id))
    kb.adjust(1, 2)
    return kb.as_markup()


def analytics_actions_menu(diagnosis: dict | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    focus_items = (diagnosis or {}).get("focus_items") or []
    item = focus_items[0] if focus_items else None
    if item:
        filters = item.get("filters") or {}
        kind = ""
        value = ""
        if filters.get("criterion_code"):
            kind = "criterion"
            value = filters["criterion_code"]
        elif filters.get("error_category"):
            kind = "error"
            value = filters["error_category"]
        elif filters.get("task_code"):
            kind = "task"
            value = filters["task_code"]
        kb.button(
            text="Train this weakness",
            callback_data=AnalyticsCB(action="train", kind=kind, value=value),
        )
        kb.button(
            text="Show examples",
            callback_data=AnalyticsCB(action="examples", kind=kind, value=value),
        )
        kb.button(
            text="History",
            callback_data=AnalyticsCB(action="history", kind=kind, value=value),
        )
    else:
        kb.button(text="History", callback_data=MenuCB(action="history"))
    kb.button(text="Back", callback_data=MenuCB(action="back"))
    kb.adjust(1)
    return kb.as_markup()
