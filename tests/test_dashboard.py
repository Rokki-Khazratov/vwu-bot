"""Calibration dashboard + enriched admin attempt detail."""

from app.content.seed import seed_all
from app.main import app
from app.modules.llm.factory import get_llm_provider
from tests._fakes import VALID_EVALUATION, FakeProvider

ANSWER = "I understand why the school wants to ban phones during lessons. " * 18


async def test_panel_serves_html(client):
    resp = await client.get("/panel")
    assert resp.status_code == 200
    assert "VWU Calibration" in resp.text
    assert "/api/v1" in resp.text


async def test_admin_attempt_detail_includes_answer_and_task(client, db):
    await seed_all(db)
    await db.commit()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(VALID_EVALUATION)

    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english", "exam_profile_code": "epe_b1_plus",
        "skill_code": "writing", "task_family_code": "blog_comment", "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")
    att = (await client.post("/api/v1/attempts", json={
        "session_id": sid, "task_id": tid, "answer": {"type": "text", "text": ANSWER},
    })).json()["data"]

    detail = (await client.get(f"/api/v1/admin/attempts/{att['attempt_id']}")).json()["data"]
    assert detail["answer_text"].startswith("I understand")
    assert detail["task_title"]
    assert detail["word_count"] == 198
    assert len(detail["criteria"]) == 4
