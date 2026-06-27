"""Structured per-update logging + duplicate update_id suppression (ТЗ §25, §28)."""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.core.logging import log_event

logger = logging.getLogger("bot.update")


class ContextMiddleware(BaseMiddleware):
    """Logs each update and drops duplicate update_id (Telegram re-delivery)."""

    def __init__(self, dedup_size: int = 512) -> None:
        self._seen: OrderedDict[int, None] = OrderedDict()
        self._dedup_size = dedup_size

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            if event.update_id in self._seen:
                return None
            self._seen[event.update_id] = None
            if len(self._seen) > self._dedup_size:
                self._seen.popitem(last=False)

        start = time.perf_counter()
        try:
            return await handler(event, data)
        finally:
            log_event(
                logger, logging.INFO, "update",
                handler=type(event).__name__,
                duration_ms=round((time.perf_counter() - start) * 1000, 1),
            )
