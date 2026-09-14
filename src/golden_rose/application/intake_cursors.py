"""Process-lifetime opaque cursors bound to the complete current query authority."""

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal

_KEY = secrets.token_bytes(32)


def binding(principal: StaffPrincipal, context: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "actor": str(principal.actor_id),
                "permissions": sorted(principal.permissions),
                "scope": None
                if principal.intake_scope is None
                else sorted(map(str, principal.intake_scope)),
                "context": context,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def encode_cursor(bound: str, position: dict[str, Any]) -> str:
    raw = json.dumps(
        {"v": 1, "binding": bound, "position": position}, sort_keys=True, separators=(",", ":")
    ).encode()
    return base64.urlsafe_b64encode(hmac.digest(_KEY, raw, "sha256") + raw).decode().rstrip("=")


def decode_cursor(cursor: str | None, bound: str) -> dict[str, Any] | None:
    if cursor is None:
        return None
    try:
        raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        if not hmac.compare_digest(raw[:32], hmac.digest(_KEY, raw[32:], "sha256")):
            raise ValueError
        payload = json.loads(raw[32:])
        if (
            set(payload) != {"v", "binding", "position"}
            or payload["v"] != 1
            or payload["binding"] != bound
            or not isinstance(payload["position"], dict)
            or encode_cursor(bound, payload["position"]) != cursor
        ):
            raise ValueError
        return dict(payload["position"])
    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise IntakeError("invalid_cursor", 422) from exc
