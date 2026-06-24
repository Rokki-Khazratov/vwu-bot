"""Merge provider results into a single canonical entry (ТЗ §21.4).

Policy:
- canonical translations come from PONS;
- English definitions / phonetics / audio come from Free Dictionary;
- duplicates removed; the source of each field is recorded.
"""

from __future__ import annotations

from typing import Any

from app.modules.dictionary.provider import ProviderDictionaryResult


def _dedupe(items: list) -> list:
    return list(dict.fromkeys(items))


def merge_results(
    query: str,
    source_lang: str,
    target_lang: str,
    results: list[ProviderDictionaryResult],
) -> dict[str, Any]:
    by_name = {r.provider: r for r in results if r.found}
    pons = by_name.get("pons")
    free = by_name.get("free_dictionary")

    translations: list[str] = []
    if pons:
        translations = _dedupe(pons.translations)

    definitions: list[dict] = []
    examples: list[str] = []
    phonetics: list[str] = []
    audio_urls: list[str] = []
    synonyms: list[str] = []
    if free:
        definitions = free.definitions
        examples = _dedupe(free.examples)
        phonetics = _dedupe(free.phonetics)
        audio_urls = _dedupe(free.audio_urls)
        synonyms = _dedupe(free.synonyms)

    lemma = (pons.lemma if pons else None) or (free.lemma if free else None) or query
    pos = (pons.part_of_speech if pons else None) or (free.part_of_speech if free else None)

    provider_sources = []
    if translations and pons:
        provider_sources.append({"field": "translations", "provider": "pons"})
    if free and (definitions or audio_urls):
        provider_sources.append({"field": "definitions/audio", "provider": "free_dictionary"})

    return {
        "original_query": query,
        "normalized_word": query.lower(),
        "source_language": source_lang,
        "target_language": target_lang,
        "lemma": lemma,
        "part_of_speech": pos,
        "translations": translations,
        "definitions": definitions,
        "examples": examples,
        "phonetics": phonetics,
        "audio_urls": audio_urls,
        "synonyms": synonyms,
        "forms": [],
        "provider_sources": provider_sources,
        "raw_provider_responses": {r.provider: r.raw for r in results if r.raw is not None},
        "found": bool(translations or definitions),
    }
