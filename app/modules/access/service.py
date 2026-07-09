from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserBlocked
from app.modules.access.models import User


async def resolve_user(db: AsyncSession, telegram_id: int) -> User:
    """Resolve the current user; access is open to everyone.

    A matching ``User`` row is auto-provisioned on first contact. Blocking is
    still enforced per-user via ``status``.
    """
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
