from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AccessDenied, UserBlocked
from app.modules.access.models import User


async def resolve_user(db: AsyncSession, telegram_id: int) -> User:
    """Resolve the current user, enforcing the dev allowlist (ТЗ §23.2).

    The Telegram id must be in the configured allowlist. A matching ``User`` row
    is auto-provisioned on first contact (private beta — admin pre-creates users,
    but the allowlist is the source of truth in Phase 1).
    """
    settings = get_settings()
    if telegram_id not in settings.allowlist_telegram_ids:
        raise AccessDenied("Telegram id is not allowed.")

    user = (
        await db.execute(select(User).where(User.telegram_id == telegram_id))
    ).scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, status="active")
        db.add(user)
        await db.flush()

    if user.status == "blocked":
        raise UserBlocked()

    user.last_seen_at = datetime.now(UTC)
    return user
