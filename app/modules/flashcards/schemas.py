from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AddUserWordRequest(BaseModel):
    dictionary_entry_id: uuid.UUID | None = None
    word: str | None = None
    source_lang: str = "de"
    target_lang: str = "ru"
    notes: str | None = None
    source: str | None = "manual"


class UpdateUserWordRequest(BaseModel):
    knowledge_level: str | None = None
    notes: str | None = None


class UserWordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dictionary_entry_id: uuid.UUID | None = None
    knowledge_level: str
    notes: str | None = None
    next_review_at: datetime | None = None
    created_at: datetime


class ReviewRequest(BaseModel):
    grade: str  # no|maybe|yes


class FlashcardOut(BaseModel):
    user_word_id: uuid.UUID
    front: str
    back: dict
    knowledge_level: str


class ReviewResult(BaseModel):
    user_word_id: uuid.UUID
    grade: str
    interval_days: int
    next_review_at: datetime | None = None
    knowledge_level: str
