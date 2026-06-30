from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKey
from app.core.database import Base, JSONColumn


def _now() -> datetime:
    return datetime.now(UTC)


class DictionaryEntry(UUIDPrimaryKey, Base):
    """Cached, merged dictionary lookup (ТЗ §21.5).

    Cache key: source_language:target_language:normalized_word.
    """

    __tablename__ = "dictionary_entries"
    __table_args__ = (
        UniqueConstraint(
            "source_language", "target_language", "normalized_word",
            name="uq_dictionary_cache_key",
        ),
    )

    source_language: Mapped[str] = mapped_column(String(8), index=True)
    target_language: Mapped[str] = mapped_column(String(8), index=True)
    original_query: Mapped[str] = mapped_column(String(255))
    normalized_word: Mapped[str] = mapped_column(String(255), index=True)
    lemma: Mapped[str | None] = mapped_column(String(255))
    part_of_speech: Mapped[str | None] = mapped_column(String(64))
    translations: Mapped[list | None] = mapped_column(JSONColumn)
    definitions: Mapped[list | None] = mapped_column(JSONColumn)
    examples: Mapped[list | None] = mapped_column(JSONColumn)
    phonetics: Mapped[list | None] = mapped_column(JSONColumn)
    audio_urls: Mapped[list | None] = mapped_column(JSONColumn)
    forms: Mapped[list | None] = mapped_column(JSONColumn)
    synonyms: Mapped[list | None] = mapped_column(JSONColumn)
    provider_sources: Mapped[list | None] = mapped_column(JSONColumn)
    raw_provider_responses: Mapped[dict | None] = mapped_column(JSONColumn)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
