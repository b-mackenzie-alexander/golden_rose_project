import hashlib
import hmac
import json
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

CURSOR_VERSION = 1
CURSOR_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
CURSOR_KEYS = frozenset({"v", "after_received_at", "after_employer_id", "filter_fingerprint"})
LOWERCASE_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def compute_filter_fingerprint(
    *,
    display_name_query: str,
    employer_type: Literal["household", "business"] | None,
) -> str:
    canonical_filters = json.dumps(
        {
            "display_name_query": display_name_query,
            "employer_type": employer_type,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_filters.encode("utf-8")).hexdigest()


def encode_search_cursor(
    *,
    after_received_at: datetime,
    after_employer_id: UUID,
    filter_fingerprint: str,
) -> str:
    payload = {
        "after_employer_id": str(after_employer_id),
        "after_received_at": after_received_at.astimezone(UTC).strftime(CURSOR_TIMESTAMP_FORMAT),
        "filter_fingerprint": filter_fingerprint,
        "v": CURSOR_VERSION,
    }
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return urlsafe_b64encode(canonical_payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_search_cursor(
    cursor: str,
    *,
    expected_filter_fingerprint: str | None = None,
) -> dict[str, str | int]:
    try:
        padding = "=" * (-len(cursor) % 4)
        decoded_payload = urlsafe_b64decode(cursor + padding).decode("utf-8")
        payload = json.loads(decoded_payload)

        if not isinstance(payload, dict):
            msg = "cursor payload must be an object"
            raise ValueError(msg)
        if set(payload) != CURSOR_KEYS:
            msg = "cursor payload must contain the exact expected keys"
            raise ValueError(msg)
        if payload["v"] != CURSOR_VERSION or not isinstance(payload["v"], int):
            msg = "cursor version is invalid"
            raise ValueError(msg)
        if not isinstance(payload["after_received_at"], str):
            msg = "cursor timestamp is invalid"
            raise ValueError(msg)
        datetime.strptime(payload["after_received_at"], CURSOR_TIMESTAMP_FORMAT)
        if not isinstance(payload["after_employer_id"], str):
            msg = "cursor employer id is invalid"
            raise ValueError(msg)
        UUID(payload["after_employer_id"])
        if not isinstance(
            payload["filter_fingerprint"], str
        ) or not LOWERCASE_SHA256_PATTERN.fullmatch(payload["filter_fingerprint"]):
            msg = "cursor fingerprint is invalid"
            raise ValueError(msg)
        canonical_cursor = encode_search_cursor(
            after_received_at=datetime.strptime(
                payload["after_received_at"], CURSOR_TIMESTAMP_FORMAT
            ).replace(tzinfo=UTC),
            after_employer_id=UUID(payload["after_employer_id"]),
            filter_fingerprint=payload["filter_fingerprint"],
        )
        if cursor != canonical_cursor:
            msg = "cursor transport is noncanonical"
            raise ValueError(msg)
        if expected_filter_fingerprint is not None and not hmac.compare_digest(
            payload["filter_fingerprint"],
            expected_filter_fingerprint,
        ):
            msg = "cursor fingerprint does not match current filters"
            raise ValueError(msg)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        msg = "invalid search cursor"
        raise ValueError(msg) from exc

    return {
        "v": payload["v"],
        "after_received_at": payload["after_received_at"],
        "after_employer_id": payload["after_employer_id"],
        "filter_fingerprint": payload["filter_fingerprint"],
    }
