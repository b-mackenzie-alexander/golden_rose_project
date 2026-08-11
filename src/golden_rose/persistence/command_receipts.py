from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from golden_rose.persistence.models import command_receipts


@dataclass(frozen=True, slots=True)
class CommandReceiptRecord:
    command_id: UUID
    command_schema_version: int
    command_type: str
    actor_id: UUID
    request_fingerprint: bytes
    result_entity_type: str
    result_entity_id: UUID
    result_record_version: int
    result_event_type: str
    created_at: datetime


def reserve_command_receipt(
    *,
    session: Session,
    command_id: UUID,
    actor_id: UUID,
    request_fingerprint: bytes,
    result_entity_id: UUID,
    created_at: datetime,
) -> bool:
    result = session.execute(
        insert(command_receipts)
        .values(
            command_id=command_id,
            command_schema_version=1,
            command_type="create_draft_employer",
            actor_id=actor_id,
            request_fingerprint=request_fingerprint,
            result_entity_type="employer",
            result_entity_id=result_entity_id,
            created_at=created_at,
        )
        .on_conflict_do_nothing(index_elements=[command_receipts.c.command_id])
        .returning(command_receipts.c.command_id)
    )
    return result.scalar_one_or_none() is not None


def reserve_revision_command_receipt(
    *,
    session: Session,
    command_id: UUID,
    actor_id: UUID,
    request_fingerprint: bytes,
    result_entity_id: UUID,
    result_record_version: int,
    created_at: datetime,
) -> bool:
    result = session.execute(
        insert(command_receipts)
        .values(
            command_id=command_id,
            command_schema_version=1,
            command_type="revise_draft_employer",
            actor_id=actor_id,
            request_fingerprint=request_fingerprint,
            result_entity_type="employer",
            result_entity_id=result_entity_id,
            result_record_version=result_record_version,
            result_event_type="employer.draft_revised",
            created_at=created_at,
        )
        .on_conflict_do_nothing(index_elements=[command_receipts.c.command_id])
        .returning(command_receipts.c.command_id)
    )
    return result.scalar_one_or_none() is not None


def get_command_receipt(*, session: Session, command_id: UUID) -> CommandReceiptRecord:
    row = session.execute(
        select(
            command_receipts.c.command_id,
            command_receipts.c.command_schema_version,
            command_receipts.c.command_type,
            command_receipts.c.actor_id,
            command_receipts.c.request_fingerprint,
            command_receipts.c.result_entity_type,
            command_receipts.c.result_entity_id,
            command_receipts.c.result_record_version,
            command_receipts.c.result_event_type,
            command_receipts.c.created_at,
        ).where(command_receipts.c.command_id == command_id)
    ).one()
    return CommandReceiptRecord(*row)
