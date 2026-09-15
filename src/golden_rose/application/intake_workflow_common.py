"""Transaction-local receipt, result and audit primitives for intake commands."""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.command_receipts import serialize_command_key
from golden_rose.persistence.command_results import insert_command_result
from golden_rose.persistence.models import audit_events, command_receipts


def begin_command(
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    command_type: str,
    target: UUID | None,
    payload: dict[str, Any],
) -> tuple[bytes, dict[str, Any] | None]:
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "schema": 1,
                "actor": str(principal.actor_id),
                "command": command_type,
                "target": str(target),
                "payload": payload,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).digest()
    serialize_command_key(session=session, command_id=command_id)
    receipt = (
        session.execute(select(command_receipts).where(command_receipts.c.command_id == command_id))
        .mappings()
        .one_or_none()
    )
    if receipt is not None and (
        receipt["actor_id"] != principal.actor_id
        or receipt["command_type"] != command_type
        or receipt["request_fingerprint"] != fingerprint
    ):
        raise IntakeError("idempotency_conflict")
    return fingerprint, dict(receipt) if receipt is not None else None


def write_authority(
    session: Session,
    *,
    principal: StaffPrincipal,
    command_id: UUID,
    command_type: str,
    fingerprint: bytes,
    entity_type: str,
    entity_id: UUID,
    previous_version: int,
    event_type: str,
    event_id: UUID,
    now: datetime,
    changed: list[str],
) -> None:
    version = previous_version + 1
    session.execute(
        insert(command_receipts).values(
            command_id=command_id,
            command_schema_version=1,
            command_type=command_type,
            actor_id=principal.actor_id,
            request_fingerprint=fingerprint,
            result_entity_type=entity_type,
            result_entity_id=entity_id,
            result_record_version=version,
            result_event_type=event_type,
            created_at=now,
        )
    )
    write_result_authority(
        session,
        principal=principal,
        command_id=command_id,
        command_type=command_type,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_version=previous_version,
        event_type=event_type,
        event_id=event_id,
        now=now,
        changed=changed,
    )


def write_result_authority(
    session: Session,
    *,
    principal: StaffPrincipal,
    command_id: UUID,
    command_type: str,
    entity_type: str,
    entity_id: UUID,
    previous_version: int,
    event_type: str,
    event_id: UUID,
    now: datetime,
    changed: list[str],
) -> None:
    """Append one result/event pair under the outer command's sole receipt.

    Finalization uses this for created outputs only. Reused canonical records
    receive no new creation event. Schema guards enforce allowed result sets;
    the caller owns the transaction, concrete entity authority and rollback.
    """
    version = previous_version + 1
    insert_command_result(
        session=session,
        command_id=command_id,
        entity_type=entity_type,
        entity_id=entity_id,
        result_version=version,
        event_type=event_type,
        actor_id=principal.actor_id,
        command_type=command_type,
    )
    session.execute(
        insert(audit_events).values(
            audit_event_id=event_id,
            event_schema_name=event_type,
            event_schema_version=1,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_sequence=version,
            prior_record_version=previous_version,
            new_record_version=version,
            actor_type="staff",
            actor_id=principal.actor_id,
            occurred_at=now,
            command_id=command_id,
            correlation_id=command_id,
            source_type="staff_api",
            related_event_ids=[],
            changed_fields={"field_names": changed, "approved_values": {}},
            payload_classification="sensitive_operational",
        )
    )
