"""Staff-only draft intake routes; no review, link or finalization authority."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import (
    SystemClock,
    get_clock,
    get_db_session,
    get_idempotency_key,
    get_settings,
    get_staff_principal,
)
from golden_rose.api.staff.intake_schemas import (
    CreateIntakeRequest,
    IntakeAddressDetail,
    IntakeCommandResponse,
    IntakeDetail,
    IntakeQueryPageResponse,
    QueryIntakesRequest,
    ReviseIntakeAddressRequest,
    ReviseIntakeRequest,
)
from golden_rose.application.intake_access import record_intake_access
from golden_rose.application.intake_commands import authorize_intake, execute_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.query_intakes import query_intakes
from golden_rose.application.read_linked_intake_address import read_linked_intake_address
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings
from golden_rose.persistence.intakes import get_address, get_intake, intake_detail

router = APIRouter(prefix="/api/staff/v1/intakes", tags=["staff-intakes"])
SessionDep = Annotated[Session, Depends(get_db_session)]
PrincipalDep = Annotated[StaffPrincipal, Depends(get_staff_principal)]
KeyDep = Annotated[UUID, Depends(get_idempotency_key)]
ClockDep = Annotated[SystemClock, Depends(get_clock)]


@router.post("/query", response_model=IntakeQueryPageResponse, response_model_exclude_unset=True)
def query_drafts(body: QueryIntakesRequest, session: SessionDep, principal: PrincipalDep):
    return query_intakes(session=session, principal=principal, request=body)


def _command_response(
    session, principal, command_id, body, clock, intake_id=None, section=None
) -> JSONResponse:
    result, replayed = execute_intake(
        session=session,
        principal=principal,
        command_id=command_id,
        request=body,
        clock=clock,
        intake_id=intake_id,
        section=section,
    )
    status = 201 if intake_id is None and not replayed else 200
    headers = {
        "Idempotency-Replayed": str(replayed).lower(),
        "Idempotency-Result-Version": str(result["result_record_version"]),
    }
    if status == 201:
        headers["Location"] = f"/api/staff/v1/intakes/{result['current']['summary']['intake_id']}"
    validated = IntakeCommandResponse.model_validate(result)
    return JSONResponse(
        validated.model_dump(mode="json", exclude_unset=True), status_code=status, headers=headers
    )


@router.post(
    "",
    response_model=IntakeCommandResponse,
    response_model_exclude_unset=True,
    responses={201: {"model": IntakeCommandResponse}},
)
def create_draft(
    body: CreateIntakeRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: Annotated[Settings, Depends(get_settings)],
):
    if (
        settings.environment not in {"local", "test"}
        and not settings.controlled_live_data_staff_pilot
    ):
        raise IntakeError("forbidden", 403)
    return _command_response(session, principal, command_id, body, clock)


@router.get("/{intake_id}", response_model=IntakeDetail, response_model_exclude_unset=True)
def read_draft(intake_id: UUID, session: SessionDep, principal: PrincipalDep):
    authorize_intake(principal, "intake:read", intake_id=intake_id)
    try:
        return intake_detail(session, get_intake(session, intake_id), principal=principal)
    except SQLAlchemyError as exc:
        raise IntakeError("persistence_unavailable", 503) from exc


@router.post(
    "/{intake_id}/revisions",
    response_model=IntakeCommandResponse,
    response_model_exclude_unset=True,
)
def revise_draft(
    intake_id: UUID,
    body: ReviseIntakeRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
):
    return _command_response(session, principal, command_id, body, clock, intake_id)


@router.get(
    "/{intake_id}/addresses/{section}",
    response_model=IntakeAddressDetail,
    response_model_exclude_unset=True,
)
def read_draft_address(
    intake_id: UUID, section: str, session: SessionDep, principal: PrincipalDep, request: Request
):
    authorize_intake(principal, "intake:read", section, intake_id)
    try:
        row = get_intake(session, intake_id)
        if (row["kind"] == "worker") != (section == "worker_residence"):
            raise IntakeError("invalid_request", 422)
        value = get_address(session, intake_id, section)
        linked = read_linked_intake_address(
            session=session,
            principal=principal,
            row=row,
            section=section,
        )
        # Injected protected access sink; no payload or address is logged.
        sink = getattr(request.app.state, "intake_access_sink", record_intake_access)
        sink(actor_id=principal.actor_id, intake_id=intake_id, section=section)
        return {
            "intake_id": str(intake_id),
            "version": row["version"],
            "section": section,
            "candidate": value,
            **linked,
        }
    except SQLAlchemyError as exc:
        raise IntakeError("persistence_unavailable", 503) from exc


@router.post(
    "/{intake_id}/addresses/{section}/revisions",
    response_model=IntakeCommandResponse,
    response_model_exclude_unset=True,
)
def revise_draft_address(
    intake_id: UUID,
    section: str,
    body: ReviseIntakeAddressRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
):
    return _command_response(session, principal, command_id, body, clock, intake_id, section)
