"""Dictionary lookup with mocked providers + cache behaviour (Phase 4)."""

import httpx

from app.main import app
from app.modules.dictionary.factory import get_dictionary_providers
from app.modules.dictionary.pons import PonsProvider
from app.modules.dictionary.provider import ProviderDictionaryResult
from tests._fakes import FakeDictProvider

# Realistic PONS payload: genus markup on a headword translation + an idiom.
_HEADWORD = '<strong class="headword">Voraussetzung</strong>'
_GENUS_NT = '<span class="genus"><acronym title="neuter">nt</acronym></span>'
_GENUS_F = '<span class="genus"><acronym title="feminine">f</acronym></span>'
_IDIOM = '<span class="idiom_proverb">jegliche Voraussetzungen fehlen</span>'
PONS_PAYLOAD = [{
    "lang": "de",
    "hits": [{
        "type": "entry",
        "roms": [{
            "headword": "Voraussetzung",
            "wordclass": "noun",
            "arabs": [{
                "header": "",
                "translations": [
                    {"source": _HEADWORD, "target": f"усло́вие {_GENUS_NT}"},
                    {"source": _HEADWORD, "target": f"предпосы́лка {_GENUS_F}"},
                    {"source": _IDIOM, "target": "нет никаки́х предпосылок"},
                ],
            }],
        }],
    }],
}]


async def test_pons_parser_cleans_grammar_and_splits_idioms():
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=PONS_PAYLOAD))
    provider = PonsProvider(api_key="x", transport=transport)
    result = await provider.lookup("Voraussetzung", "de", "ru")

    assert result.found is True
    assert result.part_of_speech == "noun"
    # genus markers stripped, idiom moved to examples
    assert result.translations == ["усло́вие", "предпосы́лка"]
    assert result.examples == ["нет никаки́х предпосылок"]


async def test_pons_disabled_without_key():
    provider = PonsProvider(api_key="")
    result = await provider.lookup("Haus", "de", "ru")
    assert result.found is False

DE_LOOKUP = "/api/v1/dictionary/lookup?word=Voraussetzung&source_lang=de&target_lang=ru"

PONS_RESULT = ProviderDictionaryResult(
    provider="pons", found=True, lemma="Voraussetzung", part_of_speech="noun",
    translations=["предпосылка", "условие"],
)
FREE_RESULT = ProviderDictionaryResult(
    provider="free_dictionary", found=True, lemma="house",
    definitions=[{"text": "a building for habitation", "part_of_speech": "noun"}],
    audio_urls=["https://audio/house.mp3"], phonetics=["/haʊs/"],
)


async def test_lookup_merges_and_caches(client, db):
    pons = FakeDictProvider("pons", PONS_RESULT)
    free = FakeDictProvider("free_dictionary", ProviderDictionaryResult(provider="free_dictionary"))
    app.dependency_overrides[get_dictionary_providers] = lambda: [pons, free]

    r1 = await client.get(DE_LOOKUP)
    assert r1.status_code == 200, r1.text
    data = r1.json()["data"]
    assert data["translations"] == ["предпосылка", "условие"]
    assert data["lemma"] == "Voraussetzung"

    # Second call is served from cache: providers not hit again.
    r2 = await client.get(DE_LOOKUP)
    assert r2.status_code == 200
    assert pons.calls == 1


async def test_lookup_not_found(client, db):
    empty = FakeDictProvider("pons", ProviderDictionaryResult(provider="pons"))
    app.dependency_overrides[get_dictionary_providers] = lambda: [empty]
    resp = await client.get("/api/v1/dictionary/lookup?word=zzzz&source_lang=de&target_lang=ru")
    assert resp.status_code == 404
    assert resp.json()["errors"][0]["code"] == "DICTIONARY_WORD_NOT_FOUND"


async def test_english_enrichment(client, db):
    free = FakeDictProvider("free_dictionary", FREE_RESULT)
    app.dependency_overrides[get_dictionary_providers] = lambda: [free]
    resp = await client.get("/api/v1/dictionary/lookup?word=house&source_lang=en&target_lang=ru")
    data = resp.json()["data"]
    assert data["audio_urls"] == ["https://audio/house.mp3"]
    assert data["definitions"][0]["text"].startswith("a building")
