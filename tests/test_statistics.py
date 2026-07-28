"""User statistics (Phase 3)."""

from app.content.seed import seed_all
from app.main import app
from app.modules.llm.factory import get_llm_provider
from tests._fakes import VALID_EVALUATION, FakeProvider

ANSWER_TEXT = "I understand why the school wants to ban phones during lessons. " * 18


async def _evaluated_attempt(client, db):
    await seed_all(db)
    await db.commit()
    provider = FakeProvider(VALID_EVALUATION)
    app.dependency_overrides[get_llm_provider] = lambda: provider
    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english", "task_code": "writing", "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")
    attempt = await client.post("/api/v1/attempts", json={
        "session_id": sid, "task_id": tid, "answer": {"type": "text", "text": ANSWER_TEXT},
    })
    return {
        "session_id": sid,
        "task_id": tid,
        "attempt": attempt.json()["data"],
        "provider": provider,
    }


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


async def test_diagnosis_empty(client, db):
    await seed_all(db)
    await db.commit()
    data = (await client.get("/api/v1/statistics/diagnosis")).json()["data"]
    assert data["policy_version"] == "diagnosis_v1"
    assert data["summary"]["tasks_evaluated"] == 0
    assert data["focus_items"] == []


async def test_diagnosis_after_attempt_has_focus_items(client, db):
    await _evaluated_attempt(client, db)
    data = (await client.get("/api/v1/statistics/diagnosis")).json()["data"]
    assert data["summary"]["tasks_evaluated"] == 1
    types = {item["type"] for item in data["focus_items"]}
    assert "weak_criterion" in types
    assert "repeated_error" in types
    first = data["focus_items"][0]
    assert first["recommended_action"]["type"] == "train"
    assert first["filters"]


async def test_history_filters_and_annotations(client, db):
    await _evaluated_attempt(client, db)

    by_task = (await client.get("/api/v1/sessions/history?task_code=writing")).json()["data"]
    assert len(by_task) == 1
    assert by_task[0]["task_code"] == "writing"
    assert by_task[0]["weakest_criterion"]["criterion_code"] in {
        "range_vocabulary_grammar",
        "accuracy_vocabulary_grammar",
    }
    assert by_task[0]["top_errors"][0]["category"] == "grammar"

    by_error = (
        await client.get("/api/v1/sessions/history?error_category=grammar")
    ).json()["data"]
    assert len(by_error) == 1

    no_match = (
        await client.get("/api/v1/sessions/history?criterion_code=does_not_exist")
    ).json()["data"]
    assert no_match == []


async def test_attempt_analysis_returns_persisted_payload_without_llm(client, db):
    ids = await _evaluated_attempt(client, db)
    before_calls = len(ids["provider"].calls)
    attempt_id = ids["attempt"]["attempt_id"]

    analysis = (await client.get(f"/api/v1/attempts/{attempt_id}/analysis")).json()["data"]

    after_calls = len(ids["provider"].calls)
    assert after_calls == before_calls
    assert analysis["task"]["title"]
    assert analysis["answer"]["word_count"] is not None
    assert analysis["score"]["final"] == 12
    assert analysis["errors"][0]["category"] == "grammar"
