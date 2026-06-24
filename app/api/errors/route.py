"""Custom APIRoute that wraps every successful JSON response in the envelope.

Endpoints return plain data (Pydantic models / dicts); this route class wraps the
serialised body into ``{data, meta, errors}`` and preserves the status code.
Error responses are produced by exception handlers and bypass this wrapper.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.errors.envelope import success_envelope


class EnvelopeRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Any]:
        original = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            response = await original(request)
            content_type = response.headers.get("content-type", "")
            body = getattr(response, "body", b"")
            if content_type.startswith("application/json") and body:
                data = json.loads(body)
                return JSONResponse(
                    content=success_envelope(data),
                    status_code=response.status_code,
                )
            return response

        return custom_handler
