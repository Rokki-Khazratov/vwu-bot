"""HTML escaping for user/backend text before Rich HTML (ТЗ §27)."""

from __future__ import annotations

_ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def escape(text: object) -> str:
    if text is None:
        return ""
    return "".join(_ESCAPES.get(ch, ch) for ch in str(text))
