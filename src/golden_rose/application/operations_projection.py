"""Read-only staff operations projection for dashboard modules."""

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any, cast

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
    worksites,
)

AREA_BUCKETS: tuple[tuple[str, str], ...] = (
    ("bronx", "Bronx"),
    ("brooklyn", "Brooklyn"),
    ("manhattan", "Manhattan"),
    ("queens", "Queens"),
    ("staten_island", "Staten Island"),
)

LOCALITY_TO_AREA: dict[str, str] = {
    "bronx": "bronx",
    "brooklyn": "brooklyn",
    "kings": "brooklyn",
    "manhattan": "manhattan",
    "new york": "manhattan",
    "new york city": "manhattan",
    "queens": "queens",
    "staten island": "staten_island",
    "richmond": "staten_island",
}


def _empty_area_summary() -> dict[str, dict[str, int | str]]:
    return {
        key: {
            "area_key": key,
            "area_label": label,
            "request_count": 0,
            "shift_count": 0,
            "worker_slots": 0,
            "pending_review_count": 0,
        }
        for key, label in AREA_BUCKETS
    }


def _area_key(locality: object) -> str | None:
    if not isinstance(locality, str):
        return None
    normalized = " ".join(locality.strip().lower().replace("-", " ").split())
    if not normalized:
        return None
    return LOCALITY_TO_AREA.get(normalized)


def _build_area_and_report_summary(
    *,
    request_area_rows: Sequence[Mapping[str, Any]],
    shift_area_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, int | str]], dict[str, int]]:
    areas = _empty_area_summary()
    report = {
        "request_count": 0,
        "shift_count": 0,
        "worker_slots": 0,
        "pending_review_count": 0,
        "active_area_count": 0,
        "unmapped_request_count": 0,
    }
    for row in request_area_rows:
        report["request_count"] += 1
        key = _area_key(row.get("locality"))
        if key is None:
            report["unmapped_request_count"] += 1
            continue
        area = areas[key]
        area["request_count"] = int(area["request_count"]) + 1
        if row.get("request_status") == "pending_review":
            area["pending_review_count"] = int(area["pending_review_count"]) + 1
            report["pending_review_count"] += 1

    for row in shift_area_rows:
        report["shift_count"] += 1
        worker_slots = int(row.get("worker_count") or 0)
        report["worker_slots"] += worker_slots
        key = _area_key(row.get("locality"))
        if key is None:
            continue
        area = areas[key]
        area["shift_count"] = int(area["shift_count"]) + 1
        area["worker_slots"] = int(area["worker_slots"]) + worker_slots
        if row.get("shift_status") == "pending_review":
            area["pending_review_count"] = int(area["pending_review_count"]) + 1
            report["pending_review_count"] += 1

    area_items = [areas[key] for key, _label in AREA_BUCKETS]
    report["active_area_count"] = sum(
        1 for area in area_items if int(area["request_count"]) > 0 or int(area["shift_count"]) > 0
    )
    return area_items, report


def _build_calendar_summary(calendar_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "projected_shift_count": 0,
        "worker_slots": 0,
        "pending_review_shift_count": 0,
        "coverage_day_count": 0,
        "first_shift_starts_at": None,
        "last_shift_ends_at": None,
    }
    coverage_days: set[date] = set()
    first_shift: datetime | None = None
    last_shift: datetime | None = None
    for row in calendar_rows:
        starts_at = row.get("starts_at")
        ends_at = row.get("ends_at")
        if not isinstance(starts_at, datetime) or not isinstance(ends_at, datetime):
            continue
        if ends_at <= starts_at:
            continue
        summary["projected_shift_count"] += 1
        summary["worker_slots"] += int(row.get("worker_count") or 0)
        if row.get("shift_status") == "pending_review":
            summary["pending_review_shift_count"] += 1
        coverage_days.add(starts_at.date())
        if first_shift is None or starts_at < first_shift:
            first_shift = starts_at
        if last_shift is None or ends_at > last_shift:
            last_shift = ends_at
    summary["coverage_day_count"] = len(coverage_days)
    summary["first_shift_starts_at"] = first_shift
    summary["last_shift_ends_at"] = last_shift
    return summary


def _build_queue_summary(
    *,
    request_queue_rows: Sequence[Mapping[str, Any]],
    shift_queue_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "open_item_count": 0,
        "draft_count": 0,
        "pending_review_count": 0,
        "high_priority_count": 0,
        "oldest_item_updated_at": None,
        "newest_item_updated_at": None,
    }
    oldest_item: datetime | None = None
    newest_item: datetime | None = None

    def count_row(status: object, updated_at: object, *, high_priority: bool = False) -> None:
        nonlocal oldest_item, newest_item
        summary["open_item_count"] += 1
        if status == "draft":
            summary["draft_count"] += 1
        if status == "pending_review":
            summary["pending_review_count"] += 1
        if high_priority:
            summary["high_priority_count"] += 1
        if isinstance(updated_at, datetime):
            if oldest_item is None or updated_at < oldest_item:
                oldest_item = updated_at
            if newest_item is None or updated_at > newest_item:
                newest_item = updated_at

    for row in request_queue_rows:
        count_row(row.get("request_status"), row.get("updated_at"))
    for row in shift_queue_rows:
        status = row.get("shift_status")
        count_row(status, row.get("updated_at"), high_priority=status == "pending_review")

    summary["oldest_item_updated_at"] = oldest_item
    summary["newest_item_updated_at"] = newest_item
    return summary


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
        request_area_rows = (
            session.execute(
                select(
                    worksites.c.locality,
                    staffing_requests.c.request_status,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == worksites.c.employer_id)
                    & (staffing_requests.c.worksite_id == worksites.c.worksite_id),
                )
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        shift_area_rows = (
            session.execute(
                select(
                    worksites.c.locality,
                    shift_needs.c.shift_status,
                    shift_needs.c.worker_count,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(
                    worksites,
                    (worksites.c.employer_id == staffing_requests.c.employer_id)
                    & (worksites.c.worksite_id == staffing_requests.c.worksite_id),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        shift_calendar_rows = (
            session.execute(
                select(
                    shift_needs.c.shift_status,
                    shift_needs.c.worker_count,
                    shift_needs.c.starts_at,
                    shift_needs.c.ends_at,
                )
                .join(
                    staffing_requests,
                    (staffing_requests.c.employer_id == shift_needs.c.employer_id)
                    & (
                        staffing_requests.c.staffing_request_id == shift_needs.c.staffing_request_id
                    ),
                )
                .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        request_queue_rows = (
            session.execute(
                select(
                    staffing_requests.c.request_status,
                    staffing_requests.c.updated_at,
                )
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
        shift_queue_rows = (
            session.execute(
                select(
                    shift_needs.c.shift_status,
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
                .where(
                    employers.c.lifecycle_status == "draft",
                    staffing_requests.c.request_status.in_(("draft", "pending_review")),
                    shift_needs.c.shift_status.in_(("draft", "pending_review")),
                )
                .limit(500)
            )
            .mappings()
            .all()
        )
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    area_summary, report_summary = _build_area_and_report_summary(
        request_area_rows=cast(Sequence[Mapping[str, Any]], request_area_rows),
        shift_area_rows=cast(Sequence[Mapping[str, Any]], shift_area_rows),
    )
    calendar_summary = _build_calendar_summary(
        cast(Sequence[Mapping[str, Any]], shift_calendar_rows)
    )
    queue_summary = _build_queue_summary(
        request_queue_rows=cast(Sequence[Mapping[str, Any]], request_queue_rows),
        shift_queue_rows=cast(Sequence[Mapping[str, Any]], shift_queue_rows),
    )
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
        "area_summary": area_summary,
        "report_summary": report_summary,
        "calendar_summary": calendar_summary,
        "queue_summary": queue_summary,
    }
