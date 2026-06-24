from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.tasks.schemas import TaskInstanceOut


class SessionOptions(BaseModel):
    difficulty: str | None = None
    prefer_new_task: bool = True


class CreateSessionRequest(BaseModel):
    subject_code: str
    exam_profile_code: str
    skill_code: str
    task_family_code: str
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
