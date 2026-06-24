"""Seed loader: reads versioned content files and upserts them into the DB.

Run as ``python -m app.content.seed``. Idempotent — safe to re-run.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.core.logging import configure_logging
from app.modules.access.models import User
from app.modules.catalog.models import (
    ExamProfile,
    Skill,
    Subject,
    TaskBlueprint,
    TaskFamily,
)
from app.modules.evaluation.models import (
    DependencyRule,
    ErrorTaxonomy,
    EvaluationProfile,
    OutputSchema,
    PenaltyRule,
    PerformanceBand,
    PromptTemplate,
    Rubric,
    RubricCriterion,
)
from app.modules.tasks.models import TaskInstance

PROFILE_DIR = Path(__file__).parent / "english" / "epe_b1_plus"


def _yaml(name: str) -> dict[str, Any]:
    return yaml.safe_load((PROFILE_DIR / name).read_text(encoding="utf-8"))


def _json(name: str) -> dict[str, Any]:
    return json.loads((PROFILE_DIR / name).read_text(encoding="utf-8"))


async def _get(db: AsyncSession, model, **match):
    stmt = select(model)
    for key, value in match.items():
        stmt = stmt.where(getattr(model, key) == value)
    return (await db.execute(stmt)).scalar_one_or_none()


async def _upsert(db: AsyncSession, model, match: dict, defaults: dict):
    obj = await _get(db, model, **match)
    if obj is None:
        obj = model(**match, **defaults)
        db.add(obj)
    else:
        for key, value in defaults.items():
            setattr(obj, key, value)
    await db.flush()
    return obj


async def seed_all(db: AsyncSession) -> dict[str, Any]:
    """Seed the English EPE B1+ profile. Returns key created/updated objects."""
    catalog = _yaml("catalog.yaml")
    rubric_data = _yaml("rubric.yaml")
    eval_prompt = _yaml("evaluation_prompt.yaml")
    gen_prompt = _yaml("generation_prompt.yaml")
    taxonomy = _yaml("error_taxonomy.yaml")
    tasks = _yaml("tasks.yaml")["tasks"]
    eval_schema = _json("output_schema.json")
    gen_schema = _json("generation_schema.json")

    # --- Catalog ---
    subject = await _upsert(
        db, Subject, {"code": catalog["subject"]["code"]},
        {"name": catalog["subject"]["name"], "description": catalog["subject"].get("description")},
    )
    exam = await _upsert(
        db, ExamProfile,
        {"subject_id": subject.id, "code": catalog["exam_profile"]["code"]},
        {
            "name": catalog["exam_profile"]["name"],
            "level": catalog["exam_profile"].get("level"),
            "version": catalog["exam_profile"].get("version", "v1"),
            "description": catalog["exam_profile"].get("description"),
        },
    )
    skill = await _upsert(
        db, Skill, {"exam_profile_id": exam.id, "code": catalog["skill"]["code"]},
        {"name": catalog["skill"]["name"], "position": catalog["skill"].get("position", 0)},
    )
    family = await _upsert(
        db, TaskFamily, {"skill_id": skill.id, "code": catalog["task_family"]["code"]},
        {
            "name": catalog["task_family"]["name"],
            "answer_format": catalog["task_family"]["answer_format"],
            "default_evaluator_code": catalog["task_family"].get("default_evaluator_code"),
            "description": catalog["task_family"].get("description"),
        },
    )

    # --- Rubric + criteria + bands ---
    rubric = await _upsert(
        db, Rubric, {"code": rubric_data["code"], "version": rubric_data["version"]},
        {
            "name": rubric_data["name"],
            "exam_profile_id": exam.id,
            "task_family_id": family.id,
            "max_score": rubric_data["max_score"],
            "description": rubric_data.get("description"),
        },
    )
    for crit in rubric_data["criteria"]:
        criterion = await _upsert(
            db, RubricCriterion, {"rubric_id": rubric.id, "code": crit["code"]},
            {
                "name": crit["name"],
                "position": crit.get("position", 0),
                "min_score": crit.get("min_score", 0),
                "max_score": crit.get("max_score", 5),
                "weight": crit.get("weight", 1.0),
            },
        )
        for band in crit["bands"]:
            existing = await _get(
                db, PerformanceBand, criterion_id=criterion.id, score=band["score"]
            )
            if existing is None:
                db.add(PerformanceBand(criterion_id=criterion.id, score=band["score"],
                                       descriptor=band["descriptor"].strip()))
            else:
                existing.descriptor = band["descriptor"].strip()
    await db.flush()

    # --- Penalty & dependency rules (replace to keep config in sync) ---
    for pr in rubric_data.get("penalty_rules", []):
        existing = await _get(db, PenaltyRule, rubric_id=rubric.id, code=pr["code"])
        if existing is None:
            db.add(PenaltyRule(rubric_id=rubric.id, code=pr["code"], rule_type=pr["rule_type"],
                               condition=pr["condition"], action=pr.get("action", {}),
                               priority=pr.get("priority", 0)))
        else:
            existing.condition = pr["condition"]
            existing.action = pr.get("action", {})
    existing_deps = (await db.execute(
        select(DependencyRule).where(DependencyRule.rubric_id == rubric.id)
    )).scalars().all()
    if not existing_deps:
        for dr in rubric_data.get("dependency_rules", []):
            db.add(DependencyRule(rubric_id=rubric.id, condition=dr["condition"],
                                  action=dr["action"], priority=dr.get("priority", 0)))
    await db.flush()

    # --- Prompts, schemas, taxonomy ---
    eval_prompt_row = await _upsert(
        db, PromptTemplate, {"code": eval_prompt["code"], "version": eval_prompt["version"]},
        {
            "purpose": eval_prompt["purpose"],
            "system_template": eval_prompt["system_template"],
            "user_template": eval_prompt["user_template"],
            "provider_hint": eval_prompt.get("provider_hint"),
            "model_hint": eval_prompt.get("model_hint"),
            "settings": eval_prompt.get("settings"),
        },
    )
    await _upsert(
        db, PromptTemplate, {"code": gen_prompt["code"], "version": gen_prompt["version"]},
        {
            "purpose": gen_prompt["purpose"],
            "system_template": gen_prompt["system_template"],
            "user_template": gen_prompt["user_template"],
            "provider_hint": gen_prompt.get("provider_hint"),
            "model_hint": gen_prompt.get("model_hint"),
            "settings": gen_prompt.get("settings"),
        },
    )
    eval_schema_row = await _upsert(
        db, OutputSchema, {"code": eval_schema["title"], "version": "v1"},
        {"json_schema": eval_schema},
    )
    await _upsert(
        db, OutputSchema, {"code": gen_schema["title"], "version": "v1"},
        {"json_schema": gen_schema},
    )
    taxonomy_row = await _upsert(
        db, ErrorTaxonomy, {"code": taxonomy["code"], "version": taxonomy["version"]},
        {"name": taxonomy["name"], "subject_id": subject.id, "categories": taxonomy},
    )

    # --- Evaluation profile ---
    eval_profile = await _upsert(
        db, EvaluationProfile, {"code": "epe_b1_plus_blog_eval_v1", "version": "v1"},
        {
            "task_family_id": family.id,
            "evaluator_code": "LLMWritingEvaluator",
            "rubric_id": rubric.id,
            "prompt_template_id": eval_prompt_row.id,
            "output_schema_id": eval_schema_row.id,
            "error_taxonomy_id": taxonomy_row.id,
            "temperature": 0.2,
            "max_retries": 1,
            "confidence_threshold": 0.5,
        },
    )

    # --- Blueprint (link rubric + evaluation profile) ---
    bp = catalog["blueprint"]
    blueprint = await _upsert(
        db, TaskBlueprint, {"code": bp["code"], "version": bp.get("version", "v1")},
        {
            "task_family_id": family.id,
            "title": bp["title"],
            "difficulty": bp.get("difficulty"),
            "recommended_minutes": bp.get("recommended_minutes"),
            "target_word_count_min": bp.get("target_word_count_min"),
            "target_word_count_max": bp.get("target_word_count_max"),
            "max_score": bp.get("max_score"),
            "rubric_id": rubric.id,
            "evaluation_profile_id": eval_profile.id,
            "answer_schema": {"type": "text"},
        },
    )

    # --- Sample tasks ---
    for t in tasks:
        await _upsert(
            db, TaskInstance, {"checksum": t["checksum"]},
            {
                "blueprint_id": blueprint.id,
                "title": t["title"],
                "difficulty": t.get("difficulty"),
                "content": {
                    "source_post": t["source_post"],
                    "instruction": t["instruction"],
                    "target_words": t.get("target_words"),
                },
                "content_points": t["content_points"],
                "answer_config": {"type": "text"},
                "max_score": bp.get("max_score"),
                "recommended_minutes": t.get("recommended_minutes"),
                "status": "active",
            },
        )

    # --- Allowlist users ---
    for tid in get_settings().allowlist_telegram_ids:
        await _upsert(db, User, {"telegram_id": tid}, {"status": "active"})

    await db.flush()
    return {"subject": subject, "blueprint": blueprint, "rubric": rubric}


async def main() -> None:
    configure_logging(get_settings().log_level)
    async with SessionFactory() as db:
        await seed_all(db)
        await db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
