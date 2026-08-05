import hashlib
import json
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.auth.permissions import can_create_draft_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.identifiers import IdentifierFactory
from golden_rose.persistence.audit_events import insert_employer_created_event
from golden_rose.persistence.command_receipts import (
    get_command_receipt,
    reserve_command_receipt,
)
from golden_rose.persistence.employers import (
    EmployerRecord,
    get_employer_by_id,
    insert_draft_employer,
)


@dataclass(frozen=True, slots=True)
class CreateDraftEmployerResult:
    employer: EmployerRecord
    replayed: bool


class SafePersistenceError(RuntimeError):
    pass


class IdempotencyConflictError(RuntimeError):
    pass


def create_draft_employer(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    employer_type: Literal["household", "business"],
    display_name: str,
    clock: Clock,
    identifiers: IdentifierFactory,
) -> CreateDraftEmployerResult:
    if not can_create_draft_employer(principal):
        msg = "principal lacks employer:draft:create"
        raise PermissionError(msg)

    now = clock.now()
    employer_id = identifiers.new_uuid4()
    audit_event_id = identifiers.new_uuid4()
    request_fingerprint = _build_request_fingerprint(
        employer_type=employer_type,
        display_name=display_name,
    )

    try:
        receipt_inserted = reserve_command_receipt(
            session=session,
            command_id=command_id,
            actor_id=principal.actor_id,
            request_fingerprint=request_fingerprint,
            result_entity_id=employer_id,
            created_at=now,
        )
        if not receipt_inserted:
            existing_receipt = get_command_receipt(session=session, command_id=command_id)
            if (
                existing_receipt.actor_id != principal.actor_id
                or existing_receipt.command_schema_version != 1
                or existing_receipt.command_type != "create_draft_employer"
                or existing_receipt.result_entity_type != "employer"
                or existing_receipt.request_fingerprint != request_fingerprint
            ):
                raise IdempotencyConflictError("idempotency conflict")
            employer = get_employer_by_id(
                session=session, employer_id=existing_receipt.result_entity_id
            )
            session.rollback()
            return CreateDraftEmployerResult(employer=employer, replayed=True)
        employer = insert_draft_employer(
            session=session,
            employer_id=employer_id,
            employer_type=employer_type,
            display_name=display_name,
            created_by=principal.actor_id,
            created_at=now,
        )
        insert_employer_created_event(
            session=session,
            audit_event_id=audit_event_id,
            employer_id=employer_id,
            actor_id=principal.actor_id,
            command_id=command_id,
            occurred_at=now,
            changed_fields=_build_changed_fields(employer_type=employer_type),
        )
        session.flush()
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise

    return CreateDraftEmployerResult(employer=employer, replayed=False)


def _build_request_fingerprint(
    *,
    employer_type: Literal["household", "business"],
    display_name: str,
) -> bytes:
    payload = json.dumps(
        {
            "command_schema_version": 1,
            "command_type": "create_draft_employer",
            "employer_type": employer_type,
            "display_name": display_name,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).digest()


def _build_changed_fields(*, employer_type: Literal["household", "business"]) -> dict[str, object]:
    return {
        "field_names": [
            "employer_type",
            "display_name",
            "lifecycle_status",
            "source_channel",
        ],
        "approved_values": {
            "employer_type": employer_type,
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
        },
    }
