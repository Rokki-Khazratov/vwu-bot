import json

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
