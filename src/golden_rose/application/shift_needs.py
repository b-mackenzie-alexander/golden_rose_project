"""Draft shift-need commands under governed staffing requests."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import insert, select, update
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.staff.employer_output_schemas import (
    CreateShiftNeedRequest,
    QueryShiftNeedsRequest,
    SubmitForReviewRequest,
)
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.read_employer_output import read_employer_output
from golden_rose.auth.permissions import (
    EMPLOYER_READ_PERMISSION,
    SHIFT_NEED_CREATE_PERMISSION,
    SHIFT_NEED_READ_PERMISSION,
    SHIFT_NEED_SUBMIT_REVIEW_PERMISSION,
    STAFFING_REQUEST_SUBMIT_REVIEW_PERMISSION,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    employers,
    shift_need_events,
    shift_needs,
    staffing_request_events,
    staffing_requests,
)


@dataclass(frozen=True, slots=True)
class ShiftNeedResult:
    payload: dict[str, object]
    replayed: bool


@dataclass(frozen=True, slots=True)
class StaffingRequestResult:
    payload: dict[str, object]
    replayed: bool


def _detail(row) -> dict[str, object]:
    return {
        "shift_need_id": row["shift_need_id"],
        "employer_id": row["employer_id"],
        "staffing_request_id": row["staffing_request_id"],
        "request_version_at_creation": row["request_version_at_creation"],
        "shift_status": row["shift_status"],
        "role_title": row["role_title"],
        "worker_count": row["worker_count"],
        "starts_at": row["starts_at"],
        "ends_at": row["ends_at"],
        "time_zone": row["time_zone"],
        "notes": row["notes"],
        "version": row["version"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _read_shift_need(
    *,
    session: Session,
    employer_id: UUID,
    request_id: UUID,
    shift_need_id: UUID,
) -> dict[str, object] | None:
    row = (
        session.execute(
            select(shift_needs)
            .join(employers, employers.c.employer_id == shift_needs.c.employer_id)
            .where(
                shift_needs.c.employer_id == employer_id,
                shift_needs.c.staffing_request_id == request_id,
                shift_needs.c.shift_need_id == shift_need_id,
                employers.c.lifecycle_status == "draft",
            )
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _detail(row)


def _require_read(principal: StaffPrincipal) -> None:
    required = {EMPLOYER_READ_PERMISSION, "staffing_request:read", SHIFT_NEED_READ_PERMISSION}
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)


def query_shift_needs(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    request_id: UUID,
    request: QueryShiftNeedsRequest,
) -> dict[str, object]:
    _require_read(principal)
    try:
        parent = session.execute(
            select(staffing_requests.c.staffing_request_id)
            .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
            .where(
                staffing_requests.c.employer_id == employer_id,
                staffing_requests.c.staffing_request_id == request_id,
                staffing_requests.c.request_status.in_(("draft", "pending_review")),
                employers.c.lifecycle_status == "draft",
            )
        ).one_or_none()
        if parent is None:
            raise IntakeError("not_found", 404)
        rows = (
            session.execute(
                select(shift_needs)
                .where(
                    shift_needs.c.employer_id == employer_id,
                    shift_needs.c.staffing_request_id == request_id,
                )
                .order_by(shift_needs.c.starts_at.asc(), shift_needs.c.shift_need_id.asc())
                .limit(request.page_size)
            )
            .mappings()
            .all()
        )
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    return {"items": [_detail(row) for row in rows]}


def read_shift_need(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    request_id: UUID,
    shift_need_id: UUID,
) -> dict[str, object]:
    _require_read(principal)
    try:
        detail = _read_shift_need(
            session=session,
            employer_id=employer_id,
            request_id=request_id,
            shift_need_id=shift_need_id,
        )
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    if detail is None:
        raise IntakeError("not_found", 404)
    return detail


def create_shift_need(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    request_id: UUID,
    command_id: UUID,
    body: CreateShiftNeedRequest,
    now: datetime,
) -> ShiftNeedResult:
    required = {
        EMPLOYER_READ_PERMISSION,
        "staffing_request:read",
        SHIFT_NEED_CREATE_PERMISSION,
        SHIFT_NEED_READ_PERMISSION,
    }
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    if body.starts_at.tzinfo is None or body.ends_at.tzinfo is None:
        raise IntakeError("invalid_request", 422)
    if body.starts_at >= body.ends_at:
        raise IntakeError("invalid_request", 422)
    try:
        ZoneInfo(body.time_zone)
    except ZoneInfoNotFoundError as exc:
        raise IntakeError("invalid_request", 422) from exc

    try:
        existing = (
            session.execute(
                select(shift_need_events)
                .where(shift_need_events.c.command_id == command_id)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            if (
                existing["actor_id"] != principal.actor_id
                or existing["employer_id"] != employer_id
                or existing["staffing_request_id"] != request_id
            ):
                raise IntakeError("conflict", 409)
            detail = _read_shift_need(
                session=session,
                employer_id=employer_id,
                request_id=request_id,
                shift_need_id=existing["shift_need_id"],
            )
            if detail is None:
                raise IntakeError("not_found", 404)
            return ShiftNeedResult(
                {
                    "command_id": command_id,
                    "result_record_version": existing["new_version"],
                    "event_type": existing["event_type"],
                    "current": detail,
                },
                True,
            )

        try:
            parent = (
                session.execute(
                    select(
                        staffing_requests.c.version,
                        staffing_requests.c.role_title,
                        staffing_requests.c.worker_count,
                    )
                    .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                    .where(
                        staffing_requests.c.employer_id == employer_id,
                        staffing_requests.c.staffing_request_id == request_id,
                        staffing_requests.c.request_status == "draft",
                        employers.c.lifecycle_status == "draft",
                    )
                    .with_for_update()
                )
                .mappings()
                .one()
            )
        except NoResultFound as exc:
            raise IntakeError("not_found", 404) from exc

        if parent["version"] != body.expected_request_version:
            raise IntakeError("stale", 412)
        if body.worker_count > parent["worker_count"]:
            raise IntakeError("invalid_request", 422)

        shift_need_id = uuid4()
        row = {
            "shift_need_id": shift_need_id,
            "employer_id": employer_id,
            "staffing_request_id": request_id,
            "request_version_at_creation": parent["version"],
            "shift_status": "draft",
            "role_title": body.role_title,
            "worker_count": body.worker_count,
            "starts_at": body.starts_at,
            "ends_at": body.ends_at,
            "time_zone": body.time_zone,
            "notes": body.notes,
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "created_by": principal.actor_id,
            "updated_by": principal.actor_id,
        }
        session.execute(insert(shift_needs).values(row))
        session.execute(
            insert(shift_need_events).values(
                event_id=uuid4(),
                command_id=command_id,
                shift_need_id=shift_need_id,
                employer_id=employer_id,
                staffing_request_id=request_id,
                actor_id=principal.actor_id,
                event_type="shift_need.created",
                previous_status=None,
                new_status="draft",
                previous_version=None,
                new_version=1,
                request_version=parent["version"],
                occurred_at=now,
                reason_text=body.reason_text,
            )
        )
        session.commit()
    except IntakeError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc

    return ShiftNeedResult(
        {
            "command_id": command_id,
            "result_record_version": 1,
            "event_type": "shift_need.created",
            "current": _detail(row),
        },
        False,
    )


def submit_shift_need_for_review(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    request_id: UUID,
    shift_need_id: UUID,
    command_id: UUID,
    body: SubmitForReviewRequest,
    now: datetime,
) -> ShiftNeedResult:
    required = {
        EMPLOYER_READ_PERMISSION,
        "staffing_request:read",
        SHIFT_NEED_READ_PERMISSION,
        SHIFT_NEED_SUBMIT_REVIEW_PERMISSION,
    }
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    try:
        existing = (
            session.execute(
                select(shift_need_events)
                .where(shift_need_events.c.command_id == command_id)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            if (
                existing["event_type"] != "shift_need.submitted_for_review"
                or existing["actor_id"] != principal.actor_id
                or existing["employer_id"] != employer_id
                or existing["staffing_request_id"] != request_id
                or existing["shift_need_id"] != shift_need_id
            ):
                raise IntakeError("conflict", 409)
            detail = _read_shift_need(
                session=session,
                employer_id=employer_id,
                request_id=request_id,
                shift_need_id=shift_need_id,
            )
            if detail is None:
                raise IntakeError("not_found", 404)
            return ShiftNeedResult(
                {
                    "command_id": command_id,
                    "result_record_version": existing["new_version"],
                    "event_type": existing["event_type"],
                    "current": detail,
                },
                True,
            )

        row = (
            session.execute(
                select(
                    shift_needs.c.shift_status,
                    shift_needs.c.version,
                    shift_needs.c.starts_at,
                    shift_needs.c.ends_at,
                    shift_needs.c.time_zone,
                    staffing_requests.c.request_status,
                    staffing_requests.c.version.label("request_version"),
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
                    shift_needs.c.employer_id == employer_id,
                    shift_needs.c.staffing_request_id == request_id,
                    shift_needs.c.shift_need_id == shift_need_id,
                    staffing_requests.c.request_status == "draft",
                    employers.c.lifecycle_status == "draft",
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise IntakeError("not_found", 404)
        if row["shift_status"] != "draft":
            raise IntakeError("conflict", 409)
        if row["version"] != body.expected_version:
            raise IntakeError("stale", 412)
        if row["starts_at"] >= row["ends_at"]:
            raise IntakeError("invalid_request", 422)
        try:
            ZoneInfo(row["time_zone"])
        except ZoneInfoNotFoundError as exc:
            raise IntakeError("invalid_request", 422) from exc

        new_version = row["version"] + 1
        session.execute(
            update(shift_needs)
            .where(
                shift_needs.c.employer_id == employer_id,
                shift_needs.c.staffing_request_id == request_id,
                shift_needs.c.shift_need_id == shift_need_id,
                shift_needs.c.version == row["version"],
                shift_needs.c.shift_status == "draft",
            )
            .values(
                shift_status="pending_review",
                version=new_version,
                updated_at=now,
                updated_by=principal.actor_id,
            )
        )
        session.execute(
            insert(shift_need_events).values(
                event_id=uuid4(),
                command_id=command_id,
                shift_need_id=shift_need_id,
                employer_id=employer_id,
                staffing_request_id=request_id,
                actor_id=principal.actor_id,
                event_type="shift_need.submitted_for_review",
                previous_status="draft",
                new_status="pending_review",
                previous_version=row["version"],
                new_version=new_version,
                request_version=row["request_version"],
                occurred_at=now,
                reason_text=body.reason_text,
            )
        )
        session.commit()
        detail = _read_shift_need(
            session=session,
            employer_id=employer_id,
            request_id=request_id,
            shift_need_id=shift_need_id,
        )
        if detail is None:
            raise IntakeError("not_found", 404)
    except IntakeError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc

    return ShiftNeedResult(
        {
            "command_id": command_id,
            "result_record_version": new_version,
            "event_type": "shift_need.submitted_for_review",
            "current": detail,
        },
        False,
    )


def submit_staffing_request_for_review(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    request_id: UUID,
    command_id: UUID,
    body: SubmitForReviewRequest,
    now: datetime,
) -> StaffingRequestResult:
    required = {
        EMPLOYER_READ_PERMISSION,
        "staffing_request:read",
        SHIFT_NEED_READ_PERMISSION,
        STAFFING_REQUEST_SUBMIT_REVIEW_PERMISSION,
    }
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    try:
        existing = (
            session.execute(
                select(staffing_request_events)
                .where(staffing_request_events.c.command_id == command_id)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            if (
                existing["actor_id"] != principal.actor_id
                or existing["employer_id"] != employer_id
                or existing["staffing_request_id"] != request_id
            ):
                raise IntakeError("conflict", 409)
            detail = read_employer_output(
                session=session,
                principal=principal,
                employer_id=employer_id,
                output_id=request_id,
                section="request",
            )
            return StaffingRequestResult(
                {
                    "command_id": command_id,
                    "result_record_version": existing["new_version"],
                    "event_type": existing["event_type"],
                    "current": detail,
                },
                True,
            )

        row = (
            session.execute(
                select(staffing_requests.c.request_status, staffing_requests.c.version)
                .join(employers, employers.c.employer_id == staffing_requests.c.employer_id)
                .where(
                    staffing_requests.c.employer_id == employer_id,
                    staffing_requests.c.staffing_request_id == request_id,
                    employers.c.lifecycle_status == "draft",
                )
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise IntakeError("not_found", 404)
        if row["request_status"] != "draft":
            raise IntakeError("conflict", 409)
        if row["version"] != body.expected_version:
            raise IntakeError("stale", 412)
        child = session.execute(
            select(shift_needs.c.shift_need_id)
            .where(
                shift_needs.c.employer_id == employer_id,
                shift_needs.c.staffing_request_id == request_id,
                shift_needs.c.shift_status == "pending_review",
            )
            .limit(1)
        ).one_or_none()
        if child is None:
            raise IntakeError("invalid_request", 422)

        new_version = row["version"] + 1
        session.execute(
            update(staffing_requests)
            .where(
                staffing_requests.c.employer_id == employer_id,
                staffing_requests.c.staffing_request_id == request_id,
                staffing_requests.c.version == row["version"],
                staffing_requests.c.request_status == "draft",
            )
            .values(
                request_status="pending_review",
                version=new_version,
                updated_at=now,
                updated_by=principal.actor_id,
            )
        )
        session.execute(
            insert(staffing_request_events).values(
                event_id=uuid4(),
                command_id=command_id,
                staffing_request_id=request_id,
                employer_id=employer_id,
                actor_id=principal.actor_id,
                event_type="staffing_request.submitted_for_review",
                previous_status="draft",
                new_status="pending_review",
                previous_version=row["version"],
                new_version=new_version,
                occurred_at=now,
                reason_text=body.reason_text,
            )
        )
        session.commit()
        detail = read_employer_output(
            session=session,
            principal=principal,
            employer_id=employer_id,
            output_id=request_id,
            section="request",
        )
    except IntakeError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc

    return StaffingRequestResult(
        {
            "command_id": command_id,
            "result_record_version": new_version,
            "event_type": "staffing_request.submitted_for_review",
            "current": detail,
        },
        False,
    )
