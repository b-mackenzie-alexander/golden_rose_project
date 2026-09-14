"""Exercise raw ASGI chunking and error value suppression independently of HTTP clients."""

import asyncio

import pytest
from starlette.types import ASGIApp, Message, Scope

from golden_rose.api.intake_transport import IntakeTransportMiddleware


def invoke(
    app: ASGIApp,
    *,
    path: str = "/api/staff/v1/intakes",
    method: str = "POST",
    chunks: list[Message] | None = None,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> list[Message]:
    messages = list(chunks or [{"type": "http.request", "body": b"{}", "more_body": False}])
    output: list[Message] = []
    scope: Scope = {
        "type": "http",
        "path": path,
        "method": method,
        "headers": headers if headers is not None else [(b"content-type", b"application/json")],
    }

    async def receive() -> Message:
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        output.append(message)

    asyncio.run(IntakeTransportMiddleware(app)(scope, receive, send))
    return output


def test_streamed_body_over_limit_rejected_before_application():
    called = []

    async def app(scope, receive, send):
        called.append(True)

    output = invoke(
        app,
        chunks=[
            {"type": "http.request", "body": b"a" * 16384, "more_body": True},
            {"type": "http.request", "body": b"b" * 16385, "more_body": False},
        ],
    )
    assert not called
    assert output[0]["status"] == 413
    assert b"payload_too_large" in output[1]["body"]


def test_exact_body_limit_delivered_once_with_no_cache_headers():
    captured = []

    async def app(scope, receive, send):
        captured.append(await receive())
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"etag", b"secret"), (b"last-modified", b"yesterday")],
            }
        )
        await send({"type": "http.response.body", "body": b"{}"})

    output = invoke(
        app,
        chunks=[
            {"type": "http.request", "body": b"a" * 16384, "more_body": True},
            {"type": "http.request", "body": b"b" * 16384, "more_body": False},
        ],
    )
    assert captured == [
        {"type": "http.request", "body": b"a" * 16384 + b"b" * 16384, "more_body": False}
    ]
    headers = dict(output[0]["headers"])
    assert headers[b"cache-control"] == b"no-store"
    assert headers[b"vary"] == b"Authorization"
    assert b"etag" not in headers and b"last-modified" not in headers


@pytest.mark.parametrize("status", [401, 403, 404, 405, 409, 422, 503])
def test_arbitrary_error_payload_never_passes_through(status):
    async def app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": b'{"secret":"fictional marker"}'})

    output = invoke(app)
    assert output[0]["status"] == status
    assert b"fictional marker" not in b"".join(msg.get("body", b"") for msg in output)
    assert dict(output[0]["headers"])[b"content-type"] == b"application/problem+json"


def test_unexpected_failure_before_response_is_safe_retryable():
    async def app(scope, receive, send):
        raise RuntimeError("fictional sensitive exception")

    output = invoke(app)
    assert output[0]["status"] == 503
    assert dict(output[0]["headers"])[b"retry-after"] == b"1"
    assert b"fictional sensitive" not in output[1]["body"]


def test_neighbor_namespace_is_not_intercepted():
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    output = invoke(app, path="/api/staff/v1/intakes-other", headers=[])
    assert output[0] == {"type": "http.response.start", "status": 204, "headers": []}


def test_disconnect_does_not_call_application():
    calls = []

    async def app(scope, receive, send):
        calls.append(True)

    assert invoke(app, chunks=[{"type": "http.disconnect"}]) == []
    assert calls == []


def test_repeated_receive_delivers_disconnect_after_buffered_request():
    received = []

    async def app(scope, receive, send):
        received.append(await receive())
        received.append(await receive())
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    invoke(app)
    assert received[1] == {"type": "http.disconnect"}
