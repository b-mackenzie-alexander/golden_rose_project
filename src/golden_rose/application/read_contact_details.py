"""Canonical contact sections under the existing shared employer read authority."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import employer_contact_details, employers


def read_contact_details(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    contact_id: UUID,
    address: bool = False,
) -> dict[str, Any]:
    required = {"employer:read", "employer_contact:read", "employer_contact:details:read"}
    if address:
        required.add("party_address:read")
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    table = employer_contact_details
    address_names = ("line1", "line2", "locality", "region", "postal_code", "country")
    names = address_names if address else ("employer_id", "employer_contact_id", "phone")
    statement = (
        select(
            table.c.employer_contact_details_id.label("contact_details_id"),
            table.c.version,
            *(table.c[name] for name in names),
        )
        .join(employers, employers.c.employer_id == table.c.employer_id)
        .where(
            table.c.employer_id == employer_id,
            table.c.employer_contact_id == contact_id,
            employers.c.lifecycle_status == "draft",
        )
    )
    if address:
        statement = statement.where(employers.c.employer_type == "household")
    try:
        row = session.execute(statement).mappings().one_or_none()
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    if row is None or (address and row["line1"] is None):
        raise IntakeError("not_found", 404)
    result = dict(row)
    if address:
        values = {name: result.pop(name) for name in address_names}
        result["address"] = {name: value for name, value in values.items() if value is not None}
    return result
