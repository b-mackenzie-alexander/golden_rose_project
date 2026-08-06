from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.schemas import (
    CreateDraftEmployerRequest,
    DraftEmployerResponse,
    EmployerDetailResponse,
    EmployerSearchItemResponse,
    EmployerSearchPageResponse,
    SearchEmployersRequest,
)


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


def test_name_only_search_is_trimmed_and_nfc_normalized() -> None:
    request = SearchEmployersRequest(display_name_query="  Cafe\u0301  Staffing  ")

    assert request.display_name_query == "Café  Staffing"


def test_search_accepts_name_with_optional_type() -> None:
    request = SearchEmployersRequest(
        display_name_query="Synthetic Employer",
        employer_type="household",
    )

    assert request.display_name_query == "Synthetic Employer"
    assert request.employer_type == "household"


def test_search_rejects_name_outside_two_to_one_hundred_characters() -> None:
    with pytest.raises(ValidationError) as short_exc_info:
        SearchEmployersRequest(display_name_query="x")

    assert short_exc_info.value.errors()[0]["type"] == "value_error"

    with pytest.raises(ValidationError) as long_exc_info:
        SearchEmployersRequest(display_name_query="x" * 101)

    assert long_exc_info.value.errors()[0]["type"] == "value_error"


def test_search_rejects_unicode_control_characters() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SearchEmployersRequest(display_name_query="Bad\nName")

    assert exc_info.value.errors()[0]["type"] == "value_error"


def test_search_forbids_unknown_fields_and_invalid_type() -> None:
    with pytest.raises(ValidationError) as invalid_type_exc_info:
        SearchEmployersRequest.model_validate(
            {
                "display_name_query": "Synthetic Employer",
                "employer_type": "agency",
            }
        )

    assert invalid_type_exc_info.value.errors()[0]["type"] == "literal_error"

    with pytest.raises(ValidationError) as unexpected_field_exc_info:
        SearchEmployersRequest.model_validate(
            {
                "display_name_query": "Synthetic Employer",
                "unexpected": True,
            }
        )

    assert unexpected_field_exc_info.value.errors()[0]["type"] == "extra_forbidden"


def test_search_page_size_defaults_and_bounds() -> None:
    default_request = SearchEmployersRequest(display_name_query="Synthetic Employer")

    assert default_request.page_size == 25

    bounded_request = SearchEmployersRequest(
        display_name_query="Synthetic Employer",
        page_size=50,
    )

    assert bounded_request.page_size == 50

    with pytest.raises(ValidationError) as low_exc_info:
        SearchEmployersRequest(display_name_query="Synthetic Employer", page_size=0)

    assert low_exc_info.value.errors()[0]["type"] == "greater_than_equal"

    with pytest.raises(ValidationError) as high_exc_info:
        SearchEmployersRequest(display_name_query="Synthetic Employer", page_size=51)

    assert high_exc_info.value.errors()[0]["type"] == "less_than_equal"


def test_search_rejects_cursor_over_512_characters() -> None:
    cursor = "x" * 513

    with pytest.raises(ValidationError) as exc_info:
        SearchEmployersRequest(
            display_name_query="Synthetic Employer",
            cursor=cursor,
        )

    assert exc_info.value.errors()[0]["type"] == "string_too_long"


def test_employer_read_responses_expose_exact_accepted_fields() -> None:
    timestamp = datetime(2026, 8, 5, 3, 0, 0, tzinfo=UTC)
    employer_id = uuid4()

    detail = EmployerDetailResponse(
        employer_id=employer_id,
        employer_type="household",
        display_name="Synthetic Household 001",
        lifecycle_status="draft",
        source_channel="staff_entry",
        version=1,
        received_at=timestamp,
        created_at=timestamp,
    )
    item = EmployerSearchItemResponse(
        employer_id=employer_id,
        employer_type="household",
        display_name="Synthetic Household 001",
        lifecycle_status="draft",
        version=1,
        received_at=timestamp,
    )
    page = EmployerSearchPageResponse(items=[item], next_cursor=None)

    assert set(detail.model_dump(mode="json")) == {
        "employer_id",
        "employer_type",
        "display_name",
        "lifecycle_status",
        "source_channel",
        "version",
        "received_at",
        "created_at",
    }
    assert set(item.model_dump(mode="json")) == {
        "employer_id",
        "employer_type",
        "display_name",
        "lifecycle_status",
        "version",
        "received_at",
    }
    assert page.model_dump(mode="json") == {
        "items": [item.model_dump(mode="json")],
        "next_cursor": None,
    }


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
