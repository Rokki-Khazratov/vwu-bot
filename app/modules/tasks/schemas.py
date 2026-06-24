from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class TaskInstanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    blueprint_id: uuid.UUID
    title: str
    difficulty: str | None = None
    content: dict
    content_points: list | None = None
    answer_config: dict | None = None
    max_score: float | None = None
    recommended_minutes: int | None = None
    status: str


class BatchGenerateRequest(BaseModel):
    blueprint_code: str
    count: int = Field(default=1, ge=1, le=20)
    difficulty: str | None = None


class ActivateResponse(BaseModel):
    id: uuid.UUID
    status: str
