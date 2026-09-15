"""Current canonical output snapshots, retaining original identity and disposition."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intake_outputs import finalization_outputs, get_finalization
from golden_rose.persistence.models import (
    employer_addresses,
    employer_contact_details,
    employer_contacts,
    employers,
    intake_finalizations,
    staffing_requests,
    worker_contacts,
    worker_preferences,
    worker_residences,
    workers,
    worksites,
)

WORKER = {
    "worker": ("worker", workers),
    "contact": ("worker_contact", worker_contacts),
    "residence": ("worker_residence", worker_residences),
    "preferences": ("worker_preferences", worker_preferences),
}
EMPLOYER = {
    "employer": ("employer", employers),
    "contact": ("employer_contact", employer_contacts),
    "contact_details": ("employer_contact_details", employer_contact_details),
    "business_address": ("employer_address", employer_addresses),
    "worksite": ("worksite", worksites),
    "request": ("staffing_request", staffing_requests),
}
ADDRESS = ("line1", "line2", "locality", "region", "postal_code", "country")


def authorized_finalization(
    session: Session, principal: StaffPrincipal, intake_id: UUID
) -> dict[str, Any]:
    if "intake:read" not in principal.permissions:
        raise IntakeError("forbidden", 403)
    if principal.intake_scope is not None and intake_id not in principal.intake_scope:
        raise IntakeError("not_found", 404)
    if (
        session.scalar(
            select(intake_finalizations.c.intake_id).where(
                intake_finalizations.c.intake_id == intake_id
            )
        )
        is None
    ):
        raise IntakeError("not_found", 404)
    finalization = get_finalization(session, intake_id)
    required = (
        {"worker:read", "worker_contact:read", "worker_residence:read"}
        if finalization["kind"] == "worker"
        else {
            "employer:read",
            "employer_contact:read",
            "employer_contact:details:read",
            "party_address:read",
            "worksite:read",
            "worksite_address:read",
            "staffing_request:read",
        }
    )
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    if (
        finalization["kind"] == "worker"
        and principal.worker_scope is not None
        and finalization["worker_id"] not in principal.worker_scope
    ):
        raise IntakeError("not_found", 404)
    return finalization


def current_snapshot(
    session: Session, finalization: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    outputs = finalization_outputs(finalization)
    records = {}
    kinds = WORKER if outputs["kind"] == "worker" else EMPLOYER
    for name, (kind, table) in sorted(kinds.items(), key=lambda item: item[1][0]):
        if outputs[name] is None:
            continue
        query = select(table).where(table.c[f"{kind}_id"] == UUID(outputs[name]["id"]))
        if kind != "employer_contact":
            query = query.with_for_update()
        row = session.execute(query).mappings().one_or_none()
        if row is None:
            raise IntakeError("not_found", 404)
        records[name] = dict(row)
        outputs[name]["version"] = row["version"]

    def address(name: str) -> dict[str, Any]:
        if name not in records:
            return {}
        return {
            field: records[name][field] for field in ADDRESS if records[name][field] is not None
        }

    if outputs["kind"] == "worker":
        body = {
            "full_name": records["worker"]["full_name"],
            "phone": records["contact"]["phone"],
            "interests": records["preferences"]["interests"],
            "availability": records["preferences"]["availability"],
        }
        addresses = {"worker_residence": address("residence")}
    else:
        body = {
            "employer_type": records["employer"]["employer_type"],
            "display_name": records["employer"]["display_name"],
            "representative_name": records["contact_details"]["representative_name"],
            "phone": records["contact_details"]["phone"],
            **{
                field: records["request"][field]
                for field in ("role_title", "duties_summary", "worker_count", "schedule", "offer")
            },
        }
        addresses = {
            "party_address": address(
                "business_address" if body["employer_type"] == "business" else "contact_details"
            ),
            "worksite_address": address("worksite"),
        }
    return outputs, {"kind": outputs["kind"], "content": body, "addresses": addresses}
