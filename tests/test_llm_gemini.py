import json
import sys
import types

import httpx
import pytest

from app.core.exceptions import LLMSchemaInvalid
from app.modules.llm.gemini import GeminiProvider, to_gemini_schema
from app.modules.llm.provider import LLMRequest

SCHEMA = {
    "type": "object",
    "properties": {"score": {"type": "integer"}},
    "required": ["score"],
    "additionalProperties": False,
}


def _gemini_response(obj: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [{"content": {"parts": [{"text": json.dumps(obj)}]}}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
        },
    )


def test_to_gemini_schema_strips_unsupported_keys():
    converted = to_gemini_schema(SCHEMA)
    # supported keys kept
    assert converted["type"] == "object"
    assert "score" in converted["properties"]
    assert converted["properties"]["score"]["type"] == "integer"
    assert converted["required"] == ["score"]
    # unsupported keys dropped (Gemini responseSchema subset)
    assert "additionalProperties" not in converted


async def test_request_includes_response_schema():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(req.content)
        return _gemini_response({"score": 4})

    provider = GeminiProvider(api_key="x", transport=httpx.MockTransport(handler))
    await provider.generate_structured(
        LLMRequest(purpose="t", system_prompt="s", user_prompt="u", output_schema=SCHEMA)
    )
    gen_cfg = captured["body"]["generationConfig"]
    assert gen_cfg["responseMimeType"] == "application/json"
    assert gen_cfg["responseSchema"]["type"] == "object"


async def test_valid_output_returns_data():
    transport = httpx.MockTransport(lambda req: _gemini_response({"score": 4}))
    provider = GeminiProvider(api_key="x", transport=transport)
    result = await provider.generate_structured(
        LLMRequest(purpose="t", system_prompt="s", user_prompt="u", output_schema=SCHEMA)
    )
    assert result.status == "ok"
    assert result.data == {"score": 4}
    assert result.input_tokens == 10


async def test_repair_retry_then_success():
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        # First call: invalid (missing required), second: valid.
        return _gemini_response({} if calls["n"] == 1 else {"score": 3})

    provider = GeminiProvider(api_key="x", transport=httpx.MockTransport(handler))
    result = await provider.generate_structured(
        LLMRequest(purpose="t", system_prompt="s", user_prompt="u", output_schema=SCHEMA)
    )
    assert calls["n"] == 2
    assert result.attempts == 2
    assert result.data == {"score": 3}


async def test_schema_invalid_raises_after_retries():
    provider = GeminiProvider(
        api_key="x",
        transport=httpx.MockTransport(lambda req: _gemini_response({"wrong": True})),
    )
    with pytest.raises(LLMSchemaInvalid):
        await provider.generate_structured(
            LLMRequest(purpose="t", system_prompt="s", user_prompt="u", output_schema=SCHEMA)
        )


async def test_vertex_mode_uses_injected_google_genai_client(monkeypatch):
    captured = {}

    class FakeGenerateContentConfig:
        def __init__(self, **kwargs):
            captured["config"] = kwargs

    fake_google = types.ModuleType("google")
    fake_genai = types.ModuleType("google.genai")
    fake_types = types.ModuleType("google.genai.types")
    fake_types.GenerateContentConfig = FakeGenerateContentConfig
    fake_genai.types = fake_types
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)

    class FakeModels:
        def generate_content(self, **kwargs):
            captured["kwargs"] = kwargs
            response = types.SimpleNamespace(
                text=json.dumps({"score": 5}),
                usage_metadata=types.SimpleNamespace(
                    prompt_token_count=11,
                    candidates_token_count=6,
                    cached_content_token_count=2,
                ),
            )
            return response

    fake_client = types.SimpleNamespace(models=FakeModels())
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        google_ai_mode="vertex",
        vertex_client=fake_client,
    )
    result = await provider.generate_structured(
        LLMRequest(purpose="t", system_prompt="system", user_prompt="user", output_schema=SCHEMA)
    )

    assert result.data == {"score": 5}
    assert captured["kwargs"]["model"] == "gemini-2.5-flash"
    assert captured["kwargs"]["contents"] == "user"
    assert captured["config"]["system_instruction"] == "system"
    assert result.cached_tokens == 2
