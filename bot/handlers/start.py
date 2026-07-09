from __future__ import annotations

import asyncio
import logging
import uuid

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api_client.client import BackendClient
from bot.api_client.errors import BackendError
from bot.callbacks.factories import CatalogCB, MenuCB, SessionCB
from bot.core.config import get_settings
from bot.core.logging import log_event
from bot.keyboards.menu import main_menu, subject_actions_menu, subjects_menu, submit_confirmation
from bot.rendering.renderer import (
    render_history,
    render_profile,
    render_statistics,
    render_task,
    render_writing_feedback,
)
from bot.rendering.splitter import split_html
from bot.states.fsm import Dictionary, Training
from bot.telegram.client import TelegramClient

router = Router(name="start")
logger = logging.getLogger("bot.start")

_DENIED = "🚫 Доступ закрыт. Этот бот работает только для приглашённых пользователей."
_BLOCKED = "⛔ Ваш доступ заблокирован."
_HELP = (
    "Команды:\n"
    "/start — меню\n/profile — профиль\n/train — тренировка\n"
    "/stats — статистика\n/history — история\n"
    "/word — словарь\n/words — мои слова\n/review — повторение\n/cancel — отменить\n/help — справка"
)


async def _send_rich(message: Message, tg: TelegramClient, html: str) -> None:
    for chunk in split_html(html):
        try:
            await tg.send_rich(message.chat.id, chunk)
        except Exception:  # noqa: BLE001 - plain fallback if Rich Messages are unavailable
            await message.answer(chunk)


async def _show_menu(
    message: Message, name: str | None, backend: BackendClient, state: FSMContext
) -> None:
    subjects = await backend.subjects(message.from_user.id)
    await state.set_state(Training.select_subject)
    await message.answer(
        f"👋 Привет{', ' + name if name else ''}! Выберите предмет:",
        reply_markup=subjects_menu(subjects),
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
    await _show_menu(message, me.get("display_name") or me.get("username"), backend, state)


@router.message(Command("train"))
async def cmd_train(message: Message, state: FSMContext, backend: BackendClient) -> None:
    await state.clear()
    subjects = await backend.subjects(message.from_user.id)
    await state.set_state(Training.select_subject)
    await message.answer("Выберите предмет:", reply_markup=subjects_menu(subjects))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@router.message(Command("stats"))
async def cmd_stats(message: Message, backend: BackendClient, tg: TelegramClient) -> None:
    payload = await _stats_payload(message.from_user.id, backend)
    await _send_rich(message, tg, render_statistics(payload))


@router.message(Command("profile"))
async def cmd_profile(message: Message, backend: BackendClient, tg: TelegramClient) -> None:
    payload = await _profile_payload(message.from_user.id, backend)
    await _send_rich(message, tg, render_profile(payload))


@router.message(Command("history"))
async def cmd_history(message: Message, backend: BackendClient, tg: TelegramClient) -> None:
    items = await backend.history(message.from_user.id)
    await _send_rich(message, tg, render_history(items))


@router.message(Command("word"))
async def cmd_word(message: Message, state: FSMContext) -> None:
    await state.set_state(Dictionary.waiting_word)
    await message.answer("Напишите слово для перевода.")


@router.callback_query(MenuCB.filter(F.action == "train"))
async def menu_train(query: CallbackQuery, state: FSMContext, backend: BackendClient) -> None:
    await state.clear()
    subjects = await backend.subjects(query.from_user.id)
    await state.set_state(Training.select_subject)
    await query.message.edit_text("Выберите предмет:", reply_markup=subjects_menu(subjects))
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "stats"))
async def menu_stats(query: CallbackQuery, backend: BackendClient, tg: TelegramClient) -> None:
    payload = await _stats_payload(query.from_user.id, backend)
    await _send_rich(query.message, tg, render_statistics(payload))
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "profile"))
async def menu_profile(query: CallbackQuery, backend: BackendClient, tg: TelegramClient) -> None:
    payload = await _profile_payload(query.from_user.id, backend)
    await _send_rich(query.message, tg, render_profile(payload))
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "history"))
async def menu_history(query: CallbackQuery, backend: BackendClient, tg: TelegramClient) -> None:
    items = await backend.history(query.from_user.id)
    await _send_rich(query.message, tg, render_history(items))
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "dictionary"))
async def menu_dictionary(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Dictionary.waiting_word)
    await query.message.answer("Напишите слово для перевода.")
    await query.answer()


@router.callback_query(CatalogCB.filter(F.level == "subject"))
async def choose_subject(
    query: CallbackQuery, callback_data: CatalogCB, state: FSMContext, backend: BackendClient
) -> None:
    exams = await backend.exams(query.from_user.id, callback_data.value)
    if not exams:
        await query.message.answer("Для этого предмета пока нет активных экзаменов.")
        await query.answer()
        return
    exam = exams[0]
    await state.update_data(subject_code=callback_data.value, exam_profile_code=exam["code"])
    await state.set_state(Training.select_skill)
    title = f"{exam.get('name') or callback_data.value}: выберите раздел"
    await query.message.edit_text(title, reply_markup=subject_actions_menu(callback_data.value))
    await query.answer()


@router.callback_query(CatalogCB.filter(F.level == "subject_action"))
async def subject_action(
    query: CallbackQuery,
    callback_data: CatalogCB,
    state: FSMContext,
    backend: BackendClient,
    tg: TelegramClient,
) -> None:
    if callback_data.value != "writing":
        data = await state.get_data()
        exam_code = data.get("exam_profile_code")
        skills = await backend.skills(query.from_user.id, exam_code) if exam_code else []
        skill = next((s for s in skills if s.get("code") == callback_data.value), None)
        if skill is None:
            await query.message.answer("Этот раздел пока не настроен в backend.")
            await query.answer()
            return
        families = await backend.task_families(query.from_user.id, skill["id"])
        if not families:
            await query.message.answer("Раздел найден, но task family ещё не настроена.")
            await query.answer()
            return
        await query.message.answer(
            "Раздел уже есть в catalog, но Telegram flow для этого формата ещё не включён."
        )
        await query.answer()
        return

    data = await state.get_data()
    subject_code = data.get("subject_code", "english")
    exam_code = data.get("exam_profile_code")
    if not exam_code:
        exams = await backend.exams(query.from_user.id, subject_code)
        if not exams:
            await query.message.answer("Экзаменационный профиль не найден.")
            await query.answer()
            return
        exam_code = exams[0]["code"]

    skills = await backend.skills(query.from_user.id, exam_code)
    writing = next((s for s in skills if s.get("code") == "writing"), None)
    if writing is None:
        await query.message.answer("Writing пока не настроен для этого предмета.")
        await query.answer()
        return
    families = await backend.task_families(query.from_user.id, writing["id"])
    family = next(
        (f for f in families if f.get("code") == "blog_comment"),
        families[0] if families else None,
    )
    if family is None:
        await query.message.answer("Нет доступных типов заданий Writing.")
        await query.answer()
        return

    created = await backend.create_session(
        query.from_user.id,
        {
            "subject_code": subject_code,
            "exam_profile_code": exam_code,
            "skill_code": "writing",
            "task_family_code": family["code"],
            "mode": "single",
            "options": {"prefer_new_task": False},
        },
    )
    session = created["session"]
    task = created["task"]
    await backend.start_session(query.from_user.id, session["id"])
    await state.set_state(Training.waiting_text_answer)
    await state.update_data(
        subject_code=subject_code,
        exam_profile_code=exam_code,
        skill_code="writing",
        task_family_code=family["code"],
        session_id=session["id"],
        task_id=task["id"],
        idempotency_key=str(uuid.uuid4()),
    )
    await _send_rich(query.message, tg, render_task(task))
    await query.message.answer(
        "Напишите ответ одним сообщением. Потом я покажу preview перед отправкой."
    )
    await query.answer()


@router.message(Training.waiting_text_answer)
async def receive_writing_answer(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Нужен непустой текстовый ответ.")
        return
    data = await state.get_data()
    await state.set_state(Training.submitting)
    await state.update_data(pending_answer=text)
    preview = text if len(text) <= 1200 else text[:1200] + "\n..."
    await message.answer(
        f"Preview ответа:\n\n{preview}\n\nВы точно хотите отправить final submit?",
        reply_markup=submit_confirmation(data["session_id"]),
    )


@router.callback_query(SessionCB.filter(F.action == "continue"))
async def continue_answer(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Training.waiting_text_answer)
    await query.message.answer("Ок, отправьте новую версию ответа одним сообщением.")
    await query.answer()


@router.callback_query(SessionCB.filter(F.action == "cancel"))
async def cancel_session(
    query: CallbackQuery, callback_data: SessionCB, state: FSMContext, backend: BackendClient
) -> None:
    await backend.cancel_session(query.from_user.id, callback_data.session_id)
    await state.clear()
    await query.message.answer("Сессия отменена.", reply_markup=main_menu())
    await query.answer()


@router.callback_query(SessionCB.filter(F.action == "final_submit"))
async def final_submit(
    query: CallbackQuery,
    callback_data: SessionCB,
    state: FSMContext,
    backend: BackendClient,
    tg: TelegramClient,
) -> None:
    data = await state.get_data()
    answer = data.get("pending_answer")
    task_id = data.get("task_id")
    if not answer or not task_id:
        await query.message.answer("Ответ не найден. Отправьте его заново.")
        await state.set_state(Training.waiting_text_answer)
        await query.answer()
        return

    await query.answer()
    await state.set_state(Training.evaluating)
    await query.message.answer("Отправляю на проверку...")
    status, payload = await backend.submit_attempt(
        query.from_user.id,
        {
            "session_id": callback_data.session_id,
            "task_id": task_id,
            "answer": {"type": "text", "text": answer},
        },
        idempotency_key=data.get("idempotency_key") or str(uuid.uuid4()),
    )
    if status == 202:
        payload = await _poll_attempt(query.from_user.id, backend, payload["attempt_id"])
    await state.set_state(Training.result_ready)
    await _send_rich(query.message, tg, render_writing_feedback(payload))
    await query.message.answer("Готово.", reply_markup=main_menu())
    await state.clear()


async def _poll_attempt(tg_id: int, backend: BackendClient, attempt_id: str) -> dict:
    settings = get_settings()
    deadline = settings.eval_poll_timeout_seconds
    interval = settings.eval_poll_interval_seconds
    elapsed = 0.0
    last_payload: dict = {"attempt_id": attempt_id, "status": "evaluating"}
    while elapsed < deadline:
        await asyncio.sleep(interval)
        elapsed += interval
        status, payload = await backend.attempt_result(tg_id, attempt_id)
        last_payload = payload
        if status != 202:
            return payload
    return last_payload


async def _stats_payload(tg_id: int, backend: BackendClient) -> dict:
    overview = await backend.stats_overview(tg_id)
    criteria = await backend.stats_criteria(tg_id)
    errors = await backend.stats_errors(tg_id)
    weaknesses = await backend.stats_weaknesses(tg_id)
    return {
        **overview,
        "criteria": criteria.get("criteria", []),
        "repeated_errors": errors.get("repeated", []),
        "weaknesses": weaknesses.get("weaknesses", []),
    }


async def _profile_payload(tg_id: int, backend: BackendClient) -> dict:
    me = await backend.access_me(tg_id)
    stats = await _stats_payload(tg_id, backend)
    history = await backend.history(tg_id)
    return {
        "me": me,
        "overview": stats,
        "weaknesses": stats.get("weaknesses", []),
        "history": history,
    }


@router.message(Dictionary.waiting_word)
async def dictionary_lookup(message: Message, backend: BackendClient) -> None:
    word = (message.text or "").strip()
    if not word:
        await message.answer("Напишите одно слово.")
        return
    result = await backend.dictionary_lookup(message.from_user.id, word, "en", "ru")
    translations = result.get("translations") or result.get("meanings") or []
    await message.answer(f"{word}: {translations or result}")


@router.callback_query(MenuCB.filter(F.action == "back"))
async def menu_back(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.message.edit_text("Меню:", reply_markup=main_menu())
    await query.answer()
