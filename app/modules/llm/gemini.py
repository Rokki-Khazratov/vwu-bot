"""Gemini provider adapter (ТЗ §19, §40).

Uses the Generative Language API ``generateContent`` endpoint in JSON mode
(``responseMimeType=application/json``) and validates the result against our
own JSON Schema. We deliberately do not pass Gemini's ``responseSchema`` so the
same stored JSON Schema works across providers; correctness is enforced by local
validation + one deterministic repair retry.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMSchemaInvalid, LLMUnavailable, ProviderQuotaExceeded
from app.core.logging import log_event
from app.modules.llm.provider import LLMProvider, LLMRequest, StructuredLLMResult
from app.modules.llm.validation import validate_against_schema

logger = logging.getLogger("app.llm.gemini")

_NETWORK_RETRIES = 2
_TIMEOUT_SECONDS = 60.0

# Keys Gemini's responseSchema (OpenAPI subset) understands. Everything else
# (additionalProperties, $schema, numeric/array bounds) is dropped here but
# still enforced by our local JSON Schema validation + repair retry.
_GEMINI_SCHEMA_KEYS = {"type", "properties", "required", "items", "enum", "nullable", "format"}


def to_gemini_schema(schema: dict) -> dict:
    """Convert a JSON Schema to Gemini's responseSchema subset (recursive)."""
    if not isinstance(schema, dict):
        return schema
    out: dict = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            out["properties"] = {k: to_gemini_schema(v) for k, v in value.items()}
        elif key == "items":
            out["items"] = to_gemini_schema(value)
        elif key in _GEMINI_SCHEMA_KEYS:
            out[key] = value
    return out


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.gemini_model
        self._base_url = (base_url or settings.gemini_base_url).rstrip("/")
        self._transport = transport  # injected in tests

    def _url(self) -> str:
        return f"{self._base_url}/v1beta/models/{self._model}:generateContent"

    def _build_body(
        self, system_prompt: str, user_prompt: str, temperature: float, schema: dict | None
    ) -> dict:
        generation_config: dict = {
            "responseMimeType": "application/json",
            "temperature": temperature,
        }
        if schema:
            # Constrain the output shape at the provider; values still validated locally.
            generation_config["responseSchema"] = to_gemini_schema(schema)
        return {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": generation_config,
        }

    async def _post(self, body: dict) -> dict:
        """POST with backoff for network/5xx errors (ТЗ §19.3)."""
        last_exc: Exception | None = None
        async with httpx.AsyncClient(
            timeout=_TIMEOUT_SECONDS, transport=self._transport
        ) as http:
            for attempt in range(_NETWORK_RETRIES + 1):
                try:
                    resp = await http.post(
                        self._url(),
                        params={"key": self._api_key},
                        json=body,
                    )
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_exc = exc
                else:
                    if resp.status_code == 429:
                        raise ProviderQuotaExceeded()
                    if resp.status_code < 500:
                        resp.raise_for_status()
                        return resp.json()
                    last_exc = httpx.HTTPStatusError(
                        "5xx", request=resp.request, response=resp
                    )
                if attempt < _NETWORK_RETRIES:
                    await asyncio.sleep(0.5 * (2**attempt))
        raise LLMUnavailable(f"Gemini request failed: {last_exc}")

    @staticmethod
    def _extract_text(payload: dict) -> str | None:
        candidates = payload.get("candidates") or []
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts") or []
        texts = [p.get("text", "") for p in parts if "text" in p]
        return "".join(texts) if texts else None

    @staticmethod
    def _usage(payload: dict) -> dict:
        usage = payload.get("usageMetadata", {})
        return {
            "input_tokens": usage.get("promptTokenCount"),
            "output_tokens": usage.get("candidatesTokenCount"),
            "cached_tokens": usage.get("cachedContentTokenCount"),
        }

    async def generate_structured(self, request: LLMRequest) -> StructuredLLMResult:
        system_prompt = request.system_prompt
        user_prompt = request.user_prompt
        started = time.perf_counter()
        last_errors: list[str] = []
        payload: dict = {}

        for attempt in range(request.max_repair_retries + 1):
            body = self._build_body(
                system_prompt, user_prompt, request.temperature, request.output_schema
            )
            payload = await self._post(body)
            text = self._extract_text(payload)

            if text is None:
                # No content -> treat as refusal (ТЗ §19.3).
                return StructuredLLMResult(
                    data={}, raw_response=payload, model=self._model, provider=self.name,
                    status="refusal", error_code="LLM_REFUSAL",
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    attempts=attempt + 1, **self._usage(payload),
                )

            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                last_errors = [f"invalid JSON: {exc}"]
                data = None

            if data is not None:
                last_errors = validate_against_schema(data, request.output_schema)
                if not last_errors:
                    return StructuredLLMResult(
                        data=data, raw_response=payload, model=self._model,
                        provider=self.name, status="ok",
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        attempts=attempt + 1, **self._usage(payload),
                    )

            if attempt < request.max_repair_retries:
                log_event(logger, logging.WARNING, "schema_repair_retry",
                          purpose=request.purpose, errors=last_errors[:5])
                user_prompt = (
                    f"{request.user_prompt}\n\n"
                    "Your previous response was invalid. Fix these issues and return "
                    "ONLY valid JSON matching the schema:\n- "
                    + "\n- ".join(last_errors[:10])
                )

        raise LLMSchemaInvalid(
            "LLM output failed schema validation after repair.",
            details={"errors": last_errors[:10]},
        )
