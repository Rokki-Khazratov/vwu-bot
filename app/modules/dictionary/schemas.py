from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class DictionaryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_language: str
    target_language: str
    original_query: str
    lemma: str | None = None
    part_of_speech: str | None = None
    translations: list | None = None
    definitions: list | None = None
    examples: list | None = None
    phonetics: list | None = None
    audio_urls: list | None = None
    synonyms: list | None = None
    provider_sources: list | None = None
