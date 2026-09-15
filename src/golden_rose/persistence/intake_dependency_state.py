"""Status-only canonical dependency checks; never project protected facts."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_finalization_schemas import CanonicalLinkReference
from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.models import (
    employer_addresses,
    employer_contact_details,
    employer_contacts,
    employers,
    work_interests,
    worker_contacts,
    worker_interest_selections,
    worker_preferences,
    worker_residences,
    workers,
    worksites,
)

TABLES = {
    "worker": workers,
    "worker_contact": worker_contacts,
    "worker_residence": worker_residences,
    "worker_preferences": worker_preferences,
    "employer": employers,
    "employer_contact": employer_contacts,
    "employer_contact_details": employer_contact_details,
    "worksite": worksites,
    "employer_address": employer_addresses,
}


def dependencies_current(session: Session, kind: str, references: dict[str, Any]) -> bool:
    """Compare immutable review expectations with current IDs/versions and catalog state.

    This is an advisory read, not finalization authority or a locked snapshot.
    Callers must already authorize the intake. No canonical field values are read.
    """
    if not references:
        return True
    names = set(references)
    allowed = {name for name in TABLES if name.startswith(kind)}
    if kind == "employer":
        allowed.add("worksite")
    if (
        kind not in names
        or not names <= allowed
        or (kind == "worker" and names != allowed)
        or (("employer_contact" in names) != ("employer_contact_details" in names))
    ):
        raise IntakeError("persistence_unavailable", 503)
    try:
        refs = {
            name: CanonicalLinkReference.model_validate(ref) for name, ref in references.items()
        }
    except ValidationError as exc:
        raise IntakeError("persistence_unavailable", 503) from exc
    for name in (kind, *sorted(names - {kind})):
        table = TABLES[name]
        query = select(table.c.version).where(table.c[f"{name}_id"] == refs[name].id)
        if name != kind:
            query = query.where(table.c[f"{kind}_id"] == refs[kind].id)
        if name == "employer_contact_details":
            query = query.where(table.c.employer_contact_id == refs["employer_contact"].id)
        if session.scalar(query) != refs[name].version:
            return False
    if kind == "worker":
        selections = worker_interest_selections
        stale = session.scalar(
            select(selections.c.interest_id)
            .outerjoin(
                work_interests,
                selections.c.interest_id == work_interests.c.interest_id,
            )
            .where(
                selections.c.worker_preferences_id == refs["worker_preferences"].id,
                or_(
                    work_interests.c.interest_id.is_(None),
                    work_interests.c.active.is_(False),
                    work_interests.c.version != selections.c.catalog_version,
                ),
            )
            .limit(1)
        )
        if stale is not None:
            return False
    return True
