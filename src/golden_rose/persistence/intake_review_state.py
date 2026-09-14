"""Minimized current review and retained follow-up projections."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.models import (
    intake_follow_up_events,
    intake_reviews,
    work_interest_versions,
    work_interests,
)


def selected_interests(
    session: Session, content: dict[str, Any], *, lock: bool = False, require_current: bool = False
) -> bool:
    selections = content.get("interests", {}).get("selections", [])
    if not selections:
        return False
    from uuid import UUID

    ids = sorted((UUID(item["interest_id"]) for item in selections), key=str)
    stmt = (
        select(work_interests)
        .where(work_interests.c.interest_id.in_(ids))
        .order_by(work_interests.c.interest_id)
    )
    if lock:
        stmt = stmt.with_for_update()
    rows = {str(row["interest_id"]): row for row in session.execute(stmt).mappings()}
    historical_pairs = set(
        session.execute(
            select(work_interest_versions.c.interest_id, work_interest_versions.c.version).where(
                tuple_(work_interest_versions.c.interest_id, work_interest_versions.c.version).in_(
                    [(UUID(item["interest_id"]), item["catalog_version"]) for item in selections]
                )
            )
        ).all()
    )
    current = True
    for selection in selections:
        row = rows.get(str(selection["interest_id"]))
        if (
            row is None
            or (UUID(selection["interest_id"]), selection["catalog_version"])
            not in historical_pairs
        ):
            if lock:
                raise IntakeError("invalid_request", 422)
            return False
        if not row["active"] or row["version"] != selection["catalog_version"]:
            current = False
    if require_current and not current:
        raise IntakeError("incomplete", 422, missing_fields=["interests"])
    return current


def latest_follow_up(session: Session, intake_id: Any) -> dict[str, Any] | None:
    row = (
        session.execute(
            select(intake_follow_up_events)
            .where(intake_follow_up_events.c.intake_id == intake_id)
            .order_by(intake_follow_up_events.c.version.desc())
            .limit(1)
        )
        .mappings()
        .one_or_none()
    )
    return dict(row) if row else None


def review_projection(
    session: Session, row: dict[str, Any], now: datetime | None = None
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    latest = (
        session.execute(
            select(intake_reviews)
            .where(intake_reviews.c.intake_id == row["intake_id"])
            .order_by(intake_reviews.c.result_version.desc())
            .limit(1)
        )
        .mappings()
        .one_or_none()
    )
    result: dict[str, Any] = {"review_status": "unreviewed"}
    metadata = None
    if latest:
        result["review_status"] = (
            "needs_follow_up"
            if latest["outcome"] == "needs_follow_up"
            else (
                "current"
                if latest["reviewed_content_version"] == row["content_version"]
                else "stale"
            )
        )
        if (
            result["review_status"] == "current"
            and row["content"].get("interests", {}).get("selections")
            and not selected_interests(session, row["content"])
        ):
            result["review_status"] = "stale"
        metadata = {
            key: latest[key]
            for key in (
                "review_id",
                "reviewed_record_version",
                "reviewed_content_version",
                "outcome",
                "actor_id",
                "actor_display_name",
                "occurred_at",
            )
        }
    follow = latest_follow_up(session, row["intake_id"])
    if follow:
        result["follow_up"] = {
            "owner_staff_id": str(follow["owner_staff_id"]),
            "next_follow_up_at": follow["next_follow_up_at"].astimezone(UTC).isoformat(),
            "overdue": follow["next_follow_up_at"] < (now or datetime.now(UTC)),
        }
    return result, metadata
