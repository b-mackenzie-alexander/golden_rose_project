"""Selective employer output insertion for the finalization orchestrator.

Requires the additive employer migration. The outer command must first
authorize fields, lock/recheck current review and own receipt/audit/finalization
authority plus commit/rollback. This helper neither links nor updates records.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert
from sqlalchemy.orm import Session

from golden_rose.application.intake_contracts import Address, EmployerDraftContent
from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.employer_contacts import insert_employer_contact
from golden_rose.persistence.employers import insert_draft_employer
from golden_rose.persistence.intakes import address_complete
from golden_rose.persistence.models import (
    employer_addresses,
    employer_contact_details,
    entity_authorities,
    staffing_requests,
    worksites,
)


def insert_new_employer_group(
    session: Session,
    *,
    content: dict[str, Any],
    party_address: dict[str, str] | None,
    worksite_address: dict[str, str] | None,
    actor_id: UUID,
    now: datetime,
) -> dict[str, UUID]:
    return insert_employer_group(
        session,
        content=content,
        party_address=party_address,
        worksite_address=worksite_address,
        actor_id=actor_id,
        now=now,
        reused={},
    )


def insert_employer_group(
    session: Session,
    *,
    content: dict[str, Any],
    party_address: dict[str, str] | None,
    worksite_address: dict[str, str] | None,
    actor_id: UUID,
    now: datetime,
    reused: dict[str, Any],
) -> dict[str, UUID]:
    """Insert only unselected outputs and one new request; return created IDs only.

    Caller must lock/resolve same-parent references and verify the exact reviewed
    effective facts. Reused rows receive neither writes nor new authority.
    """
    content = EmployerDraftContent.model_validate(content).to_content()
    party = Address.model_validate(party_address or {}).to_content()
    worksite = Address.model_validate(worksite_address or {}).to_content()
    missing = [
        field
        for field in (
            "employer_type",
            "display_name",
            "representative_name",
            "phone",
            "role_title",
            "duties_summary",
            "worker_count",
        )
        if not content.get(field)
    ]
    if content.get("schedule", {}).get("mode", "unknown") == "unknown":
        missing.append("schedule")
    if not all(
        content.get("offer", {}).get(key) is not None
        for key in (
            "minimum",
            "currency",
            "basis",
            "per_worker",
        )
    ):
        missing.append("offer")
    for section, address in (("party_address", party), ("worksite_address", worksite)):
        if not address_complete(address):
            missing.append(section)
    if missing:
        raise IntakeError("incomplete", 422, missing_fields=missing)
    business = content["employer_type"] == "business"
    kinds = [
        "employer",
        "employer_contact",
        "employer_contact_details",
        "worksite",
        "staffing_request",
    ]
    if business:
        kinds.append("employer_address")
    if reused and (
        "employer" not in reused
        or not set(reused) <= set(kinds) - {"staffing_request"}
        or (("employer_contact" in reused) != ("employer_contact_details" in reused))
    ):
        raise IntakeError("invalid_request", 422)
    created = {kind: uuid4() for kind in kinds if kind not in reused}
    identities = {**created, **{kind: UUID(ref["id"]) for kind, ref in reused.items()}}
    parent = identities["employer"]
    attribution = {
        "created_by": actor_id,
        "updated_by": actor_id,
        "created_at": now,
        "updated_at": now,
        "version": 1,
    }
    if "employer" in created:
        insert_draft_employer(
            session=session,
            employer_id=parent,
            employer_type=content["employer_type"],
            display_name=content["display_name"],
            created_by=actor_id,
            created_at=now,
        )
    if "employer_contact" in created:
        insert_employer_contact(
            session=session,
            employer_id=parent,
            employer_contact_id=identities["employer_contact"],
            full_name=content["representative_name"],
            created_by=actor_id,
            created_at=now,
        )
    if "employer_contact_details" in created:
        session.execute(
            insert(employer_contact_details).values(
                employer_contact_details_id=identities["employer_contact_details"],
                employer_id=parent,
                employer_contact_id=identities["employer_contact"],
                representative_name=content["representative_name"],
                phone=content["phone"],
                email=content.get("email"),
                **({} if business else party),
                **attribution,
            )
        )
    if "employer_address" in created:
        session.execute(
            insert(employer_addresses).values(
                employer_address_id=identities["employer_address"],
                employer_id=parent,
                purpose="business",
                **party,
                **attribution,
            )
        )
    if "worksite" in created:
        session.execute(
            insert(worksites).values(
                worksite_id=identities["worksite"],
                employer_id=parent,
                location_verification_status="supplied",
                service_area_status="unassigned",
                map_area_status="pending",
                **worksite,
                **attribution,
            )
        )
    session.execute(
        insert(staffing_requests).values(
            staffing_request_id=identities["staffing_request"],
            employer_id=parent,
            employer_contact_id=identities["employer_contact"],
            worksite_id=identities["worksite"],
            employer_address_id=identities.get("employer_address"),
            request_type="general_labor" if business else "household",
            request_status="draft",
            source_channel="staff_entry",
            received_at=now,
            **{
                key: content[key]
                for key in ("role_title", "duties_summary", "worker_count", "schedule", "offer")
            },
            **attribution,
        )
    )
    for kind, identity in created.items():
        session.execute(
            insert(entity_authorities).values(
                entity_type=kind,
                entity_id=identity,
                **{f"{kind}_id": identity},
            )
        )
    return created
