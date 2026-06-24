from app.modules.catalog.models import Subject


async def test_access_me_allowlisted(client):
    resp = await client.get("/api/v1/access/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["telegram_id"] == 111111111


async def test_access_denied_for_unknown_id(client):
    resp = await client.get("/api/v1/access/me", headers={"X-Telegram-User-Id": "999"})
    assert resp.status_code == 403
    assert resp.json()["errors"][0]["code"] == "ACCESS_DENIED"


async def test_list_subjects(client, db):
    db.add(Subject(code="english", name="English"))
    await db.commit()

    resp = await client.get("/api/v1/subjects")
    assert resp.status_code == 200
    codes = [s["code"] for s in resp.json()["data"]]
    assert "english" in codes


async def test_subject_not_found(client):
    resp = await client.get("/api/v1/subjects/nope/exams")
    assert resp.status_code == 404
    assert resp.json()["errors"][0]["code"] == "SUBJECT_NOT_FOUND"
