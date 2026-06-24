"""Admin authorization dependency.

Phase 2 reuses the allowlist auth (any allowlisted user is an admin in the
private beta). A dedicated admin credential / role check lands in Phase 6 —
isolating it here means handlers don't change when that arrives.
"""

from __future__ import annotations

from fastapi import Depends

from app.api.dependencies.auth import get_current_user
from app.modules.access.models import User


async def require_admin(user: User = Depends(get_current_user)) -> User:
    return user
