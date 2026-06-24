"""Celery tasks (ТЗ §31).

The async cores (``_*_async``) hold the logic and are awaited directly in tests;
the Celery tasks are thin sync wrappers that run them over a worker session.
"""

from __future__ import annotations

import logging
import uuid

from app.core.logging import log_event
from app.modules.evaluation.attempts_service import evaluate_attempt_by_id
from app.modules.evaluation.models import Attempt
from app.modules.llm.factory import get_llm_provider
from app.modules.system import jobs
from app.modules.tasks.generation import generate_tasks
from app.modules.training import service as training_service
from app.workers.celery_app import celery_app
from app.workers.runtime import run, worker_session

logger = logging.getLogger("app.workers")


async def _evaluate_attempt_async(attempt_id: str, job_id: str | None) -> None:
    aid = uuid.UUID(attempt_id)
    jid = uuid.UUID(job_id) if job_id else None
    if jid:
        async with worker_session() as db:
            await jobs.mark_running(db, jid)
    try:
        async with worker_session() as db:
            await evaluate_attempt_by_id(db, get_llm_provider(), aid)
        if jid:
            async with worker_session() as db:
                await jobs.mark_succeeded(db, jid)
    except Exception as exc:
        async with worker_session() as db:
            attempt = await db.get(Attempt, aid)
            if attempt is not None and attempt.status != "evaluated":
                attempt.status = "failed"
            if jid:
                await jobs.mark_failed(db, jid, str(exc))
        raise


async def _batch_generate_async(blueprint_code: str, count: int, job_id: str | None) -> dict:
    jid = uuid.UUID(job_id) if job_id else None
    if jid:
        async with worker_session() as db:
            await jobs.mark_running(db, jid)
    try:
        async with worker_session() as db:
            created = await generate_tasks(
                db, get_llm_provider(), blueprint_code=blueprint_code, count=count
            )
            result = {"created": len(created)}
        if jid:
            async with worker_session() as db:
                await jobs.mark_succeeded(db, jid, result)
        return result
    except Exception as exc:
        if jid:
            async with worker_session() as db:
                await jobs.mark_failed(db, jid, str(exc))
        raise


async def _cleanup_expired_sessions_async() -> int:
    async with worker_session() as db:
        return await training_service.expire_due_sessions(db)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def evaluate_attempt(self, attempt_id: str, job_id: str | None = None) -> None:
    try:
        run(_evaluate_attempt_async(attempt_id, job_id))
    except Exception as exc:  # noqa: BLE001
        log_event(logger, logging.ERROR, "evaluation_task_failed",
                  attempt_id=attempt_id, error=str(exc))
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def batch_generate(self, blueprint_code: str, count: int, job_id: str | None = None) -> None:
    try:
        run(_batch_generate_async(blueprint_code, count, job_id))
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc) from exc


@celery_app.task
def cleanup_expired_sessions() -> int:
    return run(_cleanup_expired_sessions_async())
