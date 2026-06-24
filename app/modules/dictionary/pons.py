"""PONS dictionary API adapter (primary DE/EN -> RU translations) — ТЗ §21.2.

https://en.pons.com/p/online-dictionary/developers/api
GET /v1/dictionary?q={word}&l={dict}&in={src}  with header  X-Secret: <key>
Only active when a PONS API key is configured; otherwise returns "not found"
so the lookup degrades gracefully (ТЗ §21.4: stale/partial beats total failure).
"""

from __future__ import annotations

import html
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

# Source markers that indicate an idiom / example rather than a headword translation.
_EXAMPLE_MARKERS = ("idiom_proverb", "example", "collocator", "rhetoric")

_SPAN_BLOCK_RE = re.compile(r"<span[^>]*>.*?</span>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    """Strip grammar spans (genus, etc.) and remaining markup; unescape entities."""
    text = _SPAN_BLOCK_RE.sub("", text or "")
    text = _TAG_RE.sub("", text)
    return _WS_RE.sub(" ", html.unescape(text)).strip()


def _is_example(source_raw: str) -> bool:
    return any(marker in source_raw for marker in _EXAMPLE_MARKERS)


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
                        result.lemma = _clean(rom.get("headword", "")) or None
                    if not result.part_of_speech:
                        result.part_of_speech = rom.get("wordclass")
                    for arab in rom.get("arabs", []):
                        for tr in arab.get("translations", []):
                            target = _clean(tr.get("target", ""))
                            if not target:
                                continue
                            if _is_example(tr.get("source", "")):
                                result.examples.append(target)
                            else:
                                result.translations.append(target)

        result.translations = list(dict.fromkeys(result.translations))
        result.examples = list(dict.fromkeys(result.examples))
        result.found = bool(result.translations)
        return result
