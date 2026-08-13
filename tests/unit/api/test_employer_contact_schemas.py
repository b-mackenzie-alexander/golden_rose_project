from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.schemas import (
    EmployerContactCreateRequest,
    EmployerContactQueryPageResponse,
    EmployerContactQueryRequest,
    EmployerContactResponse,
    EmployerContactSummaryResponse,
)


def test_employer_contact_create_transport_schema_preserves_raw_name_and_forbids_extra_fields() -> (
    None
):
    raw_full_name = "  Cafe\u0301 Contact  "

    request = EmployerContactCreateRequest.model_validate({"full_name": raw_full_name})

    assert request.full_name == raw_full_name

    with pytest.raises(ValidationError) as exc_info:
        EmployerContactCreateRequest.model_validate(
            {
                "full_name": raw_full_name,
                "employer_contact_id": "forbidden",
            }
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"


def test_employer_contact_response_schema_has_exact_minimized_fields_and_rejects_extras() -> None:
    timestamp = datetime(2026, 8, 12, 19, 0, 0, tzinfo=UTC)

    response = EmployerContactResponse(
        employer_contact_id=UUID("12121212-1212-4212-8212-121212121212"),
        employer_id=UUID("34343434-3434-4434-8434-343434343434"),
        full_name="Café Contact",
        version=1,
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert response.model_dump(mode="json") == {
        "employer_contact_id": "12121212-1212-4212-8212-121212121212",
        "employer_id": "34343434-3434-4434-8434-343434343434",
        "full_name": "Café Contact",
        "version": 1,
        "created_at": "2026-08-12T19:00:00Z",
        "updated_at": "2026-08-12T19:00:00Z",
    }

    with pytest.raises(ValidationError) as exc_info:
        EmployerContactResponse.model_validate(
            {
                "employer_contact_id": "12121212-1212-4212-8212-121212121212",
                "employer_id": "34343434-3434-4434-8434-343434343434",
                "full_name": "Café Contact",
                "version": 1,
                "created_at": "2026-08-12T19:00:00Z",
                "updated_at": "2026-08-12T19:00:00Z",
                "created_by": "forbidden",
            }
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"


def test_employer_contact_query_schemas_have_exact_bounded_fields_and_minimized_page_shape() -> (
    None
):
    timestamp = datetime(2026, 8, 12, 19, 30, 0, tzinfo=UTC)

    request = EmployerContactQueryRequest.model_validate(
        {
            "page_size": 25,
            "cursor": "opaque-cursor-token",
        }
    )

    assert request.model_dump() == {
        "page_size": 25,
        "cursor": "opaque-cursor-token",
    }

    summary = EmployerContactSummaryResponse(
        employer_contact_id=UUID("56565656-5656-4565-8565-565656565656"),
        employer_id=UUID("78787878-7878-4878-8878-787878787878"),
        full_name="Café Contact",
        version=1,
        created_at=timestamp,
        updated_at=timestamp,
    )
    page = EmployerContactQueryPageResponse(items=[summary], next_cursor="next-page-token")

    assert page.model_dump(mode="json") == {
        "items": [
            {
                "employer_contact_id": "56565656-5656-4565-8565-565656565656",
                "employer_id": "78787878-7878-4878-8878-787878787878",
                "full_name": "Café Contact",
                "version": 1,
                "created_at": "2026-08-12T19:30:00Z",
                "updated_at": "2026-08-12T19:30:00Z",
            }
        ],
        "next_cursor": "next-page-token",
    }

    with pytest.raises(ValidationError) as exc_info:
        EmployerContactQueryRequest.model_validate(
            {
                "page_size": 25,
                "cursor": "opaque-cursor-token",
                "display_name_query": "forbidden",
            }
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"

    with pytest.raises(ValidationError) as exc_info:
        EmployerContactQueryPageResponse.model_validate(
            {
                "items": [
                    {
                        "employer_contact_id": "56565656-5656-4565-8565-565656565656",
                        "employer_id": "78787878-7878-4878-8878-787878787878",
                        "full_name": "Café Contact",
                        "version": 1,
                        "created_at": "2026-08-12T19:30:00Z",
                        "updated_at": "2026-08-12T19:30:00Z",
                    }
                ],
                "next_cursor": "next-page-token",
                "total_count": 1,
            }
        )

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"
