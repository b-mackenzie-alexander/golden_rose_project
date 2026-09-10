from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.contact_text import validate_contact_full_name
from golden_rose.application.create_draft_employer import IdempotencyConflictError
from golden_rose.application.errors import EmployerNotFoundError, SafePersistenceError
from golden_rose.application.synthetic_data import require_develop_synthetic_value
from golden_rose.auth.permissions import can_create_draft_employer_contact, can_read_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.config import Environment
from golden_rose.identifiers import IdentifierFactory
from golden_rose.persistence.audit_events import insert_employer_contact_created_event
from golden_rose.persistence.command_receipts import (
    get_command_receipt,
    reserve_create_employer_contact_receipt,
)
from golden_rose.persistence.employer_contacts import (
    EmployerContactRecord,
    build_create_employer_contact_request_fingerprint,
    get_employer_contact_by_id,
    insert_employer_contact,
)
from golden_rose.persistence.entity_authorities import insert_employer_contact_authority
from golden_rose.persistence.models import employers


@dataclass(frozen=True, slots=True)
class CreateEmployerContactResult:
    contact: EmployerContactRecord
    employer_contact_id: UUID
    employer_id: UUID
    full_name: str
    version: int
    created_at: object
    updated_at: object
    replayed: bool
    result_record_version: int


def create_employer_contact(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    command_id: UUID,
    full_name: str,
    clock: Clock,
    identifiers: IdentifierFactory,
    environment: Environment = "local",
) -> CreateEmployerContactResult:
    if not can_read_employer(principal):
        msg = "principal lacks employer:read"
        raise PermissionError(msg)
    if not can_create_draft_employer_contact(principal):
        msg = "principal lacks employer_contact:draft:create"
        raise PermissionError(msg)

    normalized_full_name = validate_contact_full_name(full_name)
    require_develop_synthetic_value(
        environment=environment,
        field="contact_full_name",
        value=normalized_full_name,
    )
    now = clock.now()
    employer_contact_id = identifiers.new_uuid4()
    audit_event_id = identifiers.new_uuid4()
    request_fingerprint = build_create_employer_contact_request_fingerprint(
        employer_id=employer_id,
        full_name=normalized_full_name,
    )

    try:
        receipt_inserted = reserve_create_employer_contact_receipt(
            session=session,
            command_id=command_id,
            actor_id=principal.actor_id,
            request_fingerprint=request_fingerprint,
            result_entity_id=employer_contact_id,
            created_at=now,
        )
        if not receipt_inserted:
            existing_receipt = get_command_receipt(session=session, command_id=command_id)
            if (
                existing_receipt.actor_id != principal.actor_id
                or existing_receipt.command_schema_version != 1
                or existing_receipt.command_type != "create_employer_contact"
                or existing_receipt.result_entity_type != "employer_contact"
                or existing_receipt.request_fingerprint != request_fingerprint
            ):
                raise IdempotencyConflictError("idempotency conflict")
            if existing_receipt.result_record_version != 1:
                raise SafePersistenceError("persistence operation failed")
            contact = get_employer_contact_by_id(
                session=session,
                employer_contact_id=existing_receipt.result_entity_id,
            )
            if contact.version < existing_receipt.result_record_version:
                raise SafePersistenceError("persistence operation failed")
            session.rollback()
            return CreateEmployerContactResult(
                contact=contact,
                employer_contact_id=contact.employer_contact_id,
                employer_id=contact.employer_id,
                full_name=contact.full_name,
                version=contact.version,
                created_at=contact.created_at,
                updated_at=contact.updated_at,
                replayed=True,
                result_record_version=existing_receipt.result_record_version,
            )

        parent = session.execute(
            select(employers.c.employer_id)
            .where(
                employers.c.employer_id == employer_id,
                employers.c.lifecycle_status == "draft",
            )
            .with_for_update()
        ).one_or_none()
        if parent is None:
            session.rollback()
            raise EmployerNotFoundError("employer not found")

        contact = insert_employer_contact(
            session=session,
            employer_contact_id=employer_contact_id,
            employer_id=employer_id,
            full_name=normalized_full_name,
            created_by=principal.actor_id,
            created_at=now,
        )
        insert_employer_contact_authority(
            session=session,
            employer_contact_id=employer_contact_id,
        )
        insert_employer_contact_created_event(
            session=session,
            audit_event_id=audit_event_id,
            employer_contact_id=employer_contact_id,
            actor_id=principal.actor_id,
            command_id=command_id,
            occurred_at=now,
        )
        session.flush()
        session.commit()
    except NoResultFound as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise

    return CreateEmployerContactResult(
        contact=contact,
        employer_contact_id=contact.employer_contact_id,
        employer_id=contact.employer_id,
        full_name=contact.full_name,
        version=contact.version,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
        replayed=False,
        result_record_version=1,
    )
