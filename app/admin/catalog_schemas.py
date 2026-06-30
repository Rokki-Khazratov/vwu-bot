from __future__ import annotations

import uuid

from pydantic import BaseModel


class SubjectCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class SubjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ExamProfileCreate(BaseModel):
    subject_code: str
    code: str
    name: str
    level: str | None = None
    version: str = "v1"
    description: str | None = None


class ExamProfileUpdate(BaseModel):
    name: str | None = None
    level: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SkillCreate(BaseModel):
    exam_profile_code: str
    code: str
    name: str
    position: int = 0
    description: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    position: int | None = None
    description: str | None = None
    is_active: bool | None = None


class TaskFamilyCreate(BaseModel):
    skill_id: uuid.UUID
    code: str
    name: str
    answer_format: str
    default_evaluator_code: str | None = None
    description: str | None = None


class TaskFamilyUpdate(BaseModel):
    name: str | None = None
    answer_format: str | None = None
    default_evaluator_code: str | None = None
    description: str | None = None
    is_active: bool | None = None


class BlueprintCreate(BaseModel):
    task_family_id: uuid.UUID
    code: str
    version: str = "v1"
    title: str
    difficulty: str | None = None
    recommended_minutes: int | None = None
    target_word_count_min: int | None = None
    target_word_count_max: int | None = None
    max_score: float | None = None
    rubric_id: uuid.UUID | None = None
    evaluation_profile_id: uuid.UUID | None = None
    guideline_id: uuid.UUID | None = None


class BlueprintUpdate(BaseModel):
    title: str | None = None
    difficulty: str | None = None
    recommended_minutes: int | None = None
    target_word_count_min: int | None = None
    target_word_count_max: int | None = None
    max_score: float | None = None
    rubric_id: uuid.UUID | None = None
    evaluation_profile_id: uuid.UUID | None = None
    guideline_id: uuid.UUID | None = None
    is_active: bool | None = None
