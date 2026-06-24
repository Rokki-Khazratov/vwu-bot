from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluation.models import (
    Attempt,
    DependencyRule,
    EvaluationProfile,
    EvaluationResult,
    OutputSchema,
    PenaltyRule,
    PerformanceBand,
    PromptTemplate,
    Rubric,
    RubricCriterion,
)


async def get_evaluation_profile(
    db: AsyncSession, profile_id: uuid.UUID
) -> EvaluationProfile | None:
    return (
        await db.execute(select(EvaluationProfile).where(EvaluationProfile.id == profile_id))
    ).scalar_one_or_none()


async def get_rubric(db: AsyncSession, rubric_id: uuid.UUID) -> Rubric | None:
    return (await db.execute(select(Rubric).where(Rubric.id == rubric_id))).scalar_one_or_none()


async def get_criteria(db: AsyncSession, rubric_id: uuid.UUID) -> list[RubricCriterion]:
    rows = await db.execute(
        select(RubricCriterion)
        .where(RubricCriterion.rubric_id == rubric_id)
        .order_by(RubricCriterion.position)
    )
    return list(rows.scalars())


async def get_bands(db: AsyncSession, criterion_id: uuid.UUID) -> list[PerformanceBand]:
    rows = await db.execute(
        select(PerformanceBand)
        .where(PerformanceBand.criterion_id == criterion_id)
        .order_by(PerformanceBand.score.desc())
    )
    return list(rows.scalars())


async def get_penalty_rules(db: AsyncSession, rubric_id: uuid.UUID) -> list[PenaltyRule]:
    rows = await db.execute(
        select(PenaltyRule)
        .where(PenaltyRule.rubric_id == rubric_id, PenaltyRule.is_active.is_(True))
        .order_by(PenaltyRule.priority)
    )
    return list(rows.scalars())


async def get_dependency_rules(db: AsyncSession, rubric_id: uuid.UUID) -> list[DependencyRule]:
    rows = await db.execute(
        select(DependencyRule).where(DependencyRule.rubric_id == rubric_id)
    )
    return list(rows.scalars())


async def get_prompt(db: AsyncSession, prompt_id: uuid.UUID) -> PromptTemplate | None:
    return (
        await db.execute(select(PromptTemplate).where(PromptTemplate.id == prompt_id))
    ).scalar_one_or_none()


async def get_output_schema(db: AsyncSession, schema_id: uuid.UUID) -> OutputSchema | None:
    return (
        await db.execute(select(OutputSchema).where(OutputSchema.id == schema_id))
    ).scalar_one_or_none()


async def get_attempt(db: AsyncSession, attempt_id: uuid.UUID) -> Attempt | None:
    return (await db.execute(select(Attempt).where(Attempt.id == attempt_id))).scalar_one_or_none()


async def get_result_for_attempt(
    db: AsyncSession, attempt_id: uuid.UUID
) -> EvaluationResult | None:
    return (
        await db.execute(
            select(EvaluationResult).where(EvaluationResult.attempt_id == attempt_id)
        )
    ).scalar_one_or_none()
