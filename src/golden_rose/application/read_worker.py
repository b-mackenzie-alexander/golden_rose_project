"""Permission-separated exact canonical reads; no intake snapshot overlay."""

from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    worker_contacts,
    worker_preferences,
    worker_residences,
    workers,
)

WorkerSection = Literal["identity", "contact", "residence", "preferences"]


def read_worker(
    *,
    session: Session,
    principal: StaffPrincipal,
    worker_id: UUID,
    section: WorkerSection,
) -> dict[str, Any]:
    required = {"worker:read"}
    if section == "contact":
        required.add("worker_contact:read")
    elif section == "residence":
        required.add("worker_residence:read")
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    if principal.worker_scope is not None and worker_id not in principal.worker_scope:
        raise IntakeError("not_found", 404)
    if section == "identity":
        statement = (
            select(
                workers.c.worker_id,
                workers.c.full_name,
                workers.c.version,
                worker_contacts.c.worker_contact_id.label("contact_id"),
                worker_residences.c.worker_residence_id.label("residence_id"),
                worker_preferences.c.worker_preferences_id.label("preferences_id"),
                workers.c.created_at,
                workers.c.updated_at,
            )
            .select_from(workers)
            .join(worker_contacts, worker_contacts.c.worker_id == workers.c.worker_id)
            .join(worker_residences, worker_residences.c.worker_id == workers.c.worker_id)
            .join(worker_preferences, worker_preferences.c.worker_id == workers.c.worker_id)
            .where(workers.c.worker_id == worker_id)
        )
    else:
        table, names = {
            "contact": (worker_contacts, ("worker_contact_id", "worker_id", "version", "phone")),
            "residence": (
                worker_residences,
                (
                    "worker_residence_id",
                    "worker_id",
                    "version",
                    "line1",
                    "line2",
                    "locality",
                    "region",
                    "postal_code",
                    "country",
                ),
            ),
            "preferences": (
                worker_preferences,
                (
                    "worker_preferences_id",
                    "worker_id",
                    "version",
                    "interests",
                    "availability",
                    "self_reported",
                ),
            ),
        }[section]
        statement = select(*(table.c[name] for name in names)).where(table.c.worker_id == worker_id)
    try:
        row = session.execute(statement).mappings().one_or_none()
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    if row is None:
        raise IntakeError("not_found", 404)
    result = dict(row)
    if section == "residence":
        address = {
            name: result.pop(name)
            for name in (
                "line1",
                "line2",
                "locality",
                "region",
                "postal_code",
                "country",
            )
        }
        result["address"] = {name: value for name, value in address.items() if value is not None}
    return result
