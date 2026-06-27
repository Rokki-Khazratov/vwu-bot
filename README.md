# vwu-bot

Telegram bot for the VWU exam-prep assistant. Thin client over the backend API
(branch `api`). All academic logic, evaluation and storage live in the backend.

## Run (dev)

1. Start the backend (branch `api`) and add your Telegram id to its
   `ALLOWLIST_TELEGRAM_IDS`.
2. `cp .env.example .env` and set `BOT_TOKEN` + `BACKEND_BASE_URL`.
3. `pip install -e ".[dev]"` then `python -m bot.main` (long polling).

## Test

`pytest` — backend client (respx-mocked) and rendering units.

Stack: aiogram 3 · httpx · pydantic-settings. Rich Messages (Bot API 10.1) are
sent via a raw HTTP adapter behind `bot/telegram/client.py` (aiogram 3.27 has no
typed methods yet).
