from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import SessionInvalidState
from app.modules.access.models import User
from app.modules.dictionary.factory import get_dictionary_providers
from app.modules.dictionary.provider import DictionaryProvider
from app.modules.flashcards import service
from app.modules.flashcards.schemas import (
    AddUserWordRequest,
    FlashcardOut,
    ReviewRequest,
    ReviewResult,
    UpdateUserWordRequest,
    UserWordOut,
)

# Personal vocabulary
words_router = APIRouter(prefix="/user-words", tags=["user-words"], route_class=EnvelopeRoute)
# Flashcard review
cards_router = APIRouter(prefix="/flashcards", tags=["flashcards"], route_class=EnvelopeRoute)


@words_router.post("", response_model=UserWordOut)
async def add_word(
    payload: AddUserWordRequest,
    db: AsyncSession = Depends(get_db),
    providers: list[DictionaryProvider] = Depends(get_dictionary_providers),
    user: User = Depends(get_current_user),
) -> UserWordOut:
    word = await service.add_user_word(
        db, providers, user_id=user.id,
        dictionary_entry_id=payload.dictionary_entry_id, word=payload.word,
        source_lang=payload.source_lang, target_lang=payload.target_lang,
        notes=payload.notes, source=payload.source,
    )
    return UserWordOut.model_validate(word)


@words_router.get("", response_model=list[UserWordOut])
async def list_words(
    level: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[UserWordOut]:
    words = await service.list_user_words(db, user.id, level=level)
    return [UserWordOut.model_validate(w) for w in words]


@words_router.patch("/{user_word_id}", response_model=UserWordOut)
async def update_word(
    user_word_id: uuid.UUID,
    payload: UpdateUserWordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserWordOut:
    word = await service.update_user_word(
        db, user_word_id, user.id,
        knowledge_level=payload.knowledge_level, notes=payload.notes,
    )
    return UserWordOut.model_validate(word)


@words_router.delete("/{user_word_id}")
async def delete_word(
    user_word_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await service.archive_user_word(db, user_word_id, user.id)
    return {"archived": True}


@cards_router.get("/next", response_model=FlashcardOut | None)
async def next_card(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FlashcardOut | None:
    pair = await service.next_card(db, user.id)
    if pair is None:
        return None
    word, entry = pair
    front, back = service.card_front_back(word, entry)
    return FlashcardOut(
        user_word_id=word.id, front=front, back=back, knowledge_level=word.knowledge_level
    )


@cards_router.post("/{user_word_id}/review", response_model=ReviewResult)
async def review_card(
    user_word_id: uuid.UUID,
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewResult:
    if payload.grade not in {"no", "maybe", "yes"}:
        raise SessionInvalidState("Grade must be one of: no, maybe, yes.")
    word = await service.review(db, user.id, user_word_id, payload.grade)
    return ReviewResult(
        user_word_id=word.id, grade=payload.grade, interval_days=word.interval_days,
        next_review_at=word.next_review_at, knowledge_level=word.knowledge_level,
    )


@cards_router.get("/stats")
async def flashcard_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await service.stats(db, user.id)
