from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_review_schemas import ReviewIntakeRequest
from golden_rose.application import intake_review_snapshot as snapshots
from golden_rose.application import review_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.linked_intake_snapshot import LinkedSnapshot
from tests.unit.test_resolve_intake_links import PRINCIPAL


@pytest.fixture
def snapshot_case(monkeypatch) -> tuple[Any, ...]:
    row = {
        "intake_id": uuid4(),
        "kind": "employer",
        "version": 2,
        "content_version": 2,
        "lifecycle_status": "draft",
        "_has_link_row": True,
        "content": {
            "employer_type": "household",
            "display_name": "Candidate",
            "representative_name": "Candidate contact",
            "phone": "Candidate phone",
            "role_title": "New request",
            "worker_count": 2,
        },
    }
    canonical = LinkedSnapshot(
        {"employer_type": "business", "display_name": "Canonical"},
        {},
        {},
        False,
    )
    read = Mock(return_value=canonical)
    address = Mock(return_value={"line1": "Candidate address"})
    monkeypatch.setattr(snapshots, "read_linked_snapshot", read)
    monkeypatch.setattr(snapshots, "get_address", address)
    return row, read, address


def test_linked_employer_preserves_only_unselected_candidate_fields(snapshot_case):
    row, _, address = snapshot_case
    original = deepcopy(row)
    result = snapshots.build_review_snapshot(Mock(), PRINCIPAL, row, {"employer": {}})
    assert result["content"] == {
        **row["content"],
        "employer_type": "business",
        "display_name": "Canonical",
    }
    assert row == original
    assert address.call_count == 2


def test_worker_never_fills_canonical_gaps_from_candidate(snapshot_case):
    row, read, address = snapshot_case
    row["kind"] = "worker"
    row["content"] = {"full_name": "Candidate", "phone": "Candidate phone"}
    read.return_value = LinkedSnapshot({"full_name": "Canonical"}, {}, {}, False)
    result = snapshots.build_review_snapshot(Mock(), PRINCIPAL, row, {"worker": {}})
    assert result == {"kind": "worker", "content": {"full_name": "Canonical"}, "addresses": {}}
    address.assert_not_called()


@pytest.mark.parametrize("kind", ["household", "business"])
def test_selected_contact_and_addresses_never_fall_back(snapshot_case, kind):
    row, read, address = snapshot_case
    read.return_value = LinkedSnapshot(
        {"employer_type": kind, "display_name": "Canonical"}, {}, {}, False
    )
    refs: dict[str, Any] = {name: {} for name in ("employer", "employer_contact", "worksite")}
    if kind == "business":
        refs["employer_address"] = {}
    result = snapshots.build_review_snapshot(Mock(), PRINCIPAL, row, refs)
    assert "phone" not in result["content"] and "representative_name" not in result["content"]
    assert result["addresses"] == {}
    assert result["content"]["role_title"] == "New request"
    address.assert_not_called()


def test_stale_dependencies_stop_before_candidate_address_reads(snapshot_case):
    row, read, address = snapshot_case
    read.return_value = LinkedSnapshot({}, {}, {}, True)
    with pytest.raises(IntakeError) as error:
        snapshots.build_review_snapshot(Mock(), PRINCIPAL, row, {"employer": {}})
    assert error.value.code == "dependency_changed"
    address.assert_not_called()


def test_predecessor_without_link_row_never_selects_successor_columns(monkeypatch):
    getter = Mock()
    monkeypatch.setattr(snapshots, "get_link_dependencies", getter)
    assert snapshots.review_dependencies(Mock(), PRINCIPAL, {"_has_link_row": False}) == {}
    getter.assert_not_called()


def test_linked_permissions_checked_without_canonical_reads(monkeypatch, snapshot_case):
    row, read, _ = snapshot_case
    monkeypatch.setattr(
        snapshots,
        "get_link_dependencies",
        Mock(
            return_value={
                "employer": {"id": str(uuid4()), "version": 1},
                "worksite": {"id": str(uuid4()), "version": 1},
            }
        ),
    )
    principal = replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {"worksite_address:read"})
    with pytest.raises(IntakeError) as error:
        snapshots.review_dependencies(Mock(), principal, row)
    assert error.value.status == 403
    read.assert_not_called()


@pytest.fixture
def review_case(monkeypatch, snapshot_case) -> tuple[Any, ...]:
    row, _, _ = snapshot_case
    principal = replace(
        PRINCIPAL,
        permissions=PRINCIPAL.permissions
        | {
            "intake:read",
            "intake:review",
            "party_address:read",
            "worksite_address:read",
        },
    )
    snapshot = {"kind": "employer", "content": {"display_name": "Canonical"}, "addresses": {}}
    refs = {"employer": {"id": str(uuid4()), "version": 1}}
    mocks = {}
    for name, value in {
        "get_intake": row,
        "begin_command": (b"x" * 32, None),
        "review_dependencies": refs,
        "build_review_snapshot": snapshot,
        "missing_fields": [],
        "selected_interests": True,
        "write_authority": None,
        "intake_detail": {},
    }.items():
        mocks[name] = Mock(return_value=value)
        monkeypatch.setattr(review_intake, name, mocks[name])
    clock = Mock()
    clock.now.return_value = datetime(2026, 9, 14, tzinfo=UTC)
    directory = Mock()
    directory.resolve.return_value.display_name = "Fictional reviewer"
    args = {
        "session": Mock(spec=Session),
        "principal": principal,
        "command_id": uuid4(),
        "request": ReviewIntakeRequest(expected_version=2, outcome="intake_reviewed"),
        "clock": clock,
        "directory": directory,
        "intake_id": row["intake_id"],
    }
    return args, mocks, snapshot, refs


def test_review_checks_and_persists_effective_snapshot_and_exact_dependencies(review_case):
    args, mocks, snapshot, refs = review_case
    review_intake.execute_review(**args)
    assert mocks["missing_fields"].call_args.args[1]["content"] == snapshot["content"]
    assert mocks["missing_fields"].call_args.kwargs["addresses"] == snapshot["addresses"]
    assert mocks["selected_interests"].call_args.args[1] == snapshot["content"]
    payload = next(
        call.args[0].compile().params
        for call in args["session"].execute.call_args_list
        if call.args[0].table.name == "intake_review_payloads"
    )
    assert payload["reviewed_content"] == snapshot
    assert payload["dependency_refs"] == refs
    args["session"].commit.assert_called_once()


def test_replay_reauthorizes_but_does_not_build_a_new_snapshot(review_case):
    args, mocks, _, _ = review_case
    mocks["begin_command"].return_value = (b"x" * 32, {"result_record_version": 2})
    _, replayed = review_intake.execute_review(**args)
    assert replayed and mocks["review_dependencies"].call_count == 2
    mocks["build_review_snapshot"].assert_not_called()
    args["session"].execute.assert_not_called()
    args["session"].rollback.assert_called_once()


def test_stale_link_stops_review_without_writes(review_case):
    args, mocks, _, _ = review_case
    mocks["build_review_snapshot"].side_effect = IntakeError("dependency_changed")
    with pytest.raises(IntakeError):
        review_intake.execute_review(**args)
    args["session"].execute.assert_not_called()
    args["session"].rollback.assert_called_once()
