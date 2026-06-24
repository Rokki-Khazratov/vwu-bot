"""Idempotency-Key handling for write endpoints (ТЗ §30)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IdempotencyConflict
from app.core.security import stable_payload_hash
from app.modules.system.models import IdempotencyKey


async def lookup(db: AsyncSession, key: str, payload: object) -> tuple[dict, int] | None:
    """Return the stored (response, status) for this key, or None if unseen.

    Raises IdempotencyConflict if the key was used with a different payload.
    """
    request_hash = stable_payload_hash(payload)
    existing = (
        await db.execute(select(IdempotencyKey).where(IdempotencyKey.key == key))
    ).scalar_one_or_none()
    if existing is None:
        return None
    if existing.request_hash != request_hash:
        raise IdempotencyConflict()
    return existing.response_json or {}, existing.status_code


async def store(
    db: AsyncSession, key: str, payload: object, response: dict, status_code: int = 200
) -> None:
    db.add(IdempotencyKey(
        key=key,
        request_hash=stable_payload_hash(payload),
        response_json=response,
        status_code=status_code,
    ))
    await db.flush()
