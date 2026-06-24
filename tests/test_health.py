async def test_live(client):
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == {"status": "alive"}
    assert body["errors"] == []
    assert body["meta"]["request_id"]


async def test_ready(client):
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["data"] == {"status": "ready"}
