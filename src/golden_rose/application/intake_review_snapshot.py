"""Protected effective review facts; selected canonical fields replace candidates."""

from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import LinkIntakeRequest
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.linked_intake_snapshot import read_linked_snapshot
from golden_rose.application.resolve_intake_links import authorize_link_selection
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.intake_links import get_link_dependencies
from golden_rose.persistence.intakes import get_address


def review_dependencies(
    session: Session,
    principal: StaffPrincipal,
    row: dict[str, Any],
) -> dict[str, Any]:
    """Recheck selected-field rights on fresh commands and original retries."""
    if not row.get("_has_link_row"):
        return {}
    refs = get_link_dependencies(session, row["intake_id"])
    if not refs:
        return {}
    request = LinkIntakeRequest.model_validate(
        {
            "expected_version": row["version"],
            "party": refs[row["kind"]],
            "contact": refs.get("employer_contact"),
            "worksite": refs.get("worksite"),
            "business_address": refs.get("employer_address"),
        }
    )
    authorize_link_selection(principal=principal, kind=row["kind"], request=request)
    return refs


def build_review_snapshot(
    session: Session,
    principal: StaffPrincipal,
    row: dict[str, Any],
    dependencies: dict[str, Any],
) -> dict[str, Any]:
    """Caller owns intake lock, completeness/catalog checks and the transaction."""
    linked = read_linked_snapshot(
        session=session,
        principal=principal,
        kind=row["kind"],
        dependencies=dependencies,
    )
    if linked.dependency_stale:
        raise IntakeError("dependency_changed")
    content = deepcopy(row["content"])
    sections = (
        ("worker_residence",)
        if row["kind"] == "worker"
        else (
            "party_address",
            "worksite_address",
        )
    )
    replaced_addresses: set[str] = set()
    if dependencies:
        if row["kind"] == "worker":
            content = {}
            replaced_addresses.add("worker_residence")
        else:
            for field in ("employer_type", "display_name"):
                content.pop(field, None)
            if "employer_contact" in dependencies:
                for field in ("representative_name", "phone", "email"):
                    content.pop(field, None)
                if linked.content["employer_type"] == "household":
                    replaced_addresses.add("party_address")
            if "employer_address" in dependencies:
                replaced_addresses.add("party_address")
            if "worksite" in dependencies:
                replaced_addresses.add("worksite_address")
    content.update(deepcopy(linked.content))
    addresses = {
        section: address
        for section in sections
        if section not in replaced_addresses
        and (address := get_address(session, row["intake_id"], section)) is not None
    }
    addresses.update(deepcopy(linked.addresses))
    return {"kind": row["kind"], "content": content, "addresses": addresses}
