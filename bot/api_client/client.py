"""Typed gateway to the backend API.

Unwraps the `{data, meta, errors}` envelope, maps errors to BackendError, injects
auth/idempotency/request-id headers. All methods are scoped to a Telegram user id.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from bot.api_client.errors import BackendError, BackendUnavailable
from bot.core.config import Settings, get_settings


class BackendClient:
    def __init__(self, settings: Settings | None = None, client: httpx.AsyncClient | None = None):
        self._settings = settings or get_settings()
        self._client = client or httpx.AsyncClient(
            base_url=self._settings.api_base,
            timeout=self._settings.request_timeout_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- low-level ---
    def _headers(self, tg_id: int, *, write: bool = False) -> dict[str, str]:
        headers = {
            "X-Telegram-User-Id": str(tg_id),
            "X-Request-Id": str(uuid.uuid4()),
        }
        if self._settings.bot_service_token:
            headers["Authorization"] = f"Bearer {self._settings.bot_service_token}"
        if write:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        return headers

    @staticmethod
    def _unwrap(resp: httpx.Response) -> Any:
        try:
            body = resp.json()
        except ValueError:
            raise BackendError("INVALID_RESPONSE", f"non-JSON ({resp.status_code})",
                               http_status=resp.status_code) from None
        errors = body.get("errors") or []
        if resp.status_code >= 400 or errors:
            err = errors[0] if errors else {"code": "HTTP_ERROR", "message": str(resp.status_code)}
            raise BackendError(err.get("code", "HTTP_ERROR"), err.get("message", ""),
                               err.get("details"), resp.status_code)
        return body.get("data")

    async def _request(
        self, method: str, path: str, tg_id: int, *,
        write: bool = False, json: dict | None = None, params: dict | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[int, Any]:
        headers = self._headers(tg_id, write=write)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        try:
            resp = await self._client.request(
                method, path, json=json, params=params, headers=headers
            )
        except httpx.HTTPError as exc:
            raise BackendUnavailable(str(exc)) from exc
        return resp.status_code, self._unwrap(resp)

    async def _get(self, path: str, tg_id: int, **params) -> Any:
        _, data = await self._request("GET", path, tg_id, params=params or None)
        return data

    async def _post(self, path: str, tg_id: int, json: dict | None = None, **kw) -> Any:
        _, data = await self._request("POST", path, tg_id, write=True, json=json, **kw)
        return data

    # --- access ---
    async def access_me(self, tg_id: int) -> dict:
        return await self._get("/access/me", tg_id)

    # --- catalog ---
    async def subjects(self, tg_id: int) -> list[dict]:
        return await self._get("/subjects", tg_id)

    async def exams(self, tg_id: int, subject_code: str) -> list[dict]:
        return await self._get(f"/subjects/{subject_code}/exams", tg_id)

    async def skills(self, tg_id: int, exam_code: str) -> list[dict]:
        return await self._get(f"/exam-profiles/{exam_code}/skills", tg_id)

    async def task_families(self, tg_id: int, skill_id: str) -> list[dict]:
        return await self._get(f"/skills/{skill_id}/task-families", tg_id)

    # --- sessions ---
    async def create_session(self, tg_id: int, payload: dict) -> dict:
        return await self._post("/sessions", tg_id, json=payload)

    async def start_session(self, tg_id: int, session_id: str) -> dict:
        return await self._post(f"/sessions/{session_id}/start", tg_id)

    async def cancel_session(self, tg_id: int, session_id: str) -> dict:
        return await self._post(f"/sessions/{session_id}/cancel", tg_id)

    async def session_result(self, tg_id: int, session_id: str) -> dict:
        return await self._get(f"/sessions/{session_id}/result", tg_id)

    async def history(self, tg_id: int) -> list[dict]:
        return await self._get("/sessions/history", tg_id)

    # --- attempts (handles 200 sync + 202 async) ---
    async def submit_attempt(
        self, tg_id: int, payload: dict, idempotency_key: str
    ) -> tuple[int, dict]:
        return await self._request("POST", "/attempts", tg_id, write=True,
                                   json=payload, idempotency_key=idempotency_key)

    async def attempt_result(self, tg_id: int, attempt_id: str) -> tuple[int, dict]:
        return await self._request("GET", f"/attempts/{attempt_id}/result", tg_id)

    # --- statistics ---
    async def stats_overview(self, tg_id: int) -> dict:
        return await self._get("/statistics/overview", tg_id)

    async def stats_criteria(self, tg_id: int) -> dict:
        return await self._get("/statistics/criteria", tg_id)

    async def stats_errors(self, tg_id: int) -> dict:
        return await self._get("/statistics/errors", tg_id)

    async def stats_weaknesses(self, tg_id: int) -> dict:
        return await self._get("/statistics/weaknesses", tg_id)

    # --- dictionary / flashcards ---
    async def dictionary_lookup(self, tg_id: int, word: str, src: str, tgt: str) -> dict:
        return await self._get(
            "/dictionary/lookup", tg_id, word=word, source_lang=src, target_lang=tgt
        )

    async def add_user_word(self, tg_id: int, payload: dict) -> dict:
        return await self._post("/user-words", tg_id, json=payload)

    async def user_words(self, tg_id: int) -> list[dict]:
        return await self._get("/user-words", tg_id)

    async def next_card(self, tg_id: int) -> dict | None:
        return await self._get("/flashcards/next", tg_id)

    async def review_card(self, tg_id: int, user_word_id: str, grade: str) -> dict:
        return await self._post(f"/flashcards/{user_word_id}/review", tg_id, json={"grade": grade})

    async def flashcard_stats(self, tg_id: int) -> dict:
        return await self._get("/flashcards/stats", tg_id)
