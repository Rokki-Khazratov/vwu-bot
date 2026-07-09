from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Guideline, TaskBlueprintGuideline, TaskInstanceGuideline

_PURPOSE_ROLES = {
    "generation": {"generation", "example", "notes"},
    "evaluation": {"evaluation", "example", "notes"},
}


def _include_for(link: TaskBlueprintGuideline | TaskInstanceGuideline, purpose: str) -> bool:
    if purpose == "generation" and not link.include_in_generation:
        return False
    if purpose == "evaluation" and not link.include_in_evaluation:
        return False
    return link.role in _PURPOSE_ROLES.get(purpose, {link.role})


async def linked_guidelines_for_blueprint(
    db: AsyncSession, blueprint_id: uuid.UUID, *, purpose: str
) -> list[dict[str, Any]]:
    rows = await db.execute(
        select(TaskBlueprintGuideline, Guideline)
        .join(Guideline, TaskBlueprintGuideline.guideline_id == Guideline.id)
        .where(
            TaskBlueprintGuideline.blueprint_id == blueprint_id,
            Guideline.status == "active",
        )
        .order_by(TaskBlueprintGuideline.position, Guideline.code)
    )
    return [
        _serialize(link, guideline)
        for link, guideline in rows.all()
        if _include_for(link, purpose)
    ]


async def linked_guidelines_for_task(
    db: AsyncSession, task_id: uuid.UUID, *, purpose: str
) -> list[dict[str, Any]]:
    rows = await db.execute(
        select(TaskInstanceGuideline, Guideline)
        .join(Guideline, TaskInstanceGuideline.guideline_id == Guideline.id)
        .where(TaskInstanceGuideline.task_id == task_id, Guideline.status == "active")
        .order_by(TaskInstanceGuideline.position, Guideline.code)
    )
    return [
        _serialize(link, guideline)
        for link, guideline in rows.all()
        if _include_for(link, purpose)
    ]


async def guidelines_for_task_context(
    db: AsyncSession, *, task_id: uuid.UUID, blueprint_id: uuid.UUID, purpose: str
) -> list[dict[str, Any]]:
    task_guidelines = await linked_guidelines_for_task(db, task_id, purpose=purpose)
    blueprint_guidelines = await linked_guidelines_for_blueprint(
        db, blueprint_id, purpose=purpose
    )
    seen: set[tuple[str, str, str]] = set()
    merged: list[dict[str, Any]] = []
    for item in task_guidelines + blueprint_guidelines:
        key = (item["code"], item["version"], item["role"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def format_guideline_block(guidelines: list[dict[str, Any]]) -> str:
    if not guidelines:
        return ""
    parts = ["Additional role-based guidelines:"]
    for item in guidelines:
        body = (item.get("body_markdown") or "").strip()
        if not body:
            continue
        parts.append(
            f"\n### {item['role']}: {item['code']}@{item['version']}\n{body}"
        )
    return "\n".join(parts).strip()


def guideline_metadata(guidelines: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "id": str(item["id"]),
            "code": item["code"],
            "version": item["version"],
            "role": item["role"],
        }
        for item in guidelines
    ]


def _serialize(
    link: TaskBlueprintGuideline | TaskInstanceGuideline, guideline: Guideline
) -> dict[str, Any]:
    return {
        "id": guideline.id,
        "code": guideline.code,
        "version": guideline.version,
        "role": link.role,
        "position": link.position,
        "body_markdown": guideline.body_markdown,
    }
