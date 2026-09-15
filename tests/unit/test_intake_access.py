import json
import subprocess
import sys
from uuid import uuid4

from golden_rose.application.intake_access import (
    record_contact_address_access,
    record_employer_output_access,
    record_worker_access,
)


def test_employer_output_sink_emits_only_attribution(capsys):
    actor_id, employer_id, output_id = uuid4(), uuid4(), uuid4()
    record_employer_output_access(
        actor_id=actor_id, employer_id=employer_id, output_id=output_id, section="worksite_address"
    )
    captured = capsys.readouterr()
    event = json.loads(captured.err)
    assert event["event"] == "restricted_employer_output_address_read"
    assert event["staff_actor_id"] == str(actor_id)
    assert event["employer_id"] == str(employer_id)
    assert event["output_id"] == str(output_id)
    assert event["section"] == "worksite_address"
    assert set(event) == {
        "event",
        "staff_actor_id",
        "employer_id",
        "output_id",
        "section",
        "occurred_at",
    }
    assert captured.out == ""


def test_contact_address_sink_emits_only_attribution(capsys):
    actor_id, employer_id, contact_id = uuid4(), uuid4(), uuid4()
    record_contact_address_access(actor_id=actor_id, employer_id=employer_id, contact_id=contact_id)
    captured = capsys.readouterr()
    event = json.loads(captured.err)
    assert event["event"] == "restricted_contact_address_read"
    assert event["staff_actor_id"] == str(actor_id)
    assert event["employer_id"] == str(employer_id)
    assert event["contact_id"] == str(contact_id)
    assert set(event) == {"event", "staff_actor_id", "employer_id", "contact_id", "occurred_at"}
    assert captured.out == ""


def test_default_restricted_sink_emits_attribution_without_values():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
from uuid import UUID
from uvicorn import Config
from golden_rose.application.intake_access import record_intake_access
Config('unused:app')
record_intake_access(actor_id=UUID('22222222-2222-4222-8222-222222222222'),
    intake_id=UUID('33333333-3333-4333-8333-333333333333'), section='worker_residence')
""",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    event = json.loads(result.stderr)
    assert event["event"] == "restricted_intake_address_read"
    assert event["staff_actor_id"] == "22222222-2222-4222-8222-222222222222"
    assert event["intake_id"] == "33333333-3333-4333-8333-333333333333"
    assert event["section"] == "worker_residence"
    assert set(event) == {"event", "staff_actor_id", "intake_id", "section", "occurred_at"}
    assert result.stdout == ""


def test_worker_residence_sink_emits_only_attribution(capsys):
    actor_id, worker_id = uuid4(), uuid4()
    record_worker_access(actor_id=actor_id, worker_id=worker_id)
    captured = capsys.readouterr()
    event = json.loads(captured.err)
    assert event["event"] == "restricted_worker_residence_read"
    assert event["staff_actor_id"] == str(actor_id)
    assert event["worker_id"] == str(worker_id)
    assert set(event) == {"event", "staff_actor_id", "worker_id", "occurred_at"}
    assert captured.out == ""
