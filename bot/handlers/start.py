from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api_client.client import BackendClient
from bot.api_client.errors import BackendError
from bot.callbacks.factories import MenuCB
from bot.core.logging import log_event
from bot.keyboards.menu import main_menu

router = Router(name="start")
logger = logging.getLogger("bot.start")

_DENIED = "🚫 Доступ закрыт. Этот бот работает только для приглашённых пользователей."
_BLOCKED = "⛔ Ваш доступ заблокирован."
_HELP = (
    "Команды:\n"
    "/start — меню\n/train — тренировка\n/stats — статистика\n/history — история\n"
    "/word — словарь\n/words — мои слова\n/review — повторение\n/cancel — отменить\n/help — справка"
)


async def _show_menu(message: Message, name: str | None) -> None:
    await message.answer(
        f"👋 Привет{', ' + name if name else ''}! Чем займёмся?",
        reply_markup=main_menu(),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, backend: BackendClient) -> None:
    await state.clear()
    tg_id = message.from_user.id
    try:
        me = await backend.access_me(tg_id)
    except BackendError as exc:
        log_event(logger, logging.INFO, "access_denied", tg_user_id=tg_id, error_code=exc.code)
        await message.answer(_BLOCKED if exc.code == "USER_BLOCKED" else _DENIED)
        return
    if me.get("status") == "blocked":
        await message.answer(_BLOCKED)
        return
    await _show_menu(message, me.get("display_name") or me.get("username"))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@router.callback_query(MenuCB.filter(F.action == "back"))
async def menu_back(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.message.edit_text("Меню:", reply_markup=main_menu())
    await query.answer()
