import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

CURSOR_VERSION = 1
CURSOR_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
CURSOR_KEYS = frozenset(
    {"after_created_at", "after_employer_contact_id", "employer_id", "page_size", "v"}
)


@dataclass(frozen=True, slots=True)
class ContactCursor:
    version: int
    employer_id: UUID
    page_size: int
    after_created_at: datetime
    after_employer_contact_id: UUID


def encode_contact_cursor(cursor: ContactCursor) -> str:
    payload = {
        "after_created_at": cursor.after_created_at.astimezone(UTC).strftime(
            CURSOR_TIMESTAMP_FORMAT
        ),
        "after_employer_contact_id": str(cursor.after_employer_contact_id),
        "employer_id": str(cursor.employer_id),
        "page_size": cursor.page_size,
        "v": cursor.version,
    }
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return urlsafe_b64encode(canonical_payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_contact_cursor(
    cursor: str,
    *,
    expected_employer_id: UUID | None = None,
    expected_page_size: int | None = None,
) -> ContactCursor:
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
        if not isinstance(payload["page_size"], int):
            msg = "cursor page size is invalid"
            raise ValueError(msg)
        if not isinstance(payload["after_created_at"], str):
            msg = "cursor timestamp is invalid"
            raise ValueError(msg)
        after_created_at = datetime.strptime(
            payload["after_created_at"], CURSOR_TIMESTAMP_FORMAT
        ).replace(tzinfo=UTC)
        if not isinstance(payload["employer_id"], str):
            msg = "cursor employer id is invalid"
            raise ValueError(msg)
        employer_id = UUID(payload["employer_id"])
        if not isinstance(payload["after_employer_contact_id"], str):
            msg = "cursor employer contact id is invalid"
            raise ValueError(msg)
        after_employer_contact_id = UUID(payload["after_employer_contact_id"])

        canonical_cursor = encode_contact_cursor(
            ContactCursor(
                version=payload["v"],
                employer_id=employer_id,
                page_size=payload["page_size"],
                after_created_at=after_created_at,
                after_employer_contact_id=after_employer_contact_id,
            )
        )
        if cursor != canonical_cursor:
            msg = "cursor transport is noncanonical"
            raise ValueError(msg)
        if expected_employer_id is not None and employer_id != expected_employer_id:
            msg = "cursor employer id does not match current parent"
            raise ValueError(msg)
        if expected_page_size is not None and payload["page_size"] != expected_page_size:
            msg = "cursor page size does not match current page size"
            raise ValueError(msg)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        msg = "invalid contact cursor"
        raise ValueError(msg) from exc

    return ContactCursor(
        version=payload["v"],
        employer_id=employer_id,
        page_size=payload["page_size"],
        after_created_at=after_created_at,
        after_employer_contact_id=after_employer_contact_id,
    )
