"""Immutable output identities; canonical field reads remain separate."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.models import intake_finalizations


def get_finalization(session: Session, intake_id: UUID) -> dict[str, Any]:
    row = (
        session.execute(
            select(intake_finalizations).where(intake_finalizations.c.intake_id == intake_id)
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise IntakeError("persistence_unavailable", 503)
    return dict(row)


def finalization_outputs(row: dict[str, Any]) -> dict[str, Any]:
    if row["kind"] == "employer":
        result: dict[str, Any] = {"kind": "employer"}
        for name, kind in (
            ("employer", "employer"),
            ("contact", "employer_contact"),
            ("contact_details", "employer_contact_details"),
            ("worksite", "worksite"),
            ("request", "staffing_request"),
            ("business_address", "employer_address"),
        ):
            result[name] = (
                None
                if row.get(f"{kind}_id") is None
                else {
                    "id": str(row[f"{kind}_id"]),
                    "version": row[f"{kind}_version"],
                    "disposition": row[f"{kind}_disposition"],
                }
            )
        return result
    return {
        "kind": "worker",
        **{
            name: {
                "id": str(row[f"{kind}_id"]),
                "version": row[f"{kind}_version"],
                "disposition": row[f"{kind}_disposition"],
            }
            for name, kind in (
                ("worker", "worker"),
                ("contact", "worker_contact"),
                ("residence", "worker_residence"),
                ("preferences", "worker_preferences"),
            )
        },
    }
