from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
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
        exam_profile_code=payload.exam_profile_code,
        skill_code=payload.skill_code,
        task_family_code=payload.task_family_code,
        mode=payload.mode,
        prefer_new_task=payload.options.prefer_new_task,
    )
    return CreateSessionResponse(
        session=SessionOut.model_validate(session),
        task=TaskInstanceOut.model_validate(task),
        answer_format=(task.answer_config or {}).get("type", "text"),
        recommended_minutes=task.recommended_minutes,
        available_actions=service.available_actions(session),
    )


@router.get("/history", response_model=list[SessionOut])
async def history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SessionOut]:
    sessions = await repo.list_sessions(db, user.id)
    return [SessionOut.model_validate(s) for s in sessions]


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
