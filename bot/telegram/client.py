"""TelegramClient: aiogram for updates/normal messages + a raw HTTP adapter for
Bot API 10.1 Rich Messages (aiogram 3.27 has no typed methods yet — ТЗ §26).

Swap the raw adapter for aiogram's typed calls once it ships 10.1 support; the
interface (send_rich / send_rich_draft / edit_rich) stays the same.
"""

from __future__ import annotations

from typing import Any

import httpx
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup


def _markup(reply_markup: InlineKeyboardMarkup | dict | None) -> dict | None:
    if reply_markup is None:
        return None
    if isinstance(reply_markup, dict):
        return reply_markup
    return reply_markup.model_dump(exclude_none=True)


class TelegramClient:
    def __init__(self, bot: Bot, token: str, http: httpx.AsyncClient | None = None) -> None:
        self.bot = bot
        self._base = f"https://api.telegram.org/bot{token}"
        self._http = http or httpx.AsyncClient(timeout=30.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _call(self, method: str, payload: dict[str, Any]) -> dict:
        resp = await self._http.post(f"{self._base}/{method}",
                                     json={k: v for k, v in payload.items() if v is not None})
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {data.get('description')}")
        return data["result"]

    async def send_rich(
        self, chat_id: int, html: str, reply_markup: InlineKeyboardMarkup | dict | None = None
    ) -> dict:
        return await self._call("sendRichMessage", {
            "chat_id": chat_id,
            "rich_message": {"html": html},
            "reply_markup": _markup(reply_markup),
        })

    async def send_rich_draft(self, chat_id: int, draft_id: int, html: str) -> dict:
        return await self._call("sendRichMessageDraft", {
            "chat_id": chat_id,
            "draft_id": draft_id,
            "rich_message": {"html": html},
        })

    async def edit_rich(self, chat_id: int, message_id: int, html: str,
                        reply_markup: InlineKeyboardMarkup | dict | None = None) -> dict:
        return await self._call("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "rich_message": {"html": html},
            "reply_markup": _markup(reply_markup),
        })
