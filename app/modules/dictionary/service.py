"""Cache-first dictionary lookup (ТЗ §21)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_model import ensure_aware
from app.core.config import get_settings
from app.core.exceptions import DictionaryWordNotFound
from app.modules.dictionary.merge import merge_results
from app.modules.dictionary.models import DictionaryEntry
from app.modules.dictionary.provider import DictionaryProvider
from app.modules.writing.word_count import normalize_text


def _now() -> datetime:
    return datetime.now(UTC)


async def _get_cached(
    db: AsyncSession, source: str, target: str, normalized: str
) -> DictionaryEntry | None:
    entry = (await db.execute(
        select(DictionaryEntry).where(
            DictionaryEntry.source_language == source,
            DictionaryEntry.target_language == target,
            DictionaryEntry.normalized_word == normalized,
        )
    )).scalar_one_or_none()
    return entry


async def lookup(
    db: AsyncSession,
    providers: list[DictionaryProvider],
    *,
    word: str,
    source_lang: str,
    target_lang: str,
) -> DictionaryEntry:
    normalized = normalize_text(word).lower()
    if not normalized:
        raise DictionaryWordNotFound("Empty query.")

    cached = await _get_cached(db, source_lang, target_lang, normalized)
    if cached is not None and (
        cached.expires_at is None or ensure_aware(cached.expires_at) > _now()
    ):
        return cached

    results = await asyncio.gather(
        *(p.lookup(normalized, source_lang, target_lang) for p in providers)
    )
    merged = merge_results(normalized, source_lang, target_lang, list(results))

    if not merged["found"]:
        # Serve stale cache rather than failing entirely (ТЗ §21.4).
        if cached is not None:
            return cached
        raise DictionaryWordNotFound(f"No entry for '{word}'.")

    ttl = timedelta(hours=get_settings().dictionary_cache_ttl_hours)
    fields = {k: v for k, v in merged.items() if k != "found"}
    if cached is None:
        cached = DictionaryEntry(**fields, fetched_at=_now(), expires_at=_now() + ttl)
        db.add(cached)
    else:
        for key, value in fields.items():
            setattr(cached, key, value)
        cached.fetched_at = _now()
        cached.expires_at = _now() + ttl
    await db.flush()
    return cached
