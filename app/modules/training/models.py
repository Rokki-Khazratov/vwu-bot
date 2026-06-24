from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKey
from app.core.database import Base, JSONColumn


def _now() -> datetime:
    return datetime.now(UTC)


class TrainingSession(UUIDPrimaryKey, Base):
    __tablename__ = "training_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    exam_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exam_profiles.id"))
    skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    task_family_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("task_families.id"))
    mode: Mapped[str] = mapped_column(String(16), default="single")
    status: Mapped[str] = mapped_column(String(16), default="created", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score_earned: Mapped[float | None] = mapped_column(Numeric(6, 2))
    score_max: Mapped[float | None] = mapped_column(Numeric(6, 2))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict | None] = mapped_column(JSONColumn)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class SessionTask(UUIDPrimaryKey, Base):
    __tablename__ = "session_tasks"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_sessions.id"), index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_instances.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="pending")
