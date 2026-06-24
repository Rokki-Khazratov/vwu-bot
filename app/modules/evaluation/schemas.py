from __future__ import annotations

import uuid

from pydantic import BaseModel


class AnswerIn(BaseModel):
    type: str = "text"
    text: str | None = None


class AttemptRequest(BaseModel):
    session_id: uuid.UUID
    task_id: uuid.UUID
    answer: AnswerIn
