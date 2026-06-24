"""Rubric-driven writing evaluation pipeline (ТЗ §18, Writing §13–18).

The LLM selects criterion bands and surfaces errors; the backend applies the
dependency rule, the word-count penalty and computes the final score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EvaluationFailed
from app.modules.evaluation import repository as repo
from app.modules.evaluation.models import (
    Attempt,
    ContentPointAssessment,
    CriterionScore,
    ErrorEvent,
    EvaluationProfile,
    EvaluationResult,
)
from app.modules.evaluation.scoring import (
    apply_dependency_rules,
    compute_final_score,
    word_count_penalty,
)
from app.modules.llm.prompt import render_template
from app.modules.llm.provider import LLMProvider, LLMRequest
from app.modules.llm.repository import record_llm_call
from app.modules.tasks.models import TaskInstance
from app.modules.writing.semantic import build_feedback_blocks


@dataclass
class WritingEvaluation:
    result: EvaluationResult
    semantic_blocks: list[dict[str, Any]]


def _rubric_block(criteria: list, bands_by_criterion: dict) -> str:
    lines: list[str] = []
    for crit in criteria:
        lines.append(f"\n## {crit.name} (code: {crit.code}, {crit.min_score}-{crit.max_score})")
        for band in bands_by_criterion.get(crit.id, []):
            lines.append(f"  {band.score}: {band.descriptor}")
    return "\n".join(lines)


def _content_points_block(task: TaskInstance) -> str:
    points = task.content_points or []
    return "\n".join(f"- {p['id']}: {p['instruction']}" for p in points)


async def evaluate_writing(
    db: AsyncSession,
    provider: LLMProvider,
    *,
    task: TaskInstance,
    attempt: Attempt,
    profile: EvaluationProfile,
) -> WritingEvaluation:
    rubric = await repo.get_rubric(db, profile.rubric_id)
    prompt = await repo.get_prompt(db, profile.prompt_template_id)
    schema = await repo.get_output_schema(db, profile.output_schema_id)
    if rubric is None or prompt is None or schema is None:
        raise EvaluationFailed("Evaluation profile is missing rubric/prompt/schema.")

    criteria = await repo.get_criteria(db, rubric.id)
    bands_by_criterion = {c.id: await repo.get_bands(db, c.id) for c in criteria}
    penalty_rules = await repo.get_penalty_rules(db, rubric.id)
    dependency_rules = await repo.get_dependency_rules(db, rubric.id)

    content = task.content or {}
    source = content.get("source_post", {})
    variables = {
        "rubric_block": _rubric_block(criteria, bands_by_criterion),
        "task_title": task.title,
        "source_author": source.get("author", ""),
        "source_body": source.get("body", ""),
        "instruction": content.get("instruction", ""),
        "content_points_block": _content_points_block(task),
        "target_words": content.get("target_words", ""),
        "rubric_code": rubric.code,
        "word_count": attempt.word_count or 0,
        "candidate_text": attempt.normalized_answer or "",
    }

    result_llm = await provider.generate_structured(
        LLMRequest(
            purpose="writing_evaluation",
            system_prompt=render_template(prompt.system_template, variables),
            user_prompt=render_template(prompt.user_template, variables),
            output_schema=schema.json_schema,
            temperature=profile.temperature,
            max_repair_retries=profile.max_retries,
        )
    )
    await record_llm_call(
        db, result_llm, purpose="writing_evaluation",
        prompt_code=prompt.code, prompt_version=prompt.version,
        schema_code=schema.code, schema_version=schema.version,
    )

    data = result_llm.data
    raw_scores = {c["code"]: int(c["score"]) for c in data["criteria"]}

    # Deterministic post-processing (Writing §17).
    adjusted = apply_dependency_rules(raw_scores, [
        {"condition": r.condition, "action": r.action, "priority": r.priority}
        for r in dependency_rules
    ])
    raw_total = float(sum(adjusted.values()))

    wc_rule = next((r for r in penalty_rules if r.rule_type == "word_count"), None)
    penalty = word_count_penalty(
        attempt.word_count or 0, {"condition": wc_rule.condition} if wc_rule else None
    )
    max_score = float(rubric.max_score)
    final = compute_final_score(raw_total, penalty.penalty, penalty.zero_total, max_score)

    # Persist result + children.
    result = EvaluationResult(
        attempt_id=attempt.id,
        status="evaluated",
        raw_score=raw_total,
        penalty_total=round(final - raw_total, 2),
        final_score=final,
        max_score=max_score,
        summary=None,
        strengths=data.get("strengths", []),
        recommendations=data.get("recommendations", []),
        confidence=data.get("confidence"),
        raw_provider_response=result_llm.raw_response,
        provider_metadata={
            "model": result_llm.model,
            "provider": result_llm.provider,
            "attempts": result_llm.attempts,
            "penalties": [{"code": "word_count", "value": penalty.penalty,
                           "details": penalty.details}],
        },
    )
    db.add(result)
    await db.flush()

    for c in data["criteria"]:
        db.add(CriterionScore(
            evaluation_result_id=result.id,
            criterion_code=c["code"],
            score=adjusted.get(c["code"], c["score"]),
            max_score=5,
            selected_band=c.get("selected_band"),
            explanation=c.get("explanation"),
            evidence=c.get("evidence", []),
        ))
    for cp in data.get("content_points", []):
        db.add(ContentPointAssessment(
            evaluation_result_id=result.id,
            content_point_id=cp["id"],
            status=cp["status"],
            evidence=cp.get("evidence"),
            comment=cp.get("comment"),
        ))
    for err in data.get("errors", []):
        db.add(ErrorEvent(
            attempt_id=attempt.id,
            evaluation_result_id=result.id,
            category=err.get("category", "grammar"),
            subcategory=err.get("subcategory"),
            severity=err.get("severity"),
            source_fragment=err.get("source_fragment"),
            corrected_fragment=err.get("corrected_fragment"),
            explanation=err.get("explanation"),
            criterion_code=err.get("criterion_code"),
        ))

    # Update attempt scores.
    attempt.status = "evaluated"
    attempt.evaluator_code = "LLMWritingEvaluator"
    attempt.evaluation_profile_id = profile.id
    attempt.score_raw = raw_total
    attempt.penalty_total = round(final - raw_total, 2)
    attempt.score_final = final
    attempt.score_max = max_score
    await db.flush()

    blocks = build_feedback_blocks(
        data, final_score=final, raw_score=raw_total, max_score=max_score,
        penalty=penalty, adjusted_scores=adjusted,
    )
    return WritingEvaluation(result=result, semantic_blocks=blocks)
