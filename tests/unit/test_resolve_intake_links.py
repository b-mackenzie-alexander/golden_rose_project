from dataclasses import replace
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest

from golden_rose.api.staff.intake_finalization_schemas import (
    CanonicalLinkReference,
    LinkIntakeRequest,
)
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.resolve_intake_links import resolve_link_dependencies
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(
    uuid4(),
    "synthetic_staff",
    frozenset(
        {
            "worker:read",
            "worker_contact:read",
            "worker_residence:read",
            "employer:read",
            "employer_contact:read",
            "employer_contact:details:read",
            "party_address:read",
            "worksite:read",
            "worksite_address:read",
        }
    ),
)


def request(**kwargs) -> LinkIntakeRequest:
    return LinkIntakeRequest(
        expected_version=1, party=CanonicalLinkReference(id=uuid4(), version=1), **kwargs
    )


def rows(session, values) -> None:
    results = []
    for value in values:
        result = Mock()
        result.mappings.return_value.one_or_none.return_value = value
        results.append(result)
    session.execute.side_effect = results


@pytest.mark.parametrize("kind", ["worker", "employer"])
def test_unlink_has_no_canonical_lookup(kind):
    session = Mock()
    assert (
        resolve_link_dependencies(
            session=session,
            principal=PRINCIPAL,
            kind=kind,
            request=LinkIntakeRequest(expected_version=1, party=None),
        )
        == {}
    )
    session.execute.assert_not_called()


@pytest.mark.parametrize(
    "permission", ["worker:read", "worker_contact:read", "worker_residence:read"]
)
def test_worker_authorization_precedes_lookup(permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            kind="worker",
            request=request(),
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


def test_worker_scope_is_not_intake_scope():
    session = Mock()
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session,
            principal=replace(PRINCIPAL, worker_scope=frozenset()),
            kind="worker",
            request=request(),
        )
    assert error.value.status == 404
    session.execute.assert_not_called()


def test_worker_resolves_exact_children_without_values_or_writes():
    session = Mock()
    command = request()
    assert command.party is not None
    data = [{"worker_id": command.party.id, "version": 1}]
    for name in ("worker_contact", "worker_residence", "worker_preferences"):
        data.append({f"{name}_id": uuid4(), "version": 1})
    rows(session, data)
    result = resolve_link_dependencies(
        session=session, principal=PRINCIPAL, kind="worker", request=command
    )
    assert result == {
        name: {"id": str(row[f"{name}_id"]), "version": 1}
        for name, row in zip(
            ("worker", "worker_contact", "worker_residence", "worker_preferences"),
            data,
            strict=True,
        )
    }
    for call in session.execute.call_args_list:
        assert set(call.args[0].selected_columns.keys()) <= {
            "worker_id",
            "worker_contact_id",
            "worker_residence_id",
            "worker_preferences_id",
            "version",
        }
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


@pytest.mark.parametrize(
    "state,code", [(None, "not_found"), ({"version": 2}, "dependency_changed")]
)
def test_party_missing_or_changed(state, code):
    session = Mock()
    rows(session, [state])
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session, principal=PRINCIPAL, kind="worker", request=request()
        )
    assert error.value.code == code


def test_worker_missing_child_is_canonical_incomplete():
    session = Mock()
    command = request()
    assert command.party is not None
    rows(session, [{"worker_id": command.party.id, "version": 1}, None])
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session, principal=PRINCIPAL, kind="worker", request=command
        )
    assert error.value.code == "canonical_incomplete"


def test_worker_rejects_employer_sublinks():
    session = Mock()
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session,
            principal=PRINCIPAL,
            kind="worker",
            request=request(worksite=CanonicalLinkReference(id=uuid4(), version=1)),
        )
    assert error.value.status == 422
    session.execute.assert_not_called()


def employer_request() -> LinkIntakeRequest:
    return request(
        **{
            name: CanonicalLinkReference(id=uuid4(), version=1)
            for name in ("contact", "worksite", "business_address")
        }
    )


def employer_rows(command) -> list[Any]:
    return [
        {"employer_id": command.party.id, "version": 1, "employer_type": "business"},
        {"employer_contact_id": command.contact.id, "version": 1},
        {"employer_contact_details_id": uuid4(), "version": 1},
        {"worksite_id": command.worksite.id, "version": 1},
        {"employer_address_id": command.business_address.id, "version": 1},
    ]


def test_employer_locks_parent_and_resolves_same_parent_children():
    session, command = Mock(), employer_request()
    data = employer_rows(command)
    rows(session, data)
    result = resolve_link_dependencies(
        session=session, principal=PRINCIPAL, kind="employer", request=command
    )
    assert set(result) == {
        "employer",
        "employer_contact",
        "employer_contact_details",
        "worksite",
        "employer_address",
    }
    assert result["employer_contact_details"]["id"] == str(data[2]["employer_contact_details_id"])
    statements = [call.args[0] for call in session.execute.call_args_list]
    assert "FOR UPDATE" in str(statements[0])
    assert command.party is not None and command.contact is not None
    for statement in statements[1:]:
        assert command.party.id in statement.compile().params.values()
        assert "FOR UPDATE" not in str(statement)
    assert command.contact.id in statements[2].compile().params.values()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


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
def test_employer_selected_permissions_precede_lookup(permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            kind="employer",
            request=employer_request(),
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


@pytest.mark.parametrize(
    "index,code",
    [(1, "not_found"), (2, "canonical_incomplete"), (3, "not_found"), (4, "not_found")],
)
def test_employer_missing_selected_rows(index, code):
    session, command = Mock(), employer_request()
    data = employer_rows(command)
    data[index] = None
    rows(session, data)
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session, principal=PRINCIPAL, kind="employer", request=command
        )
    assert error.value.code == code


@pytest.mark.parametrize("index", [1, 3, 4])
def test_employer_changed_selected_version(index):
    session, command = Mock(), employer_request()
    data = employer_rows(command)
    data[index]["version"] = 2
    rows(session, data)
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session, principal=PRINCIPAL, kind="employer", request=command
        )
    assert error.value.code == "dependency_changed"


def test_household_cannot_select_business_address():
    session, command = Mock(), employer_request()
    data = employer_rows(command)
    data[0]["employer_type"] = "household"
    rows(session, data)
    with pytest.raises(IntakeError) as error:
        resolve_link_dependencies(
            session=session, principal=PRINCIPAL, kind="employer", request=command
        )
    assert error.value.status == 422
    assert session.execute.call_count == 1


def test_employer_parent_only_does_not_require_unselected_section_permissions():
    session, command = Mock(), request()
    assert command.party is not None
    rows(session, [{"employer_id": command.party.id, "version": 1, "employer_type": "household"}])
    result = resolve_link_dependencies(
        session=session,
        principal=replace(PRINCIPAL, permissions=frozenset({"employer:read"})),
        kind="employer",
        request=command,
    )
    assert result == {"employer": {"id": str(command.party.id), "version": 1}}


def test_storage_error_and_transaction_ownership_remain_with_caller():
    from sqlalchemy.exc import OperationalError

    session = Mock()
    session.execute.side_effect = OperationalError("private", {}, Exception("private"))
    with pytest.raises(OperationalError):
        resolve_link_dependencies(
            session=session, principal=PRINCIPAL, kind="worker", request=request()
        )
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
