import json
from base64 import urlsafe_b64encode
from datetime import UTC, datetime
from uuid import UUID

import pytest

from golden_rose.application.contact_cursor import (
    ContactCursor,
    decode_contact_cursor,
    encode_contact_cursor,
)


def test_contact_cursor_round_trips_exact_parent_page_size_and_boundary() -> None:
    boundary_created_at = datetime(2026, 8, 12, 23, 0, 0, tzinfo=UTC)
    employer_id = UUID("d1d1d1d1-d1d1-41d1-81d1-d1d1d1d1d1d1")
    employer_contact_id = UUID("d2d2d2d2-d2d2-42d2-82d2-d2d2d2d2d2d2")

    cursor = encode_contact_cursor(
        ContactCursor(
            version=1,
            employer_id=employer_id,
            page_size=25,
            after_created_at=boundary_created_at,
            after_employer_contact_id=employer_contact_id,
        )
    )

    assert "=" not in cursor
    assert decode_contact_cursor(cursor) == ContactCursor(
        version=1,
        employer_id=employer_id,
        page_size=25,
        after_created_at=boundary_created_at,
        after_employer_contact_id=employer_contact_id,
    )


def test_contact_cursor_rejects_malformed_noncanonical_cross_parent_and_page_size_mismatch() -> (
    None
):
    boundary_created_at = datetime(2026, 8, 12, 23, 5, 0, tzinfo=UTC)
    employer_id = UUID("d3d3d3d3-d3d3-43d3-83d3-d3d3d3d3d3d3")
    employer_contact_id = UUID("d4d4d4d4-d4d4-44d4-84d4-d4d4d4d4d4d4")

    canonical_cursor = encode_contact_cursor(
        ContactCursor(
            version=1,
            employer_id=employer_id,
            page_size=25,
            after_created_at=boundary_created_at,
            after_employer_contact_id=employer_contact_id,
        )
    )
    malformed_cursor = "not-base64!"
    noncanonical_cursor = canonical_cursor + "="
    cross_parent_cursor = (
        urlsafe_b64encode(
            json.dumps(
                {
                    "after_created_at": boundary_created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "after_employer_contact_id": str(employer_contact_id),
                    "employer_id": str(UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")),
                    "page_size": 25,
                    "v": 1,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        .decode("ascii")
        .rstrip("=")
    )
    page_size_mismatch_cursor = (
        urlsafe_b64encode(
            json.dumps(
                {
                    "after_created_at": boundary_created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "after_employer_contact_id": str(employer_contact_id),
                    "employer_id": str(employer_id),
                    "page_size": 10,
                    "v": 1,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        .decode("ascii")
        .rstrip("=")
    )

    for cursor in (
        malformed_cursor,
        noncanonical_cursor,
        cross_parent_cursor,
        page_size_mismatch_cursor,
    ):
        with pytest.raises(ValueError, match="invalid contact cursor"):
            decode_contact_cursor(
                cursor,
                expected_employer_id=employer_id,
                expected_page_size=25,
            )
