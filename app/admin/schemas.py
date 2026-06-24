from __future__ import annotations

import uuid
from datetime import datetime

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
