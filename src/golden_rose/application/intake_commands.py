import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.intake_contracts import validate_content
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.command_receipts import serialize_command_key
from golden_rose.persistence.command_results import insert_command_result
from golden_rose.persistence.intakes import get_address, get_intake, intake_detail
from golden_rose.persistence.models import (
    audit_events,
    command_receipts,
    entity_authorities,
    intake_addresses,
    intakes,
)

ADDRESS_PERMISSIONS = {
    "worker_residence": "worker_residence",
    "party_address": "party_address",
    "worksite_address": "worksite_address",
}
ADDRESS_FIELDS = {
    "residential_address": "worker_residence",
    "party_address": "party_address",
    "worksite_address": "worksite_address",
}


def authorize_intake(
    principal: StaffPrincipal,
    action: str,
    section: str | None = None,
    intake_id: UUID | None = None,
) -> None:
    required = {"intake:read", action}
    if section is not None:
        if section not in ADDRESS_PERMISSIONS:
            raise IntakeError("invalid_request", 422)
        required.add(f"{section}:read")
        if action != "intake:read":
            required.add(f"{section}:write")
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    if (
        intake_id is not None
        and principal.intake_scope is not None
        and intake_id not in principal.intake_scope
    ):
        raise IntakeError("not_found", 404)


def execute_intake(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    request: Any,
    clock: Clock,
    intake_id: UUID | None = None,
    section: str | None = None,
) -> tuple[dict[str, Any], bool]:
    """One transaction owns candidate, exact audit, result and receipt."""

    creating = intake_id is None
    action = "intake:draft:create" if creating else "intake:draft:revise"
    authorize_intake(principal, action, section, intake_id)
    payload = request.model_dump(mode="json", exclude_unset=True)
    supplied = request.content.to_content() if section is None else {}
    if creating:
        for field, address_section in ADDRESS_FIELDS.items():
            if field in request.content.model_fields_set:
                authorize_intake(principal, action, address_section)
    command_type = (
        "create_intake" if creating else ("revise_intake_address" if section else "revise_intake")
    )
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "schema": 1,
                "actor": str(principal.actor_id),
                "command": command_type,
                "target": str(intake_id),
                "section": section,
                "payload": payload,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).digest()
    if (
        supplied.get("interests", {}).get("selections")
        and "work_interest:read" not in principal.permissions
    ):
        raise IntakeError("forbidden", 403)
    try:
        serialize_command_key(session=session, command_id=command_id)
        receipt = (
            session.execute(
                select(command_receipts).where(
                    command_receipts.c.command_id == command_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if receipt is not None:
            if (
                receipt["actor_id"] != principal.actor_id
                or receipt["command_type"] != command_type
                or receipt["request_fingerprint"] != fingerprint
            ):
                raise IntakeError("idempotency_conflict")
            result_id = receipt["result_entity_id"]
            authorize_intake(principal, action, section, result_id)
            current = get_intake(session, result_id)
            if current["version"] < receipt["result_record_version"]:
                raise IntakeError("persistence_unavailable", 503)
            response = {
                "command_id": str(command_id),
                "result_record_version": receipt["result_record_version"],
                "current": intake_detail(session, current, principal=principal),
            }
            session.rollback()
            return response, True
        if creating and principal.intake_scope is not None:
            # A finite record scope can replay its known result, but cannot create.
            raise IntakeError("forbidden", 403)
        now = clock.now()
        if creating:
            intake_id = uuid4()
            values = dict(supplied)
            addresses = {s: values.pop(f) for f, s in ADDRESS_FIELDS.items() if f in values}
            row = {
                "intake_id": intake_id,
                "kind": request.kind,
                "schema_version": 1,
                "content": values,
                "lifecycle_status": "draft",
                "version": 1,
                "content_version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": principal.actor_id,
                "updated_by": principal.actor_id,
            }
            session.execute(insert(intakes).values(**row))
            session.execute(
                insert(entity_authorities).values(
                    entity_type="intake",
                    entity_id=intake_id,
                    intake_id=intake_id,
                )
            )
            changed = sorted(set(values) | set(addresses))
            previous_version = 0
        else:
            if intake_id is None:
                raise IntakeError("invalid_request", 422)
            row = get_intake(session, intake_id, lock=True)
            if row["lifecycle_status"] != "draft":
                raise IntakeError("already_finalized")
            if section and ((row["kind"] == "worker") != (section == "worker_residence")):
                raise IntakeError("invalid_request", 422)
            if row["version"] != request.expected_version:
                raise IntakeError("version_conflict")
            previous_version = row["version"]
            if previous_version >= 2_147_483_647:
                raise IntakeError("version_conflict")
            addresses = {}
            if section is None:
                values = validate_content(row["kind"], supplied).to_content()
                if values == row["content"]:
                    raise IntakeError("no_change")
                changed = sorted(
                    k
                    for k in set(values) | set(row["content"])
                    if values.get(k) != row["content"].get(k)
                )
                row["content"] = values
            else:
                address = request.address.to_content() if request.address is not None else None
                if (address or None) == get_address(session, intake_id, section):
                    raise IntakeError("no_change")
                addresses = {section: address}
                changed = [section]
            row.update(
                version=previous_version + 1,
                content_version=row["content_version"] + 1,
                updated_at=now,
                updated_by=principal.actor_id,
            )
            session.execute(
                update(intakes)
                .where(intakes.c.intake_id == intake_id)
                .values(
                    content=row["content"],
                    version=row["version"],
                    content_version=row["content_version"],
                    updated_at=now,
                    updated_by=principal.actor_id,
                )
            )
        if row["content"].get("interests", {}).get("selections"):
            if "work_interest:read" not in principal.permissions:
                raise IntakeError("forbidden", 403)
            from golden_rose.persistence.intake_review_state import selected_interests

            selected_interests(session, row["content"], lock=True)
        for address_section, address in addresses.items():
            columns = {
                key: (address or {}).get(key)
                for key in (
                    "line1",
                    "line2",
                    "locality",
                    "region",
                    "postal_code",
                    "country",
                )
            }
            stmt = pg_insert(intake_addresses).values(
                intake_id=intake_id,
                section=address_section,
                **columns,
            )
            session.execute(
                stmt.on_conflict_do_update(
                    index_elements=["intake_id", "section"],
                    set_=columns,
                )
            )
        event_type = "intake.created" if creating else "intake.revised"
        session.execute(
            insert(command_receipts).values(
                command_id=command_id,
                command_schema_version=1,
                command_type=command_type,
                actor_id=principal.actor_id,
                request_fingerprint=fingerprint,
                result_entity_type="intake",
                result_entity_id=intake_id,
                result_record_version=row["version"],
                result_event_type=event_type,
                created_at=now,
            )
        )
        insert_command_result(
            session=session,
            command_id=command_id,
            entity_type="intake",
            entity_id=intake_id,
            result_version=row["version"],
            event_type=event_type,
            actor_id=principal.actor_id,
            command_type=command_type,
        )
        session.execute(
            insert(audit_events).values(
                audit_event_id=uuid4(),
                event_schema_name=event_type,
                event_schema_version=1,
                event_type=event_type,
                entity_type="intake",
                entity_id=intake_id,
                entity_sequence=row["version"],
                prior_record_version=previous_version,
                new_record_version=row["version"],
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
        response = {
            "command_id": str(command_id),
            "result_record_version": row["version"],
            "current": intake_detail(session, row, principal=principal),
        }
        session.commit()
        return response, False
    except ValidationError as exc:
        session.rollback()
        raise IntakeError("invalid_request", 422) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    except Exception:
        session.rollback()
        raise
