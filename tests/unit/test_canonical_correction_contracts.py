"""Canonical corrections must never accept partial drafts or other sections."""

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.application import canonical_correction_contracts as contracts

ADDRESS = {
    "line1": "100 Fictional Street",
    "locality": "Example",
    "region": "NY",
    "postal_code": "10001",
    "country": "US",
}
CASES: list[tuple[str, dict[str, Any]]] = [
    ("CorrectWorkerRequest", {"full_name": "Fictional Worker"}),
    (
        "CorrectWorkerContactRequest",
        {"phone": "2125550100", "email": "worker@example.test"},
    ),
    ("CorrectWorkerResidenceRequest", {"address": ADDRESS}),
    (
        "CorrectWorkerPreferencesRequest",
        {
            "interests": {"other_description": "Fictional service"},
            "availability": {"mode": "flexible"},
        },
    ),
    (
        "CorrectContactDetailsRequest",
        {
            "representative_name": "Fictional Representative",
            "phone": "2125550101",
            "email": "employer@example.test",
        },
    ),
    ("CorrectContactAddressRequest", {"address": ADDRESS}),
    ("CorrectEmployerAddressRequest", {"address": ADDRESS}),
    ("CorrectWorksiteAddressRequest", {"address": ADDRESS}),
    (
        "CorrectStaffingRequestRequest",
        {
            "role_title": "Fictional role",
            "duties_summary": "Fictional duties",
            "worker_count": 1,
            "schedule": {"mode": "to_be_discussed"},
            "offer": {"minimum": "20", "currency": "USD", "basis": "hour", "per_worker": True},
        },
    ),
]


@pytest.mark.parametrize("name,values", CASES)
def test_correction_dtos_require_reason_version_and_only_authorized_section(name, values):
    model = getattr(contracts, name)
    body = {"expected_version": 1, "reason_text": "Correct reported facts", **deepcopy(values)}
    assert model.model_validate(body).section_values() == values
    for key in body:
        if key == "email":
            continue
        invalid = deepcopy(body)
        del invalid[key]
        with pytest.raises(ValidationError):
            model.model_validate(invalid)
    for patch in (
        {"expected_version": True},
        {"expected_version": "1"},
        {"expected_version": 0},
        {"expected_version": 2147483647},
        {"reason_text": " "},
        {"reason_text": "x" * 513},
        {"intake_id": str(uuid4())},
        {"lifecycle_status": "open"},
    ):
        with pytest.raises(ValidationError):
            model.model_validate({**body, **patch})
    event = str(uuid4())
    assert (
        str(model.model_validate({**body, "corrects_event_id": event}).corrects_event_id) == event
    )
    with pytest.raises(ValidationError):
        model.model_validate({**body, "corrects_event_id": event.replace("-", "")})


@pytest.mark.parametrize(
    "name",
    [
        "CorrectWorkerResidenceRequest",
        "CorrectContactAddressRequest",
        "CorrectEmployerAddressRequest",
        "CorrectWorksiteAddressRequest",
    ],
)
@pytest.mark.parametrize(
    "address",
    [
        {},
        {"line1": "Fictional Street"},
        {"line1": "Fictional Street", "locality": "Example", "country": "US"},
        {**ADDRESS, "secret": "not allowed"},
    ],
)
def test_address_corrections_require_complete_address(name, address):
    with pytest.raises(ValidationError):
        getattr(contracts, name).model_validate(
            {"expected_version": 1, "reason_text": "Correction", "address": address}
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"interests": {}},
        {"availability": {"mode": "unknown"}},
        {"availability": {"mode": "flexible", "ranges": []}},
    ],
)
def test_preferences_cannot_become_incomplete(patch):
    with pytest.raises(ValidationError):
        contracts.CorrectWorkerPreferencesRequest.model_validate(
            {"expected_version": 1, "reason_text": "Correction", **deepcopy(CASES[3][1]), **patch}
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"schedule": {"mode": "unknown"}},
        {"offer": {}},
        {"worker_count": True},
        {"worker_count": 1001},
    ],
)
def test_request_cannot_become_incomplete(patch):
    with pytest.raises(ValidationError):
        contracts.CorrectStaffingRequestRequest.model_validate(
            {"expected_version": 1, "reason_text": "Correction", **deepcopy(CASES[-1][1]), **patch}
        )


def test_contact_phone_correction_cannot_erase_address():
    with pytest.raises(ValidationError):
        contracts.CorrectContactDetailsRequest.model_validate(
            {"expected_version": 1, "reason_text": "Correction", **CASES[4][1], "address": ADDRESS}
        )


@pytest.mark.parametrize(
    ("model", "values"),
    [
        (contracts.CorrectWorkerContactRequest, {"phone": "2125550100"}),
        (
            contracts.CorrectContactDetailsRequest,
            {"representative_name": "Fictional Representative", "phone": "2125550101"},
        ),
    ],
)
def test_contact_corrections_preserve_an_omitted_email(model, values):
    request = model.model_validate({"expected_version": 1, "reason_text": "Clear email", **values})
    assert "email" not in request.section_values()


@pytest.mark.parametrize(
    ("model", "values"),
    [
        (contracts.CorrectWorkerContactRequest, {"phone": "2125550100"}),
        (
            contracts.CorrectContactDetailsRequest,
            {"representative_name": "Fictional Representative", "phone": "2125550101"},
        ),
    ],
)
def test_contact_corrections_allow_an_explicit_null_email_to_clear(model, values):
    request = model.model_validate(
        {"expected_version": 1, "reason_text": "Clear email", "email": None, **values}
    )
    assert request.section_values()["email"] is None
