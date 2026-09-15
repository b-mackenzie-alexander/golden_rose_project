"""Separate current-facts review; original intake/review/output evidence stays unchanged."""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.canonical_correction_schemas import (
    CanonicalReviewResponse,
    CanonicalReviewState,
    ReviewCanonicalOutputsRequest,
)
from golden_rose.api.staff.intake_review_schemas import ReviewedSnapshot
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_workflow_common import begin_command, write_authority
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.canonical_reviews import authorized_finalization, current_snapshot
from golden_rose.persistence.intake_review_state import selected_interests
from golden_rose.persistence.intakes import missing_fields
from golden_rose.persistence.models import (
    canonical_output_review_payloads,
    canonical_output_reviews,
    canonical_review_heads,
    entity_authorities,
)


def _head(session: Session, intake_id: UUID, *, lock: bool = False) -> dict[str, Any] | None:
    query = select(canonical_review_heads).where(canonical_review_heads.c.intake_id == intake_id)
    if lock:
        query = query.with_for_update()
    row = session.execute(query).mappings().one_or_none()
    return dict(row) if row else None


def _state(
    session: Session,
    head: dict[str, Any] | None,
    dependencies: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    status = "unreviewed"
    if head and head["version"]:
        prior = session.scalar(
            select(canonical_output_reviews.c.dependencies).where(
                canonical_output_reviews.c.review_id == head["latest_review_id"]
            )
        )
        current = prior == dependencies
        if snapshot["kind"] == "worker" and snapshot["content"].get("interests", {}).get(
            "selections"
        ):
            current = current and selected_interests(session, snapshot["content"])
        status = "current" if current else "stale"
    return CanonicalReviewState.model_validate(
        {
            "review_version": head["version"] if head else 0,
            "latest_review_id": head["latest_review_id"] if head else None,
            "status": status,
            "dependencies": dependencies,
        }
    ).model_dump(mode="json")


def read_current_review(
    *, session: Session, principal: StaffPrincipal, intake_id: UUID
) -> dict[str, Any]:
    try:
        finalization = authorized_finalization(session, principal, intake_id)
        head = _head(session, intake_id, lock=True)
        deps, snapshot = current_snapshot(session, finalization)
        result = _state(session, head, deps, snapshot)
        session.commit()
        return result
    except IntakeError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc


def execute_current_review(
    *,
    session: Session,
    principal: StaffPrincipal,
    intake_id: UUID,
    command_id: UUID,
    request: ReviewCanonicalOutputsRequest,
    clock: Clock,
) -> tuple[dict[str, Any], bool]:
    if "canonical:review" not in principal.permissions:
        raise IntakeError("forbidden", 403)
    try:
        finalization = authorized_finalization(session, principal, intake_id)
        fingerprint, receipt = begin_command(
            session,
            principal,
            command_id,
            "review_canonical_outputs",
            intake_id,
            request.to_content(),
        )
        session.execute(
            pg_insert(canonical_review_heads)
            .values(canonical_output_review_id=intake_id, intake_id=intake_id, version=0)
            .on_conflict_do_nothing(index_elements=[canonical_review_heads.c.intake_id])
        )
        head = _head(session, intake_id, lock=True)
        if head is None:
            raise IntakeError("persistence_unavailable", 503)
        deps, snapshot = current_snapshot(session, finalization)
        if receipt is not None:
            review_id = session.scalar(
                select(canonical_output_reviews.c.review_id).where(
                    canonical_output_reviews.c.command_id == command_id
                )
            )
            result = CanonicalReviewResponse.model_validate(
                {
                    "command_id": command_id,
                    "review_id": review_id,
                    "result_record_version": receipt["result_record_version"],
                    "current": _state(session, head, deps, snapshot),
                }
            ).model_dump(mode="json")
            session.commit()
            return result, True
        if head["version"] != request.expected_review_version:
            raise IntakeError("version_conflict")
        if request.expected_versions.model_dump(mode="json") != deps:
            raise IntakeError("dependency_changed")
        selected_interests(session, snapshot["content"], lock=True, require_current=True)
        missing = missing_fields(
            session,
            {"kind": snapshot["kind"], "content": snapshot["content"], "intake_id": intake_id},
            addresses=snapshot["addresses"],
        )
        if missing:
            raise IntakeError("incomplete", 422, missing_fields=missing)
        snapshot = ReviewedSnapshot.model_validate(snapshot).model_dump(
            mode="json", exclude_none=True, exclude_unset=True
        )
        now = clock.now()
        review_id, event_id = uuid4(), uuid4()
        version = head["version"] + 1
        if head["version"] == 0:
            session.execute(
                insert(entity_authorities).values(
                    entity_type="canonical_output_review",
                    entity_id=intake_id,
                    canonical_output_review_id=intake_id,
                )
            )
        session.execute(
            update(canonical_review_heads)
            .where(canonical_review_heads.c.intake_id == intake_id)
            .values(
                version=version,
                latest_review_id=review_id,
                updated_by=principal.actor_id,
                updated_at=now,
            )
        )
        write_authority(
            session,
            principal=principal,
            command_id=command_id,
            command_type="review_canonical_outputs",
            fingerprint=fingerprint,
            entity_type="canonical_output_review",
            entity_id=intake_id,
            previous_version=head["version"],
            event_type="canonical_output_review.reviewed",
            event_id=event_id,
            now=now,
            changed=["current_review"],
        )
        session.execute(
            insert(canonical_output_reviews).values(
                review_id=review_id,
                intake_id=intake_id,
                original_review_id=finalization["review_id"],
                command_id=command_id,
                event_id=event_id,
                result_version=version,
                actor_id=principal.actor_id,
                occurred_at=now,
                dependencies=deps,
            )
        )
        session.execute(
            insert(canonical_output_review_payloads).values(
                review_id=review_id, reviewed_content=snapshot, note=request.note
            )
        )
        head.update(version=version, latest_review_id=review_id)
        result = CanonicalReviewResponse.model_validate(
            {
                "command_id": command_id,
                "review_id": review_id,
                "result_record_version": version,
                "current": _state(session, head, deps, snapshot),
            }
        ).model_dump(mode="json")
        session.commit()
        return result, False
    except IntakeError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
