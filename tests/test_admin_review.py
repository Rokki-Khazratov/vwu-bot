"""Admin review + human correction workflow (Phase 2)."""

from app.content.seed import seed_all
from app.main import app
from app.modules.llm.factory import get_llm_provider
from tests._fakes import VALID_EVALUATION, FakeProvider

ANSWER_TEXT = "I understand why the school wants to ban phones during lessons. " * 18


async def _run_attempt(client, db) -> str:
    await seed_all(db)
    await db.commit()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(VALID_EVALUATION)

    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english", "exam_profile_code": "epe_b1_plus",
        "skill_code": "writing", "task_family_code": "blog_comment", "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")
    res = (await client.post("/api/v1/attempts", json={
        "session_id": sid, "task_id": tid, "answer": {"type": "text", "text": ANSWER_TEXT},
    })).json()["data"]
    return res["attempt_id"]


async def test_admin_lists_and_views_attempt(client, db):
    attempt_id = await _run_attempt(client, db)

    listing = await client.get("/api/v1/admin/attempts")
    assert listing.status_code == 200
    assert any(a["id"] == attempt_id for a in listing.json()["data"])

    detail = await client.get(f"/api/v1/admin/attempts/{attempt_id}")
    assert detail.json()["data"]["status"] == "evaluated"


async def test_correct_score_recomputes_and_audits(client, db):
    attempt_id = await _run_attempt(client, db)

    # Override two criteria; final recomputes from criterion sum (no penalty here).
    resp = await client.patch(f"/api/v1/admin/attempts/{attempt_id}/score", json={
        "criteria": {"task_achievement": 5, "accuracy_vocabulary_grammar": 4},
        "reason": "Teacher calibration.",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    # raw 14 (4+4+3+3) -> 5+4+3+4 = 16; the -2 word-count penalty is preserved.
    assert data["score"]["raw"] == 16
    assert data["score"]["final"] == 14

    logs = await client.get("/api/v1/admin/audit-logs?entity_type=attempt")
    actions = [x["action"] for x in logs.json()["data"]]
    assert "correct_score" in actions


async def test_correct_final_score_directly(client, db):
    attempt_id = await _run_attempt(client, db)
    resp = await client.patch(f"/api/v1/admin/attempts/{attempt_id}/score", json={
        "final_score": 11, "reason": "Manual override.",
    })
    assert resp.json()["data"]["score"]["final"] == 11


async def test_correct_feedback(client, db):
    attempt_id = await _run_attempt(client, db)
    resp = await client.patch(f"/api/v1/admin/attempts/{attempt_id}/feedback", json={
        "recommendations": ["Practise linking words.", "Vary sentence length."],
        "reason": "Tailored advice.",
    })
    assert resp.json()["data"]["recommendations"] == [
        "Practise linking words.", "Vary sentence length.",
    ]


async def test_llm_calls_observability(client, db):
    await _run_attempt(client, db)
    resp = await client.get("/api/v1/admin/llm-calls?purpose=writing_evaluation")
    assert resp.status_code == 200
    calls = resp.json()["data"]
    assert len(calls) >= 1
    assert calls[0]["provider"] == "fake"


async def test_task_reject_audited(client, db):
    await seed_all(db)
    await db.commit()
    fake = FakeProvider(VALID_EVALUATION)
    from tests._fakes import VALID_GENERATION
    fake.set_response(VALID_GENERATION)
    app.dependency_overrides[get_llm_provider] = lambda: fake

    gen = await client.post("/api/v1/admin/tasks/batch-generate", json={
        "blueprint_code": "epe_b1_plus_blog_comment_v1", "count": 1,
    })
    task_id = gen.json()["data"][0]["id"]
    rej = await client.post(f"/api/v1/admin/tasks/{task_id}/reject")
    assert rej.json()["data"]["status"] == "rejected"

    logs = await client.get("/api/v1/admin/audit-logs?entity_type=task")
    assert "task_rejected" in [x["action"] for x in logs.json()["data"]]
