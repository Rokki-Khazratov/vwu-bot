from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKey
from app.core.database import Base, JSONColumn


def _now() -> datetime:
    return datetime.now(UTC)


class BackgroundJob(UUIDPrimaryKey, Base):
    """Observable background job with retry/dead-letter state (ТЗ §31)."""

    __tablename__ = "background_jobs"

    kind: Mapped[str] = mapped_column(String(64), index=True)  # evaluation|batch_generation|...
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    # queued|running|succeeded|failed|dead
    ref_id: Mapped[str | None] = mapped_column(String(64), index=True)  # e.g. attempt id
    payload: Mapped[dict | None] = mapped_column(JSONColumn)
    result: Mapped[dict | None] = mapped_column(JSONColumn)
    error: Mapped[str | None] = mapped_column(String(1024))
    attempts: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class AuditLog(UUIDPrimaryKey, Base):
    """Append-only record of admin mutations (ТЗ §33)."""

    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column()
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    before: Mapped[dict | None] = mapped_column(JSONColumn)
    after: Mapped[dict | None] = mapped_column(JSONColumn)
    reason: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class IdempotencyKey(UUIDPrimaryKey, Base):
    """Stores the response for a (key, request-hash) pair (ТЗ §30)."""

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response_json: Mapped[dict | None] = mapped_column(JSONColumn)
    status_code: Mapped[int] = mapped_column(default=200)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
