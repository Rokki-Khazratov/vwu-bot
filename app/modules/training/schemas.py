from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.tasks.schemas import TaskInstanceOut


class SessionOptions(BaseModel):
    difficulty: str | None = None
    prefer_new_task: bool = True
    focus_criterion: str | None = None
    focus_error_category: str | None = None


class CreateSessionRequest(BaseModel):
    subject_code: str
    task_code: str | None = None
    blueprint_code: str | None = None
    exam_profile_code: str | None = None
    skill_code: str | None = None
    task_family_code: str | None = None
    mode: str = "single"
    options: SessionOptions = Field(default_factory=SessionOptions)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mode: str
    status: str
    score_earned: float | None = None
    score_max: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class SessionHistoryOut(SessionOut):
    subject_code: str | None = None
    task_code: str | None = None
    exam_profile_code: str | None = None
    skill_code: str | None = None
    task_family_code: str | None = None
    task_id: uuid.UUID | None = None
    task_title: str | None = None
    attempt_id: uuid.UUID | None = None
    duration_seconds: int | None = None
    top_errors: list[dict] = Field(default_factory=list)
    weakest_criterion: dict | None = None


class CreateSessionResponse(BaseModel):
    session: SessionOut
    task: TaskInstanceOut
    answer_format: str
    recommended_minutes: int | None = None
    available_actions: list[str]


class NextTaskResponse(BaseModel):
    task: TaskInstanceOut
    answer_format: str
    recommended_minutes: int | None = None
