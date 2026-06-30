"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.errors.handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.middleware import RequestContextMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="VWU Learning Assistant API",
        version="0.1.0",
        description="Backend for the VWU exam-prep assistant.",
    )

    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_v1_router)

    # Calibration dashboard at /panel (static HTML over the admin API).
    from app.admin.dashboard import router as dashboard_router

    app.include_router(dashboard_router)

    # Admin web panel at /admin (SQLAdmin).
    from app.admin.panel import setup_admin

    setup_admin(app)

    return app


app = create_app()
