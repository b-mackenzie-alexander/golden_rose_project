"""Atomic link commands with currently authorized, minimized intake responses."""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import LinkIntakeRequest
from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_workflow_common import begin_command, write_authority
from golden_rose.application.resolve_intake_links import (
    authorize_link_selection,
    resolve_link_dependencies,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.intake_links import get_link_dependencies, write_link_dependencies
from golden_rose.persistence.intakes import get_intake, intake_detail


def execute_link_intake(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    intake_id: UUID,
    request: LinkIntakeRequest,
    clock: Clock,
) -> tuple[dict[str, Any], bool]:
    """Own the write and current-detail projection in one transaction."""
    authorize_intake(principal, "intake:link", intake_id=intake_id)
    try:
        initial = get_intake(session, intake_id)
        authorize_link_selection(principal=principal, kind=initial["kind"], request=request)
        fingerprint, receipt = begin_command(
            session,
            principal,
            command_id,
            "link_intake",
            intake_id,
            request.model_dump(mode="json"),
        )
        row = get_intake(session, intake_id, lock=True)
        authorize_link_selection(principal=principal, kind=row["kind"], request=request)
        if receipt is not None:
            if (
                receipt["result_entity_type"] != "intake"
                or receipt["result_entity_id"] != intake_id
                or receipt["result_event_type"] != "intake.linked"
                or not 2 <= receipt["result_record_version"] <= row["version"]
            ):
                raise IntakeError("persistence_unavailable", 503)
            result = {
                "command_id": str(command_id),
                "result_record_version": receipt["result_record_version"],
                "current": intake_detail(session, row, principal=principal),
            }
            session.rollback()
            return result, True
        if row["lifecycle_status"] != "draft":
            raise IntakeError("already_finalized")
        if row["version"] != request.expected_version:
            raise IntakeError("version_conflict")
        if max(row["version"], row["content_version"]) >= 2147483647:
            raise IntakeError("version_conflict")
        dependencies = resolve_link_dependencies(
            session=session,
            principal=principal,
            kind=row["kind"],
            request=request,
        )
        if dependencies == get_link_dependencies(session, intake_id):
            raise IntakeError("no_change")
        now = clock.now()
        write_link_dependencies(
            session,
            intake_id=intake_id,
            dependencies=dependencies,
            version=row["version"] + 1,
            content_version=row["content_version"] + 1,
            updated_at=now,
            updated_by=principal.actor_id,
        )
        write_authority(
            session,
            principal=principal,
            command_id=command_id,
            command_type="link_intake",
            fingerprint=fingerprint,
            entity_type="intake",
            entity_id=intake_id,
            previous_version=row["version"],
            event_type="intake.linked",
            event_id=uuid4(),
            now=now,
            changed=["links"],
        )
        result = {
            "command_id": str(command_id),
            "result_record_version": row["version"] + 1,
            "current": intake_detail(session, get_intake(session, intake_id), principal=principal),
        }
        session.commit()
        return result, False
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    except Exception:
        session.rollback()
        raise
