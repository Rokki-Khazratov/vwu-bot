import httpx
import pytest
import respx

from bot.api_client.client import BackendClient
from bot.api_client.errors import BackendError, BackendUnavailable
from bot.core.config import Settings

BASE = "http://testbackend"
API = BASE + "/api/v1"


def _client() -> BackendClient:
    return BackendClient(Settings(backend_base_url=BASE, bot_service_token="svc"))


def _envelope(data, errors=None):
    return {"data": data, "meta": {"request_id": "r1"}, "errors": errors or []}


@respx.mock
async def test_access_me_unwraps_envelope():
    respx.get(f"{API}/access/me").mock(
        return_value=httpx.Response(200, json=_envelope({"telegram_id": 111, "status": "active"}))
    )
    client = _client()
    me = await client.access_me(111)
    assert me["status"] == "active"
    # headers injected
    req = respx.calls.last.request
    assert req.headers["X-Telegram-User-Id"] == "111"
    assert req.headers["Authorization"] == "Bearer svc"
    await client.aclose()


@respx.mock
async def test_error_envelope_raises_backend_error():
    respx.get(f"{API}/access/me").mock(
        return_value=httpx.Response(
            403, json=_envelope(None, [{"code": "ACCESS_DENIED", "message": "no"}])
        )
    )
    client = _client()
    with pytest.raises(BackendError) as ei:
        await client.access_me(999)
    assert ei.value.code == "ACCESS_DENIED"
    assert ei.value.http_status == 403
    await client.aclose()


@respx.mock
async def test_submit_attempt_returns_status_and_idempotency_header():
    route = respx.post(f"{API}/attempts").mock(
        return_value=httpx.Response(
            202, json=_envelope({"attempt_id": "a1", "status": "evaluating"})
        )
    )
    client = _client()
    status, data = await client.submit_attempt(
        111, {"session_id": "s", "task_id": "t", "answer": {"type": "text", "text": "x"}},
        idempotency_key="key-1",
    )
    assert status == 202
    assert data["attempt_id"] == "a1"
    assert route.calls.last.request.headers["Idempotency-Key"] == "key-1"
    await client.aclose()


@respx.mock
async def test_transport_failure_raises_backend_unavailable():
    respx.get(f"{API}/subjects").mock(side_effect=httpx.ConnectError("boom"))
    client = _client()
    with pytest.raises(BackendUnavailable):
        await client.subjects(111)
    await client.aclose()
