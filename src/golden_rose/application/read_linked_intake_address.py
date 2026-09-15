"""Read one selected canonical address without reading sibling sections."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_schemas import CanonicalLinkReference
from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_contracts import Address
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intake_links import get_link_dependencies
from golden_rose.persistence.models import (
    employer_addresses,
    employer_contact_details,
    employers,
    worker_residences,
    worksites,
)

ADDRESS_FIELDS = ("line1", "line2", "locality", "region", "postal_code", "country")


def read_linked_intake_address(
    *,
    session: Session,
    principal: StaffPrincipal,
    row: dict[str, Any],
    section: str,
) -> dict[str, Any]:
    """Caller reads the candidate separately and owns the protected access receipt.

    Return current canonical values and their current source version, not a copy
    into candidate storage. This advisory read neither locks nor owns commit.
    """
    authorize_intake(principal, "intake:read", section, row["intake_id"])
    if (row["kind"] == "worker") != (section == "worker_residence"):
        raise IntakeError("invalid_request", 422)
    if not row.get("_has_link_row"):
        return {"resolved": None}
    dependencies = get_link_dependencies(session, row["intake_id"])
    if not dependencies:
        return {"resolved": None}
    try:
        refs = {
            name: CanonicalLinkReference.model_validate(ref) for name, ref in dependencies.items()
        }
        parent = refs[row["kind"]]
    except (ValidationError, KeyError) as exc:
        raise IntakeError("persistence_unavailable", 503) from exc
    required = {f"{row['kind']}:read"}
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    if row["kind"] == "worker":
        if principal.worker_scope is not None and parent.id not in principal.worker_scope:
            raise IntakeError("not_found", 404)
        name, table = "worker_residence", worker_residences
    elif section == "worksite_address":
        name, table = "worksite", worksites
        required.add("worksite:read")
    else:
        employer_type = session.scalar(
            select(employers.c.employer_type).where(
                employers.c.employer_id == parent.id,
                employers.c.lifecycle_status == "draft",
            )
        )
        if employer_type is None:
            raise IntakeError("not_found", 404)
        if employer_type == "household":
            name, table = "employer_contact_details", employer_contact_details
            required.update({"employer_contact:read", "employer_contact:details:read"})
        else:
            name, table = "employer_address", employer_addresses
    if name not in refs:
        return {"resolved": None}
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    query = select(table.c.version, *(table.c[field] for field in ADDRESS_FIELDS)).where(
        table.c[f"{name}_id"] == refs[name].id,
        table.c[f"{row['kind']}_id"] == parent.id,
    )
    if name == "employer_contact_details":
        if "employer_contact" not in refs:
            raise IntakeError("persistence_unavailable", 503)
        query = query.where(table.c.employer_contact_id == refs["employer_contact"].id)
    values = session.execute(query).mappings().one_or_none()
    if values is None:
        raise IntakeError("not_found", 404)
    content = {field: values[field] for field in ADDRESS_FIELDS if values[field] is not None}
    try:
        address = Address.model_validate(content).to_content() if content else None
    except ValidationError as exc:
        raise IntakeError("persistence_unavailable", 503) from exc
    return {
        "resolved": address,
        "source_ref": {"id": str(refs[name].id), "version": values["version"]},
    }
