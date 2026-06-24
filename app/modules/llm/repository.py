from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import stable_payload_hash
from app.modules.llm.models import LLMCall
from app.modules.llm.provider import StructuredLLMResult


async def record_llm_call(
    db: AsyncSession,
    result: StructuredLLMResult,
    *,
    purpose: str,
    prompt_code: str | None = None,
    prompt_version: str | None = None,
    schema_code: str | None = None,
    schema_version: str | None = None,
    request_payload: dict | None = None,
) -> LLMCall:
    call = LLMCall(
        provider=result.provider,
        model=result.model,
        purpose=purpose,
        prompt_template_code=prompt_code,
        prompt_template_version=prompt_version,
        output_schema_code=schema_code,
        output_schema_version=schema_version,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cached_tokens=result.cached_tokens,
        estimated_cost=result.estimated_cost,
        latency_ms=result.latency_ms,
        status=result.status,
        error_code=result.error_code,
        request_checksum=stable_payload_hash(request_payload) if request_payload else None,
        raw_response=result.raw_response,
    )
    db.add(call)
    await db.flush()
    return call
