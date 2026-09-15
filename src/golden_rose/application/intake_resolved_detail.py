"""Selected non-address canonical fields and minimized address completeness."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_schemas import CanonicalLinkReference
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intake_dependency_state import TABLES
from golden_rose.persistence.intake_links import get_link_dependencies

FIELDS = {
    "worker": ("full_name",),
    "worker_contact": ("phone",),
    "worker_preferences": ("interests", "availability"),
    "worker_residence": (),
    "employer": ("employer_type", "display_name"),
    "employer_contact": ("full_name",),
    "employer_contact_details": ("phone",),
    "employer_address": (),
    "worksite": (),
}
ADDRESS_SECTIONS = {
    "worker_residence": "worker_residence",
    "employer_contact_details": "party_address",
    "employer_address": "party_address",
    "worksite": "worksite_address",
}


def resolved_detail_fields(
    session: Session,
    principal: StaffPrincipal,
    row: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool], dict[str, Any], bool]:
    """Caller owns intake authorization; never select or return raw address fields."""
    dependencies = get_link_dependencies(session, row["intake_id"])
    if not dependencies:
        return {}, {}, {}, False
    kind = row["kind"]
    names = set(dependencies)
    allowed = {name for name in FIELDS if name.startswith(kind)}
    if kind == "employer":
        allowed.add("worksite")
    if (
        kind not in names
        or not names <= allowed
        or (kind == "worker" and names != allowed)
        or (("employer_contact" in names) != ("employer_contact_details" in names))
    ):
        raise IntakeError("persistence_unavailable", 503)
    required = {f"{kind}:read"}
    if "worker_contact" in names:
        required.add("worker_contact:read")
    if "employer_contact" in names:
        required.update({"employer_contact:read", "employer_contact:details:read"})
    if "worksite" in names:
        required.add("worksite:read")
    if not required <= principal.permissions:
        raise IntakeError("forbidden", 403)
    try:
        refs = {
            name: CanonicalLinkReference.model_validate(ref) for name, ref in dependencies.items()
        }
    except ValidationError as exc:
        raise IntakeError("persistence_unavailable", 503) from exc
    parent_id = refs[kind].id
    if (
        kind == "worker"
        and principal.worker_scope is not None
        and parent_id not in principal.worker_scope
    ):
        raise IntakeError("not_found", 404)
    resolved: dict[str, Any] = {}
    complete: dict[str, bool] = {}
    stale = False
    for name in (kind, *sorted(names - {kind})):
        table = TABLES[name]
        columns: list[Any] = [table.c.version, *(table.c[field] for field in FIELDS[name])]
        if name in ADDRESS_SECTIONS:

            def nonblank(field: str, table: Any = table) -> Any:
                return func.coalesce(func.length(func.btrim(table.c[field])) > 0, False)

            columns.append(
                and_(
                    *(nonblank(field) for field in ("line1", "locality", "country")),
                    or_(table.c.country != "US", and_(nonblank("region"), nonblank("postal_code"))),
                ).label("address_complete")
            )
        query = select(*columns).where(table.c[f"{name}_id"] == refs[name].id)
        if name != kind:
            query = query.where(table.c[f"{kind}_id"] == parent_id)
        elif kind == "employer":
            query = query.where(table.c.lifecycle_status == "draft")
        if name == "employer_contact_details":
            query = query.where(table.c.employer_contact_id == refs["employer_contact"].id)
        record = session.execute(query).mappings().one_or_none()
        if record is None:
            raise IntakeError("not_found", 404)
        stale = stale or record["version"] != refs[name].version
        for field in FIELDS[name]:
            output = "representative_name" if name == "employer_contact" else field
            if record[field] is not None:
                resolved[output] = record[field]
        if name in ADDRESS_SECTIONS:
            if name == "employer_contact_details" and resolved["employer_type"] != "household":
                continue
            if name == "employer_address" and resolved["employer_type"] != "business":
                # Legacy parent revisions may change type after selection/finalization.
                # Keep the original reference, but do not use a business address as
                # completeness evidence for the current household contact.
                if not stale:
                    raise IntakeError("persistence_unavailable", 503)
                continue
            complete[ADDRESS_SECTIONS[name]] = bool(record["address_complete"])
    return resolved, complete, dependencies, stale
