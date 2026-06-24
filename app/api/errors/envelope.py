"""Response envelope helpers (ТЗ §24)."""

from __future__ import annotations

from typing import Any

from app.core.context import get_request_id


def meta() -> dict[str, Any]:
    return {"request_id": get_request_id()}


def success_envelope(data: Any) -> dict[str, Any]:
    return {"data": data, "meta": meta(), "errors": []}


def error_envelope(code: str, message: str, details: dict | None = None) -> dict[str, Any]:
    return {
        "data": None,
        "meta": meta(),
        "errors": [{"code": code, "message": message, "details": details or {}}],
    }
