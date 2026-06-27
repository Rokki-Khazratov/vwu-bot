"""Bot entrypoint: dispatcher wiring + long-polling (webhook in Phase B4)."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.api_client.client import BackendClient
from bot.core.config import get_settings
from bot.core.logging import configure_logging
from bot.handlers import errors as errors_handlers
from bot.handlers import start as start_handlers
from bot.middlewares.context import ContextMiddleware
from bot.telegram.client import TelegramClient

logger = logging.getLogger("bot.main")


def build_dispatcher() -> Dispatcher:
    settings = get_settings()
    if settings.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage

        storage = RedisStorage.from_url(settings.redis_url)
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    dp.update.middleware(ContextMiddleware())
    dp.include_router(start_handlers.router)
    dp.include_router(errors_handlers.router)
    return dp


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set")

    bot = Bot(token=settings.bot_token)
    backend = BackendClient(settings)
    tg = TelegramClient(bot, settings.bot_token)

    dp = build_dispatcher()
    dp["backend"] = backend
    dp["tg"] = tg

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await backend.aclose()
        await tg.aclose()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
