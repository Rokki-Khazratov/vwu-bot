from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKey
from app.core.database import Base


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    interface_language: Mapped[str] = mapped_column(String(8), default="ru")
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|blocked|inactive
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
