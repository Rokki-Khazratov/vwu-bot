"""End-to-end writing flow with a mocked LLM provider (ТЗ §39)."""

import uuid

from sqlalchemy import func, select

from app.content.seed import seed_all
from app.main import app
from app.modules.catalog.models import Guideline, TaskBlueprintGuideline
from app.modules.evaluation.models import Attempt, ErrorEvent, EvaluationResult
from app.modules.llm.factory import get_llm_provider
from tests._fakes import VALID_EVALUATION, FakeProvider

# ~250 words → falls in the no-penalty band (225–275).
ANSWER_TEXT = "word " * 250


async def _create_started_session(client) -> dict:
    resp = await client.post("/api/v1/sessions", json={
        "subject_code": "english",
        "task_code": "writing",
        "mode": "single",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    session_id = data["session"]["id"]
    task_id = data["task"]["id"]
    start = await client.post(f"/api/v1/sessions/{session_id}/start")
    assert start.status_code == 200
    return {"session_id": session_id, "task_id": task_id}


async def test_full_writing_flow(client, db):
    await seed_all(db)
    await db.commit()
    fake = FakeProvider(VALID_EVALUATION)
    app.dependency_overrides[get_llm_provider] = lambda: fake

    ids = await _create_started_session(client)
    resp = await client.post("/api/v1/attempts", json={
        "session_id": ids["session_id"],
        "task_id": ids["task_id"],
        "answer": {"type": "text", "text": ANSWER_TEXT},
    })
    assert resp.status_code == 200, resp.text
    payload = resp.json()["data"]

    assert payload["status"] == "evaluated"
    assert len(payload["criteria"]) == 4
    # 4 + 4 + 3 + 3 = 14 raw, no word-count penalty → final 14/20.
    assert payload["score"]["raw"] == 14
    assert payload["score"]["final"] == 14
    assert payload["score"]["max"] == 20
    assert len(payload["content_points"]) == 3
    assert payload["semantic_blocks"][0]["type"] == "heading"
    error_count = (await db.execute(select(func.count()).select_from(ErrorEvent))).scalar()
    assert error_count >= 1

    # Session is finalised.
    hist = await client.get("/api/v1/sessions/history")
    assert hist.json()["data"][0]["status"] == "completed"


async def test_attempt_idempotency(client, db):
    await seed_all(db)
    await db.commit()
    fake = FakeProvider(VALID_EVALUATION)
    app.dependency_overrides[get_llm_provider] = lambda: fake

    ids = await _create_started_session(client)
    body = {
        "session_id": ids["session_id"],
        "task_id": ids["task_id"],
        "answer": {"type": "text", "text": ANSWER_TEXT},
    }
    headers = {"Idempotency-Key": "abc-123"}
    first = await client.post("/api/v1/attempts", json=body, headers=headers)
    second = await client.post("/api/v1/attempts", json=body, headers=headers)

    assert first.json()["data"]["attempt_id"] == second.json()["data"]["attempt_id"]
    assert len(fake.calls) == 1  # provider invoked only once


async def test_dependency_zero_when_ta_zero(client, db):
    await seed_all(db)
    await db.commit()
    zero_ta = {**VALID_EVALUATION, "criteria": [
        {**c, "score": 0, "selected_band": 0} if c["code"] == "task_achievement" else c
        for c in VALID_EVALUATION["criteria"]
    ]}
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(zero_ta)

    ids = await _create_started_session(client)
    resp = await client.post("/api/v1/attempts", json={
        "session_id": ids["session_id"],
        "task_id": ids["task_id"],
        "answer": {"type": "text", "text": ANSWER_TEXT},
    })
    payload = resp.json()["data"]
    # task_achievement = 0 → all criteria 0 → final 0.
    assert payload["score"]["raw"] == 0
    assert payload["score"]["final"] == 0


async def test_writing_evaluation_uses_linked_guidelines(client, db):
    seeded = await seed_all(db)
    guideline = Guideline(
        code="writing_eval_extra",
        version="v1",
        default_role="evaluation",
        body_markdown="Always mention whether the answer follows the uploaded sample rules.",
        checksum="test",
        status="active",
    )
    db.add(guideline)
    await db.flush()
    db.add(
        TaskBlueprintGuideline(
            blueprint_id=seeded["blueprint"].id,
            guideline_id=guideline.id,
            role="evaluation",
            position=0,
            include_in_generation=False,
            include_in_evaluation=True,
        )
    )
    await db.commit()
    fake = FakeProvider(VALID_EVALUATION)
    app.dependency_overrides[get_llm_provider] = lambda: fake

    ids = await _create_started_session(client)
    resp = await client.post("/api/v1/attempts", json={
        "session_id": ids["session_id"],
        "task_id": ids["task_id"],
        "answer": {"type": "text", "text": ANSWER_TEXT},
    })
    assert resp.status_code == 200, resp.text
    assert "uploaded sample rules" in fake.calls[0].system_prompt

    attempt = await db.get(Attempt, uuid.UUID(resp.json()["data"]["attempt_id"]))
    result = (await db.execute(
        select(EvaluationResult).where(EvaluationResult.attempt_id == attempt.id)
    )).scalar_one()
    guideline_codes = [item["code"] for item in result.provider_metadata["guidelines"]]
    assert "writing_eval_extra" in guideline_codes
    assert "english_writing_evaluation" in guideline_codes


async def test_grammar_flow_uses_answer_key(client, db):
    await seed_all(db)
    await db.commit()
    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english",
        "task_code": "grammar",
        "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")

    resp = await client.post("/api/v1/attempts", json={
        "session_id": sid,
        "task_id": tid,
        "answer": {"type": "text", "text": "1. had\n2. since\n3. in\n4. wrong\n5. helpful"},
    })
    assert resp.status_code == 200, resp.text
    payload = resp.json()["data"]
    assert payload["score"]["final"] == 8
    assert payload["score"]["max"] == 10
    assert payload["errors"][0]["category"] == "grammar"


async def test_reading_flow_uses_answer_key(client, db):
    await seed_all(db)
    await db.commit()
    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english",
        "task_code": "reading",
        "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")

    resp = await client.post("/api/v1/attempts", json={
        "session_id": sid,
        "task_id": tid,
        "answer": {
            "type": "text",
            "text": "1. bike lanes\n2. shop owners\n3. true\n4. false",
        },
    })
    assert resp.status_code == 200, resp.text
    payload = resp.json()["data"]
    assert payload["score"]["final"] == 8
    assert payload["score"]["max"] == 8
    assert payload["errors"] == []
