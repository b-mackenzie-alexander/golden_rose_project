"""Internal authorized canonical facts for later linked review/finalization."""

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import CanonicalLinkReference
from golden_rose.application.intake_contracts import (
    Address,
    EmployerDraftContent,
    WorkerDraftContent,
)
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

ADDRESS_FIELDS = ("line1", "line2", "locality", "region", "postal_code", "country")
WORKER_FIELDS = {
    "worker": (workers, ("full_name",)),
    "worker_contact": (worker_contacts, ("phone", "email")),
    "worker_preferences": (worker_preferences, ("interests", "availability", "self_reported")),
    "worker_residence": (worker_residences, ADDRESS_FIELDS),
}
EMPLOYER_FIELDS = {
    "employer": (employers, ("employer_type", "display_name")),
    "employer_contact": (employer_contacts, ("full_name",)),
    "employer_contact_details": (
        employer_contact_details,
        ("representative_name", "phone", "email", *ADDRESS_FIELDS),
    ),
    "employer_address": (employer_addresses, ("purpose", *ADDRESS_FIELDS)),
    "worksite": (worksites, ADDRESS_FIELDS),
}


@dataclass(frozen=True)
class LinkedSnapshot:
    content: dict[str, Any] = field(repr=False)
    addresses: dict[str, dict[str, Any]] = field(repr=False)
    current_dependencies: dict[str, Any]
    dependency_stale: bool


def read_linked_snapshot(
    *,
    session: Session,
    principal: StaffPrincipal,
    kind: Literal["worker", "employer"],
    dependencies: dict[str, Any],
) -> LinkedSnapshot:
    """Read selected facts only; never merge candidate values or persist changes.

    Requires all selected field rights because this is a protected snapshot, not
    an ordinary detail DTO. Callers own intake authorization, command/review locks,
    transaction completion, catalog currency and completeness. Never serialize
    this internal object directly into an ordinary response. Employer parents are
    locked against existing revisions; PR D must add the currently immutable
    worker/child lock protocol before enabling corrections.
    """
    if not dependencies:
        return LinkedSnapshot({}, {}, {}, False)
    fields = WORKER_FIELDS if kind == "worker" else EMPLOYER_FIELDS
    names = set(dependencies)
    if (kind == "worker" and names != set(WORKER_FIELDS)) or (
        kind == "employer"
        and (
            "employer" not in names
            or not names <= set(EMPLOYER_FIELDS)
            or (("employer_contact" in names) != ("employer_contact_details" in names))
        )
    ):
        raise IntakeError("invalid_request", 422)
    try:
        expected = {
            name: CanonicalLinkReference.model_validate(value)
            for name, value in dependencies.items()
        }
    except ValidationError as exc:
        raise IntakeError("invalid_request", 422) from exc
    required = (
        {"worker:read", "worker_contact:read", "worker_residence:read"}
        if kind == "worker"
        else {"employer:read"}
    )
    if "employer_contact" in names:
        required.update(
            {"employer_contact:read", "employer_contact:details:read", "party_address:read"}
        )
    if "worksite" in names:
        required.update({"worksite:read", "worksite_address:read"})
    if "employer_address" in names:
        required.add("party_address:read")
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    parent_id = expected[kind].id
    if (
        kind == "worker"
        and principal.worker_scope is not None
        and parent_id not in principal.worker_scope
    ):
        raise IntakeError("not_found", 404)
    records: dict[str, Any] = {}
    current: dict[str, Any] = {}
    # Parent first, then fixed entity-name order shared with future command locks.
    for name in sorted(names):
        table, columns = fields[name]
        statement = select(
            table.c[f"{name}_id"], table.c.version, *(table.c[c] for c in columns)
        ).where(table.c[f"{name}_id"] == expected[name].id)
        if name != kind:
            statement = statement.where(table.c[f"{kind}_id"] == parent_id)
        elif kind == "employer":
            statement = statement.where(table.c.lifecycle_status == "draft").with_for_update()
        if name == "employer_contact_details":
            statement = statement.where(
                table.c.employer_contact_id == expected["employer_contact"].id
            )
        row = (
            session.execute(
                statement if name == "employer_contact" else statement.with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise IntakeError("not_found", 404)
        records[name] = dict(row)
        current[name] = {"id": str(row[f"{name}_id"]), "version": row["version"]}
    content: dict[str, Any] = {}
    addresses: dict[str, dict[str, Any]] = {}

    def address(section: str, record: dict[str, Any]) -> None:
        raw = {key: record[key] for key in ADDRESS_FIELDS if record[key] is not None}
        addresses[section] = Address.model_validate(raw).to_content()

    try:
        if kind == "worker":
            preferences = records["worker_preferences"]
            if preferences["self_reported"] is not True:
                raise IntakeError("canonical_incomplete")
            content = WorkerDraftContent.model_validate(
                {
                    "full_name": records["worker"]["full_name"],
                    "phone": records["worker_contact"]["phone"],
                    "email": records["worker_contact"]["email"],
                    "interests": preferences["interests"],
                    "availability": preferences["availability"],
                }
            ).to_content()
            address("worker_residence", records["worker_residence"])
        else:
            parent = records["employer"]
            content = {
                "employer_type": parent["employer_type"],
                "display_name": parent["display_name"],
            }
            if "employer_contact" in records:
                content.update(
                    representative_name=records["employer_contact_details"]["representative_name"],
                    phone=records["employer_contact_details"]["phone"],
                    email=records["employer_contact_details"]["email"],
                )
                if parent["employer_type"] == "household":
                    address("party_address", records["employer_contact_details"])
            if "employer_address" in records:
                if (
                    parent["employer_type"] != "business"
                    or records["employer_address"]["purpose"] != "business"
                ):
                    raise IntakeError("canonical_incomplete")
                address("party_address", records["employer_address"])
            if "worksite" in records:
                address("worksite_address", records["worksite"])
            content = EmployerDraftContent.model_validate(content).to_content()
    except ValidationError as exc:
        raise IntakeError("canonical_incomplete") from exc
    expected_values = {name: value.model_dump(mode="json") for name, value in expected.items()}
    return LinkedSnapshot(content, addresses, current, current != expected_values)
