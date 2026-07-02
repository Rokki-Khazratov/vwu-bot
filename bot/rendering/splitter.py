"""Split rendered Rich HTML into chunks under the Rich Message char limit (ТЗ §14).

Splits on block boundaries (double newline) so we never cut a tag in half.
"""

from __future__ import annotations

from bot.telegram.limits import MAX_CHARS


def split_html(html: str, max_chars: int = MAX_CHARS) -> list[str]:
    if len(html) <= max_chars:
        return [html]

    chunks: list[str] = []
    current = ""
    for block in html.split("\n\n"):
        piece = block if not current else current + "\n\n" + block
        if len(piece) <= max_chars:
            current = piece
            continue
        if current:
            chunks.append(current)
        # Single block still too large -> hard-split by length.
        while len(block) > max_chars:
            chunks.append(block[:max_chars])
            block = block[max_chars:]
        current = block
    if current:
        chunks.append(current)
    return chunks
