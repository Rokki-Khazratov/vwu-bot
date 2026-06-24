"""Per-request context (request id) propagated via contextvars."""

import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str | None) -> str:
    rid = value or str(uuid.uuid4())
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get()
