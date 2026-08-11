from datetime import datetime
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.orm import Session

from golden_rose.persistence.models import audit_events


def insert_employer_created_event(
    *,
    session: Session,
    audit_event_id: UUID,
    employer_id: UUID,
    actor_id: UUID,
    command_id: UUID,
    occurred_at: datetime,
    changed_fields: dict[str, object],
) -> None:
    session.execute(
        insert(audit_events).values(
            audit_event_id=audit_event_id,
            event_schema_name="employer.created",
            event_schema_version=1,
            event_type="employer.created",
            entity_type="employer",
            entity_id=employer_id,
            entity_sequence=1,
            prior_record_version=0,
            new_record_version=1,
            actor_type="staff",
            actor_id=actor_id,
            initiating_staff_actor_id=None,
            occurred_at=occurred_at,
            effective_at=None,
            command_id=command_id,
            correlation_id=command_id,
            reason_code=None,
            reason_text=None,
            source_type="staff_api",
            source_reference=None,
            related_event_ids=[],
            changed_fields=changed_fields,
            payload_classification="sensitive_operational",
        )
    )


def insert_employer_draft_revised_event(
    *,
    session: Session,
    audit_event_id: UUID,
    employer_id: UUID,
    actor_id: UUID,
    command_id: UUID,
    occurred_at: datetime,
    prior_record_version: int,
    new_record_version: int,
    changed_fields: dict[str, object],
) -> None:
    session.execute(
        insert(audit_events).values(
            audit_event_id=audit_event_id,
            event_schema_name="employer.draft_revised",
            event_schema_version=1,
            event_type="employer.draft_revised",
            entity_type="employer",
            entity_id=employer_id,
            entity_sequence=new_record_version,
            prior_record_version=prior_record_version,
            new_record_version=new_record_version,
            actor_type="staff",
            actor_id=actor_id,
            initiating_staff_actor_id=None,
            occurred_at=occurred_at,
            effective_at=None,
            command_id=command_id,
            correlation_id=command_id,
            reason_code=None,
            reason_text=None,
            source_type="staff_api",
            source_reference=None,
            related_event_ids=[],
            changed_fields=changed_fields,
            payload_classification="sensitive_operational",
        )
    )
