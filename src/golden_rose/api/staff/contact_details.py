"""Local/test contact detail reads; legacy contact DTOs remain unchanged."""

from uuid import UUID

from fastapi import APIRouter, Request

from golden_rose.api.staff.contact_detail_schemas import ContactAddress, ContactDetails
from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import PrincipalDep, SessionDep
from golden_rose.application.intake_access import record_contact_address_access
from golden_rose.application.read_contact_details import read_contact_details

router = APIRouter(
    prefix="/api/staff/v1/employers/{employer_id}/contacts/{contact_id}/details",
    tags=["staff-contact-details"],
)


@router.get("", response_model=ContactDetails)
def details(
    employer_id: UUID,
    contact_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return read_contact_details(
        session=session, principal=principal, employer_id=employer_id, contact_id=contact_id
    )


@router.get("/address", response_model=ContactAddress, response_model_exclude_none=True)
def address(
    employer_id: UUID,
    contact_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
    request: Request,
):
    local_only(settings)
    result = ContactAddress.model_validate(
        read_contact_details(
            session=session,
            principal=principal,
            employer_id=employer_id,
            contact_id=contact_id,
            address=True,
        )
    )
    sink = getattr(request.app.state, "contact_address_access_sink", record_contact_address_access)
    sink(actor_id=principal.actor_id, employer_id=employer_id, contact_id=contact_id)
    return result
