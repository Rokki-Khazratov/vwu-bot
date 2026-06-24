"""Provider selection. Phase 1 = Gemini only; the dependency is overridable
in tests and ready for a second adapter in Phase 6."""

from __future__ import annotations

from functools import lru_cache

from app.modules.llm.gemini import GeminiProvider
from app.modules.llm.provider import LLMProvider


@lru_cache
def _default_provider() -> LLMProvider:
    return GeminiProvider()


def get_llm_provider() -> LLMProvider:
    return _default_provider()
