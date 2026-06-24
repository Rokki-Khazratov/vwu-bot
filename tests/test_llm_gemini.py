import json

import httpx
import pytest

from app.core.exceptions import LLMSchemaInvalid
from app.modules.llm.gemini import GeminiProvider
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
