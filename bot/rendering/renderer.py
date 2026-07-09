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

    score = payload.get("score", {})
    criteria_rows = [
        [
            c.get("code", ""),
            f"{c.get('score', '')}/{c.get('max_score', '')}",
            c.get("explanation", ""),
        ]
        for c in payload.get("criteria", [])
    ]
    content_points = [
        {"id": cp.get("id"), "status": cp.get("status"), "comment": cp.get("comment")}
        for cp in payload.get("content_points", [])
    ]
    errors = [
        {
            "category": e.get("category"),
            "severity": e.get("severity"),
            "before": e.get("source_fragment"),
            "after": e.get("corrected_fragment"),
            "explanation": e.get("explanation"),
        }
        for e in payload.get("errors", [])
    ]
    generated = [
        {"type": "heading", "level": 1, "text": "Результат"},
        {
            "type": "status",
            "text": f"Балл: {score.get('final')} / {score.get('max')}",
        },
    ]
    if score.get("penalty_total"):
        generated.append(
            {"type": "paragraph", "text": f"Штрафы: -{score.get('penalty_total')}"}
        )
    if criteria_rows:
        generated.append(
            {
                "type": "score_table",
                "headers": ["Критерий", "Балл", "Комментарий"],
                "rows": criteria_rows,
            }
        )
    if content_points:
        generated.append({"type": "content_point_list", "items": content_points})
    if payload.get("strengths"):
        generated.append(
            {"type": "recommendation_list", "role": "strengths", "items": payload["strengths"]}
        )
    if errors:
        generated.append({"type": "error_list", "items": errors})
    if payload.get("recommendations"):
        generated.append(
            {
                "type": "recommendation_list",
                "role": "recommendations",
                "items": payload["recommendations"],
            }
        )
    if len(generated) > 2:
        return render_blocks(generated)

    # Minimal fallback when the backend didn't attach blocks or detailed rows.
    return (
        f"<h1>Результат</h1>\n\n"
        f"<p>Балл: {escape(score.get('final'))} / {escape(score.get('max'))}</p>"
    )


def render_task(task: dict[str, Any]) -> str:
    content = task.get("content") or {}
    source = content.get("source_post") or {}
    points = task.get("content_points") or []
    rows = "".join(
        f"<li>{escape(point.get('instruction'))}</li>"
        for point in points
    )
    target = content.get("target_words")
    recommended = task.get("recommended_minutes")
    meta = []
    if target:
        meta.append(f"Объем: около {escape(target)} слов")
    if recommended:
        meta.append(f"Время: {escape(recommended)} мин")
    meta_text = " · ".join(meta)
    return "\n\n".join(
        part
        for part in [
            f"<h1>{escape(task.get('title'))}</h1>",
            f"<p><b>{escape(source.get('author'))}</b>: {escape(source.get('body'))}</p>"
            if source
            else "",
            f"<p>{escape(content.get('instruction'))}</p>" if content.get("instruction") else "",
            f"<h4>Content points</h4><ul>{rows}</ul>" if rows else "",
            f"<p>{escape(meta_text)}</p>" if meta_text else "",
        ]
        if part
    )


def render_statistics(payload: dict[str, Any]) -> str:
    avg = payload.get("average_percent")
    sessions = payload.get("sessions_completed") or payload.get("completed_sessions") or 0
    tasks = payload.get("tasks_evaluated", 0)
    parts = [
        "<h1>Статистика</h1>",
        f"<p>Завершено сессий: {escape(sessions)}<br>Проверено заданий: {escape(tasks)}</p>",
        f"<p>Средний результат: {escape(avg) if avg is not None else '—'}%</p>",
    ]
    if payload.get("criteria"):
        rows = [
            [c.get("criterion_code", ""), c.get("avg_score", ""), c.get("max_score", "")]
            for c in payload["criteria"]
        ]
        parts.append(_table(rows, ["Критерий", "Средний", "Макс."]))
    if payload.get("weaknesses"):
        items = "".join(
            f"<li>{escape(w.get('criterion_code'))}: {escape(w.get('weakness_score'))}</li>"
            for w in payload["weaknesses"][:5]
        )
        parts.append(f"<h4>Слабые места</h4><ul>{items}</ul>")
    if payload.get("repeated_errors"):
        items = "".join(
            f"<li>{escape(e.get('category'))}: {escape(e.get('count'))}</li>"
            for e in payload["repeated_errors"][:5]
        )
        parts.append(f"<h4>Повторяющиеся ошибки</h4><ul>{items}</ul>")
    return "\n\n".join(parts)


def render_profile(payload: dict[str, Any]) -> str:
    me = payload.get("me", {})
    overview = payload.get("overview", {})
    history = payload.get("history", [])
    weaknesses = payload.get("weaknesses", [])
    avg = overview.get("average_percent")
    name = me.get("display_name") or me.get("username") or me.get("telegram_id")
    parts = [
        "<h1>Профиль</h1>",
        f"<p><b>{escape(name)}</b><br>Статус: {escape(me.get('status'))}</p>",
        (
            f"<p>Сессий: {escape(overview.get('sessions_completed', 0))}<br>"
            f"Средний результат: {escape(avg) if avg is not None else '—'}%</p>"
        ),
    ]
    if weaknesses:
        items = "".join(
            f"<li>{escape(w.get('criterion_code'))}: {escape(w.get('weakness_score'))}</li>"
            for w in weaknesses[:3]
        )
        parts.append(f"<h4>Фокус</h4><ul>{items}</ul>")
    if history:
        items = "".join(
            f"<li>{escape(h.get('task_title') or h.get('mode'))}: "
            f"{escape(h.get('score_earned'))}/{escape(h.get('score_max'))}</li>"
            for h in history[:5]
        )
        parts.append(f"<h4>Последние задания</h4><ul>{items}</ul>")
    return "\n\n".join(parts)


def render_history(items: list[dict[str, Any]]) -> str:
    if not items:
        return "<h1>История</h1>\n\n<p>Пока нет завершённых заданий.</p>"
    lis = []
    for item in items[:10]:
        score = "—"
        if item.get("score_earned") is not None and item.get("score_max") is not None:
            score = f"{item['score_earned']} / {item['score_max']}"
        title = item.get("task_title") or item.get("mode") or "Session"
        status = item.get("status") or ""
        lis.append(f"<li><b>{escape(title)}</b><br>{escape(status)} · {escape(score)}</li>")
    return f"<h1>История</h1>\n\n<ul>{''.join(lis)}</ul>"
