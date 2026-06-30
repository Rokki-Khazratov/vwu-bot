"""Personal vocabulary + flashcard review flow (Phase 4)."""

from app.main import app
from app.modules.dictionary.factory import get_dictionary_providers
from app.modules.dictionary.provider import ProviderDictionaryResult
from tests._fakes import FakeDictProvider

PONS_RESULT = ProviderDictionaryResult(
    provider="pons", found=True, lemma="Voraussetzung",
    translations=["предпосылка"],
)


def _use_pons():
    app.dependency_overrides[get_dictionary_providers] = lambda: [
        FakeDictProvider("pons", PONS_RESULT)
    ]


async def test_add_word_via_lookup_and_list(client, db):
    _use_pons()
    add = await client.post("/api/v1/user-words", json={
        "word": "Voraussetzung", "source_lang": "de", "target_lang": "ru",
    })
    assert add.status_code == 200, add.text
    assert add.json()["data"]["knowledge_level"] == "new"

    listing = await client.get("/api/v1/user-words")
    assert len(listing.json()["data"]) == 1


async def test_flashcard_review_cycle(client, db):
    _use_pons()
    await client.post("/api/v1/user-words", json={
        "word": "Voraussetzung", "source_lang": "de", "target_lang": "ru",
    })

    # Card is due immediately.
    card = (await client.get("/api/v1/flashcards/next")).json()["data"]
    assert card["front"] == "Voraussetzung"
    assert card["back"]["translations"] == ["предпосылка"]
    uw_id = card["user_word_id"]

    review = await client.post(f"/api/v1/flashcards/{uw_id}/review", json={"grade": "yes"})
    data = review.json()["data"]
    assert data["interval_days"] == 1
    assert data["next_review_at"] is not None

    # No longer due (scheduled into the future) -> next card is null.
    nxt = (await client.get("/api/v1/flashcards/next")).json()["data"]
    assert nxt is None

    stats = (await client.get("/api/v1/flashcards/stats")).json()["data"]
    assert stats["total"] == 1
    assert stats["reviews_logged"] == 1
    assert stats["algorithm_version"] == "sm2_v1"


async def test_delete_archives_word(client, db):
    _use_pons()
    add = await client.post("/api/v1/user-words", json={
        "word": "Voraussetzung", "source_lang": "de", "target_lang": "ru",
    })
    uw_id = add.json()["data"]["id"]
    deleted = await client.delete(f"/api/v1/user-words/{uw_id}")
    assert deleted.json()["data"]["archived"] is True
    assert (await client.get("/api/v1/user-words")).json()["data"] == []
