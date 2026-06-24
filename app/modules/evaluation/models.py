from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKey
from app.core.database import Base, JSONColumn


def _now() -> datetime:
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Rubric-driven scoring config (ТЗ §7)                                          #
# --------------------------------------------------------------------------- #
class Rubric(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "rubrics"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_rubric_code_version"),)

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(32), default="v1")
    exam_profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exam_profiles.id"))
    task_family_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("task_families.id"))
    max_score: Mapped[float] = mapped_column(Numeric(6, 2))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="active")


class RubricCriterion(UUIDPrimaryKey, Base):
    __tablename__ = "rubric_criteria"
    __table_args__ = (UniqueConstraint("rubric_id", "code", name="uq_criterion_code"),)

    rubric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubrics.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0)
    min_score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=5)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[str | None] = mapped_column(Text)


class PerformanceBand(UUIDPrimaryKey, Base):
    __tablename__ = "performance_bands"

    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubric_criteria.id"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    descriptor: Mapped[str] = mapped_column(Text)
    machine_rules: Mapped[dict | None] = mapped_column(JSONColumn)
    examples: Mapped[dict | None] = mapped_column(JSONColumn)


class PenaltyRule(UUIDPrimaryKey, Base):
    __tablename__ = "penalty_rules"

    rubric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubrics.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    rule_type: Mapped[str] = mapped_column(String(32))  # word_count|hard_zero|max_cap
    condition: Mapped[dict] = mapped_column(JSONColumn)
    action: Mapped[dict] = mapped_column(JSONColumn)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class DependencyRule(UUIDPrimaryKey, Base):
    __tablename__ = "dependency_rules"

    rubric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubrics.id"), index=True)
    condition: Mapped[dict] = mapped_column(JSONColumn)
    action: Mapped[dict] = mapped_column(JSONColumn)
    priority: Mapped[int] = mapped_column(Integer, default=0)


# --------------------------------------------------------------------------- #
# Evaluation config (ТЗ §8–10)                                                  #
# --------------------------------------------------------------------------- #
class PromptTemplate(UUIDPrimaryKey, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_prompt_code_version"),)

    code: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32), default="v1")
    system_template: Mapped[str] = mapped_column(Text)
    user_template: Mapped[str] = mapped_column(Text)
    provider_hint: Mapped[str | None] = mapped_column(String(64))
    model_hint: Mapped[str | None] = mapped_column(String(64))
    settings: Mapped[dict | None] = mapped_column(JSONColumn)
    checksum: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active")


class OutputSchema(UUIDPrimaryKey, Base):
    __tablename__ = "output_schemas"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_output_schema_code_version"),)

    code: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    json_schema: Mapped[dict] = mapped_column(JSONColumn)
    status: Mapped[str] = mapped_column(String(16), default="active")


class ErrorTaxonomy(UUIDPrimaryKey, Base):
    __tablename__ = "error_taxonomies"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_taxonomy_code_version"),)

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(32), default="v1")
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id"))
    categories: Mapped[dict] = mapped_column(JSONColumn)
    status: Mapped[str] = mapped_column(String(16), default="active")


class EvaluationProfile(UUIDPrimaryKey, Base):
    __tablename__ = "evaluation_profiles"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_eval_profile_code_version"),)

    code: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    task_family_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("task_families.id"))
    evaluator_code: Mapped[str] = mapped_column(String(64))
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rubrics.id"))
    prompt_template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prompt_templates.id"))
    output_schema_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("output_schemas.id"))
    error_taxonomy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("error_taxonomies.id"))
    provider_policy: Mapped[dict | None] = mapped_column(JSONColumn)
    model_policy: Mapped[dict | None] = mapped_column(JSONColumn)
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    max_retries: Mapped[int] = mapped_column(Integer, default=1)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    is_active: Mapped[bool] = mapped_column(default=True)


# --------------------------------------------------------------------------- #
# Attempts & results (ТЗ §15, §17)                                              #
# --------------------------------------------------------------------------- #
class Attempt(UUIDPrimaryKey, Base):
    __tablename__ = "attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_sessions.id"), index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_instances.id"), index=True)
    raw_answer: Mapped[dict] = mapped_column(JSONColumn)
    normalized_answer: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    evaluator_code: Mapped[str | None] = mapped_column(String(64))
    evaluation_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evaluation_profiles.id")
    )
    score_raw: Mapped[float | None] = mapped_column(Numeric(6, 2))
    penalty_total: Mapped[float | None] = mapped_column(Numeric(6, 2))
    score_final: Mapped[float | None] = mapped_column(Numeric(6, 2))
    score_max: Mapped[float | None] = mapped_column(Numeric(6, 2))
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class EvaluationResult(UUIDPrimaryKey, Base):
    __tablename__ = "evaluation_results"

    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="evaluated")
    raw_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    penalty_total: Mapped[float | None] = mapped_column(Numeric(6, 2))
    final_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    max_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list | None] = mapped_column(JSONColumn)
    recommendations: Mapped[list | None] = mapped_column(JSONColumn)
    confidence: Mapped[float | None] = mapped_column(Float)
    raw_provider_response: Mapped[dict | None] = mapped_column(JSONColumn)
    provider_metadata: Mapped[dict | None] = mapped_column(JSONColumn)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CriterionScore(UUIDPrimaryKey, Base):
    __tablename__ = "criterion_scores"

    evaluation_result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_results.id"), index=True
    )
    criterion_code: Mapped[str] = mapped_column(String(64))
    score: Mapped[int] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer)
    selected_band: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[list | None] = mapped_column(JSONColumn)


class ContentPointAssessment(UUIDPrimaryKey, Base):
    __tablename__ = "content_point_assessments"

    evaluation_result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_results.id"), index=True
    )
    content_point_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    evidence: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)


class ErrorEvent(UUIDPrimaryKey, Base):
    __tablename__ = "error_events"

    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id"), index=True)
    evaluation_result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_results.id"), index=True
    )
    category: Mapped[str] = mapped_column(String(64))
    subcategory: Mapped[str | None] = mapped_column(String(64))
    severity: Mapped[str | None] = mapped_column(String(16))
    source_fragment: Mapped[str | None] = mapped_column(Text)
    corrected_fragment: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    criterion_code: Mapped[str | None] = mapped_column(String(64))
    content_point_id: Mapped[str | None] = mapped_column(String(64))
    start_offset: Mapped[int | None] = mapped_column(Integer)
    end_offset: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list | None] = mapped_column(JSONColumn)
