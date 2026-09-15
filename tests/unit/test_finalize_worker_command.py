"""Orchestrator boundaries; real commit/rollback acceptance remains in integration tests."""

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import FinalizeIntakeRequest
from golden_rose.application import finalize_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal


@pytest.fixture
def command(monkeypatch) -> tuple[Any, ...]:
    row = {
        "intake_id": uuid4(),
        "kind": "worker",
        "content": {},
        "version": 2,
        "content_version": 1,
        "lifecycle_status": "draft",
    }
    principal = StaffPrincipal(
        uuid4(),
        "test",
        frozenset(
            {
                "intake:read",
                "intake:finalize",
                "worker_residence:read",
                "worker_residence:write",
            }
        ),
    )
    identities = {
        kind: uuid4()
        for kind in (
            "worker",
            "worker_contact",
            "worker_residence",
            "worker_preferences",
        )
    }
    mocks = {}
    results: dict[str, Any] = {
        "get_intake": row,
        "begin_command": (b"x" * 32, None),
        "require_finalization_review": None,
        "selected_interests": False,
        "missing_fields": [],
        "get_address": {"line1": "Fictional"},
        "insert_worker_group": identities,
        "write_authority": None,
        "write_result_authority": None,
        "intake_detail": {"summary": {"version": 3}},
    }
    for name, result in results.items():
        mocks[name] = Mock(return_value=result)
        monkeypatch.setattr(finalize_intake, name, mocks[name])
    clock = Mock()
    clock.now.return_value = datetime(2026, 9, 14, tzinfo=UTC)
    arguments = {
        "session": Mock(spec=Session),
        "principal": principal,
        "command_id": uuid4(),
        "intake_id": row["intake_id"],
        "request": FinalizeIntakeRequest(expected_version=2, review_id=uuid4()),
        "clock": clock,
    }
    return arguments, mocks


def test_new_group_uses_one_outer_commit_and_four_created_child_events(command):
    arguments, mocks = command
    result, replayed = finalize_intake.execute_new_intake_finalization(**arguments)
    assert not replayed and result["result_record_version"] == 3
    arguments["session"].commit.assert_called_once_with()
    arguments["session"].rollback.assert_not_called()
    mocks["write_authority"].assert_called_once()
    assert mocks["write_result_authority"].call_count == 4
    for call in mocks["write_result_authority"].call_args_list:
        assert call.kwargs["command_id"] == arguments["command_id"]
        assert call.kwargs["principal"] is arguments["principal"]
        assert call.kwargs["previous_version"] == 0
    assert mocks["get_intake"].call_args.kwargs == {"lock": True}
    mocks["require_finalization_review"].assert_called_once()


@pytest.mark.parametrize("failure_at", ["execute", "commit"])
def test_storage_failure_is_unknown_and_rolls_back_outer_transaction(command, failure_at):
    arguments, _ = command
    getattr(arguments["session"], failure_at).side_effect = OperationalError(
        "Fictional failure", {}, RuntimeError("unavailable")
    )
    with pytest.raises(IntakeError) as caught:
        finalize_intake.execute_new_intake_finalization(**arguments)
    assert caught.value.status == 503 and str(caught.value) == "persistence_unavailable"
    arguments["session"].rollback.assert_called_once_with()


def test_incomplete_reviewed_content_cannot_create_outputs(command):
    arguments, mocks = command
    mocks["missing_fields"].return_value = ["phone"]
    with pytest.raises(IntakeError) as caught:
        finalize_intake.execute_new_intake_finalization(**arguments)
    assert caught.value.status == 422 and caught.value.missing_fields == ["phone"]
    mocks["insert_worker_group"].assert_not_called()
    arguments["session"].commit.assert_not_called()


def test_write_revocation_denies_before_lookup_or_receipt(command):
    arguments, mocks = command
    arguments["principal"] = replace(arguments["principal"], permissions=frozenset())
    with pytest.raises(IntakeError) as caught:
        finalize_intake.execute_new_intake_finalization(**arguments)
    assert caught.value.status == 403
    mocks["get_intake"].assert_not_called()
    mocks["begin_command"].assert_not_called()


@pytest.mark.parametrize("kind,count", [("household", 5), ("business", 6)])
def test_new_employer_uses_one_outer_commit_and_exact_outputs(command, monkeypatch, kind, count):
    arguments, mocks = command
    row = mocks["get_intake"].return_value
    row.update(kind="employer", content={"employer_type": kind})
    principal = arguments["principal"]
    arguments["principal"] = replace(
        principal,
        permissions=principal.permissions
        | {
            "party_address:read",
            "party_address:write",
            "worksite_address:read",
            "worksite_address:write",
        },
    )
    kinds = [
        "employer",
        "employer_contact",
        "employer_contact_details",
        "worksite",
        "staffing_request",
    ]
    if kind == "business":
        kinds.append("employer_address")
    insert = Mock(return_value={entity: uuid4() for entity in kinds})
    monkeypatch.setattr(finalize_intake, "insert_new_employer_group", insert)
    result, replayed = finalize_intake.execute_new_intake_finalization(**arguments)
    assert not replayed
    assert result["finalization"]["kind"] == "employer"
    assert (result["finalization"]["business_address"] is not None) == (kind == "business")
    assert mocks["write_result_authority"].call_count == count
    mocks["insert_worker_group"].assert_not_called()
    mocks["selected_interests"].assert_not_called()
    arguments["session"].commit.assert_called_once()
