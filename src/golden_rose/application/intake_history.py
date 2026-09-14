"""Minimized attributable history and bounded assignment options."""

from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_review_schemas import PageRequest
from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_cursors import binding, decode_cursor, encode_cursor
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.review_intake import authorize_snapshot, review_sections
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_directory import StaffDirectory
from golden_rose.persistence.intakes import get_intake
from golden_rose.persistence.models import (
    audit_events,
    intake_follow_up_events,
    intake_history_payloads,
    intake_review_payloads,
    intake_reviews,
)


def query_history(
    *,
    session: Session,
    principal: StaffPrincipal,
    directory: StaffDirectory,
    intake_id: UUID,
    request: PageRequest,
) -> dict[str, Any]:
    authorize_intake(principal, "intake:read", intake_id=intake_id)
    get_intake(session, intake_id)
    bound = binding(
        principal,
        {"route": "intake-history", "intake_id": str(intake_id), "page_size": request.page_size},
    )
    position = decode_cursor(request.cursor, bound)
    stmt = select(audit_events).where(
        audit_events.c.entity_type == "intake", audit_events.c.entity_id == intake_id
    )
    if position:
        try:
            version, event_id = position["version"], UUID(position["id"])
            if type(version) is not int or version < 1:
                raise ValueError
        except (ValueError, KeyError, TypeError) as exc:
            raise IntakeError("invalid_cursor", 422) from exc
        stmt = stmt.where(
            or_(
                audit_events.c.new_record_version < version,
                and_(
                    audit_events.c.new_record_version == version,
                    audit_events.c.audit_event_id < event_id,
                ),
            )
        )
    rows = (
        session.execute(
            stmt.order_by(
                audit_events.c.new_record_version.desc(), audit_events.c.audit_event_id.desc()
            ).limit(request.page_size + 1)
        )
        .mappings()
        .all()
    )
    selected = rows[: request.page_size]
    ids = [row["audit_event_id"] for row in selected]
    reviews = {
        row["event_id"]: row
        for row in session.execute(
            select(intake_reviews).where(intake_reviews.c.event_id.in_(ids))
        ).mappings()
    }
    follows = {
        row["event_id"]: row
        for row in session.execute(
            select(intake_follow_up_events).where(intake_follow_up_events.c.event_id.in_(ids))
        ).mappings()
    }
    # Content version is a count of material fact commands, not aggregate sequence.
    prior = audit_events.alias("prior_content_events")
    content_count = (
        select(func.count())
        .select_from(prior)
        .where(
            prior.c.entity_type == "intake",
            prior.c.entity_id == intake_id,
            prior.c.new_record_version <= audit_events.c.new_record_version,
            prior.c.event_type.in_(["intake.created", "intake.revised", "intake.linked"]),
        )
        .correlate(audit_events)
        .scalar_subquery()
    )
    content_at: dict[int, int] = dict(
        session.execute(
            select(audit_events.c.new_record_version, content_count).where(
                audit_events.c.audit_event_id.in_(ids)
            )
        )
        .tuples()
        .all()
    )
    items = []
    for row in selected:
        review, follow = reviews.get(row["audit_event_id"]), follows.get(row["audit_event_id"])
        item = {
            "event_id": str(row["audit_event_id"]),
            "version": row["new_record_version"],
            "content_version": content_at[row["new_record_version"]],
            "event_type": row["event_type"],
            "actor_id": str(row["actor_id"]),
            "actor_display_name": review["actor_display_name"]
            if review
            else (
                follow["actor_display_name"] if follow else directory.display_name(row["actor_id"])
            ),
            "occurred_at": row["occurred_at"].isoformat(),
        }
        if review:
            item.update(review_id=str(review["review_id"]), outcome=review["outcome"])
        if follow:
            item.update(
                owner_staff_id=str(follow["owner_staff_id"]),
                next_follow_up_at=follow["next_follow_up_at"].isoformat(),
            )
        items.append(item)
    cursor = (
        encode_cursor(
            bound,
            {
                "version": selected[-1]["new_record_version"],
                "id": str(selected[-1]["audit_event_id"]),
            },
        )
        if len(rows) > request.page_size
        else None
    )
    return {"items": items, "next_cursor": cursor}


def read_restricted_history(
    *, session: Session, principal: StaffPrincipal, intake_id: UUID, event_id: UUID
) -> dict[str, Any]:
    authorize_intake(principal, "intake:restricted_history:read", intake_id=intake_id)
    row = get_intake(session, intake_id)
    authorize_snapshot(principal, row["kind"])
    event = session.execute(
        select(audit_events.c.audit_event_id).where(
            audit_events.c.audit_event_id == event_id,
            audit_events.c.entity_type == "intake",
            audit_events.c.entity_id == intake_id,
        )
    ).scalar_one_or_none()
    if event is None:
        raise IntakeError("not_found", 404)
    review = (
        session.execute(
            select(intake_review_payloads)
            .join(intake_reviews, intake_reviews.c.review_id == intake_review_payloads.c.review_id)
            .where(intake_reviews.c.event_id == event_id)
        )
        .mappings()
        .one_or_none()
    )
    follow = (
        session.execute(
            select(
                intake_history_payloads.c.reason_text,
                intake_history_payloads.c.note,
                intake_follow_up_events.c.action,
                intake_follow_up_events.c.reason_code,
                intake_follow_up_events.c.method,
                intake_follow_up_events.c.outcome,
                intake_follow_up_events.c.time_zone,
            )
            .join(
                intake_follow_up_events,
                intake_follow_up_events.c.event_id == intake_history_payloads.c.event_id,
            )
            .where(intake_history_payloads.c.event_id == event_id)
        )
        .mappings()
        .one_or_none()
    )
    if review is None and follow is None:
        raise IntakeError("not_found", 404)
    result: dict[str, Any] = {"event_id": str(event_id)}
    if review:
        snapshot = review["reviewed_content"]
        if (
            snapshot["content"].get("interests", {}).get("selections")
            and "work_interest:read" not in principal.permissions
        ):
            raise IntakeError("forbidden", 403)
        result["reviewed_content"] = {
            **snapshot,
            "addresses": {
                section: snapshot["addresses"].get(section)
                for section in review_sections(snapshot["kind"])
            },
        }
        if review["note"] is not None:
            result["note"] = review["note"]
    if follow:
        result["follow_up"] = {
            key: follow[key]
            for key in ("action", "reason_code", "reason_text", "method", "outcome", "time_zone")
            if follow[key] is not None
        }
        if follow["note"] is not None:
            result["note"] = follow["note"]
    return result


def query_follow_up_owners(
    *,
    session: Session,
    principal: StaffPrincipal,
    directory: StaffDirectory,
    intake_id: UUID,
    request: PageRequest,
) -> dict[str, Any]:
    authorize_intake(principal, "intake:follow_up", intake_id=intake_id)
    get_intake(session, intake_id)
    eligible = sorted(
        (
            entry
            for entry in directory.entries
            if entry.eligible(intake_id, frozenset({"intake:read", "intake:follow_up"}))
        ),
        key=lambda entry: str(entry.staff_id),
    )
    bound = binding(
        principal,
        {
            "route": "follow-up-owners",
            "intake_id": str(intake_id),
            "page_size": request.page_size,
            "directory": [
                {
                    "id": str(entry.staff_id),
                    "name": entry.display_name,
                    "permissions": sorted(entry.permissions),
                    "scope": None
                    if entry.intake_scope is None
                    else sorted(map(str, entry.intake_scope)),
                }
                for entry in eligible
            ],
        },
    )
    position = decode_cursor(request.cursor, bound)
    if position:
        if set(position) != {"id"} or not any(
            str(entry.staff_id) == position["id"] for entry in eligible
        ):
            raise IntakeError("invalid_cursor", 422)
        eligible = [entry for entry in eligible if str(entry.staff_id) > position["id"]]
    selected = eligible[: request.page_size]
    cursor = (
        encode_cursor(bound, {"id": str(selected[-1].staff_id)})
        if len(eligible) > request.page_size
        else None
    )
    return {
        "items": [
            {"staff_id": str(entry.staff_id), "display_name": entry.display_name}
            for entry in selected
        ],
        "next_cursor": cursor,
    }
