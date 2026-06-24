from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import TaskBlueprint
from app.modules.evaluation.models import OutputSchema, PromptTemplate
from app.modules.tasks.models import TaskInstance


async def get_blueprint_by_code(db: AsyncSession, code: str) -> TaskBlueprint | None:
    return (
        await db.execute(
            select(TaskBlueprint)
            .where(TaskBlueprint.code == code)
            .order_by(TaskBlueprint.version.desc())
        )
    ).scalars().first()


async def get_prompt(db: AsyncSession, code: str) -> PromptTemplate | None:
    return (
        await db.execute(select(PromptTemplate).where(PromptTemplate.code == code))
    ).scalar_one_or_none()


async def get_output_schema(db: AsyncSession, code: str) -> OutputSchema | None:
    return (
        await db.execute(select(OutputSchema).where(OutputSchema.code == code))
    ).scalar_one_or_none()


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> TaskInstance | None:
    return (
        await db.execute(select(TaskInstance).where(TaskInstance.id == task_id))
    ).scalar_one_or_none()


async def recent_titles(db: AsyncSession, blueprint_id: uuid.UUID, limit: int = 20) -> list[str]:
    rows = await db.execute(
        select(TaskInstance.title)
        .where(TaskInstance.blueprint_id == blueprint_id)
        .order_by(TaskInstance.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars())


async def find_by_checksum(db: AsyncSession, checksum: str) -> TaskInstance | None:
    return (
        await db.execute(select(TaskInstance).where(TaskInstance.checksum == checksum))
    ).scalar_one_or_none()


async def list_tasks(
    db: AsyncSession, blueprint_code: str | None = None, status: str | None = None, limit: int = 50
) -> list[TaskInstance]:
    stmt = select(TaskInstance).order_by(TaskInstance.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(TaskInstance.status == status)
    if blueprint_code:
        bp = await get_blueprint_by_code(db, blueprint_code)
        if bp is None:
            return []
        stmt = stmt.where(TaskInstance.blueprint_id == bp.id)
    return list((await db.execute(stmt)).scalars())
