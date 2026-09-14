"""Metadata-only restricted-reveal events for the existing operator log surface.

Use an explicit stream sink: Uvicorn's default logging configuration suppresses
ordinary application INFO loggers. No address, name, phone, body or URL is emitted.
A failed sink propagates so the caller does not silently reveal without a record.
"""

import json
import sys
from datetime import UTC, datetime
from uuid import UUID


def record_intake_access(*, actor_id: UUID, intake_id: UUID, section: str) -> None:
    event = {
        "event": "restricted_intake_address_read",
        "staff_actor_id": str(actor_id),
        "intake_id": str(intake_id),
        "section": section,
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    sys.stderr.write(json.dumps(event, separators=(",", ":")) + "\n")
    sys.stderr.flush()
