"""Current-user dependency.

Phase 1 (dev): the Telegram id is taken from the ``X-Telegram-User-Id`` header,
falling back to ``DEV_DEFAULT_TELEGRAM_ID``. Access is gated by the allowlist.
The bot service-token check is added in Phase 6.
"""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.config import get_settings
from app.core.exceptions import AccessDenied
from app.modules.access.models import User
from app.modules.access.service import resolve_user


async def get_current_user(
    x_telegram_user_id: int | None = Header(default=None, alias="X-Telegram-User-Id"),
    db: AsyncSession = Depends(get_db),
) -> User:
    settings = get_settings()
    telegram_id = x_telegram_user_id or settings.dev_default_telegram_id
    if telegram_id is None:
        raise AccessDenied("Missing Telegram user id.")
    return await resolve_user(db, telegram_id)
