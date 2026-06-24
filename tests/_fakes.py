"""Test doubles for the LLM provider."""

from __future__ import annotations

from typing import Any

from app.modules.dictionary.provider import DictionaryProvider, ProviderDictionaryResult
from app.modules.llm.provider import LLMProvider, LLMRequest, StructuredLLMResult


class FakeDictProvider(DictionaryProvider):
    """Returns a canned ProviderDictionaryResult and counts lookups."""

    def __init__(self, name: str, result: ProviderDictionaryResult | None = None) -> None:
        self.name = name
        self.result = result or ProviderDictionaryResult(provider=name)
        self.calls = 0

    async def lookup(self, word, source_lang, target_lang) -> ProviderDictionaryResult:
        self.calls += 1
        return self.result


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[LLMRequest] = []

    def set_response(self, response: dict[str, Any]) -> None:
        self.response = response

    async def generate_structured(self, request: LLMRequest) -> StructuredLLMResult:
        self.calls.append(request)
        return StructuredLLMResult(
            data=self.response,
            raw_response={"fake": True},
            model="fake-model",
            provider=self.name,
            status="ok",
            input_tokens=1,
            output_tokens=1,
            latency_ms=1,
        )


VALID_GENERATION = {
    "title": "Working part-time while studying?",
    "source_post": {
        "author": "Tom",
        "body": "I just started university and I'm wondering whether I should take a "
        "part-time job. Some friends say it builds experience, others say it ruins "
        "your grades. I really can't decide what makes more sense for my situation.",
    },
    "instruction": "Write a blog comment responding to Tom.",
    "content_points": [
        {"id": "cp_1", "instruction": "Discuss the benefits of part-time work.", "required": True},
        {"id": "cp_2", "instruction": "Discuss the drawbacks.", "required": True},
        {"id": "cp_3", "instruction": "Give Tom a recommendation.", "required": True},
    ],
    "topic_tags": ["work", "study", "balance"],
    "expected_register": "semi_informal",
    "target_words": 250,
}


VALID_EVALUATION = {
    "rubric_code": "epe_b1_plus_writing_20_v1",
    "criteria": [
        {"code": "task_achievement", "score": 4, "selected_band": 4,
         "explanation": "Все три пункта раскрыты.", "evidence": ["I think living at home"]},
        {"code": "organisation_coherence", "score": 4, "selected_band": 4,
         "explanation": "Хорошая связность.", "evidence": []},
        {"code": "range_vocabulary_grammar", "score": 3, "selected_band": 3,
         "explanation": "Достаточный диапазон.", "evidence": []},
        {"code": "accuracy_vocabulary_grammar", "score": 3, "selected_band": 3,
         "explanation": "Несколько ошибок.", "evidence": []},
    ],
    "content_points": [
        {"id": "cp_1", "status": "developed", "evidence": "living at home", "comment": "ок"},
        {"id": "cp_2", "status": "developed", "evidence": "moving out", "comment": "ок"},
        {"id": "cp_3", "status": "mentioned", "evidence": "I would", "comment": "кратко"},
    ],
    "strengths": ["Чёткая позиция"],
    "errors": [
        {"category": "grammar", "subcategory": "verb_form", "severity": "minor",
         "source_fragment": "he go", "corrected_fragment": "he goes",
         "explanation": "Третье лицо.", "criterion_code": "accuracy_vocabulary_grammar"},
    ],
    "recommendations": ["Повторить времена."],
    "confidence": 0.86,
}
