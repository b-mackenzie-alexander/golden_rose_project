"""Read-only staff operations projection for dashboard modules."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.permissions import EMPLOYER_READ_PERMISSION, SHIFT_NEED_READ_PERMISSION
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    employers,
    intake_finalizations,
    shift_needs,
    staffing_requests,
)


def query_operations_projection(
    *,
    session: Session,
    principal: StaffPrincipal,
    page_size: int = 50,
) -> dict[str, object]:
    required = {EMPLOYER_READ_PERMISSION, "staffing_request:read", SHIFT_NEED_READ_PERMISSION}
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    bounded_page_size = min(max(page_size, 1), 50)
    try:
        request_rows = (
            session.execute(
                select(
                    intake_finalizations.c.intake_id.label("source_intake_id"),
                    staffing_requests.c.employer_id,
                    employers.c.display_name.label("employer_name"),
                    staffing_requests.c.staffing_request_id,
                    staffing_requests.c.request_status,
                    staffing_requests.c.role_title,
                    staffing_requests.c.worker_count,
                    staffing_requests.c.version,
                    staffing_requests.c.received_at,
                    staffing_requests.c.updated_at,
                )
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .outerjoin(
                    intake_finalizations,
                    (intake_finalizations.c.employer_id == staffing_requests.c.employer_id)
                    & (
                        intake_finalizations.c.staffing_request_id
                        == staffing_requests.c.staffing_request_id
                    ),
                )
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                )
                .order_by(
                    staffing_requests.c.updated_at.desc(),
                    staffing_requests.c.staffing_request_id.asc(),
                )
                .limit(bounded_page_size)
            )
            .mappings()
            .all()
        )
        shift_rows = (
            session.execute(
                select(
                    intake_finalizations.c.intake_id.label("source_intake_id"),
                    shift_needs.c.employer_id,
                    employers.c.display_name.label("employer_name"),
                    shift_needs.c.staffing_request_id,
                    shift_needs.c.shift_need_id,
                    staffing_requests.c.request_status,
                    shift_needs.c.shift_status,
                    shift_needs.c.role_title,
                    shift_needs.c.worker_count,
                    shift_needs.c.starts_at,
                    shift_needs.c.ends_at,
                    shift_needs.c.time_zone,
                    shift_needs.c.version,
                    shift_needs.c.updated_at,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .outerjoin(
                    intake_finalizations,
                    (intake_finalizations.c.employer_id == shift_needs.c.employer_id)
                    & (
                        intake_finalizations.c.staffing_request_id
                        == shift_needs.c.staffing_request_id
                    ),
                )
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .order_by(shift_needs.c.starts_at.asc(), shift_needs.c.shift_need_id.asc())
                .limit(bounded_page_size)
            )
            .mappings()
            .all()
        )
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    return {
        "request_items": [
            {
                "item_type": "staffing_request",
                **dict(row),
            }
            for row in request_rows
        ],
        "shift_items": [
            {
                "item_type": "shift_need",
                **dict(row),
            }
            for row in shift_rows
        ],
    }
