"""Celery application (broker + result backend = Redis)."""

from __future__ import annotations

from celery import Celery

from app import models_registry  # noqa: F401 - register all ORM tables in the worker
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "vwu",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=5,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=settings.celery_eager,
    task_eager_propagates=settings.celery_eager,
    # Periodic maintenance (ТЗ §31).
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.workers.tasks.cleanup_expired_sessions",
            "schedule": 900.0,  # every 15 minutes
        },
    },
)
