"""Lightweight calibration dashboard served at /panel.

A single static HTML page (no build step) that drives the existing admin API:
review attempts, correct scores/feedback, generate tasks, inspect jobs/llm-calls.
Intended for the private-beta admin to calibrate the writing engine.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import get_settings

router = APIRouter(tags=["dashboard"])

_HTML = (Path(__file__).parent / "static" / "dashboard.html").read_text(encoding="utf-8")


@router.get("/panel", response_class=HTMLResponse, include_in_schema=False)
async def panel() -> HTMLResponse:
    settings = get_settings()
    default_id = str(settings.dev_default_telegram_id or "")
    return HTMLResponse(_HTML.replace("{{DEFAULT_TELEGRAM_ID}}", default_id))
