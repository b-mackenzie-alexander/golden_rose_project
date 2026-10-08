import pytest
from pydantic import ValidationError

from golden_rose.application.intake_contracts import (
    Address,
    Availability,
    Offer,
    Schedule,
    validate_content,
)


def test_partial_content_normalizes_and_clears():
    assert validate_content(
        "worker", {"full_name": "  Jose\u0301 ", "phone": None}
    ).to_content() == {"full_name": "José"}


@pytest.mark.parametrize(
    "content",
    [
        {"full_name": 12},
        {"full_name": "\nA"},
        {"full_name": ""},
        {"extra": "a"},
        {"phone": "123"},
        {"interests": {"selections": [{"interest_id": "invalid", "catalog_version": 1}]}},
        {"residential_address": {"line1": "X"}},
    ],
)
def test_reject_invalid_worker(content):
    with pytest.raises(ValidationError):
        validate_content("worker", content)


def test_address_partial_country_explicit():
    assert Address.model_validate({"line1": " X "}).to_content() == {"line1": "X"}
    assert Address.model_validate(
        {"region": "New York", "postal_code": "10001 1234", "country": "US"}
    ).to_content() == {"region": "NY", "postal_code": "10001-1234", "country": "US"}
    for country_value in ("us", "ZZ"):
        with pytest.raises(ValidationError):
            Address.model_validate({"country": country_value})
    for invalid_address in (
        {"region": "Fictional region", "country": "US"},
        {"postal_code": "ABCDE", "country": "US"},
    ):
        with pytest.raises(ValidationError):
            Address.model_validate(invalid_address)


@pytest.mark.parametrize(
    "offer",
    [
        {"minimum": 12},
        {"minimum": "1.001"},
        {"minimum": "-1"},
        {"minimum": "2", "maximum": "1"},
        {"per_worker": 1},
        {"negotiable": "false"},
        {"currency": "ZZZ"},
    ],
)
def test_invalid_offer(offer):
    with pytest.raises(ValidationError):
        Offer.model_validate(offer)


def test_week_wrap_overlap():
    with pytest.raises(ValidationError):
        Availability.model_validate(
            {
                "mode": "weekly",
                "time_zone": "America/New_York",
                "ranges": [
                    {
                        "weekday": 7,
                        "start_local": "23:00",
                        "end_local": "01:00",
                        "end_day_offset": 1,
                    },
                    {
                        "weekday": 1,
                        "start_local": "00:30",
                        "end_local": "02:00",
                        "end_day_offset": 0,
                    },
                ],
            }
        )


def test_schedule_rejects_dst_gap_offset():
    with pytest.raises(ValidationError):
        Schedule.model_validate(
            {
                "mode": "specified",
                "starts_at": "2026-03-08T02:30:00-05:00",
                "ends_at": "2026-03-08T04:00:00-04:00",
                "time_zone": "America/New_York",
            }
        )


@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_worker_count_and_weekday_are_strict(value):
    with pytest.raises(ValidationError):
        validate_content("employer", {"worker_count": value})
    with pytest.raises(ValidationError):
        Availability.model_validate(
            {
                "mode": "weekly",
                "time_zone": "UTC",
                "ranges": [
                    {
                        "weekday": value,
                        "start_local": "09:00",
                        "end_local": "10:00",
                        "end_day_offset": 0,
                    },
                ],
            }
        )


@pytest.mark.parametrize("value", ["+1 (212) 555-0100 ext. 123", "212-555-0100 x1", "212 555 0100"])
def test_phone_preserves_display(value):
    assert validate_content("worker", {"phone": value}).to_content()["phone"] == value


@pytest.mark.parametrize(
    "value", ["212.555.0100", "2125550100ext1234567", "2125550100x", "++2125550100", "2125550100\n"]
)
def test_phone_rejects_invalid(value):
    with pytest.raises(ValidationError):
        validate_content("worker", {"phone": value})


def test_offer_zero_is_substantive_and_null_clears():
    from golden_rose.application.intake_contracts import has_substantive_content

    assert has_substantive_content(Offer.model_validate({"minimum": "0"}).to_content())
    assert not has_substantive_content(Offer.model_validate({"negotiable": False}).to_content())
    assert Offer.model_validate({"minimum": None}).to_content() == {}


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "flexible", "ranges": []},
        {"mode": "weekly", "time_zone": "Invalid/Zone", "ranges": []},
        {"mode": "weekly"},
        {
            "mode": "weekly",
            "time_zone": "UTC",
            "ranges": [
                {"weekday": 1, "start_local": "09:00", "end_local": "09:00", "end_day_offset": 0},
            ],
        },
        {
            "mode": "weekly",
            "time_zone": "UTC",
            "ranges": [
                {"weekday": 1, "start_local": "09:00", "end_local": "10:00", "end_day_offset": 1},
            ],
        },
    ],
)
def test_availability_invalid(payload):
    with pytest.raises(ValidationError):
        Availability.model_validate(payload)


def test_availability_touching_ranges_and_24_hours_allowed():
    body = {
        "mode": "weekly",
        "time_zone": "UTC",
        "ranges": [
            {"weekday": 1, "start_local": "09:00", "end_local": "09:00", "end_day_offset": 1},
            {"weekday": 2, "start_local": "09:00", "end_local": "10:00", "end_day_offset": 0},
        ],
    }
    assert Availability.model_validate(body).to_content() == body


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "unknown", "requested_start_date": "2026-01-01"},
        {"mode": "to_be_discussed", "time_zone": "UTC"},
        {"mode": "specified", "requested_start_date": "2026-02-30"},
        {"mode": "specified", "requested_start_date": "2026-01-01", "time_zone": "UTC"},
        {
            "mode": "specified",
            "starts_at": "2026-01-01T10:00:00",
            "ends_at": "2026-01-01T11:00:00Z",
            "time_zone": "UTC",
        },
        {
            "mode": "specified",
            "starts_at": "2026-01-01T10:00:00Z",
            "ends_at": "2026-01-01T10:00:00Z",
            "time_zone": "UTC",
        },
    ],
)
def test_invalid_schedule(payload):
    with pytest.raises(ValidationError):
        Schedule.model_validate(payload)


def test_explicit_dst_fold_offsets_and_date_only_allowed():
    Schedule.model_validate(
        {
            "mode": "specified",
            "starts_at": "2026-11-01T01:30:00-04:00",
            "ends_at": "2026-11-01T01:30:00-05:00",
            "time_zone": "America/New_York",
        }
    )
    Schedule.model_validate({"mode": "specified", "requested_start_date": "2026-01-01"})


@pytest.mark.parametrize("offset", ["+00:60", "+00:99", "+24:00", "-00:60"])
def test_schedule_rejects_invalid_rfc3339_offset(offset):
    with pytest.raises(ValidationError):
        Schedule.model_validate(
            {
                "mode": "specified",
                "starts_at": f"2026-01-01T10:00:00{offset}",
                "ends_at": f"2026-01-01T11:00:00{offset}",
                "time_zone": "Etc/GMT-1",
            }
        )


@pytest.mark.parametrize(
    ("start", "end", "zone"),
    [
        ("0001-01-01T00:00:00+01:00", "0001-01-01T02:00:00+01:00", "Etc/GMT-1"),
        ("9999-12-31T22:00:00-01:00", "9999-12-31T23:59:59-01:00", "Etc/GMT+1"),
    ],
)
def test_schedule_date_boundary_overflow_is_validation_error(start, end, zone):
    with pytest.raises(ValidationError):
        Schedule.model_validate(
            {
                "mode": "specified",
                "starts_at": start,
                "ends_at": end,
                "time_zone": zone,
            }
        )
