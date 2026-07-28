from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKey
from app.core.database import Base, JSONColumn


class Subject(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)


class ExamProfile(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "exam_profiles"
    __table_args__ = (UniqueConstraint("subject_id", "code", name="uq_exam_profile_code"),)

    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    level: Mapped[str | None] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32), default="v1")
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column(JSONColumn)


class Skill(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("exam_profile_id", "code", name="uq_skill_code"),)

    exam_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exam_profiles.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)


class SubjectTask(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "subject_tasks"
    __table_args__ = (UniqueConstraint("subject_id", "code", name="uq_subject_task_code"),)

    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0)
    answer_format: Mapped[str] = mapped_column(String(32))  # text|choice|numeric|matching
    default_evaluator_code: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)


class TaskFamily(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "task_families"
    __table_args__ = (UniqueConstraint("skill_id", "code", name="uq_task_family_code"),)

    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    answer_format: Mapped[str] = mapped_column(String(32))  # text|choice|numeric|matching
    default_evaluator_code: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)


class TaskBlueprint(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "task_blueprints"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_blueprint_code_version"),)

    subject_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subject_tasks.id"), index=True
    )
    task_family_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("task_families.id"), index=True
    )
    code: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    title: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str | None] = mapped_column(String(32))
    recommended_minutes: Mapped[int | None] = mapped_column(Integer)
    target_word_count_min: Mapped[int | None] = mapped_column(Integer)
    target_word_count_max: Mapped[int | None] = mapped_column(Integer)
    max_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    generator_profile_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)  # no table yet in P1
    evaluation_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evaluation_profiles.id")
    )
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rubrics.id"))
    guideline_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("guidelines.id"))
    content_schema: Mapped[dict | None] = mapped_column(JSONColumn)
    answer_schema: Mapped[dict | None] = mapped_column(JSONColumn)
    generation_constraints: Mapped[dict | None] = mapped_column(JSONColumn)
    is_active: Mapped[bool] = mapped_column(default=True)


class Guideline(UUIDPrimaryKey, Base):
    __tablename__ = "guidelines"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_guideline_code_version"),)

    code: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    default_role: Mapped[str] = mapped_column(String(32), default="notes")
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subjects.id"))
    subject_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subject_tasks.id"))
    exam_profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exam_profiles.id"))
    skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    task_family_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("task_families.id"))
    frontmatter: Mapped[dict | None] = mapped_column(JSONColumn)
    body_markdown: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active")  # draft|active|archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class TaskBlueprintGuideline(UUIDPrimaryKey, Base):
    __tablename__ = "task_blueprint_guidelines"
    __table_args__ = (
        UniqueConstraint(
            "blueprint_id", "guideline_id", "role", name="uq_blueprint_guideline_role"
        ),
    )

    blueprint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_blueprints.id"), index=True
    )
    guideline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guidelines.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column(Integer, default=0)
    include_in_generation: Mapped[bool] = mapped_column(default=False)
    include_in_evaluation: Mapped[bool] = mapped_column(default=True)


class TaskInstanceGuideline(UUIDPrimaryKey, Base):
    __tablename__ = "task_instance_guidelines"
    __table_args__ = (
        UniqueConstraint("task_id", "guideline_id", "role", name="uq_task_guideline_role"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_instances.id"), index=True)
    guideline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guidelines.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column(Integer, default=0)
    include_in_generation: Mapped[bool] = mapped_column(default=False)
    include_in_evaluation: Mapped[bool] = mapped_column(default=True)
