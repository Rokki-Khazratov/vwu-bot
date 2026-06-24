"""Blog-comment task generation + validation pipeline (ТЗ §11, Writing §5)."""

from __future__ import annotations

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BlueprintNotFound, ValidationError
from app.modules.llm.prompt import render_template
from app.modules.llm.provider import LLMProvider, LLMRequest
from app.modules.llm.repository import record_llm_call
from app.modules.tasks import repository as repo
from app.modules.tasks.models import TaskInstance

GEN_PROMPT_CODE = "epe_b1_plus_blog_comment_gen_v1"
GEN_SCHEMA_CODE = "epe_b1_plus_blog_comment_gen_v1"


def _checksum(draft: dict) -> str:
    basis = (draft.get("title", "") + draft["source_post"]["body"]).lower().strip()
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:32]


def _validate_draft(draft: dict) -> None:
    """Post-schema semantic checks (ТЗ §11.3 / Writing §5.3)."""
    points = draft.get("content_points", [])
    if len(points) != 3:
        raise ValidationError("Exactly three content points are required.")
    ids = [p["id"] for p in points]
    if len(set(ids)) != 3:
        raise ValidationError("Content point ids must be unique.")


async def generate_tasks(
    db: AsyncSession,
    provider: LLMProvider,
    *,
    blueprint_code: str,
    count: int = 1,
    difficulty: str | None = None,
) -> list[TaskInstance]:
    blueprint = await repo.get_blueprint_by_code(db, blueprint_code)
    if blueprint is None:
        raise BlueprintNotFound()

    prompt = await repo.get_prompt(db, GEN_PROMPT_CODE)
    schema = await repo.get_output_schema(db, GEN_SCHEMA_CODE)
    if prompt is None or schema is None:
        raise ValidationError("Generation prompt or schema is not seeded.")

    target_words = blueprint.target_word_count_min or 250
    banned = await repo.recent_titles(db, blueprint.id)

    created: list[TaskInstance] = []
    for _ in range(count):
        user_prompt = render_template(
            prompt.user_template,
            {
                "difficulty": difficulty or blueprint.difficulty or "b1_plus",
                "target_words": target_words,
                "banned_topics": ", ".join(banned) or "none",
                "extra_instructions": "",
            },
        )
        result = await provider.generate_structured(
            LLMRequest(
                purpose="task_generation",
                system_prompt=prompt.system_template,
                user_prompt=user_prompt,
                output_schema=schema.json_schema,
                temperature=(prompt.settings or {}).get("temperature", 0.9),
            )
        )
        await record_llm_call(
            db, result, purpose="task_generation",
            prompt_code=prompt.code, prompt_version=prompt.version,
            schema_code=schema.code, schema_version=schema.version,
        )

        draft = result.data
        _validate_draft(draft)
        checksum = _checksum(draft)
        if await repo.find_by_checksum(db, checksum) is not None:
            continue  # exact duplicate, skip (ТЗ §11.3)

        task = TaskInstance(
            blueprint_id=blueprint.id,
            generator_prompt_id=prompt.id,
            generator_prompt_version=prompt.version,
            generator_model=result.model,
            difficulty=draft.get("difficulty") or blueprint.difficulty,
            title=draft["title"],
            content={
                "source_post": draft["source_post"],
                "instruction": draft["instruction"],
                "target_words": draft.get("target_words", target_words),
            },
            content_points=draft["content_points"],
            answer_config={"type": "text"},
            max_score=blueprint.max_score,
            recommended_minutes=blueprint.recommended_minutes,
            status="generated",
            checksum=checksum,
        )
        db.add(task)
        await db.flush()
        banned.append(task.title)
        created.append(task)

    return created
