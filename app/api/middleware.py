"""HTTP middleware: request id + structured access log (ТЗ §35)."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import set_request_id
from app.core.logging import log_event

logger = logging.getLogger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = set_request_id(request.headers.get("x-request-id"))
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            log_event(
                logger, logging.INFO, "request",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
        response.headers["x-request-id"] = rid
        return response
