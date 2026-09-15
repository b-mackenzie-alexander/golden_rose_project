"""Exact canonical employer output reads under existing shared parent authority."""

from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    employer_addresses,
    employers,
    staffing_requests,
    worksites,
)

EmployerOutputSection = Literal["business_address", "worksite", "worksite_address", "request"]


def read_employer_output(
    *,
    session: Session,
    principal: StaffPrincipal,
    employer_id: UUID,
    output_id: UUID,
    section: EmployerOutputSection,
) -> dict[str, Any]:
    required = {"employer:read"}
    required.update(
        {
            "business_address": {"party_address:read"},
            "worksite": {"worksite:read"},
            "worksite_address": {"worksite:read", "worksite_address:read"},
            "request": {"staffing_request:read"},
        }[section]
    )
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    address_names = ("line1", "line2", "locality", "region", "postal_code", "country")
    table, id_name, names = {
        "business_address": (
            employer_addresses,
            "employer_address_id",
            ("purpose", *address_names),
        ),
        "worksite": (
            worksites,
            "worksite_id",
            ("location_verification_status", "service_area_status", "map_area_status"),
        ),
        "worksite_address": (worksites, "worksite_id", address_names),
        "request": (
            staffing_requests,
            "staffing_request_id",
            (
                "employer_contact_id",
                "worksite_id",
                "employer_address_id",
                "request_type",
                "request_status",
                "source_channel",
                "role_title",
                "duties_summary",
                "worker_count",
                "schedule",
                "offer",
                "created_at",
                "received_at",
                "updated_at",
            ),
        ),
    }[section]
    statement = (
        select(
            table.c[id_name],
            table.c.employer_id,
            table.c.version,
            *(table.c[name] for name in names),
        )
        .join(employers, employers.c.employer_id == table.c.employer_id)
        .where(
            table.c.employer_id == employer_id,
            table.c[id_name] == output_id,
            employers.c.lifecycle_status == "draft",
        )
    )
    try:
        row = session.execute(statement).mappings().one_or_none()
    except SQLAlchemyError as exc:
        session.rollback()
        raise IntakeError("persistence_unavailable", 503) from exc
    if row is None:
        raise IntakeError("not_found", 404)
    result = dict(row)
    if section in {"business_address", "worksite_address"}:
        values = {name: result.pop(name) for name in address_names}
        result["address"] = {name: value for name, value in values.items() if value is not None}
    return result
