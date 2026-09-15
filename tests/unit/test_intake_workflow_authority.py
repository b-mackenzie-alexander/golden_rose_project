"""Statement-level transaction ownership; database authority has separate tests."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from golden_rose.application import intake_workflow_common
from golden_rose.auth.principal import StaffPrincipal


@pytest.fixture
def authority() -> dict[str, Any]:
    return {
        "principal": StaffPrincipal(uuid4(), "test", frozenset()),
        "command_id": uuid4(),
        "command_type": "review_intake",
        "entity_type": "intake",
        "entity_id": uuid4(),
        "previous_version": 2,
        "event_type": "intake.reviewed",
        "event_id": uuid4(),
        "now": datetime(2026, 9, 14, tzinfo=UTC),
        "changed": ["review"],
    }


def statements(session) -> list[Any]:
    return [
        (call.args[0].table.name, call.args[0].compile().params)
        for call in session.execute.call_args_list
    ]


@pytest.mark.parametrize(
    "command_type,entity_type,event_type,previous_version",
    [
        ("review_intake", "intake", "intake.reviewed", 2),
        ("follow_up_intake", "intake", "intake.follow_up_recorded", 3),
        ("create_work_interest", "work_interest", "work_interest.created", 0),
        ("revise_work_interest", "work_interest", "work_interest.revised", 1),
    ],
)
def test_existing_writer_keeps_one_exact_receipt_result_and_event(
    authority, command_type, entity_type, event_type, previous_version
):
    session = Mock(spec=Session)
    authority.update(
        command_type=command_type,
        entity_type=entity_type,
        event_type=event_type,
        previous_version=previous_version,
    )
    fingerprint = b"a" * 32
    intake_workflow_common.write_authority(session, fingerprint=fingerprint, **authority)
    emitted = statements(session)
    assert [table for table, _ in emitted] == [
        "command_receipts",
        "command_results",
        "audit_events",
    ]
    receipt, result, event = [values for _, values in emitted]
    expected_version = previous_version + 1
    assert receipt == {
        "command_id": authority["command_id"],
        "command_schema_version": 1,
        "command_type": command_type,
        "actor_id": authority["principal"].actor_id,
        "request_fingerprint": fingerprint,
        "result_entity_type": entity_type,
        "result_entity_id": authority["entity_id"],
        "result_record_version": expected_version,
        "result_event_type": event_type,
        "created_at": authority["now"],
    }
    assert result == {
        "command_id": receipt["command_id"],
        "entity_type": entity_type,
        "entity_id": receipt["result_entity_id"],
        "result_version": expected_version,
        "event_type": event_type,
        "actor_id": receipt["actor_id"],
        "command_type": command_type,
    }
    assert event["command_id"] == event["correlation_id"] == receipt["command_id"]
    assert event["actor_id"] == receipt["actor_id"]
    assert event["entity_id"] == receipt["result_entity_id"]
    assert event["event_type"] == event["event_schema_name"] == event_type
    assert event["new_record_version"] == event["entity_sequence"] == expected_version
    assert event["prior_record_version"] == previous_version
    assert event["audit_event_id"] == authority["event_id"]
    assert event["occurred_at"] == authority["now"]
    assert event["changed_fields"] == {"field_names": ["review"], "approved_values": {}}
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_child_results_share_one_command_without_additional_receipts(authority):
    session = Mock(spec=Session)
    authority.update(command_type="finalize_intake", event_type="intake.finalized")
    intake_workflow_common.write_authority(session, fingerprint=b"a" * 32, **authority)
    created = {}
    for entity_type in ("worker", "worker_contact", "worker_residence", "worker_preferences"):
        created[entity_type] = uuid4()
        intake_workflow_common.write_result_authority(
            session,
            **{
                **authority,
                "entity_type": entity_type,
                "entity_id": created[entity_type],
                "previous_version": 0,
                "event_type": f"{entity_type}.created",
                "event_id": uuid4(),
                "changed": ["created"],
            },
        )
    emitted = statements(session)
    assert sum(table == "command_receipts" for table, _ in emitted) == 1
    results = [values for table, values in emitted if table == "command_results"]
    events = [values for table, values in emitted if table == "audit_events"]
    assert len(results) == len(events) == 5
    assert len({event["audit_event_id"] for event in events}) == 5
    for result, event in zip(results[1:], events[1:], strict=True):
        assert result["command_id"] == event["command_id"] == authority["command_id"]
        assert result["actor_id"] == event["actor_id"] == authority["principal"].actor_id
        assert result["entity_id"] == event["entity_id"] == created[result["entity_type"]]
        assert result["result_version"] == event["new_record_version"] == 1
        assert event["prior_record_version"] == 0
        assert event["changed_fields"] == {"field_names": ["created"], "approved_values": {}}
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_child_event_failure_propagates_to_the_outer_transaction(authority):
    session = Mock(spec=Session)
    failure = OperationalError("fictional failure", {}, RuntimeError("unavailable"))
    session.execute.side_effect = [None, failure]
    with pytest.raises(OperationalError) as caught:
        intake_workflow_common.write_result_authority(session, **authority)
    assert caught.value is failure
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
