from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import (
    get_clock,
    get_db_session,
    get_idempotency_key,
    get_identifier_factory,
    get_staff_principal,
)
from golden_rose.api.staff.schemas import CreateDraftEmployerRequest, DraftEmployerResponse
from golden_rose.application.create_draft_employer import create_draft_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.identifiers import IdentifierFactory

router = APIRouter(prefix="/api/staff/v1/employers", tags=["staff-employers"])


@router.post("", response_model=DraftEmployerResponse, status_code=status.HTTP_201_CREATED)
def post_staff_employer(
    request: CreateDraftEmployerRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> DraftEmployerResponse:
    result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=idempotency_key,
        employer_type=request.employer_type,
        display_name=request.display_name,
        clock=clock,
        identifiers=identifiers,
    )
    if result.replayed:
        response.headers["Idempotency-Replayed"] = "true"
    return DraftEmployerResponse.model_validate(result.employer)
