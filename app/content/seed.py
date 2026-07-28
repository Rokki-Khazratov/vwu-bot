"""Seed loader: reads versioned content files and upserts them into the DB.

Run as ``python -m app.content.seed``. Idempotent — safe to re-run.
"""

from __future__ import annotations

import asyncio
import hashlib
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
    Guideline,
    Skill,
    Subject,
    SubjectTask,
    TaskBlueprint,
    TaskBlueprintGuideline,
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
GUIDELINES_DIR = PROFILE_DIR / "guidelines"
GUIDELINE_ROLES = ("generation", "evaluation", "examples", "notes")

SUBJECT_TASK_DEFAULTS = {
    "writing": {
        "name": "Writing",
        "position": 1,
        "answer_format": "text",
        "default_evaluator_code": "LLMWritingEvaluator",
        "description": "Write exam-style English responses.",
    },
    "grammar": {
        "name": "Grammar",
        "position": 2,
        "answer_format": "structured",
        "default_evaluator_code": "DeterministicGrammarEvaluator",
        "description": "Language in Use and grammar practice.",
    },
    "reading": {
        "name": "Reading",
        "position": 3,
        "answer_format": "structured",
        "default_evaluator_code": "DeterministicReadingEvaluator",
        "description": "Reading comprehension practice.",
    },
}

STRUCTURED_BLUEPRINTS = {
    "grammar": {
        "code": "epe_b1_plus_grammar_mixed_v1",
        "version": "v1",
        "title": "EPE B1+ Grammar Mixed Practice",
        "difficulty": "b1_plus",
        "recommended_minutes": 20,
        "max_score": 10,
        "answer_schema": {"type": "text_lines"},
    },
    "reading": {
        "code": "epe_b1_plus_reading_mc_v1",
        "version": "v1",
        "title": "EPE B1+ Reading Comprehension",
        "difficulty": "b1_plus",
        "recommended_minutes": 25,
        "max_score": 8,
        "answer_schema": {"type": "text_lines"},
    },
}

STRUCTURED_TASKS = {
    "grammar": [
        {
            "checksum": "seed_grammar_mixed_travel_01",
            "title": "Grammar mixed practice: travel plans",
            "content": {
                "instruction": (
                    "Complete each item. Send your answers as a numbered list, "
                    "one answer per line."
                ),
                "items": [
                    {
                        "id": "g1",
                        "prompt": "If I ___ more time, I would visit Vienna.",
                        "type": "open_gap",
                    },
                    {
                        "id": "g2",
                        "prompt": "She has lived here ___ 2021.",
                        "type": "open_gap",
                    },
                    {
                        "id": "g3",
                        "prompt": "Choose: I am interested ___ learning German.",
                        "type": "multiple_choice",
                        "options": ["A in", "B on", "C at"],
                    },
                    {
                        "id": "g4",
                        "prompt": "Correct the mistake: He don't like early classes.",
                        "type": "editing",
                    },
                    {
                        "id": "g5",
                        "prompt": "Word formation: The course was very ___. (HELP)",
                        "type": "word_formation",
                    },
                ],
            },
            "solution": {
                "answers": [
                    {"id": "g1", "answer": "had", "accepted": ["had"]},
                    {"id": "g2", "answer": "since", "accepted": ["since"]},
                    {"id": "g3", "answer": "in", "accepted": ["a", "a in", "in"]},
                    {
                        "id": "g4",
                        "answer": "He doesn't like early classes.",
                        "accepted": [
                            "he doesn't like early classes",
                            "he does not like early classes",
                        ],
                    },
                    {"id": "g5", "answer": "helpful", "accepted": ["helpful"]},
                ]
            },
            "max_score": 10,
        }
    ],
    "reading": [
        {
            "checksum": "seed_reading_transport_01",
            "title": "Reading: transport changes",
            "content": {
                "text": (
                    "Many cities are changing how people move around. In some places, "
                    "new bike lanes have reduced traffic in the centre. However, shop "
                    "owners sometimes worry that fewer parking spaces will mean fewer "
                    "customers. A recent survey showed that most young residents support "
                    "better public transport, while older residents prefer gradual changes."
                ),
                "instruction": (
                    "Answer the questions. Send your answers as a numbered list, "
                    "one answer per line."
                ),
                "items": [
                    {
                        "id": "r1",
                        "prompt": "What has reduced traffic in some city centres?",
                        "type": "short_answer",
                    },
                    {
                        "id": "r2",
                        "prompt": "Who worries about fewer parking spaces?",
                        "type": "short_answer",
                    },
                    {
                        "id": "r3",
                        "prompt": (
                            "Most young residents support better public transport. "
                            "True or false?"
                        ),
                        "type": "true_false",
                    },
                    {
                        "id": "r4",
                        "prompt": "Older residents prefer sudden changes. True or false?",
                        "type": "true_false",
                    },
                ],
            },
            "solution": {
                "answers": [
                    {
                        "id": "r1",
                        "answer": "new bike lanes",
                        "accepted": ["new bike lanes", "bike lanes"],
                    },
                    {
                        "id": "r2",
                        "answer": "shop owners",
                        "accepted": ["shop owners", "the shop owners"],
                    },
                    {"id": "r3", "answer": "true", "accepted": ["true", "t"]},
                    {"id": "r4", "answer": "false", "accepted": ["false", "f"]},
                ]
            },
            "max_score": 8,
        }
    ],
}


def _yaml(name: str) -> dict[str, Any]:
    return yaml.safe_load((PROFILE_DIR / name).read_text(encoding="utf-8"))


def _json(name: str) -> dict[str, Any]:
    return json.loads((PROFILE_DIR / name).read_text(encoding="utf-8"))


def _checksum_text(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


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


async def _seed_subject_tasks(db: AsyncSession, subject: Subject) -> dict[str, SubjectTask]:
    tasks: dict[str, SubjectTask] = {}
    for code, defaults in SUBJECT_TASK_DEFAULTS.items():
        tasks[code] = await _upsert(
            db,
            SubjectTask,
            {"subject_id": subject.id, "code": code},
            defaults,
        )
    return tasks


def _role_from_filename(path: Path) -> str:
    role = path.stem
    return "example" if role == "examples" else role


def _include_flags(role: str) -> tuple[bool, bool]:
    if role == "generation":
        return True, False
    if role == "evaluation":
        return False, True
    return True, True


async def _seed_guidelines(
    db: AsyncSession,
    *,
    subject: Subject,
    subject_tasks: dict[str, SubjectTask],
    writing_blueprint: TaskBlueprint,
) -> list[Guideline]:
    if not GUIDELINES_DIR.exists():
        return []

    seeded: list[Guideline] = []

    overview_path = GUIDELINES_DIR / "overview.md"
    if overview_path.exists():
        body = overview_path.read_text(encoding="utf-8")
        guideline = await _upsert(
            db,
            Guideline,
            {"code": "english_overview", "version": "v1"},
            {
                "default_role": "notes",
                "subject_id": subject.id,
                "subject_task_id": None,
                "frontmatter": {"source_path": str(overview_path.relative_to(PROFILE_DIR))},
                "body_markdown": body,
                "checksum": _checksum_text(body),
                "status": "active",
            },
        )
        seeded.append(guideline)
        await _link_blueprint_guideline(
            db,
            blueprint=writing_blueprint,
            guideline=guideline,
            role="notes",
            position=0,
            include_in_generation=True,
            include_in_evaluation=True,
        )

    for task_code, subject_task in subject_tasks.items():
        task_dir = GUIDELINES_DIR / task_code
        if not task_dir.exists():
            continue
        for index, filename in enumerate(GUIDELINE_ROLES, start=1):
            path = task_dir / f"{filename}.md"
            if not path.exists():
                continue
            role = _role_from_filename(path)
            include_generation, include_evaluation = _include_flags(role)
            body = path.read_text(encoding="utf-8")
            guideline = await _upsert(
                db,
                Guideline,
                {"code": f"english_{task_code}_{role}", "version": "v1"},
                {
                    "default_role": role,
                    "subject_id": subject.id,
                    "subject_task_id": subject_task.id,
                    "frontmatter": {"source_path": str(path.relative_to(PROFILE_DIR))},
                    "body_markdown": body,
                    "checksum": _checksum_text(body),
                    "status": "active",
                },
            )
            seeded.append(guideline)
            if task_code == "writing":
                await _link_blueprint_guideline(
                    db,
                    blueprint=writing_blueprint,
                    guideline=guideline,
                    role=role,
                    position=index * 10,
                    include_in_generation=include_generation,
                    include_in_evaluation=include_evaluation,
                )
    return seeded


async def _seed_structured_blueprints(
    db: AsyncSession, subject_tasks: dict[str, SubjectTask]
) -> dict[str, TaskBlueprint]:
    blueprints: dict[str, TaskBlueprint] = {}
    for task_code, data in STRUCTURED_BLUEPRINTS.items():
        subject_task = subject_tasks[task_code]
        blueprints[task_code] = await _upsert(
            db,
            TaskBlueprint,
            {"code": data["code"], "version": data["version"]},
            {
                "subject_task_id": subject_task.id,
                "task_family_id": None,
                "title": data["title"],
                "difficulty": data["difficulty"],
                "recommended_minutes": data["recommended_minutes"],
                "target_word_count_min": None,
                "target_word_count_max": None,
                "max_score": data["max_score"],
                "rubric_id": None,
                "evaluation_profile_id": None,
                "answer_schema": data["answer_schema"],
                "is_active": True,
            },
        )
    return blueprints


async def _seed_structured_tasks(
    db: AsyncSession, blueprints: dict[str, TaskBlueprint]
) -> list[TaskInstance]:
    seeded: list[TaskInstance] = []
    for task_code, tasks in STRUCTURED_TASKS.items():
        blueprint = blueprints[task_code]
        for task in tasks:
            seeded.append(
                await _upsert(
                    db,
                    TaskInstance,
                    {"checksum": task["checksum"]},
                    {
                        "blueprint_id": blueprint.id,
                        "title": task["title"],
                        "difficulty": blueprint.difficulty,
                        "content": task["content"],
                        "content_points": [
                            {"id": item["id"], "instruction": item["prompt"], "required": True}
                            for item in task["content"]["items"]
                        ],
                        "answer_config": {"type": "text_lines", "task_code": task_code},
                        "solution": task["solution"],
                        "max_score": task["max_score"],
                        "recommended_minutes": blueprint.recommended_minutes,
                        "source": "generated",
                        "status": "active",
                    },
                )
            )
    return seeded


async def _link_blueprint_guideline(
    db: AsyncSession,
    *,
    blueprint: TaskBlueprint,
    guideline: Guideline,
    role: str,
    position: int,
    include_in_generation: bool,
    include_in_evaluation: bool,
) -> TaskBlueprintGuideline:
    link = await _get(
        db,
        TaskBlueprintGuideline,
        blueprint_id=blueprint.id,
        guideline_id=guideline.id,
        role=role,
    )
    defaults = {
        "position": position,
        "include_in_generation": include_in_generation,
        "include_in_evaluation": include_in_evaluation,
    }
    if link is None:
        link = TaskBlueprintGuideline(
            blueprint_id=blueprint.id,
            guideline_id=guideline.id,
            role=role,
            **defaults,
        )
        db.add(link)
    else:
        for key, value in defaults.items():
            setattr(link, key, value)
    await db.flush()
    return link


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
    subject_tasks = await _seed_subject_tasks(db, subject)
    subject_task = subject_tasks[catalog["subject_task"]["code"]]

    # --- Rubric + criteria + bands ---
    rubric = await _upsert(
        db, Rubric, {"code": rubric_data["code"], "version": rubric_data["version"]},
        {
            "name": rubric_data["name"],
            "subject_task_id": subject_task.id,
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
            "subject_task_id": subject_task.id,
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
            "subject_task_id": subject_task.id,
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
    structured_blueprints = await _seed_structured_blueprints(db, subject_tasks)

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
                "source": "generated",
                "status": "active",
            },
        )
    structured_tasks = await _seed_structured_tasks(db, structured_blueprints)

    guidelines = await _seed_guidelines(
        db,
        subject=subject,
        subject_tasks=subject_tasks,
        writing_blueprint=blueprint,
    )

    # --- Allowlist users ---
    for tid in get_settings().allowlist_telegram_ids:
        await _upsert(db, User, {"telegram_id": tid}, {"status": "active"})

    await db.flush()
    return {
        "subject": subject,
        "subject_task": subject_task,
        "subject_tasks": subject_tasks,
        "blueprint": blueprint,
        "structured_blueprints": structured_blueprints,
        "structured_tasks": structured_tasks,
        "guidelines": guidelines,
        "rubric": rubric,
    }


async def main() -> None:
    configure_logging(get_settings().log_level)
    async with SessionFactory() as db:
        await seed_all(db)
        await db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
