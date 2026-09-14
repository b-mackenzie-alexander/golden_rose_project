import json
import subprocess
import sys


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
