"""Dictionary lookup with mocked providers + cache behaviour (Phase 4)."""

from app.main import app
from app.modules.dictionary.factory import get_dictionary_providers
from app.modules.dictionary.provider import ProviderDictionaryResult
from tests._fakes import FakeDictProvider

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
