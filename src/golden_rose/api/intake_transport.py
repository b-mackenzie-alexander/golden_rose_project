"""Bounded, value-safe transport for the intake namespace, including errors."""

from typing import Any

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_HEADERS = {
    "Cache-Control": "no-store",
    "Vary": "Authorization",
    "X-Content-Type-Options": "nosniff",
}
_CODES = {
    401: "unauthenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "version_conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "invalid_request",
    503: "persistence_unavailable",
}


def intake_problem(
    code: str, status: int, *, missing_fields: list[str] | None = None
) -> JSONResponse:
    headers = dict(_HEADERS)
    if status == 503:
        headers["Retry-After"] = "1"
    from typing import get_args

    from golden_rose.api.staff.intake_schemas import MissingIntakeField

    safe_missing = sorted(set(missing_fields or []) & set(get_args(MissingIntakeField)))
    return JSONResponse(
        {
            "type": f"urn:golden-rose:intake:{code}",
            "title": code.replace("_", " "),
            "status": status,
            "detail": "The intake request could not be completed.",
            "code": code,
            **(
                {"missing_fields": safe_missing}
                if code == "incomplete" and status == 422 and safe_missing
                else {}
            ),
        },
        status_code=status,
        headers=headers,
        media_type="application/problem+json",
    )


class IntakeTransportMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        prefixes = ("/api/staff/v1/intakes", "/api/staff/v1/work-interests")
        if scope["type"] != "http" or not any(
            path == prefix or path.startswith(prefix + "/") for prefix in prefixes
        ):
            await self.app(scope, receive, send)
            return
        body = bytearray()
        if scope["method"] == "POST":
            headers = {k.lower(): v for k, v in scope["headers"]}
            if (
                headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
                != b"application/json"
            ):
                await intake_problem("unsupported_media_type", 415)(scope, receive, send)
                return
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 32768:
                await intake_problem("payload_too_large", 413)(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False
        started = False
        replacement: Any = None

        async def bounded_receive() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def safe_send(message: Message) -> None:
            nonlocal started, replacement
            if message["type"] == "http.response.start":
                started = True
                status = message["status"]
                headers = dict(message.get("headers", []))
                if status >= 400 and headers.get(b"content-type") != b"application/problem+json":
                    status = 422 if status == 400 else (503 if status >= 500 else status)
                    replacement = intake_problem(_CODES.get(status, "invalid_request"), status)
                    if b"www-authenticate" in headers:
                        replacement.headers["WWW-Authenticate"] = headers[
                            b"www-authenticate"
                        ].decode("latin-1")
                    await replacement(scope, bounded_receive, send)
                    return
                for key, value in _HEADERS.items():
                    headers[key.lower().encode()] = value.encode()
                headers.pop(b"etag", None)
                headers.pop(b"last-modified", None)
                message["headers"] = list(headers.items())
            if replacement is None:
                await send(message)

        try:
            await self.app(scope, bounded_receive, safe_send)
        except Exception:
            if not started:
                await intake_problem("persistence_unavailable", 503)(scope, bounded_receive, send)
