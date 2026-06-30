from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks.factories import MenuCB


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎯 Тренировка", callback_data=MenuCB(action="train"))
    kb.button(text="📊 Статистика", callback_data=MenuCB(action="stats"))
    kb.button(text="📚 Словарь", callback_data=MenuCB(action="dictionary"))
    kb.button(text="🗂 История", callback_data=MenuCB(action="history"))
    kb.button(text="🧠 Повторение слов", callback_data=MenuCB(action="review"))
    kb.adjust(1, 2, 2)
    return kb.as_markup()
