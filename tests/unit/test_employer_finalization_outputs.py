"""Statement-level proof of employer output construction, not database qualification."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.employer_intake_outputs import insert_new_employer_group

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)
ACTOR = uuid4()
PARTY = {
    "line1": "10 Fictional Party Road",
    "locality": "Fictional City",
    "country": "US",
    "region": "NY",
    "postal_code": "10001",
}
WORKSITE = {**PARTY, "line1": "20 Fictional Worksite Road"}


def content(kind: str = "household") -> dict[str, Any]:
    return {
        "employer_type": kind,
        "display_name": " Fictional Employer ",
        "representative_name": "Fictional Representative",
        "phone": "202-555-0151",
        "role_title": "Fictional role",
        "duties_summary": "Fictional duties",
        "worker_count": 2,
        "schedule": {"mode": "to_be_discussed"},
        "offer": {
            "minimum": "20.00",
            "maximum": "25.00",
            "currency": "USD",
            "basis": "hour",
            "per_worker": True,
            "negotiable": True,
            "terms": "Fictional offer terms",
        },
    }


def insert_group(session: Any, kind: str = "household", **overrides: Any) -> dict[str, Any]:
    return insert_new_employer_group(
        session,
        **{
            "content": content(kind),
            "party_address": PARTY,
            "worksite_address": WORKSITE,
            "actor_id": ACTOR,
            "now": NOW,
            **overrides,
        },
    )


@pytest.mark.parametrize("kind,count", [("household", 5), ("business", 6)])
def test_employer_outputs_keep_exact_parentage_and_attribution(kind, count):
    session = Mock()
    identities = insert_group(session, kind)
    assert len(identities) == count
    assert len(set(identities.values())) == count
    statements = [call.args[0] for call in session.execute.call_args_list]
    rows = {
        statement.table.name: statement.compile().params
        for statement in statements
        if statement.table.name != "entity_authorities"
    }
    assert set(rows) == {
        "employers",
        "employer_contacts",
        "employer_contact_details",
        "worksites",
        "staffing_requests",
    } | ({"employer_addresses"} if kind == "business" else set())
    authorities = [
        statement.compile().params
        for statement in statements
        if statement.table.name == "entity_authorities"
    ]
    assert len(authorities) == count
    for entity_type, identity in identities.items():
        assert {
            "entity_type": entity_type,
            "entity_id": identity,
            f"{entity_type}_id": identity,
        } in authorities
    for row in rows.values():
        assert row["version"] == 1
        # Legacy Employer insertion leaves updated_by to its existing DB trigger.
        assert row["created_by"] == row.get("updated_by", row["created_by"]) == ACTOR
        assert row["created_at"] == row["updated_at"] == NOW
        assert row["employer_id"] == identities["employer"]
    assert rows["employers"]["display_name"] == "Fictional Employer"
    assert rows["employers"]["lifecycle_status"] == "draft"
    assert rows["employers"]["source_channel"] == "staff_entry"
    assert "phone" not in rows["employer_contacts"]
    details = rows["employer_contact_details"]
    assert details["employer_contact_id"] == identities["employer_contact"]
    assert details["representative_name"] == "Fictional Representative"
    assert details["phone"] == "202-555-0151"
    assert "email" not in details
    if kind == "household":
        assert details["line1"] == PARTY["line1"]
        assert "employer_address" not in identities
    else:
        assert not any(name in details for name in PARTY)
        assert rows["employer_addresses"]["line1"] == PARTY["line1"]
        assert rows["employer_addresses"]["purpose"] == "business"
    request = rows["staffing_requests"]
    assert request["request_type"] == ("household" if kind == "household" else "general_labor")
    assert request["request_status"] == "draft"
    assert request["source_channel"] == "staff_entry"
    assert request["received_at"] == NOW
    assert request["employer_contact_id"] == identities["employer_contact"]
    assert request["worksite_id"] == identities["worksite"]
    assert request["employer_address_id"] == identities.get("employer_address")
    assert request["offer"] == content(kind)["offer"]
    assert request["schedule"] == {"mode": "to_be_discussed"}
    assert rows["worksites"]["line1"] == WORKSITE["line1"]
    assert rows["worksites"]["location_verification_status"] == "supplied"
    assert rows["worksites"]["service_area_status"] == "unassigned"
    assert rows["worksites"]["map_area_status"] == "pending"
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_employer_output_writes_contact_email_when_supplied():
    session = Mock()
    supplied_content = content()
    supplied_content["email"] = "employer@example.test"
    insert_new_employer_group(
        session,
        content=supplied_content,
        party_address=PARTY,
        worksite_address=WORKSITE,
        actor_id=ACTOR,
        now=NOW,
    )
    details = next(
        call.args[0].compile().params
        for call in session.execute.call_args_list
        if call.args[0].table.name == "employer_contact_details"
    )
    assert details["email"] == "employer@example.test"


@pytest.mark.parametrize(
    "field",
    [
        "employer_type",
        "display_name",
        "representative_name",
        "phone",
        "role_title",
        "duties_summary",
        "worker_count",
        "schedule",
        "offer",
    ],
)
def test_incomplete_content_is_rejected_before_first_insert(field):
    session = Mock()
    candidate = content()
    del candidate[field]
    with pytest.raises(IntakeError) as error:
        insert_group(session, content=candidate)
    assert error.value.code == "incomplete"
    assert field in (error.value.missing_fields or [])
    session.execute.assert_not_called()


@pytest.mark.parametrize("section", ["party_address", "worksite_address"])
@pytest.mark.parametrize(
    "address",
    [None, {}, {"line1": "Fictional"}, {"line1": "Fictional", "locality": "City", "country": "US"}],
)
def test_incomplete_addresses_are_rejected_before_first_insert(section, address):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        insert_group(session, **{section: address})
    assert error.value.code == "incomplete"
    assert section in (error.value.missing_fields or [])
    session.execute.assert_not_called()


@pytest.mark.parametrize(
    "patch",
    [
        {"worker_count": True},
        {"unknown": "private-value"},
        {"offer": {"minimum": "25", "maximum": "20"}},
    ],
)
def test_invalid_values_are_rejected_before_first_insert(patch):
    session = Mock()
    with pytest.raises(ValidationError):
        insert_group(session, content={**content(), **patch})
    session.execute.assert_not_called()


def test_late_insert_failure_is_left_to_outer_transaction():
    session = Mock()
    failure = OperationalError("fixture", {}, Exception("fixture"))
    session.execute.side_effect = [None] * 8 + [failure]
    with pytest.raises(OperationalError):
        insert_group(session)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


@pytest.mark.parametrize(
    "patch,missing",
    [
        ({"schedule": {"mode": "unknown"}}, "schedule"),
        ({"offer": {"negotiable": True}}, "offer"),
        ({"offer": {"minimum": "20", "currency": "USD", "basis": "hour"}}, "offer"),
    ],
)
def test_partial_schedule_or_offer_does_not_create_outputs(patch, missing):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        insert_group(session, content={**content(), **patch})
    assert missing in (error.value.missing_fields or [])
    session.execute.assert_not_called()


def test_specified_schedule_remains_draft_evidence_not_a_shift():
    session = Mock()
    schedule = {"mode": "specified", "requested_start_date": "2026-10-01"}
    insert_group(session, content={**content(), "schedule": schedule})
    statements = [call.args[0] for call in session.execute.call_args_list]
    request = next(
        statement for statement in statements if statement.table.name == "staffing_requests"
    )
    assert request.compile().params["schedule"] == schedule
    assert request.compile().params["request_status"] == "draft"
    assert all(
        statement.table.name not in {"shifts", "shift_needs", "placements"}
        for statement in statements
    )
