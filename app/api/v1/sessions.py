from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.api.errors.route import EnvelopeRoute
from app.core.exceptions import SessionInvalidState, SessionNotFound
from app.modules.access.models import User
from app.modules.evaluation import repository as eval_repo
from app.modules.evaluation.payload import build_attempt_payload
from app.modules.tasks.schemas import TaskInstanceOut
from app.modules.training import repository as repo
from app.modules.training import service
from app.modules.training.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    NextTaskResponse,
    SessionHistoryOut,
    SessionOut,
)

router = APIRouter(prefix="/sessions", tags=["sessions"], route_class=EnvelopeRoute)


@router.post("", response_model=CreateSessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CreateSessionResponse:
    session, task = await service.create_session(
        db, user.id,
        subject_code=payload.subject_code,
        task_code=payload.task_code,
        blueprint_code=payload.blueprint_code,
        exam_profile_code=payload.exam_profile_code,
        skill_code=payload.skill_code,
        task_family_code=payload.task_family_code,
        mode=payload.mode,
        prefer_new_task=payload.options.prefer_new_task,
        focus_criterion=payload.options.focus_criterion,
        focus_error_category=payload.options.focus_error_category,
    )
    return CreateSessionResponse(
        session=SessionOut.model_validate(session),
        task=TaskInstanceOut.model_validate(task),
        answer_format=(task.answer_config or {}).get("type", "text"),
        recommended_minutes=task.recommended_minutes,
        available_actions=service.available_actions(session),
    )


@router.get("/history", response_model=list[SessionHistoryOut])
async def history(
    subject_code: str | None = None,
    task_code: str | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    error_category: str | None = None,
    criterion_code: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SessionHistoryOut]:
    history_rows = await repo.list_session_history(
        db,
        user.id,
        subject_code=subject_code,
        task_code=task_code,
        status=status,
        date_from=date_from,
        date_to=date_to,
        min_score=min_score,
        max_score=max_score,
        error_category=error_category,
        criterion_code=criterion_code,
        limit=limit,
        offset=offset,
    )
    return [SessionHistoryOut.model_validate(s) for s in history_rows]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionOut:
    session = await repo.get_session(db, session_id)
    if session is None or session.user_id != user.id:
        raise SessionNotFound()
    return SessionOut.model_validate(session)


@router.post("/{session_id}/start", response_model=SessionOut)
async def start_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionOut:
    session = await service.start_session(db, session_id, user.id)
    return SessionOut.model_validate(session)


@router.post("/{session_id}/cancel", response_model=SessionOut)
async def cancel_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionOut:
    session = await service.cancel_session(db, session_id, user.id)
    return SessionOut.model_validate(session)


@router.get("/{session_id}/next-task", response_model=NextTaskResponse)
async def next_task(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NextTaskResponse:
    session, task = await service.get_session_with_task(db, session_id, user.id)
    if task is None:
        raise SessionInvalidState("No task associated with this session.")
    return NextTaskResponse(
        task=TaskInstanceOut.model_validate(task),
        answer_format=(task.answer_config or {}).get("type", "text"),
        recommended_minutes=task.recommended_minutes,
    )


@router.get("/{session_id}/result")
async def session_result(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    session = await repo.get_session(db, session_id)
    if session is None or session.user_id != user.id:
        raise SessionNotFound()
    session_task = await repo.get_session_task(db, session.id)
    if session_task is None:
        raise SessionInvalidState("Session has no task.")
    from sqlalchemy import select

    from app.modules.evaluation.models import Attempt

    attempt = (await db.execute(
        select(Attempt).where(
            Attempt.session_id == session.id, Attempt.task_id == session_task.task_id
        )
    )).scalars().first()
    if attempt is None:
        raise SessionInvalidState("No attempt submitted yet.")
    result = await eval_repo.get_result_for_attempt(db, attempt.id)
    if result is None:
        raise SessionInvalidState("Result not ready.")
    return await build_attempt_payload(db, attempt, result)


@router.get("/{session_id}/analysis")
async def session_analysis(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await session_result(session_id, db, user)
