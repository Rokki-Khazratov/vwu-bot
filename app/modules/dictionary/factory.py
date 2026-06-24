"""Dictionary provider selection. Overridable in tests."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.modules.dictionary.free_dictionary import FreeDictionaryProvider
from app.modules.dictionary.pons import PonsProvider
from app.modules.dictionary.provider import DictionaryProvider


@lru_cache
def _providers() -> tuple[DictionaryProvider, ...]:
    settings = get_settings()
    return (
        PonsProvider(api_key=settings.pons_api_key, base_url=settings.pons_base_url),
        FreeDictionaryProvider(base_url=settings.free_dictionary_base_url),
    )


def get_dictionary_providers() -> list[DictionaryProvider]:
    return list(_providers())
