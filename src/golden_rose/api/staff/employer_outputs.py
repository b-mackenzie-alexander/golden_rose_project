"""Local/test canonical employer reads; no default permission activation."""

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from golden_rose.api.staff.employer_output_schemas import (
    CreateShiftNeedRequest,
    EmployerAddressDetail,
    EmployerAddressPage,
    QueryEmployerOutputsRequest,
    QueryShiftNeedsRequest,
    ShiftNeedCommandResponse,
    ShiftNeedDetail,
    ShiftNeedPage,
    StaffingRequestDetail,
    StaffingRequestPage,
    WorksiteAddress,
    WorksiteDetail,
    WorksitePage,
)
from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import ClockDep, KeyDep, PrincipalDep, SessionDep
from golden_rose.application.intake_access import record_employer_output_access
from golden_rose.application.query_employer_outputs import query_employer_outputs
from golden_rose.application.read_employer_output import read_employer_output
from golden_rose.application.shift_needs import (
    create_shift_need,
    query_shift_needs,
    read_shift_need,
)

router = APIRouter(prefix="/api/staff/v1/employers/{employer_id}", tags=["staff-employer-outputs"])


@router.post("/addresses/query", response_model=EmployerAddressPage)
def query_addresses(
    employer_id: UUID,
    body: QueryEmployerOutputsRequest,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return query_employer_outputs(
        session=session,
        principal=principal,
        employer_id=employer_id,
        kind="addresses",
        request=body,
    )


@router.post("/worksites/query", response_model=WorksitePage)
def query_worksites(
    employer_id: UUID,
    body: QueryEmployerOutputsRequest,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return query_employer_outputs(
        session=session,
        principal=principal,
        employer_id=employer_id,
        kind="worksites",
        request=body,
    )


@router.post("/requests/query", response_model=StaffingRequestPage)
def query_requests(
    employer_id: UUID,
    body: QueryEmployerOutputsRequest,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return query_employer_outputs(
        session=session, principal=principal, employer_id=employer_id, kind="requests", request=body
    )


@router.get(
    "/addresses/{address_id}",
    response_model=EmployerAddressDetail,
    response_model_exclude_none=True,
)
def business_address(
    employer_id: UUID,
    address_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
    request: Request,
):
    local_only(settings)
    result = EmployerAddressDetail.model_validate(
        read_employer_output(
            session=session,
            principal=principal,
            employer_id=employer_id,
            output_id=address_id,
            section="business_address",
        )
    )
    sink = getattr(request.app.state, "employer_output_access_sink", record_employer_output_access)
    sink(
        actor_id=principal.actor_id,
        employer_id=employer_id,
        output_id=address_id,
        section="business_address",
    )
    return result


@router.get("/worksites/{worksite_id}", response_model=WorksiteDetail)
def worksite(
    employer_id: UUID,
    worksite_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return read_employer_output(
        session=session,
        principal=principal,
        employer_id=employer_id,
        output_id=worksite_id,
        section="worksite",
    )


@router.get(
    "/worksites/{worksite_id}/address",
    response_model=WorksiteAddress,
    response_model_exclude_none=True,
)
def worksite_address(
    employer_id: UUID,
    worksite_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
    request: Request,
):
    local_only(settings)
    result = WorksiteAddress.model_validate(
        read_employer_output(
            session=session,
            principal=principal,
            employer_id=employer_id,
            output_id=worksite_id,
            section="worksite_address",
        )
    )
    sink = getattr(request.app.state, "employer_output_access_sink", record_employer_output_access)
    sink(
        actor_id=principal.actor_id,
        employer_id=employer_id,
        output_id=worksite_id,
        section="worksite_address",
    )
    return result


@router.get("/requests/{request_id}", response_model=StaffingRequestDetail)
def staffing_request(
    employer_id: UUID,
    request_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return read_employer_output(
        session=session,
        principal=principal,
        employer_id=employer_id,
        output_id=request_id,
        section="request",
    )


@router.post(
    "/requests/{request_id}/shift-needs/query",
    response_model=ShiftNeedPage,
)
def request_shift_needs(
    employer_id: UUID,
    request_id: UUID,
    body: QueryShiftNeedsRequest,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return query_shift_needs(
        session=session,
        principal=principal,
        employer_id=employer_id,
        request_id=request_id,
        request=body,
    )


@router.get(
    "/requests/{request_id}/shift-needs/{shift_need_id}",
    response_model=ShiftNeedDetail,
)
def request_shift_need(
    employer_id: UUID,
    request_id: UUID,
    shift_need_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return read_shift_need(
        session=session,
        principal=principal,
        employer_id=employer_id,
        request_id=request_id,
        shift_need_id=shift_need_id,
    )


@router.post(
    "/requests/{request_id}/shift-needs",
    response_model=ShiftNeedCommandResponse,
    responses={201: {"model": ShiftNeedCommandResponse}},
)
def create_request_shift_need(
    employer_id: UUID,
    request_id: UUID,
    body: CreateShiftNeedRequest,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
    command_id: KeyDep,
    clock: ClockDep,
):
    local_only(settings)
    result = create_shift_need(
        session=session,
        principal=principal,
        employer_id=employer_id,
        request_id=request_id,
        command_id=command_id,
        body=body,
        now=clock.now(),
    )
    validated = ShiftNeedCommandResponse.model_validate(result.payload)
    status = 200 if result.replayed else 201
    headers = {
        "Idempotency-Replayed": str(result.replayed).lower(),
        "Idempotency-Result-Version": str(validated.result_record_version),
    }
    if status == 201:
        headers["Location"] = (
            f"/api/staff/v1/employers/{employer_id}/requests/{request_id}"
            f"/shift-needs/{validated.current.shift_need_id}"
        )
    return JSONResponse(validated.model_dump(mode="json"), status_code=status, headers=headers)
