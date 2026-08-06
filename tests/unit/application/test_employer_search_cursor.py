import json
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from golden_rose.application.search_cursor import (
    compute_filter_fingerprint,
    decode_search_cursor,
    encode_search_cursor,
)


def test_filter_fingerprint_is_deterministic_for_normalized_filters() -> None:
    fingerprint_one = compute_filter_fingerprint(
        display_name_query="Café  Staffing",
        employer_type="household",
    )
    fingerprint_two = compute_filter_fingerprint(
        display_name_query="Café  Staffing",
        employer_type="household",
    )

    assert fingerprint_one == fingerprint_two
    assert len(fingerprint_one) == 64


def test_cursor_round_trips_without_transport_padding() -> None:
    timestamp = datetime(2026, 8, 5, 3, 0, 0, tzinfo=UTC)
    employer_id = uuid4()
    fingerprint = compute_filter_fingerprint(
        display_name_query="Café  Staffing",
        employer_type="household",
    )

    cursor = encode_search_cursor(
        after_received_at=timestamp,
        after_employer_id=employer_id,
        filter_fingerprint=fingerprint,
    )

    assert "=" not in cursor
    assert decode_search_cursor(cursor) == {
        "v": 1,
        "after_received_at": "2026-08-05T03:00:00.000000Z",
        "after_employer_id": str(employer_id),
        "filter_fingerprint": fingerprint,
    }


def test_cursor_rejects_malformed_or_invalid_typed_payloads() -> None:
    invalid_payload = {
        "v": "1",
        "after_received_at": "2026-08-05T03:00:00.000000Z",
        "after_employer_id": 123,
        "filter_fingerprint": [],
    }
    cursor = (
        urlsafe_b64encode(
            json.dumps(invalid_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        .decode("ascii")
        .rstrip("=")
    )

    with pytest.raises(ValueError):
        decode_search_cursor(cursor)


def test_cursor_rejects_noncanonical_transport_payload() -> None:
    timestamp = datetime(2026, 8, 5, 3, 0, 0, tzinfo=UTC)
    employer_id = uuid4()
    fingerprint = compute_filter_fingerprint(
        display_name_query="Café  Staffing",
        employer_type="household",
    )
    canonical_cursor = encode_search_cursor(
        after_received_at=timestamp,
        after_employer_id=employer_id,
        filter_fingerprint=fingerprint,
    )
    noncanonical_cursor = canonical_cursor + "="

    with pytest.raises(ValueError):
        decode_search_cursor(noncanonical_cursor)


def test_cursor_rejects_different_normalized_filters() -> None:
    timestamp = datetime(2026, 8, 5, 3, 0, 0, tzinfo=UTC)
    employer_id = uuid4()
    bound_fingerprint = compute_filter_fingerprint(
        display_name_query="Café  Staffing",
        employer_type="household",
    )
    mismatched_fingerprint = compute_filter_fingerprint(
        display_name_query="Different Employer",
        employer_type="household",
    )
    cursor = encode_search_cursor(
        after_received_at=timestamp,
        after_employer_id=employer_id,
        filter_fingerprint=bound_fingerprint,
    )

    with pytest.raises(ValueError):
        decode_search_cursor(
            cursor,
            expected_filter_fingerprint=mismatched_fingerprint,
        )


def test_cursor_encoder_canonicalizes_aware_timestamp_to_utc() -> None:
    employer_id = uuid4()
    fingerprint = compute_filter_fingerprint(
        display_name_query="Café  Staffing",
        employer_type="household",
    )
    eastern_instant = datetime(
        2026,
        8,
        4,
        23,
        0,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    utc_equivalent = datetime(2026, 8, 5, 3, 0, 0, tzinfo=UTC)

    cursor_one = encode_search_cursor(
        after_received_at=eastern_instant,
        after_employer_id=employer_id,
        filter_fingerprint=fingerprint,
    )
    cursor_two = encode_search_cursor(
        after_received_at=utc_equivalent,
        after_employer_id=employer_id,
        filter_fingerprint=fingerprint,
    )

    assert cursor_one == cursor_two
