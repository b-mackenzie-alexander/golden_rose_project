"""Local/test canonical employer reads; no default permission activation."""

from uuid import UUID

from fastapi import APIRouter, Request

from golden_rose.api.staff.employer_output_schemas import (
    EmployerAddressDetail,
    EmployerAddressPage,
    QueryEmployerOutputsRequest,
    StaffingRequestDetail,
    StaffingRequestPage,
    WorksiteAddress,
    WorksiteDetail,
    WorksitePage,
)
from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import PrincipalDep, SessionDep
from golden_rose.application.intake_access import record_employer_output_access
from golden_rose.application.query_employer_outputs import query_employer_outputs
from golden_rose.application.read_employer_output import read_employer_output

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
