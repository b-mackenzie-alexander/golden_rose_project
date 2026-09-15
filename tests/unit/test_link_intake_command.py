from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import (
    CanonicalLinkReference,
    LinkIntakeRequest,
)
from golden_rose.application import link_intake
from golden_rose.application.intake_errors import IntakeError
from tests.unit.test_resolve_intake_links import PRINCIPAL


@pytest.fixture
def command(monkeypatch) -> tuple[Any, ...]:
    row: dict[str, Any] = {
        "intake_id": uuid4(),
        "kind": "worker",
        "version": 2,
        "content_version": 1,
        "content": {"full_name": "Candidate unchanged"},
        "lifecycle_status": "draft",
    }
    dependencies: dict[str, dict[str, Any]] = {
        name: {"id": str(uuid4()), "version": 1}
        for name in ("worker", "worker_contact", "worker_residence", "worker_preferences")
    }
    mocks = {}
    for name, result in {
        "get_intake": row,
        "begin_command": (b"x" * 32, None),
        "get_link_dependencies": {},
        "resolve_link_dependencies": dependencies,
        "write_link_dependencies": None,
        "write_authority": None,
        "intake_detail": {"summary": {"version": 3}, "content_version": 2},
    }.items():
        mocks[name] = Mock(return_value=result)
        monkeypatch.setattr(link_intake, name, mocks[name])
    arguments: dict[str, Any] = {
        "session": Mock(spec=Session),
        "principal": replace(
            PRINCIPAL, permissions=PRINCIPAL.permissions | {"intake:read", "intake:link"}
        ),
        "command_id": uuid4(),
        "intake_id": row["intake_id"],
        "request": LinkIntakeRequest(
            expected_version=2,
            party=CanonicalLinkReference(id=dependencies["worker"]["id"], version=1),
        ),
        "clock": Mock(),
    }
    arguments["clock"].now.return_value = datetime(2026, 9, 14, tzinfo=UTC)
    return arguments, mocks, row


def test_one_commit_advances_versions_without_candidate_changes(command):
    args, mocks, row = command
    result, replayed = link_intake.execute_link_intake(**args)
    assert not replayed
    assert result["result_record_version"] == result["current"]["summary"]["version"] == 3
    assert result["current"]["content_version"] == 2
    assert row["content"] == {"full_name": "Candidate unchanged"}
    assert mocks["get_intake"].call_args_list[1].kwargs == {"lock": True}
    write = mocks["write_link_dependencies"].call_args.kwargs
    assert write["version"] == 3 and write["content_version"] == 2
    assert "content" not in write
    authority = mocks["write_authority"].call_args.kwargs
    assert authority["command_type"] == "link_intake"
    assert authority["event_type"] == "intake.linked"
    assert authority["changed"] == ["links"]
    args["session"].commit.assert_called_once()


def test_replay_after_later_revision_does_not_resolve_old_expected_version(command):
    args, mocks, row = command
    row.update(version=5, content_version=3, lifecycle_status="finalized")
    mocks["intake_detail"].return_value = {"summary": {"version": 5}, "content_version": 3}
    mocks["begin_command"].return_value = (
        b"x" * 32,
        {
            "result_entity_type": "intake",
            "result_entity_id": row["intake_id"],
            "result_record_version": 3,
            "result_event_type": "intake.linked",
        },
    )
    result, replayed = link_intake.execute_link_intake(**args)
    assert replayed and result["result_record_version"] == 3
    assert result["current"]["summary"]["version"] == 5
    mocks["resolve_link_dependencies"].assert_not_called()
    mocks["write_link_dependencies"].assert_not_called()
    args["session"].commit.assert_not_called()
    args["session"].rollback.assert_called_once()


@pytest.mark.parametrize(
    "permission",
    ["intake:link", "intake:read", "worker:read", "worker_contact:read", "worker_residence:read"],
)
def test_current_permissions_deny_before_receipt_resolution(command, permission):
    args, mocks, _ = command
    args["principal"] = replace(
        args["principal"], permissions=args["principal"].permissions - {permission}
    )
    with pytest.raises(IntakeError) as error:
        link_intake.execute_link_intake(**args)
    assert error.value.status == 403
    mocks["begin_command"].assert_not_called()


@pytest.mark.parametrize(
    "state,code",
    [("stale", "version_conflict"), ("finalized", "already_finalized"), ("unchanged", "no_change")],
)
def test_fresh_invalid_changes_do_not_write(command, state, code):
    args, mocks, row = command
    if state == "stale":
        row["version"] = 3
    elif state == "finalized":
        row["lifecycle_status"] = "finalized"
    else:
        mocks["get_link_dependencies"].return_value = mocks[
            "resolve_link_dependencies"
        ].return_value
    with pytest.raises(IntakeError) as error:
        link_intake.execute_link_intake(**args)
    assert error.value.code == code
    mocks["write_link_dependencies"].assert_not_called()
    args["session"].rollback.assert_called_once()


@pytest.mark.parametrize(
    "failure", ["write_link_dependencies", "write_authority", "intake_detail", "commit"]
)
def test_late_failure_rolls_back_unknown_outcome(command, failure):
    args, mocks, _ = command
    target = args["session"].commit if failure == "commit" else mocks[failure]
    target.side_effect = OperationalError("private", {}, Exception("private"))
    with pytest.raises(IntakeError) as error:
        link_intake.execute_link_intake(**args)
    assert error.value.status == 503 and "private" not in str(error.value)
    args["session"].rollback.assert_called_once()


def test_unlink_advances_versions_and_clears_references(command):
    args, mocks, _ = command
    args["request"] = LinkIntakeRequest(expected_version=2, party=None)
    mocks["get_link_dependencies"].return_value = mocks["resolve_link_dependencies"].return_value
    mocks["resolve_link_dependencies"].return_value = {}
    result, replayed = link_intake.execute_link_intake(**args)
    assert not replayed and result["current"]["content_version"] == 2
    assert mocks["write_link_dependencies"].call_args.kwargs["dependencies"] == {}


@pytest.mark.parametrize("replayed", [False, True])
def test_current_projection_permission_failure_never_commits(command, replayed):
    args, mocks, row = command
    if replayed:
        mocks["begin_command"].return_value = (
            b"x" * 32,
            {
                "result_entity_type": "intake",
                "result_entity_id": row["intake_id"],
                "result_record_version": 2,
                "result_event_type": "intake.linked",
            },
        )
    mocks["intake_detail"].side_effect = IntakeError("forbidden", 403)
    with pytest.raises(IntakeError) as error:
        link_intake.execute_link_intake(**args)
    assert error.value.status == 403
    args["session"].commit.assert_not_called()
    args["session"].rollback.assert_called_once()
    assert mocks["intake_detail"].call_args.kwargs["principal"] == args["principal"]


@pytest.mark.parametrize("field", ["version", "content_version"])
def test_version_exhaustion_fails_before_writes(command, field):
    args, mocks, row = command
    row[field] = 2147483647
    if field == "version":
        args["request"] = args["request"].model_copy(update={"expected_version": row[field]})
    with pytest.raises(IntakeError):
        link_intake.execute_link_intake(**args)
    mocks["write_link_dependencies"].assert_not_called()


def test_out_of_scope_party_fails_before_receipt_lookup(command):
    args, mocks, _ = command
    args["principal"] = replace(args["principal"], worker_scope=frozenset())
    with pytest.raises(IntakeError) as error:
        link_intake.execute_link_intake(**args)
    assert error.value.status == 404
    mocks["begin_command"].assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("result_entity_type", "worker"),
        ("result_entity_id", uuid4()),
        ("result_event_type", "intake.created"),
        ("result_record_version", 1),
        ("result_record_version", 99),
    ],
)
def test_inconsistent_replay_fails_closed(command, field, value):
    args, mocks, row = command
    receipt = {
        "result_entity_type": "intake",
        "result_entity_id": row["intake_id"],
        "result_record_version": 2,
        "result_event_type": "intake.linked",
    }
    receipt[field] = value
    mocks["begin_command"].return_value = (b"x" * 32, receipt)
    with pytest.raises(IntakeError) as error:
        link_intake.execute_link_intake(**args)
    assert error.value.status == 503
    mocks["write_link_dependencies"].assert_not_called()
