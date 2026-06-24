from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import AttemptNotFound, SessionInvalidState
from app.modules.access.models import User
from app.modules.evaluation import repository as eval_repo
from app.modules.evaluation.attempts_service import submit_attempt
from app.modules.evaluation.payload import build_attempt_payload
from app.modules.evaluation.schemas import AttemptRequest
from app.modules.llm.factory import get_llm_provider
from app.modules.llm.provider import LLMProvider
from app.modules.system import idempotency

router = APIRouter(prefix="/attempts", tags=["attempts"], route_class=EnvelopeRoute)


@router.post("")
async def create_attempt(
    payload: AttemptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider = Depends(get_llm_provider),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    # Synchronous evaluation in Phase 1 (the contract allows 202 later).
    request_fingerprint = {
        "user": str(user.id),
        "session_id": str(payload.session_id),
        "task_id": str(payload.task_id),
        "answer": payload.answer.model_dump(),
    }
    if idempotency_key:
        replay = await idempotency.lookup(db, idempotency_key, request_fingerprint)
        if replay is not None:
            return replay[0]

    result = await submit_attempt(
        db, provider,
        user_id=user.id,
        session_id=payload.session_id,
        task_id=payload.task_id,
        answer_type=payload.answer.type,
        answer_text=payload.answer.text,
    )

    if idempotency_key:
        await idempotency.store(db, idempotency_key, request_fingerprint, result, 200)
    return result


@router.get("/{attempt_id}")
async def get_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    attempt = await eval_repo.get_attempt(db, attempt_id)
    if attempt is None or attempt.user_id != user.id:
        raise AttemptNotFound()
    result = await eval_repo.get_result_for_attempt(db, attempt.id)
    if result is None:
        return {"attempt_id": str(attempt.id), "status": attempt.status}
    return await build_attempt_payload(db, attempt, result)


@router.get("/{attempt_id}/result")
async def get_attempt_result(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    attempt = await eval_repo.get_attempt(db, attempt_id)
    if attempt is None or attempt.user_id != user.id:
        raise AttemptNotFound()
    result = await eval_repo.get_result_for_attempt(db, attempt.id)
    if result is None:
        raise SessionInvalidState("Result not ready.")
    return await build_attempt_payload(db, attempt, result)
