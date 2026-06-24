"""LLM provider interface (ТЗ §19).

Providers are pure: they perform the request, validate the JSON output against the
given JSON Schema, optionally do one deterministic repair retry, and return a
``StructuredLLMResult``. Persisting ``LLMCall`` rows is the caller's job, so the
provider has no database dependency.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMRequest:
    purpose: str
    system_prompt: str
    user_prompt: str
    output_schema: dict[str, Any]
    temperature: float = 0.2
    max_repair_retries: int = 1


@dataclass
class StructuredLLMResult:
    data: dict[str, Any]
    raw_response: dict[str, Any]
    model: str
    provider: str
    status: str = "ok"  # ok|schema_invalid|timeout|error|refusal
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    latency_ms: int | None = None
    estimated_cost: float | None = None
    attempts: int = 1
    error_code: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class LLMProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    async def generate_structured(self, request: LLMRequest) -> StructuredLLMResult:
        """Run the request and return validated structured output."""
        raise NotImplementedError
