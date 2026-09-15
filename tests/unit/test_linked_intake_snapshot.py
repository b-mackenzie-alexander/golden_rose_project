from dataclasses import replace
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest

from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.linked_intake_snapshot import read_linked_snapshot
from tests.unit.test_resolve_intake_links import PRINCIPAL, rows


def worker_data() -> tuple[Any, ...]:
    names = ("worker", "worker_contact", "worker_preferences", "worker_residence")
    refs = {name: {"id": str(uuid4()), "version": 1} for name in names}
    values: dict[str, dict[str, Any]] = {
        "worker": {"full_name": "Canonical Worker"},
        "worker_contact": {"phone": "202-555-0151"},
        "worker_preferences": {
            "interests": {"other_description": "Fictional gardening"},
            "availability": {"mode": "flexible"},
            "self_reported": True,
        },
        "worker_residence": {
            "line1": "10 Fictional Road",
            "line2": None,
            "locality": "City",
            "region": "NY",
            "postal_code": "10001",
            "country": "US",
        },
    }
    data = [{f"{name}_id": refs[name]["id"], "version": 1, **values[name]} for name in names]
    return refs, data


def test_worker_snapshot_separates_address_and_versions_without_mutation():
    refs, data = worker_data()
    session = Mock()
    rows(session, data)
    result = read_linked_snapshot(
        session=session, principal=PRINCIPAL, kind="worker", dependencies=refs
    )
    assert result.content["full_name"] == "Canonical Worker"
    assert result.addresses["worker_residence"]["line1"] == "10 Fictional Road"
    assert "line1" not in result.content
    assert result.current_dependencies == refs
    assert result.dependency_stale is False
    assert refs["worker"]["version"] == 1
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_current_version_mismatch_is_flagged_not_overwritten():
    refs, data = worker_data()
    data[1]["version"] = 2
    session = Mock()
    rows(session, data)
    result = read_linked_snapshot(
        session=session, principal=PRINCIPAL, kind="worker", dependencies=refs
    )
    assert result.dependency_stale
    assert result.current_dependencies["worker_contact"]["version"] == 2
    assert refs["worker_contact"]["version"] == 1


@pytest.mark.parametrize(
    "permission", ["worker:read", "worker_contact:read", "worker_residence:read"]
)
def test_all_worker_snapshot_permissions_precede_sql(permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            kind="worker",
            dependencies=worker_data()[0],
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


def test_worker_scope_checked_before_sql():
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(
            session=session,
            principal=replace(PRINCIPAL, worker_scope=frozenset()),
            kind="worker",
            dependencies=worker_data()[0],
        )
    assert error.value.status == 404
    session.execute.assert_not_called()


@pytest.mark.parametrize("mutation", ["missing_child", "extra", "bad_version"])
def test_dependency_shape_is_exact_before_sql(mutation):
    refs, _ = worker_data()
    if mutation == "missing_child":
        del refs["worker_contact"]
    elif mutation == "extra":
        refs["employer"] = {"id": str(uuid4()), "version": 1}
    else:
        refs["worker"]["version"] = True
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(session=session, principal=PRINCIPAL, kind="worker", dependencies=refs)
    assert error.value.status == 422
    session.execute.assert_not_called()


def test_unlinked_snapshot_is_empty_without_canonical_lookup():
    session = Mock()
    result = read_linked_snapshot(
        session=session, principal=PRINCIPAL, kind="worker", dependencies={}
    )
    assert result.content == result.addresses == result.current_dependencies == {}
    assert not result.dependency_stale
    session.execute.assert_not_called()


def employer_data(kind="business") -> tuple[Any, ...]:
    address = worker_data()[1][-1]
    names = (
        ("employer", "employer_address", "employer_contact", "employer_contact_details", "worksite")
        if kind == "business"
        else ("employer", "employer_contact", "employer_contact_details", "worksite")
    )
    refs = {name: {"id": str(uuid4()), "version": 1} for name in names}
    values: dict[str, dict[str, Any]] = {
        "employer": {"employer_type": kind, "display_name": "Canonical Employer"},
        "employer_address": {**address, "purpose": "business"},
        "employer_contact": {"full_name": "Canonical Representative"},
        "employer_contact_details": {**address, "phone": "202-555-0151"},
        "worksite": address,
    }
    return refs, [{**values[name], f"{name}_id": refs[name]["id"], "version": 1} for name in names]


@pytest.mark.parametrize("kind", ["household", "business"])
def test_employer_snapshot_owns_only_selected_party_facts(kind):
    session = Mock()
    refs, data = employer_data(kind)
    rows(session, data)
    result = read_linked_snapshot(
        session=session, principal=PRINCIPAL, kind="employer", dependencies=refs
    )
    assert result.content == {
        "employer_type": kind,
        "display_name": "Canonical Employer",
        "representative_name": "Canonical Representative",
        "phone": "202-555-0151",
    }
    assert set(result.addresses) == {"party_address", "worksite_address"}
    assert not result.dependency_stale
    statements = [call.args[0] for call in session.execute.call_args_list]
    assert "FOR UPDATE" in str(statements[0])
    from uuid import UUID

    for statement in statements[1:]:
        assert UUID(refs["employer"]["id"]) in statement.compile().params.values()
    details = next(s for s in statements if "employer_contact_details" in str(s))
    assert UUID(refs["employer_contact"]["id"]) in details.compile().params.values()
    assert "Canonical Representative" not in repr(result)
    assert "10 Fictional Road" not in repr(result)


@pytest.mark.parametrize(
    "permission",
    [
        "employer:read",
        "employer_contact:read",
        "employer_contact:details:read",
        "party_address:read",
        "worksite:read",
        "worksite_address:read",
    ],
)
def test_employer_permissions_precede_snapshot_lookup(permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            kind="employer",
            dependencies=employer_data()[0],
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


def test_employer_parent_only_does_not_fill_unselected_fields():
    session = Mock()
    refs, data = employer_data()
    rows(session, data[:1])
    result = read_linked_snapshot(
        session=session,
        principal=replace(PRINCIPAL, permissions=frozenset({"employer:read"})),
        kind="employer",
        dependencies={"employer": refs["employer"]},
    )
    assert result.content == {"employer_type": "business", "display_name": "Canonical Employer"}
    assert result.addresses == {}


def test_incomplete_canonical_value_never_falls_back_to_candidate():
    session = Mock()
    refs, data = worker_data()
    data[1]["phone"] = "invalid-private-value"
    rows(session, data)
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(session=session, principal=PRINCIPAL, kind="worker", dependencies=refs)
    assert error.value.code == "canonical_incomplete"
    assert "private" not in str(error.value)


def test_missing_selected_row_is_safe_and_caller_owns_rollback():
    session = Mock()
    refs, data = worker_data()
    rows(session, [data[0], None])
    with pytest.raises(IntakeError) as error:
        read_linked_snapshot(session=session, principal=PRINCIPAL, kind="worker", dependencies=refs)
    assert error.value.status == 404
    session.rollback.assert_not_called()
