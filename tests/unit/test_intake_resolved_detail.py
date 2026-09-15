from copy import deepcopy
from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from golden_rose.application import intake_resolved_detail as module
from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence import intakes
from tests.unit.test_resolve_intake_links import PRINCIPAL


@pytest.fixture
def worker(monkeypatch):
    refs = {
        name: {"id": str(uuid4()), "version": 1}
        for name in (
            "worker",
            "worker_contact",
            "worker_preferences",
            "worker_residence",
        )
    }
    monkeypatch.setattr(module, "get_link_dependencies", Mock(return_value=refs))
    session = Mock(spec=Session)
    records = [
        {"version": 2, "full_name": "Canonical"},
        {"version": 1, "phone": "202-555-0151"},
        {
            "version": 1,
            "interests": {"other_description": "Fictional work"},
            "availability": {"mode": "flexible"},
        },
        {"version": 1, "address_complete": True},
    ]
    session.execute.return_value.mappings.return_value.one_or_none.side_effect = records
    principal = replace(
        PRINCIPAL, permissions=frozenset({"intake:read", "worker:read", "worker_contact:read"})
    )
    row = {
        "intake_id": uuid4(),
        "kind": "worker",
        "_has_link_row": True,
        "content": {"full_name": "Candidate"},
        "lifecycle_status": "draft",
    }
    return session, principal, row, refs


def test_worker_without_address_permission_reads_only_boolean_completeness(worker):
    session, principal, row, refs = worker
    original = deepcopy(row)
    content, complete, saved, stale = module.resolved_detail_fields(session, principal, row)
    assert content["full_name"] == "Canonical" and content["phone"] == "202-555-0151"
    assert complete == {"worker_residence": True}
    assert saved == refs and stale
    assert row == original
    selected = [
        c.name for call in session.execute.call_args_list for c in call.args[0].selected_columns
    ]
    assert not {"line1", "line2", "locality", "country", "postal_code", "region"} & set(selected)
    session.commit.assert_not_called()


@pytest.mark.parametrize("permission", ["worker:read", "worker_contact:read"])
def test_revoked_canonical_permission_stops_before_fields(worker, permission):
    session, principal, row, _ = worker
    principal = replace(principal, permissions=principal.permissions - {permission})
    with pytest.raises(IntakeError) as error:
        module.resolved_detail_fields(session, principal, row)
    assert error.value.status == 403
    session.execute.assert_not_called()


def test_worker_scope_is_checked_before_fields(worker):
    session, principal, row, _ = worker
    with pytest.raises(IntakeError) as error:
        module.resolved_detail_fields(session, replace(principal, worker_scope=frozenset()), row)
    assert error.value.status == 404
    session.execute.assert_not_called()


def test_detail_completeness_uses_canonical_values_without_overwriting_candidate(
    worker, monkeypatch
):
    session, principal, row, _ = worker
    row["content_version"] = 2
    monkeypatch.setattr(
        intakes,
        "intake_summary",
        Mock(
            return_value={
                "display_name": "Candidate",
                "complete": False,
                "missing_fields": ["phone"],
                "review_status": "current",
            }
        ),
    )
    monkeypatch.setattr(intakes, "review_projection", Mock(return_value=({}, None)))
    result = intakes.intake_detail(session, row, principal=principal)
    assert result["candidate"] == {"full_name": "Candidate"}
    assert result["resolved"]["full_name"] == "Canonical"
    assert result["summary"] == {
        "display_name": "Canonical",
        "complete": True,
        "missing_fields": [],
        "review_status": "stale",
    }


def test_missing_canonical_row_is_not_candidate_fallback(worker):
    session, principal, row, _ = worker
    session.execute.return_value.mappings.return_value.one_or_none.side_effect = [None]
    with pytest.raises(IntakeError) as error:
        module.resolved_detail_fields(session, principal, row)
    assert error.value.status == 404


@pytest.mark.parametrize("kind", ["household", "business"])
def test_employer_selected_fields_and_separate_address_completeness(monkeypatch, kind):
    records = {
        "employer": {"version": 1, "employer_type": kind, "display_name": "Canonical employer"},
        "employer_contact": {"version": 1, "full_name": "Canonical representative"},
        "employer_contact_details": {
            "version": 1,
            "phone": "202-555-0151",
            "address_complete": kind == "household",
        },
        "worksite": {"version": 1, "address_complete": True},
    }
    if kind == "business":
        records["employer_address"] = {"version": 1, "address_complete": True}
    refs = {name: {"id": str(uuid4()), "version": 1} for name in records}
    monkeypatch.setattr(module, "get_link_dependencies", Mock(return_value=refs))
    session = Mock(spec=Session)
    session.execute.return_value.mappings.return_value.one_or_none.side_effect = [
        records[name] for name in ("employer", *sorted(set(records) - {"employer"}))
    ]
    principal = replace(
        PRINCIPAL,
        permissions=frozenset(
            {
                "employer:read",
                "employer_contact:read",
                "employer_contact:details:read",
                "worksite:read",
            }
        ),
    )
    content, complete, _, stale = module.resolved_detail_fields(
        session,
        principal,
        {
            "intake_id": uuid4(),
            "kind": "employer",
        },
    )
    assert content == {
        "employer_type": kind,
        "display_name": "Canonical employer",
        "representative_name": "Canonical representative",
        "phone": "202-555-0151",
    }
    assert complete == {"party_address": True, "worksite_address": True}
    assert not stale


def test_partial_employer_selection_resolves_only_parent(monkeypatch):
    refs = {"employer": {"id": str(uuid4()), "version": 1}}
    monkeypatch.setattr(module, "get_link_dependencies", Mock(return_value=refs))
    session = Mock(spec=Session)
    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "version": 1,
        "employer_type": "business",
        "display_name": "Canonical",
    }
    principal = replace(PRINCIPAL, permissions=frozenset({"employer:read"}))
    content, complete, _, _ = module.resolved_detail_fields(
        session,
        principal,
        {
            "kind": "employer",
            "intake_id": uuid4(),
            "content": {"phone": "202-555-0199", "role_title": "New request"},
        },
    )
    assert content == {"employer_type": "business", "display_name": "Canonical"}
    assert complete == {}
    assert session.execute.call_count == 1


def test_incomplete_selected_address_cannot_use_complete_candidate(monkeypatch):
    candidate_address = Mock(
        return_value={"line1": "Candidate", "locality": "Town", "country": "CA"}
    )
    monkeypatch.setattr(intakes, "get_address", candidate_address)
    missing = intakes.missing_fields(
        Mock(spec=Session),
        {
            "kind": "worker",
            "intake_id": uuid4(),
            "content": {
                "full_name": "Canonical",
                "phone": "202-555-0151",
                "interests": {"other_description": "Fictional work"},
                "availability": {"mode": "flexible"},
            },
        },
        address_completeness={"worker_residence": False},
    )
    assert missing == ["worker_residence"]
    candidate_address.assert_not_called()


@pytest.mark.parametrize("version", [1, 2])
def test_parent_type_drift_retains_original_business_address_reference(monkeypatch, version):
    refs = {name: {"id": str(uuid4()), "version": 1} for name in ("employer", "employer_address")}
    monkeypatch.setattr(module, "get_link_dependencies", Mock(return_value=refs))
    session = Mock(spec=Session)
    session.execute.return_value.mappings.return_value.one_or_none.side_effect = [
        {"version": version, "employer_type": "household", "display_name": "Current household"},
        {"version": 1, "address_complete": True},
    ]
    principal = replace(PRINCIPAL, permissions=frozenset({"employer:read"}))
    row = {"kind": "employer", "intake_id": uuid4()}
    if version == 1:
        with pytest.raises(IntakeError):
            module.resolved_detail_fields(session, principal, row)
    else:
        content, complete, saved, stale = module.resolved_detail_fields(session, principal, row)
        assert content["employer_type"] == "household"
        assert complete == {} and saved == refs and stale
