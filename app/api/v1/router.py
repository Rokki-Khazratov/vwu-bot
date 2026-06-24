"""Aggregate router for /api/v1. Module routers are attached here as they land."""

from fastapi import APIRouter

from app.admin.attempts import router as admin_attempts_router
from app.admin.catalog import router as admin_catalog_router
from app.admin.observability import router as admin_observability_router
from app.admin.tasks import router as admin_tasks_router
from app.api.v1.access import router as access_router
from app.api.v1.attempts import router as attempts_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.dictionary import router as dictionary_router
from app.api.v1.flashcards import cards_router, words_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.statistics import router as statistics_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(access_router)
api_v1_router.include_router(catalog_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(attempts_router)
api_v1_router.include_router(statistics_router)
api_v1_router.include_router(dictionary_router)
api_v1_router.include_router(words_router)
api_v1_router.include_router(cards_router)
api_v1_router.include_router(admin_tasks_router)
api_v1_router.include_router(admin_attempts_router)
api_v1_router.include_router(admin_observability_router)
api_v1_router.include_router(admin_catalog_router)
