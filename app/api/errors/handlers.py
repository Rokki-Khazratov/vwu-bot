"""Global exception handlers — translate exceptions into error envelopes."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors.envelope import error_envelope
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import log_event

logger = logging.getLogger("app.errors")


def _json(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content=error_envelope(code, message, details))


def register_exception_handlers(app: FastAPI) -> None:
    settings = get_settings()

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        log_event(
            logger, logging.WARNING, "app_error",
            error_code=exc.code, path=request.url.path,
        )
        return _json(exc.http_status, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _json(422, "VALIDATION_ERROR", "Request validation failed.",
                     {"errors": exc.errors()})

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return _json(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces (ТЗ §33).
        log_event(
            logger, logging.ERROR, "unhandled_exception",
            path=request.url.path, exc_type=type(exc).__name__,
        )
        message = str(exc) if settings.is_dev else "Internal server error."
        return _json(500, "INTERNAL_ERROR", message)
