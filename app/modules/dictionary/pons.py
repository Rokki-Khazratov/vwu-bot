"""PONS dictionary API adapter (primary DE/EN -> RU translations) — ТЗ §21.2.

https://en.pons.com/p/online-dictionary/developers/api
GET /v1/dictionary?q={word}&l={dict}&in={src}  with header  X-Secret: <key>
Only active when a PONS API key is configured; otherwise returns "not found"
so the lookup degrades gracefully (ТЗ §21.4: stale/partial beats total failure).
"""

from __future__ import annotations

import re

import httpx

from app.modules.dictionary.provider import DictionaryProvider, ProviderDictionaryResult

# Supported PONS bilingual dictionaries by (source, target) language pair.
_DICT_CODES = {
    ("de", "ru"): "deru",
    ("ru", "de"): "deru",
    ("en", "ru"): "enru",
    ("ru", "en"): "enru",
    ("de", "en"): "deen",
    ("en", "de"): "deen",
}

_TAG_RE = re.compile(r"<[^>]+>")


def _strip(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()


class PonsProvider(DictionaryProvider):
    name = "pons"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.pons.com",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key or ""
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    async def lookup(
        self, word: str, source_lang: str, target_lang: str
    ) -> ProviderDictionaryResult:
        result = ProviderDictionaryResult(provider=self.name)
        dict_code = _DICT_CODES.get((source_lang, target_lang))
        if not self.enabled or dict_code is None:
            return result

        url = f"{self._base_url}/v1/dictionary"
        params = {"q": word, "l": dict_code, "in": source_lang}
        try:
            async with httpx.AsyncClient(timeout=10.0, transport=self._transport) as http:
                resp = await http.get(url, params=params, headers={"X-Secret": self._api_key})
        except httpx.HTTPError:
            return result
        if resp.status_code != 200:  # 204 = no entry
            return result

        payload = resp.json()
        result.raw = payload
        for lang_block in payload if isinstance(payload, list) else []:
            for hit in lang_block.get("hits", []):
                for rom in hit.get("roms", []):
                    if not result.lemma:
                        result.lemma = _strip(rom.get("headword", "")) or None
                    if not result.part_of_speech:
                        result.part_of_speech = rom.get("wordclass")
                    for arab in rom.get("arabs", []):
                        for tr in arab.get("translations", []):
                            target = _strip(tr.get("target", ""))
                            if target:
                                result.translations.append(target)

        result.translations = list(dict.fromkeys(result.translations))
        result.found = bool(result.translations)
        return result
