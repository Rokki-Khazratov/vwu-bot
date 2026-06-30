from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKey
from app.core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class UserWord(UUIDPrimaryKey, Base):
    """A word saved to a user's personal vocabulary, with SR scheduling state."""

    __tablename__ = "user_words"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    dictionary_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("dictionary_entries.id")
    )
    knowledge_level: Mapped[str] = mapped_column(String(16), default="new")  # new|learning|known
    source: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)

    # Spaced-repetition scheduling state.
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FlashcardReview(UUIDPrimaryKey, Base):
    """History log of one flashcard review (ТЗ §22.2)."""

    __tablename__ = "flashcard_reviews"

    user_word_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_words.id"), index=True)
    grade: Mapped[str] = mapped_column(String(8))  # no|maybe|yes
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    algorithm_version: Mapped[str] = mapped_column(String(16), default="sm2_v1")
