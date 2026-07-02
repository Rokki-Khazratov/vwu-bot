"""SemanticBlockRenderer: client-neutral backend blocks -> Telegram Rich HTML.

Maps the semantic blocks the backend emits (writing feedback, ТЗ §16/§29) into
Bot API 10.1 Rich HTML. Everything user/LLM-provided is HTML-escaped (ТЗ §27).
"""

from __future__ import annotations

from typing import Any

from bot.rendering.escaping import escape

_ROLE_HEADINGS = {
    "strengths": "Сильные стороны",
    "recommendations": "Рекомендации",
    "penalty_notice": "",
}
_STATUS_EMOJI = {
    "missing": "❌", "mentioned": "➖", "partly_developed": "🟡",
    "developed": "🟢", "well_developed": "✅",
}


def _heading(block: dict) -> str:
    level = min(max(int(block.get("level", 1)), 1), 6)
    return f"<h{level}>{escape(block.get('text'))}</h{level}>"


def _paragraph(block: dict) -> str:
    return f"<p>{escape(block.get('text'))}</p>"


def _table(rows: list[list[str]], headers: list[str] | None = None) -> str:
    parts = ["<table>"]
    if headers:
        parts.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr>")
    for row in rows:
        parts.append("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>")
    parts.append("</table>")
    return "".join(parts)


def _score_table(block: dict) -> str:
    return _table(block.get("rows", []), block.get("headers"))


def _criteria_table(block: dict) -> str:
    rows = [
        [r.get("criterion", ""), str(r.get("score", "")), r.get("explanation", "")]
        for r in block.get("rows", [])
    ]
    return _table(rows, ["Критерий", "Балл", "Комментарий"])


def _content_point_list(block: dict) -> str:
    items = block.get("items", [])
    lis = "".join(
        f"<li>{_STATUS_EMOJI.get(i.get('status'), '•')} "
        f"{escape(i.get('id'))}: {escape(i.get('comment'))}</li>"
        for i in items
    )
    return f"<h4>Content points</h4><ul>{lis}</ul>"


def _recommendation_list(block: dict) -> str:
    role = block.get("role", "recommendations")
    heading = _ROLE_HEADINGS.get(role, "Рекомендации")
    lis = "".join(f"<li>{escape(i)}</li>" for i in block.get("items", []))
    head = f"<h4>{escape(heading)}</h4>" if heading else ""
    return f"{head}<ul>{lis}</ul>"


def _error_list(block: dict) -> str:
    lis = []
    for e in block.get("items", []):
        before = escape(e.get("before"))
        after = escape(e.get("after"))
        lis.append(
            f"<li><b>{escape(e.get('category'))}</b>"
            f" <i>({escape(e.get('severity'))})</i><br>"
            f"<s>{before}</s> → <b>{after}</b><br>{escape(e.get('explanation'))}</li>"
        )
    inner = "".join(lis)
    # Long error section is collapsed (ТЗ §18).
    return f"<details><summary>Ошибки и исправления</summary><ul>{inner}</ul></details>"


_RENDERERS = {
    "heading": _heading,
    "status": _paragraph,
    "paragraph": _paragraph,
    "score_table": _score_table,
    "criteria_table": _criteria_table,
    "content_point_list": _content_point_list,
    "recommendation_list": _recommendation_list,
    "error_list": _error_list,
    "divider": lambda block: "<hr>",
}


def render_blocks(blocks: list[dict[str, Any]]) -> str:
    """Render a list of semantic blocks to Rich HTML."""
    out: list[str] = []
    for block in blocks or []:
        renderer = _RENDERERS.get(block.get("type", ""))
        if renderer is not None:
            out.append(renderer(block))
        elif block.get("text"):
            out.append(_paragraph(block))
    return "\n\n".join(out)


def render_writing_feedback(payload: dict[str, Any]) -> str:
    """Render an attempt payload (uses semantic_blocks when present)."""
    blocks = payload.get("semantic_blocks")
    if blocks:
        return render_blocks(blocks)
    # Fallback when the backend didn't attach blocks.
    score = payload.get("score", {})
    return (
        f"<h1>Результат</h1>\n\n"
        f"<p>Балл: {escape(score.get('final'))} / {escape(score.get('max'))}</p>"
    )
