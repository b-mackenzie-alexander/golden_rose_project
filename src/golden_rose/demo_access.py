import base64
import binascii
import hmac
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from pydantic import SecretStr
from starlette.types import Message, Receive, Scope, Send

_PUBLIC_PROBE_PATHS = frozenset({"/health", "/readiness"})
_DEMO_USERNAME = "golden-rose-demo"
_CHALLENGE = 'Basic realm="Golden Rose synthetic develop", charset="UTF-8"'


class DemoAccessMiddleware:
    def __init__(
        self,
        app: Callable[[Scope, Receive, Send], Awaitable[None]],
        *,
        password: SecretStr,
        expires_at: datetime,
    ) -> None:
        self._app = app
        self._password = password
        self._expires_at = expires_at

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") in _PUBLIC_PROBE_PATHS:
            await self._app(scope, receive, send)
            return

        if datetime.now(UTC) >= self._expires_at:
            await _send_empty_response(send, status=503)
            return

        authorization_values = [
            value for name, value in scope["headers"] if name.lower() == b"authorization"
        ]
        username, password = _parse_basic_credentials(authorization_values)
        username_matches = hmac.compare_digest(username, _DEMO_USERNAME)
        password_matches = hmac.compare_digest(password, self._password.get_secret_value())
        if username_matches and password_matches:
            await self._app(scope, receive, send)
            return

        await _send_denial(send)


def _parse_basic_credentials(authorization_values: list[bytes]) -> tuple[str, str]:
    if len(authorization_values) != 1:
        return "", ""
    try:
        scheme, encoded = authorization_values[0].decode("ascii").split(" ", maxsplit=1)
        if scheme.lower() != "basic" or not encoded or " " in encoded:
            return "", ""
        decoded = base64.b64decode(encoded, validate=True)
        if base64.b64encode(decoded).decode("ascii") != encoded:
            return "", ""
        credentials = decoded.decode("utf-8")
    except (UnicodeDecodeError, ValueError, binascii.Error):
        return "", ""
    username, separator, password = credentials.partition(":")
    if not separator:
        return "", ""
    return username, password


async def _send_denial(send: Send) -> None:
    await _send_empty_response(send, status=401, challenge=_CHALLENGE)


async def _send_empty_response(send: Send, *, status: int, challenge: str | None = None) -> None:
    headers = [
        (b"cache-control", b"no-store"),
        (b"content-length", b"0"),
    ]
    if challenge is not None:
        headers.insert(0, (b"www-authenticate", challenge.encode("ascii")))
    start: Message = {"type": "http.response.start", "status": status, "headers": headers}
    body: Message = {"type": "http.response.body", "body": b""}
    await send(start)
    await send(body)
