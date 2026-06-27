"""Versioned callback data factories (ТЗ §9). aiogram packs/parses these.

Keep payloads short; long ids (UUIDs) still fit Telegram's 64-byte limit.
"""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="v1menu"):
    action: str  # train | stats | dictionary | history | review | back


class CatalogCB(CallbackData, prefix="v1cat"):
    level: str  # subject | exam | skill | family | mode
    value: str  # code, or skill UUID


class SessionCB(CallbackData, prefix="v1sess"):
    action: str  # start | cancel | next
    session_id: str


class FlashcardCB(CallbackData, prefix="v1fc"):
    action: str  # show | grade
    user_word_id: str
    grade: str = ""  # no | maybe | yes


class WordCB(CallbackData, prefix="v1word"):
    action: str  # save | review | new
    entry_id: str = ""
