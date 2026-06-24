from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKey
from app.core.database import Base, JSONColumn


def _now() -> datetime:
    return datetime.now(UTC)


class TaskInstance(UUIDPrimaryKey, Base):
    __tablename__ = "task_instances"

    blueprint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_blueprints.id"), index=True)
    guideline_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("guidelines.id"))
    guideline_version: Mapped[str | None] = mapped_column(String(32))
    generator_prompt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prompt_templates.id"))
    generator_prompt_version: Mapped[str | None] = mapped_column(String(32))
    generator_model: Mapped[str | None] = mapped_column(String(64))
    difficulty: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[dict] = mapped_column(JSONColumn)
    content_points: Mapped[list | None] = mapped_column(JSONColumn)
    answer_config: Mapped[dict | None] = mapped_column(JSONColumn)
    solution: Mapped[dict | None] = mapped_column(JSONColumn)
    explanation: Mapped[str | None] = mapped_column(Text)
    hints: Mapped[list | None] = mapped_column(JSONColumn)
    max_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    recommended_minutes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="generated", index=True)
    checksum: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TaskMedia(UUIDPrimaryKey, Base):
    __tablename__ = "task_media"

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_instances.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # image|audio|video|document|chart|table
    storage_key: Mapped[str | None] = mapped_column(String(512))
    public_or_signed_url: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, default=0)
    meta: Mapped[dict | None] = mapped_column(JSONColumn)
