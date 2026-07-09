"""Admin authorization dependency.

General access is open to everyone; the ``ALLOWLIST_TELEGRAM_IDS`` setting now
gates admin endpoints only. A dedicated admin credential / role check lands in
Phase 6 — isolating it here means handlers don't change when that arrives.
"""

from __future__ import annotations

from fastapi import Depends

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AccessDenied
from app.modules.access.models import User


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.telegram_id not in get_settings().allowlist_telegram_ids:
        raise AccessDenied("Admin access requires an allowlisted Telegram id.")
    return user
