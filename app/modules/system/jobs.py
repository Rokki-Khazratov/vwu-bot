"""BackgroundJob lifecycle helpers (ТЗ §31)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.system.models import BackgroundJob

MAX_ATTEMPTS = 3


async def create_job(
    db: AsyncSession, *, kind: str, ref_id: str | None = None, payload: dict | None = None
) -> BackgroundJob:
    job = BackgroundJob(kind=kind, ref_id=ref_id, payload=payload, status="queued")
    db.add(job)
    await db.flush()
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> BackgroundJob | None:
    return await db.get(BackgroundJob, job_id)


async def mark_running(db: AsyncSession, job_id: uuid.UUID) -> None:
    job = await db.get(BackgroundJob, job_id)
    if job is not None:
        job.status = "running"
        job.attempts += 1
        await db.flush()


async def mark_succeeded(db: AsyncSession, job_id: uuid.UUID, result: dict | None = None) -> None:
    job = await db.get(BackgroundJob, job_id)
    if job is not None:
        job.status = "succeeded"
        job.result = result
        await db.flush()


async def mark_failed(db: AsyncSession, job_id: uuid.UUID, error: str) -> None:
    """Mark failed; transition to dead-letter once attempts are exhausted."""
    job = await db.get(BackgroundJob, job_id)
    if job is not None:
        job.status = "dead" if job.attempts >= MAX_ATTEMPTS else "failed"
        job.error = error[:1024]
        await db.flush()


async def list_jobs(
    db: AsyncSession, *, kind: str | None = None, status: str | None = None, limit: int = 50
) -> list[BackgroundJob]:
    stmt = select(BackgroundJob).order_by(BackgroundJob.created_at.desc()).limit(limit)
    if kind:
        stmt = stmt.where(BackgroundJob.kind == kind)
    if status:
        stmt = stmt.where(BackgroundJob.status == status)
    return list((await db.execute(stmt)).scalars())
