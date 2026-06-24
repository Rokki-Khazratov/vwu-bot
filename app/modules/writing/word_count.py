"""Deterministic word counting and text normalization (Writing §11, §13).

Contracted forms ("don't", "I'm") count as one word. Word count is computed by
the backend, never by the LLM.
"""

from __future__ import annotations

import re
import unicodedata

# A "word" is a token containing at least one letter or digit. Apostrophes and
# hyphens inside a token keep it as a single word (contractions, compounds).
_WORD_RE = re.compile(r"[^\s]*[^\W_][^\s]*", re.UNICODE)


def normalize_text(text: str) -> str:
    """Unicode-normalize and collapse whitespace."""
    normalized = unicodedata.normalize("NFC", text)
    return normalized.strip()


def count_words(text: str) -> int:
    if not text:
        return 0
    return sum(1 for token in _WORD_RE.findall(text) if any(c.isalnum() for c in token))
