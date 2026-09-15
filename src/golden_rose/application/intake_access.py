"""Metadata-only restricted-reveal events for the existing operator log surface.

Use an explicit stream sink: Uvicorn's default logging configuration suppresses
ordinary application INFO loggers. No address, name, phone, body or URL is emitted.
A failed sink propagates so the caller does not silently reveal without a record.
"""

import json
import sys
from datetime import UTC, datetime
from uuid import UUID


def record_employer_output_access(
    *, actor_id: UUID, employer_id: UUID, output_id: UUID, section: str
) -> None:
    event = {
        "event": "restricted_employer_output_address_read",
        "staff_actor_id": str(actor_id),
        "employer_id": str(employer_id),
        "output_id": str(output_id),
        "section": section,
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    sys.stderr.write(json.dumps(event, separators=(",", ":")) + "\n")
    sys.stderr.flush()


def record_contact_address_access(*, actor_id: UUID, employer_id: UUID, contact_id: UUID) -> None:
    event = {
        "event": "restricted_contact_address_read",
        "staff_actor_id": str(actor_id),
        "employer_id": str(employer_id),
        "contact_id": str(contact_id),
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    sys.stderr.write(json.dumps(event, separators=(",", ":")) + "\n")
    sys.stderr.flush()


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


def record_worker_access(*, actor_id: UUID, worker_id: UUID) -> None:
    event = {
        "event": "restricted_worker_residence_read",
        "staff_actor_id": str(actor_id),
        "worker_id": str(worker_id),
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    sys.stderr.write(json.dumps(event, separators=(",", ":")) + "\n")
    sys.stderr.flush()
