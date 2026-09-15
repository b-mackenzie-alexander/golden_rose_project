"""Version-bound review and accountable follow-up, one atomic intake command."""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_review_schemas import FollowUpIntakeRequest, ReviewIntakeRequest
from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_review_snapshot import (
    build_review_snapshot,
    review_dependencies,
)
from golden_rose.application.intake_workflow_common import begin_command, write_authority
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_directory import StaffDirectory
from golden_rose.clock import Clock
from golden_rose.persistence.intake_review_state import latest_follow_up, selected_interests
from golden_rose.persistence.intakes import get_intake, intake_detail, missing_fields
from golden_rose.persistence.models import (
    intake_follow_up_events,
    intake_history_payloads,
    intake_review_payloads,
    intake_reviews,
    intakes,
)


def review_sections(kind: str) -> tuple[str, ...]:
    return ("worker_residence",) if kind == "worker" else ("party_address", "worksite_address")


def authorize_snapshot(principal: StaffPrincipal, kind: str) -> None:
    if not {f"{section}:read" for section in review_sections(kind)} <= principal.permissions:
        raise IntakeError("forbidden", 403)


def authorize_review_content(principal: StaffPrincipal, row: dict[str, Any]) -> None:
    authorize_snapshot(principal, row["kind"])
    if (
        row["content"].get("interests", {}).get("selections")
        and "work_interest:read" not in principal.permissions
    ):
        raise IntakeError("forbidden", 403)


def execute_review(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    request: ReviewIntakeRequest | FollowUpIntakeRequest,
    clock: Clock,
    directory: StaffDirectory,
    intake_id: UUID,
) -> tuple[dict[str, Any], bool]:
    reviewing = isinstance(request, ReviewIntakeRequest)
    action = "intake:review" if reviewing else "intake:follow_up"
    authorize_intake(principal, action, intake_id=intake_id)
    if reviewing and request.outcome == "needs_follow_up":
        authorize_intake(principal, "intake:follow_up", intake_id=intake_id)
    try:
        # Kind lookup authorizes snapshot reads before any receipt can be revealed.
        initial = get_intake(session, intake_id)
        if isinstance(request, ReviewIntakeRequest):
            authorize_review_content(principal, initial)
            review_dependencies(session, principal, initial)
        actor = directory.resolve(principal.actor_id, intake_id, frozenset({"intake:read", action}))
        command_type = "review_intake" if reviewing else "follow_up_intake"
        fingerprint, receipt = begin_command(
            session,
            principal,
            command_id,
            command_type,
            intake_id,
            request.model_dump(mode="json", exclude_unset=True),
        )
        if receipt:
            current = get_intake(session, intake_id)
            if reviewing:
                authorize_review_content(principal, current)
                review_dependencies(session, principal, current)
            if current["version"] < receipt["result_record_version"]:
                raise IntakeError("persistence_unavailable", 503)
            result = {
                "command_id": str(command_id),
                "result_record_version": receipt["result_record_version"],
                "current": intake_detail(session, current, principal=principal),
            }
            session.rollback()
            return result, True
        row = get_intake(session, intake_id, lock=True)
        if reviewing:
            authorize_review_content(principal, row)
        if row["lifecycle_status"] != "draft" and reviewing:
            raise IntakeError("already_finalized")
        if row["version"] != request.expected_version:
            raise IntakeError("version_conflict")
        follow_up = not reviewing or request.outcome == "needs_follow_up"
        if follow_up:
            if request.owner_staff_id is None:
                raise IntakeError("invalid_request", 422)
            directory.resolve(
                request.owner_staff_id, intake_id, frozenset({"intake:read", "intake:follow_up"})
            )
        if isinstance(request, FollowUpIntakeRequest):
            prior = latest_follow_up(session, intake_id)
            if prior is None:
                raise IntakeError("invalid_request", 422)
            if request.action != "reassign" and request.owner_staff_id != prior["owner_staff_id"]:
                raise IntakeError("invalid_request", 422)
            if request.action == "reassign" and request.owner_staff_id == prior["owner_staff_id"]:
                raise IntakeError("no_change")
        snapshot: dict[str, Any] = {}
        dependencies: dict[str, Any] = {}
        if isinstance(request, ReviewIntakeRequest):
            dependencies = review_dependencies(session, principal, row)
            snapshot = build_review_snapshot(session, principal, row, dependencies)
            effective_row = {**row, "content": snapshot["content"]}
            authorize_review_content(principal, effective_row)
            if request.outcome == "intake_reviewed":
                selected_interests(session, snapshot["content"], lock=True, require_current=True)
                missing = missing_fields(session, effective_row, addresses=snapshot["addresses"])
                if missing:
                    raise IntakeError("incomplete", 422, missing_fields=missing)
        now, event_id, review_id = clock.now(), uuid4(), uuid4()
        previous = row["version"]
        row.update(version=previous + 1, updated_at=now, updated_by=principal.actor_id)
        session.execute(
            update(intakes)
            .where(intakes.c.intake_id == intake_id)
            .values(version=row["version"], updated_at=now, updated_by=principal.actor_id)
        )
        event_type = "intake.reviewed" if reviewing else "intake.follow_up_recorded"
        write_authority(
            session,
            principal=principal,
            command_id=command_id,
            command_type=command_type,
            fingerprint=fingerprint,
            entity_type="intake",
            entity_id=intake_id,
            previous_version=previous,
            event_type=event_type,
            event_id=event_id,
            now=now,
            changed=["review"] if reviewing else ["follow_up"],
        )
        if isinstance(request, ReviewIntakeRequest):
            session.execute(
                insert(intake_reviews).values(
                    review_id=review_id,
                    intake_id=intake_id,
                    command_id=command_id,
                    event_id=event_id,
                    reviewed_record_version=previous,
                    reviewed_content_version=row["content_version"],
                    result_version=row["version"],
                    outcome=request.outcome,
                    actor_id=principal.actor_id,
                    actor_display_name=actor.display_name,
                    occurred_at=now,
                )
            )
            session.execute(
                insert(intake_review_payloads).values(
                    review_id=review_id,
                    reviewed_content=snapshot,
                    note=request.note,
                    dependency_refs=dependencies,
                )
            )
        if follow_up:
            session.execute(
                insert(intake_follow_up_events).values(
                    event_id=event_id,
                    intake_id=intake_id,
                    command_id=command_id,
                    version=row["version"],
                    content_version=row["content_version"],
                    action="needs_follow_up"
                    if isinstance(request, ReviewIntakeRequest)
                    else request.action,
                    actor_id=principal.actor_id,
                    actor_display_name=actor.display_name,
                    occurred_at=now,
                    owner_staff_id=request.owner_staff_id,
                    next_follow_up_at=request.next_follow_up_at,
                    time_zone=request.time_zone,
                    reason_code=request.reason_code
                    if isinstance(request, ReviewIntakeRequest)
                    else None,
                    method=None if isinstance(request, ReviewIntakeRequest) else request.method,
                    outcome=None if reviewing else request.outcome,
                    review_id=review_id if isinstance(request, ReviewIntakeRequest) else None,
                )
            )
            session.execute(
                insert(intake_history_payloads).values(
                    event_id=event_id, reason_text=request.reason_text, note=request.note
                )
            )
        result = {
            "command_id": str(command_id),
            "result_record_version": row["version"],
            "current": intake_detail(session, row, principal=principal),
        }
        session.commit()
        return result, False
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    except Exception:
        session.rollback()
        raise


execute_follow_up = execute_review
