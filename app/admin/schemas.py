from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ScoreCorrectionRequest(BaseModel):
    criteria: dict[str, int] | None = None
    final_score: float | None = None
    reason: str | None = None


class FeedbackCorrectionRequest(BaseModel):
    summary: str | None = None
    strengths: list[str] | None = None
    recommendations: list[str] | None = None
    reason: str | None = None


class TaskPatchRequest(BaseModel):
    title: str | None = None
    difficulty: str | None = None
    status: str | None = None


GuidelineRole = Literal["generation", "evaluation", "example", "notes"]


class GuidelineCreateRequest(BaseModel):
    code: str
    version: str = "v1"
    role: GuidelineRole = "notes"
    status: str = "active"
    body_markdown: str
    frontmatter: dict | None = None
    subject_id: uuid.UUID | None = None
    exam_profile_id: uuid.UUID | None = None
    skill_id: uuid.UUID | None = None
    task_family_id: uuid.UUID | None = None


class GuidelineLinkRequest(BaseModel):
    guideline_id: uuid.UUID
    role: GuidelineRole
    position: int = 0
    include_in_generation: bool = False
    include_in_evaluation: bool = True


class GuidelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    version: str
    default_role: str
    status: str
    checksum: str | None = None
    body_markdown: str | None = None
    frontmatter: dict | None = None
    created_at: datetime


class LinkedGuidelineOut(BaseModel):
    id: uuid.UUID
    guideline_id: uuid.UUID
    code: str
    version: str
    role: str
    position: int
    include_in_generation: bool
    include_in_evaluation: bool


class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    task_id: uuid.UUID
    status: str
    score_final: float | None = None
    score_max: float | None = None
    word_count: int | None = None
    created_at: datetime


class LLMCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    model: str
    purpose: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    status: str
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    reason: str | None = None
    created_at: datetime


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    status: str
    ref_id: str | None = None
    error: str | None = None
    attempts: int
    created_at: datetime
    updated_at: datetime
