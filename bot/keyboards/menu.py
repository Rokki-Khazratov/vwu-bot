from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks.factories import CatalogCB, MenuCB, SessionCB


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
