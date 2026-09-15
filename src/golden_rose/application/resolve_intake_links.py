"""Unexposed canonical reference resolution for the later link transaction."""

from typing import Any, Literal

from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import LinkIntakeRequest
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.models import (
    employer_addresses,
    employer_contact_details,
    employer_contacts,
    employers,
    worker_contacts,
    worker_preferences,
    worker_residences,
    workers,
    worksites,
)


def authorize_link_selection(
    *,
    principal: StaffPrincipal,
    kind: Literal["worker", "employer"],
    request: LinkIntakeRequest,
) -> None:
    """Current field/record authorization without lookup or expected-version checks."""
    if request.party is None:
        return
    if kind == "worker" and any((request.contact, request.worksite, request.business_address)):
        raise IntakeError("invalid_request", 422)
    required = (
        {"worker:read", "worker_contact:read", "worker_residence:read"}
        if kind == "worker"
        else {"employer:read"}
    )
    if kind == "employer":
        if request.contact:
            required.update(
                {"employer_contact:read", "employer_contact:details:read", "party_address:read"}
            )
        if request.worksite:
            required.update({"worksite:read", "worksite_address:read"})
        if request.business_address:
            required.add("party_address:read")
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    party_id = request.party.id
    if (
        kind == "worker"
        and principal.worker_scope is not None
        and party_id not in principal.worker_scope
    ):
        raise IntakeError("not_found", 404)


def resolve_link_dependencies(
    *,
    session: Session,
    principal: StaffPrincipal,
    kind: Literal["worker", "employer"],
    request: LinkIntakeRequest,
) -> dict[str, Any]:
    """Resolve IDs/versions without writes; caller owns the outer transaction.

    Caller locks the intake first. Employer parents are locked before immutable
    children. PR D must add worker/child locks before enabling corrections.
    """
    authorize_link_selection(principal=principal, kind=kind, request=request)
    if request.party is None:
        return {}
    party_id = request.party.id
    table = workers if kind == "worker" else employers
    id_name = f"{kind}_id"
    columns = [table.c[id_name], table.c.version]
    if kind == "employer":
        columns.append(table.c.employer_type)
    statement = select(*columns).where(table.c[id_name] == party_id)
    if kind == "employer":
        statement = statement.where(table.c.lifecycle_status == "draft").with_for_update()
    parent = session.execute(statement).mappings().one_or_none()
    if parent is None:
        raise IntakeError("not_found", 404)
    if parent["version"] != request.party.version:
        raise IntakeError("dependency_changed")
    result: dict[str, Any] = {kind: {"id": str(party_id), "version": parent["version"]}}

    def child(
        table: Table,
        name: str,
        *,
        target: Any = None,
        expected: int | None = None,
        missing: str = "canonical_incomplete",
        contact_id: Any = None,
    ) -> None:
        column = f"{name}_id"
        query = select(table.c[column], table.c.version).where(table.c[id_name] == party_id)
        if target is not None:
            query = query.where(table.c[column] == target)
        if contact_id is not None:
            query = query.where(table.c.employer_contact_id == contact_id)
        row = session.execute(query).mappings().one_or_none()
        if row is None:
            raise IntakeError(missing, 404 if missing == "not_found" else 409)
        if expected is not None and row["version"] != expected:
            raise IntakeError("dependency_changed")
        result[name] = {"id": str(row[column]), "version": row["version"]}

    if kind == "worker":
        for table, name in (
            (worker_contacts, "worker_contact"),
            (worker_residences, "worker_residence"),
            (worker_preferences, "worker_preferences"),
        ):
            child(table, name)
        return result
    if request.business_address and parent["employer_type"] != "business":
        raise IntakeError("invalid_request", 422)
    if request.contact:
        child(
            employer_contacts,
            "employer_contact",
            target=request.contact.id,
            expected=request.contact.version,
            missing="not_found",
        )
        child(employer_contact_details, "employer_contact_details", contact_id=request.contact.id)
    if request.worksite:
        child(
            worksites,
            "worksite",
            target=request.worksite.id,
            expected=request.worksite.version,
            missing="not_found",
        )
    if request.business_address:
        child(
            employer_addresses,
            "employer_address",
            target=request.business_address.id,
            expected=request.business_address.version,
            missing="not_found",
        )
    return result
