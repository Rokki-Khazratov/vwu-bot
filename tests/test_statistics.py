"""User statistics (Phase 3)."""

from app.content.seed import seed_all
from app.main import app
from app.modules.llm.factory import get_llm_provider
from tests._fakes import VALID_EVALUATION, FakeProvider

ANSWER_TEXT = "I understand why the school wants to ban phones during lessons. " * 18


async def _evaluated_attempt(client, db):
    await seed_all(db)
    await db.commit()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(VALID_EVALUATION)
    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english", "exam_profile_code": "epe_b1_plus",
        "skill_code": "writing", "task_family_code": "blog_comment", "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")
    await client.post("/api/v1/attempts", json={
        "session_id": sid, "task_id": tid, "answer": {"type": "text", "text": ANSWER_TEXT},
    })


async def test_overview_empty(client, db):
    await seed_all(db)
    await db.commit()
    data = (await client.get("/api/v1/statistics/overview")).json()["data"]
    assert data["sessions_completed"] == 0
    assert data["tasks_evaluated"] == 0


async def test_overview_after_attempt(client, db):
    await _evaluated_attempt(client, db)
    data = (await client.get("/api/v1/statistics/overview")).json()["data"]
    assert data["sessions_completed"] == 1
    assert data["tasks_evaluated"] == 1
    assert data["avg_score"] == 12.0
    assert data["average_percent"] == 60.0
    assert len(data["recent_sessions"]) == 1


async def test_criteria_trends(client, db):
    await _evaluated_attempt(client, db)
    data = (await client.get("/api/v1/statistics/criteria")).json()["data"]
    codes = {c["criterion_code"]: c for c in data["criteria"]}
    assert len(codes) == 4
    assert codes["task_achievement"]["avg_score"] == 4.0
    assert codes["accuracy_vocabulary_grammar"]["avg_score"] == 3.0


async def test_error_trends(client, db):
    await _evaluated_attempt(client, db)
    data = (await client.get("/api/v1/statistics/errors")).json()["data"]
    cats = {c["category"]: c["count"] for c in data["categories"]}
    assert cats.get("grammar") == 1
    assert data["severity"].get("minor") == 1


async def test_weaknesses_ranked(client, db):
    await _evaluated_attempt(client, db)
    data = (await client.get("/api/v1/statistics/weaknesses")).json()["data"]
    assert data["policy_version"] == "weakness_v1"
    weak = data["weaknesses"]
    assert len(weak) == 4
    # accuracy/range (avg 3) must be weaker than task_achievement (avg 4)
    by_code = {w["criterion_code"]: w["weakness_score"] for w in weak}
    assert by_code["accuracy_vocabulary_grammar"] > by_code["task_achievement"]
    assert weak[0]["weakness_score"] >= weak[-1]["weakness_score"]
