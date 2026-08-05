from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.schemas import CreateDraftEmployerRequest, DraftEmployerResponse


def test_household_request_is_accepted() -> None:
    request = CreateDraftEmployerRequest(
        employer_type="household",
        display_name="Synthetic Household 001",
    )

    assert request.employer_type == "household"
    assert request.display_name == "Synthetic Household 001"


def test_business_request_is_accepted() -> None:
    request = CreateDraftEmployerRequest(
        employer_type="business",
        display_name="Synthetic Business 001",
    )

    assert request.employer_type == "business"
    assert request.display_name == "Synthetic Business 001"


def test_display_name_normalizes_nfc_and_trims_outer_whitespace() -> None:
    request = CreateDraftEmployerRequest(
        employer_type="household",
        display_name="  Cafe\u0301  Staffing  ",
    )

    assert request.display_name == "Café  Staffing"


def test_blank_display_name_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateDraftEmployerRequest(
            employer_type="household",
            display_name="   ",
        )

    assert exc_info.value.errors()[0]["type"] == "value_error"


def test_display_name_longer_than_200_characters_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateDraftEmployerRequest(
            employer_type="household",
            display_name="x" * 201,
        )

    assert exc_info.value.errors()[0]["type"] == "value_error"


def test_display_name_with_control_characters_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateDraftEmployerRequest(
            employer_type="household",
            display_name="Bad\nName",
        )

    assert exc_info.value.errors()[0]["type"] == "value_error"


def test_invalid_employer_type_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateDraftEmployerRequest.model_validate(
            {
                "employer_type": "agency",
                "display_name": "Synthetic Employer 001",
            }
        )

    assert exc_info.value.errors()[0]["type"] == "literal_error"


def test_unknown_property_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateDraftEmployerRequest.model_validate(
            {
                "employer_type": "household",
                "display_name": "Synthetic Employer 001",
                "unexpected": True,
            }
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize(
    "field_name",
    [
        "legal_name",
        "lifecycle_status",
        "source_channel",
        "created_by",
        "received_at",
        "created_at",
        "employer_id",
        "version",
    ],
)
def test_client_settable_system_fields_are_rejected(field_name: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateDraftEmployerRequest.model_validate(
            {
                "employer_type": "household",
                "display_name": "Synthetic Employer 001",
                field_name: "forbidden",
            }
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"


def test_response_serializes_utc_datetimes_as_rfc3339() -> None:
    timestamp = datetime(2026, 8, 4, 20, 30, 45, tzinfo=UTC)
    response = DraftEmployerResponse(
        employer_id=uuid4(),
        employer_type="household",
        display_name="Synthetic Household 001",
        lifecycle_status="draft",
        source_channel="staff_entry",
        version=1,
        received_at=timestamp,
        created_at=timestamp,
    )

    dumped = response.model_dump(mode="json")

    assert dumped["received_at"] == "2026-08-04T20:30:45Z"
    assert dumped["created_at"] == "2026-08-04T20:30:45Z"
