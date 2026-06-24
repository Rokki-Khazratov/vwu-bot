"""Free Dictionary API adapter (English enrichment, no key) — ТЗ §21.2.

https://dictionaryapi.dev/  (GET /api/v2/entries/en/{word})
Provides definitions, phonetics, audio and synonyms for English. It does not
translate, so it only runs when the source language is English.
"""

from __future__ import annotations

import httpx

from app.modules.dictionary.provider import DictionaryProvider, ProviderDictionaryResult


class FreeDictionaryProvider(DictionaryProvider):
    name = "free_dictionary"

    def __init__(
        self,
        base_url: str = "https://api.dictionaryapi.dev",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def lookup(
        self, word: str, source_lang: str, target_lang: str
    ) -> ProviderDictionaryResult:
        result = ProviderDictionaryResult(provider=self.name)
        if source_lang != "en":
            return result  # English-only enrichment

        url = f"{self._base_url}/api/v2/entries/en/{word}"
        try:
            async with httpx.AsyncClient(timeout=10.0, transport=self._transport) as http:
                resp = await http.get(url)
        except httpx.HTTPError:
            return result
        if resp.status_code != 200:
            return result

        payload = resp.json()
        if not isinstance(payload, list) or not payload:
            return result

        result.found = True
        result.raw = payload
        result.lemma = payload[0].get("word", word)
        for entry in payload:
            for ph in entry.get("phonetics", []):
                if ph.get("text"):
                    result.phonetics.append(ph["text"])
                if ph.get("audio"):
                    result.audio_urls.append(ph["audio"])
            for meaning in entry.get("meanings", []):
                if not result.part_of_speech:
                    result.part_of_speech = meaning.get("partOfSpeech")
                result.synonyms.extend(meaning.get("synonyms", []))
                for d in meaning.get("definitions", []):
                    if d.get("definition"):
                        result.definitions.append({
                            "text": d["definition"],
                            "part_of_speech": meaning.get("partOfSpeech"),
                        })
                    if d.get("example"):
                        result.examples.append(d["example"])

        # de-duplicate while preserving order
        result.phonetics = list(dict.fromkeys(result.phonetics))
        result.audio_urls = list(dict.fromkeys(u for u in result.audio_urls if u))
        result.synonyms = list(dict.fromkeys(result.synonyms))
        return result
