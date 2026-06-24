from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKey
from app.core.database import Base, JSONColumn


def _now() -> datetime:
    return datetime.now(UTC)


class LLMCall(UUIDPrimaryKey, Base):
    """Observability record for every LLM request (ТЗ §19.4)."""

    __tablename__ = "llm_calls"

    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(64), index=True)
    prompt_template_code: Mapped[str | None] = mapped_column(String(64))
    prompt_template_version: Mapped[str | None] = mapped_column(String(32))
    output_schema_code: Mapped[str | None] = mapped_column(String(64))
    output_schema_version: Mapped[str | None] = mapped_column(String(32))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cached_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))  # ok|schema_invalid|timeout|error|refusal
    error_code: Mapped[str | None] = mapped_column(String(64))
    request_checksum: Mapped[str | None] = mapped_column(String(64))
    raw_response: Mapped[dict | None] = mapped_column(JSONColumn)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
