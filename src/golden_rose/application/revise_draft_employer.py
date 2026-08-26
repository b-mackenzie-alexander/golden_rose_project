import hashlib
import json
from dataclasses import dataclass
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.employer_text import (
    normalize_employer_text,
    validate_employer_display_name,
)
from golden_rose.application.errors import (
    EmployerNotFoundError,
    EmployerVersionConflictError,
    SafePersistenceError,
)
from golden_rose.auth.permissions import can_revise_draft_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.audit_events import insert_employer_draft_revised_event
from golden_rose.persistence.command_receipts import (
    CommandReceiptRecord,
    get_command_receipt,
    reserve_revision_command_receipt,
)
from golden_rose.persistence.employers import EmployerRecord, get_authoritative_employer_by_id
from golden_rose.persistence.models import employers


@dataclass(frozen=True, slots=True)
class ReviseDraftEmployerResult:
    employer: EmployerRecord
    replayed: bool
    result_record_version: int


def revise_draft_employer(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    employer_id: UUID,
    expected_version: int,
    employer_type: Literal["household", "business"],
    display_name: str,
    clock: Clock,
) -> ReviseDraftEmployerResult:
    if not can_revise_draft_employer(principal):
        msg = "principal lacks employer:draft:revise"
        raise PermissionError(msg)

    normalized_display_name = validate_employer_display_name(display_name)
    now = clock.now()
    request_fingerprint = _build_request_fingerprint(
        employer_id=employer_id,
        expected_version=expected_version,
        employer_type=employer_type,
        display_name=normalized_display_name,
    )

    try:
        try:
            existing_receipt = get_command_receipt(session=session, command_id=command_id)
        except NoResultFound:
            existing_receipt = None
        if existing_receipt is not None:
            return _replay_existing_revision(
                session=session,
                existing_receipt=existing_receipt,
                principal=principal,
                employer_id=employer_id,
                expected_version=expected_version,
                request_fingerprint=request_fingerprint,
            )

        receipt_inserted = reserve_revision_command_receipt(
            session=session,
            command_id=command_id,
            actor_id=principal.actor_id,
            request_fingerprint=request_fingerprint,
            result_entity_id=employer_id,
            result_record_version=expected_version + 1,
            created_at=now,
        )
        if not receipt_inserted:
            try:
                existing_receipt = get_command_receipt(session=session, command_id=command_id)
            except NoResultFound as exc:
                session.rollback()
                try:
                    existing_receipt = get_command_receipt(session=session, command_id=command_id)
                except NoResultFound as retry_exc:
                    raise SafePersistenceError("persistence operation failed") from retry_exc
            result = _replay_existing_revision(
                session=session,
                existing_receipt=existing_receipt,
                principal=principal,
                employer_id=employer_id,
                expected_version=expected_version,
                request_fingerprint=request_fingerprint,
            )
            session.rollback()
            return result

        current_match = session.execute(
            select(employers.c.employer_type, employers.c.display_name)
            .where(
                employers.c.employer_id == employer_id,
                employers.c.lifecycle_status == "draft",
                employers.c.version == expected_version,
            )
            .with_for_update()
        ).one_or_none()
        if current_match is None:
            session.rollback()
            existing_employer_id = session.execute(
                select(employers.c.employer_id).where(employers.c.employer_id == employer_id)
            ).scalar_one_or_none()
            if existing_employer_id is None:
                raise EmployerNotFoundError("employer not found")
            raise EmployerVersionConflictError("employer version conflict")

        current_employer_type, current_display_name = current_match
        current_values = (current_employer_type, current_display_name)
        normalized_current_display_name = normalize_employer_text(current_display_name)
        if (
            current_employer_type == employer_type
            and normalized_current_display_name == normalized_display_name
        ):
            session.rollback()
            raise RuntimeError("employer revision requires a change")

        changed_fields = _build_changed_fields(
            current_match=current_values,
            employer_type=employer_type,
            display_name=normalized_display_name,
        )

        row = session.execute(
            update(employers)
            .where(
                employers.c.employer_id == employer_id,
                employers.c.lifecycle_status == "draft",
                employers.c.version == expected_version,
            )
            .values(
                employer_type=employer_type,
                display_name=normalized_display_name,
                updated_at=now,
                updated_by=principal.actor_id,
                version=expected_version + 1,
            )
            .returning(
                employers.c.employer_id,
                employers.c.employer_type,
                employers.c.display_name,
                employers.c.lifecycle_status,
                employers.c.source_channel,
                employers.c.received_at,
                employers.c.created_at,
                employers.c.updated_at,
                employers.c.created_by,
                employers.c.version,
            )
        ).one()
        employer = EmployerRecord(*row)
        insert_employer_draft_revised_event(
            session=session,
            audit_event_id=_build_revision_audit_event_id(command_id),
            employer_id=employer_id,
            actor_id=principal.actor_id,
            command_id=command_id,
            occurred_at=now,
            prior_record_version=expected_version,
            new_record_version=employer.version,
            changed_fields=changed_fields,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise

    return ReviseDraftEmployerResult(
        employer=employer,
        replayed=False,
        result_record_version=expected_version + 1,
    )


def _replay_existing_revision(
    *,
    session: Session,
    existing_receipt: CommandReceiptRecord,
    principal: StaffPrincipal,
    employer_id: UUID,
    expected_version: int,
    request_fingerprint: bytes,
) -> ReviseDraftEmployerResult:
    if existing_receipt.result_entity_id != employer_id:
        raise SafePersistenceError("persistence operation failed")
    if not (
        existing_receipt.command_schema_version == 1
        and existing_receipt.command_type == "revise_draft_employer"
        and existing_receipt.actor_id == principal.actor_id
        and existing_receipt.result_entity_type == "employer"
        and existing_receipt.result_entity_id == employer_id
        and existing_receipt.request_fingerprint == request_fingerprint
    ):
        raise RuntimeError("idempotency conflict")
    if existing_receipt.result_record_version != expected_version + 1:
        raise SafePersistenceError("persistence operation failed")
    if existing_receipt.result_event_type != "employer.draft_revised":
        raise SafePersistenceError("persistence operation failed")
    try:
        employer = get_authoritative_employer_by_id(session=session, employer_id=employer_id)
    except NoResultFound as exc:
        raise SafePersistenceError("persistence operation failed") from exc
    if employer.version < existing_receipt.result_record_version:
        raise SafePersistenceError("persistence operation failed")
    return ReviseDraftEmployerResult(
        employer=employer,
        replayed=True,
        result_record_version=existing_receipt.result_record_version,
    )


def _build_request_fingerprint(
    *,
    employer_id: UUID,
    expected_version: int,
    employer_type: Literal["household", "business"],
    display_name: str,
) -> bytes:
    payload = json.dumps(
        {
            "command_schema_version": 1,
            "command_type": "revise_draft_employer",
            "employer_id": str(employer_id),
            "expected_version": expected_version,
            "employer_type": employer_type,
            "display_name": display_name,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).digest()


def _build_revision_audit_event_id(command_id: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"revise_draft_employer:{command_id}")


def _build_changed_fields(
    *,
    current_match: tuple[str, str] | None,
    employer_type: Literal["household", "business"],
    display_name: str,
) -> dict[str, object]:
    if current_match is None:
        field_names = ["employer_type", "display_name"]
    else:
        current_employer_type, current_display_name = current_match
        field_names = []
        if current_employer_type != employer_type:
            field_names.append("employer_type")
        if normalize_employer_text(current_display_name) != display_name:
            field_names.append("display_name")

    approved_values: dict[str, object] = {}
    if "employer_type" in field_names:
        approved_values["employer_type"] = employer_type

    return {
        "field_names": field_names,
        "approved_values": approved_values,
    }
