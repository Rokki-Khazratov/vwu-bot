"""Async evaluation path: 202/poll dispatch + worker task logic (Phase 5)."""

import uuid

import pytest

from app.content.seed import seed_all
from app.core.config import get_settings
from app.modules.evaluation.attempts_service import create_attempt
from app.workers import runtime, tasks
from tests._fakes import VALID_EVALUATION, FakeProvider

ANSWER = "I understand why the school wants to ban phones during lessons. " * 18


async def _start_session(client):
    sess = (await client.post("/api/v1/sessions", json={
        "subject_code": "english", "exam_profile_code": "epe_b1_plus",
        "skill_code": "writing", "task_family_code": "blog_comment", "mode": "single",
    })).json()["data"]
    sid, tid = sess["session"]["id"], sess["task"]["id"]
    await client.post(f"/api/v1/sessions/{sid}/start")
    return sid, tid


async def test_async_dispatch_returns_202_and_creates_job(client, db, monkeypatch):
    await seed_all(db)
    await db.commit()
    settings = get_settings()
    monkeypatch.setattr(settings, "eval_async", True, raising=False)
    # Stub Celery dispatch — we assert dispatch happened, task logic is tested separately.
    dispatched = {}
    monkeypatch.setattr(tasks.evaluate_attempt, "delay",
                        lambda *a, **k: dispatched.update(args=a))

    sid, tid = await _start_session(client)
    resp = await client.post("/api/v1/attempts", json={
        "session_id": sid, "task_id": tid, "answer": {"type": "text", "text": ANSWER},
    })
    assert resp.status_code == 202, resp.text
    body = resp.json()["data"]
    assert body["status"] == "evaluating"
    assert body["job_id"] and body["poll"].endswith("/result")
    assert dispatched["args"][0] == body["attempt_id"]

    # Result not ready yet -> poll returns 202.
    poll = await client.get(f"/api/v1/attempts/{body['attempt_id']}/result")
    assert poll.status_code == 202
    assert poll.json()["data"]["status"] == "evaluating"

    # Job is observable.
    jobs_list = (await client.get("/api/v1/admin/jobs?kind=evaluation")).json()["data"]
    assert any(j["id"] == body["job_id"] and j["status"] == "queued" for j in jobs_list)


@pytest.fixture
def _worker_db(monkeypatch):
    """Point worker tasks at the test session factory + fake provider."""
    from tests.conftest import _Session
    runtime.set_session_factory(_Session)
    monkeypatch.setattr(tasks, "get_llm_provider", lambda: FakeProvider(VALID_EVALUATION))
    yield
    runtime.set_session_factory(None)


async def test_worker_evaluates_attempt(client, db, _worker_db):
    await seed_all(db)
    await db.commit()
    sid, tid = await _start_session(client)
    attempt = await create_attempt(
        db, user_id=(await _first_user_id(db)), session_id=uuid.UUID(sid),
        task_id=uuid.UUID(tid), answer_type="text", answer_text=ANSWER,
    )
    await db.commit()

    # Run the worker core directly (same loop, test DB).
    from app.modules.system.jobs import create_job
    job = await create_job(db, kind="evaluation", ref_id=str(attempt.id))
    await db.commit()
    await tasks._evaluate_attempt_async(str(attempt.id), str(job.id))

    result = (await client.get(f"/api/v1/attempts/{attempt.id}/result")).json()["data"]
    assert result["status"] == "evaluated"
    assert result["score"]["final"] == 12  # 14 raw - 2 word-count penalty
    jobs_list = (await client.get("/api/v1/admin/jobs")).json()["data"]
    assert any(j["id"] == str(job.id) and j["status"] == "succeeded" for j in jobs_list)


async def _first_user_id(db):
    from sqlalchemy import select

    from app.modules.access.models import User
    return (await db.execute(
        select(User.id).where(User.telegram_id == 111111111)
    )).scalars().first()
