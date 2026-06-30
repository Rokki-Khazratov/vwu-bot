"""Personal vocabulary + flashcard review service (ТЗ §22)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DictionaryWordNotFound, ValidationError
from app.modules.dictionary import service as dictionary_service
from app.modules.dictionary.models import DictionaryEntry
from app.modules.dictionary.provider import DictionaryProvider
from app.modules.flashcards.models import FlashcardReview, UserWord
from app.modules.flashcards.scheduler import (
    ALGORITHM_VERSION,
    ScheduleState,
    knowledge_level_for,
    schedule,
)


def _now() -> datetime:
    return datetime.now(UTC)


async def add_user_word(
    db: AsyncSession,
    providers: list[DictionaryProvider],
    *,
    user_id: uuid.UUID,
    dictionary_entry_id: uuid.UUID | None,
    word: str | None,
    source_lang: str,
    target_lang: str,
    notes: str | None,
    source: str | None,
) -> UserWord:
    entry_id = dictionary_entry_id
    if entry_id is None:
        if not word:
            raise ValidationError("Provide either dictionary_entry_id or word.")
        entry = await dictionary_service.lookup(
            db, providers, word=word, source_lang=source_lang, target_lang=target_lang
        )
        entry_id = entry.id
    else:
        exists = await db.get(DictionaryEntry, entry_id)
        if exists is None:
            raise DictionaryWordNotFound("Unknown dictionary entry.")

    user_word = UserWord(
        user_id=user_id, dictionary_entry_id=entry_id,
        knowledge_level="new", source=source, notes=notes,
        next_review_at=_now(),  # due immediately
    )
    db.add(user_word)
    await db.flush()
    return user_word


async def list_user_words(
    db: AsyncSession, user_id: uuid.UUID, level: str | None = None
) -> list[UserWord]:
    stmt = (
        select(UserWord)
        .where(UserWord.user_id == user_id, UserWord.archived_at.is_(None))
        .order_by(UserWord.created_at.desc())
    )
    if level:
        stmt = stmt.where(UserWord.knowledge_level == level)
    return list((await db.execute(stmt)).scalars())


async def _owned_word(db: AsyncSession, user_word_id: uuid.UUID, user_id: uuid.UUID) -> UserWord:
    word = await db.get(UserWord, user_word_id)
    if word is None or word.user_id != user_id:
        raise DictionaryWordNotFound("User word not found.")
    return word


async def update_user_word(
    db: AsyncSession, user_word_id: uuid.UUID, user_id: uuid.UUID, **changes
) -> UserWord:
    word = await _owned_word(db, user_word_id, user_id)
    for key, value in changes.items():
        if value is not None:
            setattr(word, key, value)
    await db.flush()
    return word


async def archive_user_word(
    db: AsyncSession, user_word_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    word = await _owned_word(db, user_word_id, user_id)
    word.archived_at = _now()
    await db.flush()


async def next_card(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[UserWord, DictionaryEntry] | None:
    word = (await db.execute(
        select(UserWord)
        .where(
            UserWord.user_id == user_id,
            UserWord.archived_at.is_(None),
            (UserWord.next_review_at.is_(None)) | (UserWord.next_review_at <= _now()),
        )
        .order_by(UserWord.next_review_at.asc().nullsfirst())
        .limit(1)
    )).scalars().first()
    if word is None:
        return None
    entry = await db.get(DictionaryEntry, word.dictionary_entry_id)
    return word, entry


async def review(
    db: AsyncSession, user_id: uuid.UUID, user_word_id: uuid.UUID, grade: str
) -> UserWord:
    word = await _owned_word(db, user_word_id, user_id)
    new_state = schedule(
        ScheduleState(word.ease_factor, word.repetitions, word.interval_days), grade
    )
    word.ease_factor = new_state.ease_factor
    word.repetitions = new_state.repetitions
    word.interval_days = new_state.interval_days
    word.last_reviewed_at = _now()
    word.next_review_at = _now() + timedelta(days=new_state.interval_days)
    word.knowledge_level = knowledge_level_for(new_state.repetitions, grade)

    db.add(FlashcardReview(
        user_word_id=word.id, grade=grade, reviewed_at=_now(),
        next_review_at=word.next_review_at, interval_days=new_state.interval_days,
        algorithm_version=ALGORITHM_VERSION,
    ))
    await db.flush()
    return word


async def stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    level_rows = await db.execute(
        select(UserWord.knowledge_level, func.count())
        .where(UserWord.user_id == user_id, UserWord.archived_at.is_(None))
        .group_by(UserWord.knowledge_level)
    )
    by_level = {lvl: int(cnt) for lvl, cnt in level_rows.all()}
    due = (await db.execute(
        select(func.count()).select_from(UserWord).where(
            UserWord.user_id == user_id,
            UserWord.archived_at.is_(None),
            (UserWord.next_review_at.is_(None)) | (UserWord.next_review_at <= _now()),
        )
    )).scalar() or 0
    reviews = (await db.execute(
        select(func.count()).select_from(FlashcardReview)
        .join(UserWord, UserWord.id == FlashcardReview.user_word_id)
        .where(UserWord.user_id == user_id)
    )).scalar() or 0
    return {
        "by_level": by_level,
        "total": sum(by_level.values()),
        "due": int(due),
        "reviews_logged": int(reviews),
        "algorithm_version": ALGORITHM_VERSION,
    }


def card_front_back(word: UserWord, entry: DictionaryEntry | None) -> tuple[str, dict]:
    if entry is None:
        return "(unknown)", {}
    front = entry.lemma or entry.original_query
    back = {
        "translations": entry.translations or [],
        "definitions": entry.definitions or [],
        "examples": entry.examples or [],
        "phonetics": entry.phonetics or [],
    }
    return front, back
