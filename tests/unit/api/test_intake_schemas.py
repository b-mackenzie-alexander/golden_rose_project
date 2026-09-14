from typing import Any

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.intake_schemas import (
    CreateIntakeRequest,
    QueryIntakesRequest,
    ReviseIntakeRequest,
)


@pytest.mark.parametrize("content", [{}, {"phone": None}, {"availability": {"mode": "unknown"}}])
def test_create_floor(content):
    with pytest.raises(ValidationError):
        CreateIntakeRequest.model_validate({"kind": "worker", "content": content})


def test_create_address_only():
    body = CreateIntakeRequest.model_validate(
        {"kind": "worker", "content": {"residential_address": {"locality": "X"}}}
    )
    assert body.content.to_content() == {"residential_address": {"locality": "X"}}


def test_revision_defers_kind_validation_but_rejects_address():
    with pytest.raises(ValidationError):
        ReviseIntakeRequest.model_validate(
            {"expected_version": 1, "content": {"residential_address": {}}}
        )


@pytest.mark.parametrize(
    "body",
    [
        {"kind": "worker", "page_size": True},
        {"kind": "worker", "reference": "1"},
        {"kind": "worker", "name_query": "x"},
        {"kind": "worker", "name_query": "ab", "reference": "00000000-0000-0000-0000-000000000001"},
    ],
)
def test_query_validation(body):
    with pytest.raises(ValidationError):
        QueryIntakesRequest.model_validate(body)


def response_detail() -> dict[str, Any]:
    return {
        "summary": {
            "intake_id": "00000000-0000-0000-0000-000000000001",
            "kind": "worker",
            "version": 1,
            "lifecycle": "draft",
            "complete": False,
            "missing_fields": ["phone"],
            "review_status": "unreviewed",
            "updated_at": "2026-09-14T12:00:00Z",
        },
        "content_version": 1,
        "candidate": {"full_name": "Fictional Person"},
        "resolved": {},
        "links": {},
        "dependency_stale": False,
    }


def test_response_preserves_missing_name_and_values():
    from golden_rose.api.staff.intake_schemas import IntakeDetail

    payload = response_detail()
    assert (
        IntakeDetail.model_validate(payload).model_dump(mode="json", exclude_unset=True) == payload
    )


@pytest.mark.parametrize(
    ("target", "key", "value"),
    [
        ("summary", "phone", "2125550100"),
        ("summary", "missing_fields", ["secret address"]),
        ("summary", "offer", {"terms": "Private terms"}),
        ("candidate", "residential_address", {"line1": "Private street"}),
        ("candidate", "phone_search_key", "2125550100"),
        ("resolved", "full_name", "Future canonical name"),
        ("links", "worker_id", "00000000-0000-0000-0000-000000000002"),
    ],
)
def test_response_rejects_unapproved_fields(target, key, value):
    from golden_rose.api.staff.intake_schemas import IntakeDetail

    payload = response_detail()
    payload[target][key] = value
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_response_candidate_must_match_kind():
    from golden_rose.api.staff.intake_schemas import IntakeDetail

    payload = response_detail()
    payload["candidate"] = {"employer_type": "business"}
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_intake_routes_publish_explicit_response_contracts():
    from fastapi import FastAPI

    from golden_rose.api.staff.intakes import router

    app = FastAPI()
    app.include_router(router)
    paths = app.openapi()["paths"]
    expected = {
        "/api/staff/v1/intakes": ("post", "IntakeCommandResponse"),
        "/api/staff/v1/intakes/query": ("post", "IntakeQueryPageResponse"),
        "/api/staff/v1/intakes/{intake_id}": ("get", "IntakeDetail"),
        "/api/staff/v1/intakes/{intake_id}/revisions": ("post", "IntakeCommandResponse"),
        "/api/staff/v1/intakes/{intake_id}/addresses/{section}": ("get", "IntakeAddressDetail"),
        "/api/staff/v1/intakes/{intake_id}/addresses/{section}/revisions": (
            "post",
            "IntakeCommandResponse",
        ),
    }
    for path, (method, model) in expected.items():
        assert paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"][
            "$ref"
        ].endswith("/" + model)
    assert "201" in paths["/api/staff/v1/intakes"]["post"]["responses"]


def test_address_response_keeps_cleared_null_and_rejects_future_resolved():
    from golden_rose.api.staff.intake_schemas import IntakeAddressDetail

    payload = {
        "intake_id": "00000000-0000-0000-0000-000000000001",
        "version": 1,
        "section": "worker_residence",
        "candidate": None,
        "resolved": None,
    }
    assert (
        IntakeAddressDetail.model_validate(payload).model_dump(mode="json", exclude_unset=True)
        == payload
    )
    with pytest.raises(ValidationError):
        IntakeAddressDetail.model_validate({**payload, "resolved": {"line1": "Hidden"}})


def test_command_response_rejects_result_newer_than_current():
    from golden_rose.api.staff.intake_schemas import IntakeCommandResponse

    with pytest.raises(ValidationError):
        IntakeCommandResponse.model_validate(
            {
                "command_id": "00000000-0000-0000-0000-000000000002",
                "result_record_version": 2,
                "current": response_detail(),
            }
        )
