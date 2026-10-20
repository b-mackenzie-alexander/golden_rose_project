"""Atomic canonical corrections; no writes to finalized intake or original outputs."""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.canonical_correction_schemas import CanonicalCorrectionResponse
from golden_rose.application.canonical_correction_contracts import CorrectionRequest
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_workflow_common import begin_command, write_authority
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.canonical_corrections import SPECS, CorrectionSpec, section_snapshot
from golden_rose.persistence.intake_review_state import selected_interests
from golden_rose.persistence.models import (
    canonical_correction_payloads,
    canonical_corrections,
    employers,
    worker_interest_selections,
)


def authorize_correction(principal: StaffPrincipal, spec: CorrectionSpec, parent_id: UUID) -> None:
    if not spec.permissions <= principal.permissions:
        raise IntakeError("forbidden", 403)
    if (
        spec.entity.startswith("worker")
        and principal.worker_scope is not None
        and parent_id not in principal.worker_scope
    ):
        raise IntakeError("not_found", 404)


def correction_target(
    session: Session, spec: CorrectionSpec, parent_id: UUID, target_id: UUID, *, lock: bool
) -> dict[str, Any]:
    table = spec.table
    statement = select(table)
    if spec.entity.startswith("worker"):
        statement = statement.where(table.c.worker_id == parent_id)
        if spec.entity == "worker":
            statement = statement.where(table.c.worker_id == target_id)
    else:
        statement = statement.where(table.c.employer_id == parent_id)
        column = (
            "employer_contact_id"
            if spec.entity == "employer_contact_details"
            else f"{spec.entity}_id"
        )
        statement = statement.where(table.c[column] == target_id)
        parent_query = select(employers.c.employer_type, employers.c.lifecycle_status).where(
            employers.c.employer_id == parent_id
        )
        if lock:
            parent_query = parent_query.with_for_update()
        parent = session.execute(parent_query).mappings().one_or_none()
        if parent is None or parent["lifecycle_status"] != "draft":
            raise IntakeError("not_found", 404)
    if lock:
        statement = statement.with_for_update()
    row = session.execute(statement).mappings().one_or_none()
    if row is None:
        raise IntakeError("not_found", 404)
    return dict(row)


def execute_correction(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    command_type: str,
    parent_id: UUID,
    target_id: UUID,
    request: CorrectionRequest,
    clock: Clock,
) -> tuple[dict[str, Any], bool]:
    spec = SPECS.get(command_type)
    if spec is None or type(request) is not spec.model:
        raise IntakeError("invalid_request", 422)
    authorize_correction(principal, spec, parent_id)
    try:
        fingerprint, receipt = begin_command(
            session,
            principal,
            command_id,
            command_type,
            target_id,
            {"parent_id": str(parent_id), **request.to_content()},
        )
        row = correction_target(session, spec, parent_id, target_id, lock=True)
        identity = row[f"{spec.entity}_id"]
        if receipt is not None:
            event_id = session.scalar(
                select(canonical_corrections.c.event_id).where(
                    canonical_corrections.c.command_id == command_id
                )
            )
            if event_id is None:
                raise IntakeError("persistence_unavailable", 503)
            result = _response(
                command_id,
                event_id,
                spec.entity,
                identity,
                receipt["result_record_version"],
                row["version"],
            )
            session.commit()
            return result, True
        if command_type == "correct_contact_address":
            parent_type = session.scalar(
                select(employers.c.employer_type).where(employers.c.employer_id == parent_id)
            )
            if parent_type != "household":
                raise IntakeError("invalid_request", 422)
        if spec.entity == "staffing_request" and row["request_status"] != "draft":
            raise IntakeError("version_conflict")
        if row["version"] != request.expected_version:
            raise IntakeError("version_conflict")
        values = request.section_values()
        before = section_snapshot(spec, row)
        if "email" in spec.fields and "email" not in values:
            values = {**before, **values}
        if values == before:
            raise IntakeError("no_change")
        if request.corrects_event_id is not None:
            prior = (
                session.execute(
                    select(canonical_corrections).where(
                        canonical_corrections.c.event_id == request.corrects_event_id,
                        canonical_corrections.c.entity_type == spec.entity,
                        canonical_corrections.c.entity_id == identity,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if prior is None:
                raise IntakeError("invalid_request", 422)
        if spec.entity == "worker_preferences":
            selected_interests(session, values, lock=True, require_current=True)
        now = clock.now()
        event_id = uuid4()
        version = row["version"] + 1
        changed = (
            {name: values["address"].get(name) for name in spec.fields} if spec.address else values
        )
        session.execute(
            update(spec.table)
            .where(spec.table.c[f"{spec.entity}_id"] == identity)
            .values(**changed, version=version, updated_by=principal.actor_id, updated_at=now)
        )
        if spec.entity == "worker_preferences":
            session.execute(
                delete(worker_interest_selections).where(
                    worker_interest_selections.c.worker_preferences_id == identity
                )
            )
            for selection in values["interests"].get("selections", []):
                session.execute(
                    insert(worker_interest_selections).values(
                        worker_preferences_id=identity,
                        interest_id=UUID(selection["interest_id"]),
                        catalog_version=selection["catalog_version"],
                    )
                )
        write_authority(
            session,
            principal=principal,
            command_id=command_id,
            command_type=command_type,
            fingerprint=fingerprint,
            entity_type=spec.entity,
            entity_id=identity,
            previous_version=row["version"],
            event_type=f"{spec.entity}.corrected",
            event_id=event_id,
            now=now,
            changed=sorted(values),
        )
        session.execute(
            insert(canonical_corrections).values(
                event_id=event_id,
                command_id=command_id,
                command_type=command_type,
                entity_type=spec.entity,
                entity_id=identity,
                previous_version=row["version"],
                result_version=version,
                actor_id=principal.actor_id,
                occurred_at=now,
                corrects_event_id=request.corrects_event_id,
            )
        )
        session.execute(
            insert(canonical_correction_payloads).values(
                event_id=event_id, reason_text=request.reason_text, before=before, after=values
            )
        )
        result = _response(command_id, event_id, spec.entity, identity, version, version)
        session.commit()
        return result, False
    except IntakeError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc


def _response(
    command_id: UUID,
    event_id: UUID,
    entity: str,
    identity: UUID,
    result_version: int,
    current_version: int,
) -> dict[str, Any]:
    return CanonicalCorrectionResponse.model_validate(
        {
            "command_id": command_id,
            "event_id": event_id,
            "result_record_version": result_version,
            "target": {"entity_type": entity, "id": identity, "current_version": current_version},
        }
    ).model_dump(mode="json")
