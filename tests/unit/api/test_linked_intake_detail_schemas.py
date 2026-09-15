from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.intake_schemas import IntakeAddressDetail, IntakeDetail, IntakeSummary
from tests.unit.api.test_intake_schemas import response_detail


def linked(kind="worker") -> dict[str, Any]:
    result = response_detail()
    result["summary"]["kind"] = kind
    result["candidate"] = (
        {"full_name": "Candidate"} if kind == "worker" else {"display_name": "Candidate"}
    )
    names = (
        ("worker", "worker_contact", "worker_residence", "worker_preferences")
        if kind == "worker"
        else ("employer",)
    )
    result["links"] = {name: {"id": str(uuid4()), "version": 2} for name in names}
    result["resolved"] = (
        {"full_name": "Canonical"}
        if kind == "worker"
        else {"employer_type": "business", "display_name": "Canonical"}
    )
    return result


@pytest.mark.parametrize("kind", ["worker", "employer"])
@pytest.mark.parametrize("stale", [True, False])
def test_typed_linked_facts_round_trip_separately(kind, stale):
    payload = linked(kind)
    payload["dependency_stale"] = stale
    assert (
        IntakeDetail.model_validate(payload).model_dump(mode="json", exclude_unset=True) == payload
    )


@pytest.mark.parametrize(
    "field",
    [
        "line1",
        "residential_address",
        "party_address",
        "worksite_address",
        "role_title",
        "offer",
        "private_note",
    ],
)
def test_resolved_employer_rejects_addresses_and_new_request_fields(field):
    payload = linked("employer")
    payload["resolved"][field] = "Forbidden"
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


@pytest.mark.parametrize("field", ["phone", "representative_name"])
def test_unselected_contact_cannot_be_present_even_as_null(field):
    payload = linked("employer")
    payload["resolved"][field] = None
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_selected_contact_and_details_allow_phone():
    payload = linked("employer")
    for name in ("employer_contact", "employer_contact_details"):
        payload["links"][name] = {"id": str(uuid4()), "version": 1}
    payload["resolved"].update(phone="202-555-0151", representative_name="Canonical Contact")
    assert IntakeDetail.model_validate(payload).resolved.phone == "202-555-0151"


@pytest.mark.parametrize(
    "name", ["worker", "worker_contact", "worker_residence", "worker_preferences"]
)
def test_worker_requires_all_selected_children(name):
    payload = linked()
    del payload["links"][name]
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


@pytest.mark.parametrize("version", [True, "1", 0, 2147483648])
def test_reference_versions_are_strict(version):
    payload = linked()
    payload["links"]["worker"]["version"] = version
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_cross_kind_resolved_fields_and_references_are_rejected():
    payload = linked("employer")
    payload["resolved"] = {"full_name": "Worker"}
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)
    payload = linked("employer")
    payload["links"]["worker"] = {"id": str(uuid4()), "version": 1}
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_selected_contact_requires_details():
    payload = linked("employer")
    payload["links"]["employer_contact"] = {"id": str(uuid4()), "version": 1}
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


@pytest.mark.parametrize("section", ["worker_residence", "party_address", "worksite_address"])
def test_restricted_address_preserves_separate_candidates_and_source(section):
    payload = {
        "intake_id": str(uuid4()),
        "version": 3,
        "section": section,
        "candidate": {"line1": "Candidate address"},
        "resolved": {"line1": "Canonical address"},
        "source_ref": {"id": str(uuid4()), "version": 2},
    }
    result = IntakeAddressDetail.model_validate(payload)
    assert result.model_dump(mode="json", exclude_unset=True) == payload
    payload.pop("source_ref")
    with pytest.raises(ValidationError):
        IntakeAddressDetail.model_validate(payload)


def test_resolved_worker_rejects_address_values():
    payload = linked()
    payload["resolved"]["residential_address"] = {"line1": "Protected"}
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_household_rejects_business_address():
    payload = linked("employer")
    payload["resolved"]["employer_type"] = "household"
    payload["links"]["employer_address"] = {"id": str(uuid4()), "version": 1}
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate(payload)


def test_changed_parent_type_keeps_original_business_address_only_when_stale():
    payload = linked("employer")
    payload["resolved"]["employer_type"] = "household"
    payload["links"]["employer_address"] = {"id": str(uuid4()), "version": 1}
    payload["dependency_stale"] = True
    assert (
        IntakeDetail.model_validate(payload).model_dump(mode="json", exclude_unset=True)["links"]
        == payload["links"]
    )


def test_unavailable_query_summary_cannot_claim_name_missing_fields_or_full_detail():
    payload = linked()
    summary = {**payload["summary"], "complete": None, "missing_fields": []}
    summary.pop("display_name", None)
    assert IntakeSummary.model_validate(summary).complete is None
    for patch in ({"display_name": "Hidden canonical"}, {"missing_fields": ["phone"]}):
        with pytest.raises(ValidationError):
            IntakeSummary.model_validate({**summary, **patch})
    with pytest.raises(ValidationError):
        IntakeDetail.model_validate({**payload, "summary": summary})
