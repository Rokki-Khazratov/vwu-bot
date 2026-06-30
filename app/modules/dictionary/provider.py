"""Dictionary provider interface (ТЗ §21.3)."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderDictionaryResult:
    provider: str
    found: bool = False
    lemma: str | None = None
    part_of_speech: str | None = None
    translations: list[str] = field(default_factory=list)
    definitions: list[dict[str, Any]] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    phonetics: list[str] = field(default_factory=list)
    audio_urls: list[str] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)
    raw: Any = None


class DictionaryProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    async def lookup(
        self, word: str, source_lang: str, target_lang: str
    ) -> ProviderDictionaryResult:
        raise NotImplementedError
