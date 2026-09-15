"""Transaction-local preconditions for the PR C finalization orchestrator."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import FinalizeIntakeRequest
from golden_rose.api.staff.intake_schemas import (
    EmployerFinalizationOutputs,
    WorkerFinalizationOutputs,
)
from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_review_snapshot import (
    build_review_snapshot,
    review_dependencies,
)
from golden_rose.application.intake_workflow_common import (
    begin_command,
    write_authority,
    write_result_authority,
)
from golden_rose.application.linked_intake_snapshot import read_linked_snapshot
from golden_rose.application.review_intake import authorize_review_content
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.employer_intake_outputs import (
    insert_employer_group,
    insert_new_employer_group,
)
from golden_rose.persistence.intake_outputs import finalization_outputs, get_finalization
from golden_rose.persistence.intake_review_state import selected_interests
from golden_rose.persistence.intakes import get_address, get_intake, intake_detail, missing_fields
from golden_rose.persistence.models import (
    command_results,
    employers,
    intake_finalizations,
    intake_review_payloads,
    intake_reviews,
    intakes,
)
from golden_rose.persistence.workers import insert_worker_group

WORKER_KINDS = ("worker", "worker_contact", "worker_residence", "worker_preferences")


def authorize_finalization_fields(
    session: Session,
    principal: StaffPrincipal,
    row: dict[str, Any],
    dependencies: dict[str, Any],
) -> tuple[str, ...]:
    sections = (
        ("worker_residence",) if row["kind"] == "worker" else ("party_address", "worksite_address")
    )
    reused_sections = set()
    if dependencies and row["kind"] == "worker":
        reused_sections.add("worker_residence")
    elif dependencies:
        employer_type = session.scalar(
            select(employers.c.employer_type).where(
                employers.c.employer_id == UUID(dependencies["employer"]["id"]),
                employers.c.lifecycle_status == "draft",
            )
        )
        if employer_type is None:
            raise IntakeError("not_found", 404)
        if "worksite" in dependencies:
            reused_sections.add("worksite_address")
        if (employer_type == "household" and "employer_contact_details" in dependencies) or (
            employer_type == "business" and "employer_address" in dependencies
        ):
            reused_sections.add("party_address")
    for section in sections:
        action = "intake:read" if section in reused_sections else "intake:finalize"
        authorize_intake(principal, action, section, row["intake_id"])
    authorize_review_content(principal, row)
    return sections


def require_finalization_review(
    *,
    session: Session,
    principal: StaffPrincipal,
    row: dict[str, Any],
    request: FinalizeIntakeRequest,
    dependency_refs: dict[str, Any],
) -> None:
    """Check a fresh command after replay resolution, under the intake row lock.

    The caller resolves and locks canonical dependencies before supplying their
    current references. Completeness, current catalog selections and permissions
    to create canonical fields are additional checks owned by the orchestrator.
    This helper neither writes nor commits and is not a finalization endpoint.
    """
    authorize_intake(principal, "intake:finalize", intake_id=row["intake_id"])
    authorize_review_content(principal, row)
    if row["lifecycle_status"] != "draft":
        raise IntakeError("already_finalized")
    if row["version"] != request.expected_version:
        raise IntakeError("version_conflict")
    # Reviews are immutable; serializing on the intake prevents a concurrent
    # review or follow-up from changing which disposition is latest.
    latest = (
        session.execute(
            select(
                intake_reviews.c.review_id,
                intake_reviews.c.outcome,
                intake_reviews.c.reviewed_content_version,
                intake_review_payloads.c.dependency_refs,
            )
            .outerjoin(
                intake_review_payloads,
                intake_review_payloads.c.review_id == intake_reviews.c.review_id,
            )
            .where(intake_reviews.c.intake_id == row["intake_id"])
            .order_by(intake_reviews.c.result_version.desc())
            .limit(1)
        )
        .mappings()
        .one_or_none()
    )
    if (
        latest is None
        or latest["review_id"] != request.review_id
        or latest["outcome"] != "intake_reviewed"
        or latest["reviewed_content_version"] != row["content_version"]
    ):
        raise IntakeError("review_required")
    if latest["dependency_refs"] is None:
        raise IntakeError("persistence_unavailable", 503)
    if latest["dependency_refs"] != dependency_refs:
        raise IntakeError("dependency_changed")


def execute_new_intake_finalization(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    intake_id: UUID,
    request: FinalizeIntakeRequest,
    clock: Clock,
) -> tuple[dict[str, Any], bool]:
    """Create new outputs or reuse selected records; reuse awaits schema admission."""
    authorize_intake(principal, "intake:finalize", intake_id=intake_id)
    try:
        initial = get_intake(session, intake_id)
        initial_dependencies = review_dependencies(session, principal, initial)
        authorize_finalization_fields(session, principal, initial, initial_dependencies)
        fingerprint, receipt = begin_command(
            session,
            principal,
            command_id,
            "finalize_intake",
            intake_id,
            request.model_dump(mode="json"),
        )
        row = get_intake(session, intake_id, lock=True)
        dependencies = review_dependencies(session, principal, row)
        sections = authorize_finalization_fields(session, principal, row, dependencies)
        if receipt is not None:
            finalized = get_finalization(session, intake_id)
            try:
                outputs = finalization_outputs(finalized)
                output_model = (
                    WorkerFinalizationOutputs
                    if row["kind"] == "worker"
                    else EmployerFinalizationOutputs
                )
                output_model.model_validate(outputs)
            except (ValidationError, KeyError) as exc:
                raise IntakeError("persistence_unavailable", 503) from exc
            output_kinds = (
                WORKER_KINDS
                if row["kind"] == "worker"
                else (
                    "employer",
                    "employer_contact",
                    "employer_contact_details",
                    "worksite",
                    "employer_address",
                    "staffing_request",
                )
            )
            if dependencies != {
                name: {"id": str(finalized[f"{name}_id"]), "version": finalized[f"{name}_version"]}
                for name in output_kinds
                if finalized.get(f"{name}_disposition") == "reused"
            }:
                raise IntakeError("persistence_unavailable", 503)
            expected_results = 1 + sum(
                finalized.get(f"{name}_disposition") == "created" for name in output_kinds
            )
            result_count = session.scalar(
                select(func.count())
                .select_from(command_results)
                .where(command_results.c.command_id == command_id)
            )
            if (
                finalized["command_id"] != command_id
                or finalized["review_id"] != request.review_id
                or finalized["actor_id"] != principal.actor_id
                or finalized["result_version"] != receipt["result_record_version"]
                or receipt["result_entity_id"] != intake_id
                or row["lifecycle_status"] != "finalized"
                or row["version"] < receipt["result_record_version"]
                or result_count != expected_results
                or finalized["kind"] != row["kind"]
            ):
                raise IntakeError("persistence_unavailable", 503)
            result = {
                "command_id": str(command_id),
                "result_record_version": finalized["result_version"],
                "current": intake_detail(session, row, principal=principal),
                "finalization": finalization_outputs(finalized),
            }
            session.rollback()
            return result, True
        reused: dict[str, Any] = {}
        effective = row
        addresses: dict[str, Any] = {}
        if dependencies:
            if row["kind"] == "worker":
                snapshot = read_linked_snapshot(
                    session=session,
                    principal=principal,
                    kind="worker",
                    dependencies=dependencies,
                )
                if snapshot.dependency_stale:
                    raise IntakeError("dependency_changed")
                effective = {**row, "content": snapshot.content}
                addresses = snapshot.addresses
                reused = snapshot.current_dependencies
            else:
                reviewed = build_review_snapshot(session, principal, row, dependencies)
                effective = {**row, "content": reviewed["content"]}
                addresses = reviewed["addresses"]
                reused = dependencies
                # Canonical type can change between pre-key authorization and its lock.
                authorize_finalization_fields(session, principal, effective, dependencies)
        require_finalization_review(
            session=session,
            principal=principal,
            row=effective,
            request=request,
            dependency_refs=reused,
        )
        if row["kind"] == "worker":
            selected_interests(session, effective["content"], lock=True, require_current=True)
        missing = (
            missing_fields(session, effective, addresses=addresses)
            if reused
            else missing_fields(session, row)
        )
        if missing:
            if reused and row["kind"] == "worker":
                raise IntakeError("canonical_incomplete")
            if reused:
                canonical_fields = {"employer_type", "display_name"}
                if "employer_contact" in reused:
                    canonical_fields.update({"representative_name", "phone"})
                    if effective["content"]["employer_type"] == "household":
                        canonical_fields.add("party_address")
                if "employer_address" in reused:
                    canonical_fields.add("party_address")
                if "worksite" in reused:
                    canonical_fields.add("worksite_address")
                if canonical_fields.intersection(missing):
                    raise IntakeError("canonical_incomplete")
            raise IntakeError("incomplete", 422, missing_fields=missing)
        if not reused:
            addresses = {section: get_address(session, intake_id, section) for section in sections}
        absent = [section for section, address in addresses.items() if address is None]
        if absent:
            raise IntakeError("incomplete", 422, missing_fields=absent)
        now = clock.now()
        if reused and row["kind"] == "employer":
            identities = insert_employer_group(
                session,
                content=effective["content"],
                party_address=addresses.get("party_address"),
                worksite_address=addresses.get("worksite_address"),
                actor_id=principal.actor_id,
                now=now,
                reused=reused,
            )
        elif reused:
            identities = {}
        elif row["kind"] == "worker":
            identities = insert_worker_group(
                session,
                content=row["content"],
                address=addresses["worker_residence"] or {},
                actor_id=principal.actor_id,
                now=now,
            )
        else:
            identities = insert_new_employer_group(
                session,
                content=row["content"],
                party_address=addresses["party_address"],
                worksite_address=addresses["worksite_address"],
                actor_id=principal.actor_id,
                now=now,
            )
        previous = row["version"]
        row.update(
            version=previous + 1,
            lifecycle_status="finalized",
            updated_at=now,
            updated_by=principal.actor_id,
        )
        session.execute(
            update(intakes)
            .where(intakes.c.intake_id == intake_id)
            .values(
                version=row["version"],
                lifecycle_status="finalized",
                updated_at=now,
                updated_by=principal.actor_id,
            )
        )
        write_authority(
            session,
            principal=principal,
            command_id=command_id,
            command_type="finalize_intake",
            fingerprint=fingerprint,
            entity_type="intake",
            entity_id=intake_id,
            previous_version=previous,
            event_type="intake.finalized",
            event_id=uuid4(),
            now=now,
            changed=["lifecycle_status"],
        )
        changed_fields = {
            "worker": ["full_name"],
            "worker_contact": ["phone"],
            "worker_residence": sorted(addresses.get("worker_residence") or {}),
            "worker_preferences": ["interests", "availability", "self_reported"],
            "employer": ["employer_type", "display_name", "lifecycle_status", "source_channel"],
            "employer_contact": ["full_name"],
            "employer_contact_details": ["representative_name", "phone"]
            + (
                sorted(addresses.get("party_address") or {})
                if effective["content"].get("employer_type") == "household"
                else []
            ),
            "employer_address": ["purpose"] + sorted(addresses.get("party_address") or {}),
            "worksite": ["location_verification_status", "service_area_status", "map_area_status"]
            + sorted(addresses.get("worksite_address") or {}),
            "staffing_request": [
                "role_title",
                "duties_summary",
                "worker_count",
                "schedule",
                "offer",
                "request_type",
                "request_status",
                "source_channel",
            ],
        }
        finalized = {
            "intake_id": intake_id,
            "command_id": command_id,
            "review_id": request.review_id,
            "content_version": row["content_version"],
            "result_version": row["version"],
            "kind": row["kind"],
            "actor_id": principal.actor_id,
            "occurred_at": now,
        }
        for kind, identity in identities.items():
            write_result_authority(
                session,
                principal=principal,
                command_id=command_id,
                command_type="finalize_intake",
                entity_type=kind,
                entity_id=identity,
                previous_version=0,
                event_type=f"{kind}.created",
                event_id=uuid4(),
                now=now,
                changed=changed_fields[kind],
            )
            finalized.update(
                {f"{kind}_id": identity, f"{kind}_version": 1, f"{kind}_disposition": "created"}
            )
        for kind, reference in reused.items():
            finalized.update(
                {
                    f"{kind}_id": UUID(reference["id"]),
                    f"{kind}_version": reference["version"],
                    f"{kind}_disposition": "reused",
                }
            )
        session.execute(insert(intake_finalizations).values(**finalized))
        result = {
            "command_id": str(command_id),
            "result_record_version": row["version"],
            "current": intake_detail(session, row, principal=principal),
            "finalization": finalization_outputs(finalized),
        }
        session.commit()
        return result, False
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    except Exception:
        session.rollback()
        raise
