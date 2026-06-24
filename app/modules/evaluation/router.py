"""Evaluation Router: selects the evaluator from the task's EvaluationProfile.

Phase 1 supports the LLM writing evaluator. Rule-based evaluators
(ExactMatch/MultipleChoice/Numeric/…) land in Phase 2 (ТЗ §16).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EvaluationFailed
from app.modules.catalog.models import TaskBlueprint
from app.modules.evaluation import repository as repo
from app.modules.evaluation.models import Attempt
from app.modules.llm.provider import LLMProvider
from app.modules.tasks.models import TaskInstance
from app.modules.writing.engine import WritingEvaluation, evaluate_writing


async def route_and_evaluate(
    db: AsyncSession, provider: LLMProvider, *, task: TaskInstance, attempt: Attempt
) -> WritingEvaluation:
    blueprint = (
        await db.execute(select(TaskBlueprint).where(TaskBlueprint.id == task.blueprint_id))
    ).scalar_one_or_none()
    if blueprint is None or blueprint.evaluation_profile_id is None:
        raise EvaluationFailed("Task has no evaluation profile.")

    profile = await repo.get_evaluation_profile(db, blueprint.evaluation_profile_id)
    if profile is None:
        raise EvaluationFailed("Evaluation profile not found.")

    if profile.evaluator_code == "LLMWritingEvaluator":
        return await evaluate_writing(db, provider, task=task, attempt=attempt, profile=profile)

    raise EvaluationFailed(
        f"Evaluator '{profile.evaluator_code}' is not available in this version."
    )
