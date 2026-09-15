"""Minimized authoritative reads; no commit authority in persistence helpers."""

from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy import and_, exists, select
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intake_outputs import finalization_outputs, get_finalization
from golden_rose.persistence.intake_review_state import review_projection, selected_interests
from golden_rose.persistence.models import (
    audit_events,
    command_results,
    intake_addresses,
    intake_links,
    intakes,
)


def get_intake(session: Session, intake_id: UUID, *, lock: bool = False) -> dict[str, Any]:
    # The existence probe also works on predecessor schemas with closed link storage.
    stmt = select(
        intakes,
        exists().where(intake_links.c.intake_id == intakes.c.intake_id).label("_has_link_row"),
    ).where(intakes.c.intake_id == intake_id)
    if lock:
        stmt = stmt.with_for_update()
    row = session.execute(stmt).mappings().one_or_none()
    if row is None:
        raise IntakeError("not_found", 404)
    result = dict(row)
    proof = session.execute(
        select(command_results.c.command_id)
        .join(
            audit_events,
            and_(
                audit_events.c.command_id == command_results.c.command_id,
                audit_events.c.entity_id == command_results.c.entity_id,
                audit_events.c.entity_type == command_results.c.entity_type,
                audit_events.c.new_record_version == command_results.c.result_version,
                audit_events.c.actor_id == command_results.c.actor_id,
                audit_events.c.event_type == command_results.c.event_type,
            ),
        )
        .where(
            command_results.c.entity_type == "intake",
            command_results.c.entity_id == intake_id,
            command_results.c.result_version == row["version"],
            command_results.c.actor_id == row["updated_by"],
        )
    ).scalar_one_or_none()
    if proof is None:
        raise IntakeError("persistence_unavailable", 503)
    return result


def get_address(session: Session, intake_id: UUID, section: str) -> dict[str, str] | None:
    row = (
        session.execute(
            select(intake_addresses).where(
                intake_addresses.c.intake_id == intake_id,
                intake_addresses.c.section == section,
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    values = {
        key: value
        for key, value in row.items()
        if key not in {"intake_id", "section"} and value is not None
    }
    return values or None


def address_complete(address: dict[str, str] | None) -> bool:
    if not address:
        return False
    fields = {"line1", "locality", "country"}
    if address.get("country") == "US":
        fields |= {"region", "postal_code"}
    return all(address.get(field) for field in fields)


def missing_fields(
    session: Session,
    row: dict[str, Any],
    *,
    addresses: dict[str, dict[str, str]] | None = None,
    address_completeness: dict[str, bool] | None = None,
) -> list[str]:
    content = row["content"]
    if row["kind"] == "worker":
        missing = [f for f in ("full_name", "phone") if not content.get(f)]
        interests = content.get("interests", {})
        if interests.get("selections"):
            if not selected_interests(session, content):
                missing.append("interests")
        elif not interests.get("other_description"):
            missing.append("interests")
        if content.get("availability", {}).get("mode", "unknown") == "unknown":
            missing.append("availability")
        sections = ["worker_residence"]
    else:
        missing = [
            f
            for f in (
                "employer_type",
                "display_name",
                "representative_name",
                "phone",
                "role_title",
                "duties_summary",
                "worker_count",
            )
            if not content.get(f)
        ]
        if content.get("schedule", {}).get("mode", "unknown") == "unknown":
            missing.append("schedule")
        offer = content.get("offer", {})
        if not all(
            offer.get(k) is not None for k in ("minimum", "currency", "basis", "per_worker")
        ):
            missing.append("offer")
        sections = ["party_address", "worksite_address"]
    for section in sections:
        if address_completeness is not None and section in address_completeness:
            if not address_completeness[section]:
                missing.append(section)
            continue
        address = (
            get_address(session, row["intake_id"], section)
            if addresses is None
            else addresses.get(section)
        )
        if not address_complete(address):
            missing.append(section)
    return missing


def intake_summary(session: Session, row: dict[str, Any]) -> dict[str, Any]:
    missing = missing_fields(session, row)
    result = {
        "intake_id": str(row["intake_id"]),
        "kind": row["kind"],
        "version": row["version"],
        "lifecycle": row["lifecycle_status"],
        "complete": not missing,
        "missing_fields": missing,
        "review_status": "unreviewed",
        "updated_at": row["updated_at"].astimezone(UTC).isoformat(),
    }
    name = row["content"].get("full_name" if row["kind"] == "worker" else "display_name")
    if name:
        result["display_name"] = name
    if row["content"].get("offer"):
        result["offer"] = {k: v for k, v in row["content"]["offer"].items() if k != "terms"}
    result.update(review_projection(session, row)[0])
    return result


def _populate_linked_detail(
    session: Session, row: dict[str, Any], principal: StaffPrincipal | None, result: dict[str, Any]
) -> None:
    # Import here to keep command/schema imports out of the base read module.
    from golden_rose.application.intake_resolved_detail import resolved_detail_fields

    if principal is None:
        raise IntakeError("forbidden", 403)
    resolved, complete, dependencies, stale = resolved_detail_fields(session, principal, row)
    if dependencies:
        content = dict(row["content"]) if row["kind"] == "employer" else {}
        if row["kind"] == "employer":
            for field in ("employer_type", "display_name"):
                content.pop(field, None)
            if "employer_contact" in dependencies:
                for field in ("representative_name", "phone"):
                    content.pop(field, None)
        content.update(resolved)
        missing = missing_fields(
            session, {**row, "content": content}, address_completeness=complete
        )
        result.update(resolved=resolved, links=dependencies, dependency_stale=stale)
        result["summary"].update(complete=not missing, missing_fields=missing)
        display_name = resolved.get("full_name" if row["kind"] == "worker" else "display_name")
        result["summary"].pop("display_name", None)
        if display_name:
            result["summary"]["display_name"] = display_name
        if stale and result["summary"]["review_status"] == "current":
            result["summary"]["review_status"] = "stale"


def intake_query_summary(
    session: Session, row: dict[str, Any], principal: StaffPrincipal
) -> dict[str, Any]:
    result = {"summary": intake_summary(session, row)}
    if row.get("_has_link_row"):
        try:
            _populate_linked_detail(session, row, principal, result)
        except IntakeError as error:
            if error.status not in {403, 404}:
                raise
            # Retain authorized intake recovery metadata without substituting
            # candidate completeness or leaking canonical names after revocation.
            result["summary"].pop("display_name", None)
            result["summary"].update(complete=None, missing_fields=[])
    return result["summary"]


def intake_detail(
    session: Session,
    row: dict[str, Any],
    *,
    principal: StaffPrincipal | None = None,
) -> dict[str, Any]:
    result = {
        "summary": intake_summary(session, row),
        "content_version": row["content_version"],
        "candidate": row["content"],
        "resolved": {},
        "links": {},
        "dependency_stale": False,
    }

    if row.get("_has_link_row"):
        _populate_linked_detail(session, row, principal, result)

    latest = review_projection(session, row)[1]
    if latest is not None:
        result["latest_review"] = latest
    if row["lifecycle_status"] == "finalized":
        result["finalization"] = finalization_outputs(get_finalization(session, row["intake_id"]))
    return result
