from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SubjectOut(_Base):
    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_active: bool


class ExamProfileOut(_Base):
    id: uuid.UUID
    code: str
    name: str
    level: str | None = None
    version: str
    description: str | None = None
    is_active: bool


class SkillOut(_Base):
    id: uuid.UUID
    code: str
    name: str
    position: int
    is_active: bool


class TaskFamilyOut(_Base):
    id: uuid.UUID
    code: str
    name: str
    answer_format: str
    default_evaluator_code: str | None = None
    is_active: bool


class TaskBlueprintOut(_Base):
    id: uuid.UUID
    code: str
    version: str
    title: str
    difficulty: str | None = None
    recommended_minutes: int | None = None
    target_word_count_min: int | None = None
    target_word_count_max: int | None = None
    max_score: float | None = None
    is_active: bool
