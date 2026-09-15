"""Protected correction and current-review evidence with current field authorization."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_review_schemas import ReviewedSnapshot
from golden_rose.application.correct_canonical_records import correction_target
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.canonical_corrections import SPECS
from golden_rose.persistence.canonical_reviews import authorized_finalization
from golden_rose.persistence.models import (
    canonical_correction_payloads,
    canonical_corrections,
    canonical_output_review_payloads,
    canonical_output_reviews,
)


def read_correction_history(
    *, session: Session, principal: StaffPrincipal, event_id: UUID
) -> dict[str, Any]:
    if "intake:restricted_history:read" not in principal.permissions:
        raise IntakeError("forbidden", 403)
    row = (
        session.execute(
            select(canonical_corrections).where(canonical_corrections.c.event_id == event_id)
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise IntakeError("not_found", 404)
    spec = SPECS[row["command_type"]]
    required = {p for p in spec.permissions if p.endswith(":read")}
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    target = (
        session.execute(
            select(spec.table).where(spec.table.c[f"{spec.entity}_id"] == row["entity_id"])
        )
        .mappings()
        .one_or_none()
    )
    if target is None:
        raise IntakeError("not_found", 404)
    parent_id = target["worker_id"] if spec.entity.startswith("worker") else target["employer_id"]
    if (
        spec.entity.startswith("worker")
        and principal.worker_scope is not None
        and parent_id not in principal.worker_scope
    ):
        raise IntakeError("not_found", 404)
    target_id = (
        target["employer_contact_id"]
        if spec.entity == "employer_contact_details"
        else row["entity_id"]
    )
    correction_target(session, spec, parent_id, target_id, lock=False)
    payload = (
        session.execute(
            select(canonical_correction_payloads).where(
                canonical_correction_payloads.c.event_id == event_id
            )
        )
        .mappings()
        .one_or_none()
    )
    if payload is None:
        raise IntakeError("persistence_unavailable", 503)
    return {
        "event_id": str(event_id),
        "target": {
            "entity_type": row["entity_type"],
            "id": str(row["entity_id"]),
            "current_version": target["version"],
        },
        "previous_version": row["previous_version"],
        "result_version": row["result_version"],
        "actor_id": str(row["actor_id"]),
        "occurred_at": row["occurred_at"].isoformat(),
        "corrects_event_id": str(row["corrects_event_id"]) if row["corrects_event_id"] else None,
        "reason_text": payload["reason_text"],
        "before": spec.model.model_validate(
            {
                "expected_version": row["previous_version"],
                "reason_text": payload["reason_text"],
                **payload["before"],
            }
        ).section_values(),
        "after": spec.model.model_validate(
            {
                "expected_version": row["previous_version"],
                "reason_text": payload["reason_text"],
                **payload["after"],
            }
        ).section_values(),
    }


def read_current_review_history(
    *, session: Session, principal: StaffPrincipal, intake_id: UUID, review_id: UUID
) -> dict[str, Any]:
    if "intake:restricted_history:read" not in principal.permissions:
        raise IntakeError("forbidden", 403)
    authorized_finalization(session, principal, intake_id)
    row = (
        session.execute(
            select(canonical_output_review_payloads)
            .join(
                canonical_output_reviews,
                canonical_output_reviews.c.review_id
                == canonical_output_review_payloads.c.review_id,
            )
            .where(
                canonical_output_reviews.c.intake_id == intake_id,
                canonical_output_reviews.c.review_id == review_id,
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise IntakeError("not_found", 404)
    return {
        "review_id": str(review_id),
        "reviewed_content": ReviewedSnapshot.model_validate(row["reviewed_content"]).model_dump(
            mode="json", exclude_none=True, exclude_unset=True
        ),
        "note": row["note"],
    }
