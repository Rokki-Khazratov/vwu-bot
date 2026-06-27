"""Global error handling: map BackendError codes to user messages (ТЗ §24)."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from bot.api_client.errors import BackendError
from bot.core.logging import log_event

router = Router(name="errors")
logger = logging.getLogger("bot.errors")

_MESSAGES = {
    "ACCESS_DENIED": "🚫 Доступ закрыт.",
    "USER_BLOCKED": "⛔ Доступ заблокирован.",
    "SESSION_EXPIRED": "⏰ Сессия истекла. Начните заново: /train",
    "SESSION_INVALID_STATE": "↩️ Состояние сброшено, начните заново: /train",
    "SESSION_NOT_FOUND": "Сессия не найдена. /train",
    "INVALID_ANSWER_FORMAT": "✍️ Нужен непустой текстовый ответ.",
    "ATTEMPT_DUPLICATE": "Ответ уже отправлен на проверку.",
    "LLM_UNAVAILABLE": "🤖 Проверка временно недоступна, попробуйте обновить позже.",
    "PROVIDER_QUOTA_EXCEEDED": "Лимит провайдера исчерпан, попробуйте позже.",
    "DICTIONARY_WORD_NOT_FOUND": "Слово не найдено — проверьте написание.",
    "VALIDATION_ERROR": "Неверный формат запроса.",
    "BACKEND_UNAVAILABLE": "⚠️ Сервер недоступен. Попробуйте позже.",
}


def message_for(code: str) -> str:
    return _MESSAGES.get(code, "⚠️ Что-то пошло не так. Попробуйте ещё раз.")


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    exc = event.exception
    update = event.update
    msg = update.message or (update.callback_query.message if update.callback_query else None)

    if isinstance(exc, BackendError):
        log_event(logger, logging.WARNING, "backend_error", error_code=exc.code)
        text = message_for(exc.code)
    else:
        log_event(logger, logging.ERROR, "unhandled_exception", exc_type=type(exc).__name__)
        text = "⚠️ Внутренняя ошибка. Попробуйте позже."

    if msg is not None:
        try:
            await msg.answer(text)
        except Exception:  # noqa: BLE001 - last-resort, never raise from error handler
            pass
    if update.callback_query is not None:
        try:
            await update.callback_query.answer()
        except Exception:  # noqa: BLE001
            pass
    return True
