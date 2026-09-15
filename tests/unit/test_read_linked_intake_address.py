from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from golden_rose.application import read_linked_intake_address as reader
from golden_rose.application.intake_errors import IntakeError
from tests.unit.test_resolve_intake_links import PRINCIPAL


@pytest.fixture
def setup(monkeypatch):
    refs = {
        name: {"id": str(uuid4()), "version": 1}
        for name in (
            "worker",
            "worker_residence",
            "employer",
            "employer_contact",
            "employer_contact_details",
            "employer_address",
            "worksite",
        )
    }
    getter = Mock(return_value=refs)
    monkeypatch.setattr(reader, "get_link_dependencies", getter)
    session = Mock(spec=Session)
    session.scalar.return_value = "household"
    session.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "version": 2,
        "line1": "Canonical street",
        "line2": None,
        "locality": "Fictional City",
        "region": None,
        "postal_code": None,
        "country": "CA",
    }
    args = {
        "session": session,
        "principal": replace(
            PRINCIPAL,
            permissions=PRINCIPAL.permissions
            | {
                "intake:read",
                "worker_residence:read",
                "party_address:read",
                "worksite_address:read",
                "employer_contact:read",
                "employer_contact:details:read",
                "worksite:read",
                "employer:read",
                "worker:read",
            },
        ),
        "row": {"intake_id": uuid4(), "kind": "worker", "_has_link_row": True},
        "section": "worker_residence",
    }
    return args, getter, refs


@pytest.mark.parametrize(
    "kind,section,source",
    [
        ("worker", "worker_residence", "worker_residence"),
        ("household", "party_address", "employer_contact_details"),
        ("business", "party_address", "employer_address"),
        ("business", "worksite_address", "worksite"),
    ],
)
def test_reads_only_selected_section_and_current_source_version(setup, kind, section, source):
    args, _, refs = setup
    args["row"]["kind"] = "worker" if kind == "worker" else "employer"
    args["section"] = section
    args["session"].scalar.return_value = kind
    result = reader.read_linked_intake_address(**args)
    assert result["resolved"]["line1"] == "Canonical street"
    assert result["source_ref"] == {"id": refs[source]["id"], "version": 2}
    statement = args["session"].execute.call_args.args[0]
    assert {c.name for c in statement.selected_columns} == {"version", *reader.ADDRESS_FIELDS}
    assert f"{args['row']['kind']}_id =" in str(statement)
    if source == "employer_contact_details":
        assert "employer_contact_id =" in str(statement)
    assert "FOR UPDATE" not in str(statement)
    args["session"].commit.assert_not_called()


def test_unlinked_predecessor_does_not_query_link_columns(setup):
    args, getter, _ = setup
    args["row"]["_has_link_row"] = False
    assert reader.read_linked_intake_address(**args) == {"resolved": None}
    getter.assert_not_called()
    args["session"].execute.assert_not_called()


@pytest.mark.parametrize("permission", ["intake:read", "worker_residence:read", "worker:read"])
def test_missing_permissions_do_not_read_address(setup, permission):
    args, _, _ = setup
    args["principal"] = replace(
        args["principal"], permissions=args["principal"].permissions - {permission}
    )
    with pytest.raises(IntakeError) as error:
        reader.read_linked_intake_address(**args)
    assert error.value.status == 403
    args["session"].execute.assert_not_called()


def test_worker_scope_does_not_read_address(setup):
    args, _, _ = setup
    args["principal"] = replace(args["principal"], worker_scope=frozenset())
    with pytest.raises(IntakeError) as error:
        reader.read_linked_intake_address(**args)
    assert error.value.status == 404
    args["session"].execute.assert_not_called()


def test_selected_missing_record_is_not_empty_resolved_address(setup):
    args, _, _ = setup
    args["session"].execute.return_value.mappings.return_value.one_or_none.return_value = None
    with pytest.raises(IntakeError) as error:
        reader.read_linked_intake_address(**args)
    assert error.value.status == 404


@pytest.mark.parametrize(
    "section,permission",
    [
        ("party_address", "employer:read"),
        ("party_address", "party_address:read"),
        ("party_address", "employer_contact:read"),
        ("party_address", "employer_contact:details:read"),
        ("worksite_address", "worksite:read"),
        ("worksite_address", "worksite_address:read"),
    ],
)
def test_employer_field_denial_never_reads_address(setup, section, permission):
    args, _, _ = setup
    args["row"]["kind"] = "employer"
    args["section"] = section
    args["principal"] = replace(
        args["principal"], permissions=args["principal"].permissions - {permission}
    )
    with pytest.raises(IntakeError) as error:
        reader.read_linked_intake_address(**args)
    assert error.value.status == 403
    args["session"].execute.assert_not_called()
