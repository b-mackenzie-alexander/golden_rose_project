"""Review/follow-up, new-party finalization and local synthetic catalogs."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from golden_rose.api.dependencies import get_settings, get_staff_directory
from golden_rose.api.staff.intake_finalization_schemas import (
    FinalizeIntakeRequest,
    LinkIntakeRequest,
)
from golden_rose.api.staff.intake_review_schemas import (
    CreateWorkInterestRequest,
    FollowUpIntakeRequest,
    FollowUpOwnersPage,
    IntakeHistoryPage,
    PageRequest,
    QueryWorkInterestsRequest,
    RestrictedHistoryResponse,
    ReviewIntakeRequest,
    ReviseWorkInterestRequest,
    WorkInterestCommandResponse,
    WorkInterestPage,
)
from golden_rose.api.staff.intake_schemas import IntakeCommandResponse
from golden_rose.api.staff.intakes import ClockDep, KeyDep, PrincipalDep, SessionDep
from golden_rose.application.finalize_intake import execute_new_intake_finalization
from golden_rose.application.intake_access import record_intake_access
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.intake_history import (
    query_follow_up_owners,
    query_history,
    read_restricted_history,
)
from golden_rose.application.link_intake import execute_link_intake
from golden_rose.application.review_intake import execute_review
from golden_rose.application.work_interests import execute_work_interest, query_work_interests
from golden_rose.auth.staff_directory import StaffDirectory
from golden_rose.config import Settings

router = APIRouter(prefix="/api/staff/v1")
DirectoryDep = Annotated[StaffDirectory, Depends(get_staff_directory)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def local_only(settings: Settings) -> None:
    if (
        settings.environment not in {"local", "test"}
        and not settings.controlled_live_data_staff_pilot
    ):
        raise IntakeError("forbidden", 403)


def mutation_response(
    result: dict[str, Any],
    replayed: bool,
    *,
    create_location: str | None = None,
    intake: bool = True,
) -> JSONResponse:
    body = (
        IntakeCommandResponse.model_validate(result).model_dump(mode="json", exclude_unset=True)
        if intake
        else WorkInterestCommandResponse.model_validate(result).model_dump(
            mode="json", exclude_unset=True
        )
    )
    headers = {
        "Idempotency-Replayed": str(replayed).lower(),
        "Idempotency-Result-Version": str(result["result_record_version"]),
    }
    status = 200
    if create_location and not replayed:
        headers["Location"] = create_location
        status = 201
    return JSONResponse(body, status_code=status, headers=headers)


@router.post(
    "/intakes/{intake_id}/links",
    response_model=IntakeCommandResponse,
    response_model_exclude_unset=True,
)
def link(
    intake_id: UUID,
    body: LinkIntakeRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_link_intake(
        session=session,
        principal=principal,
        command_id=command_id,
        intake_id=intake_id,
        request=body,
        clock=clock,
    )
    return mutation_response(result, replayed)


@router.post("/intakes/{intake_id}/reviews", response_model=IntakeCommandResponse)
def review(
    intake_id: UUID,
    body: ReviewIntakeRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    directory: DirectoryDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_review(
        session=session,
        principal=principal,
        command_id=command_id,
        request=body,
        clock=clock,
        directory=directory,
        intake_id=intake_id,
    )
    return mutation_response(result, replayed)


@router.post(
    "/intakes/{intake_id}/finalizations",
    response_model=IntakeCommandResponse,
    response_model_exclude_unset=True,
    responses={201: {"model": IntakeCommandResponse}},
)
def finalize(
    intake_id: UUID,
    body: FinalizeIntakeRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_new_intake_finalization(
        session=session,
        principal=principal,
        command_id=command_id,
        request=body,
        clock=clock,
        intake_id=intake_id,
    )
    return mutation_response(result, replayed, create_location=f"/api/staff/v1/intakes/{intake_id}")


@router.post("/intakes/{intake_id}/follow-ups", response_model=IntakeCommandResponse)
def follow_up(
    intake_id: UUID,
    body: FollowUpIntakeRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    directory: DirectoryDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_review(
        session=session,
        principal=principal,
        command_id=command_id,
        request=body,
        clock=clock,
        directory=directory,
        intake_id=intake_id,
    )
    return mutation_response(result, replayed)


@router.post(
    "/intakes/{intake_id}/history/query",
    response_model=IntakeHistoryPage,
    response_model_exclude_unset=True,
)
def history(
    intake_id: UUID,
    body: PageRequest,
    session: SessionDep,
    principal: PrincipalDep,
    directory: DirectoryDep,
):
    return query_history(
        session=session, principal=principal, directory=directory, intake_id=intake_id, request=body
    )


@router.get(
    "/intakes/{intake_id}/history/{event_id}/restricted",
    response_model=RestrictedHistoryResponse,
    response_model_exclude_unset=True,
)
def restricted_history(
    intake_id: UUID,
    event_id: UUID,
    request: Request,
    session: SessionDep,
    principal: PrincipalDep,
):
    result = read_restricted_history(
        session=session, principal=principal, intake_id=intake_id, event_id=event_id
    )
    sink = getattr(request.app.state, "intake_access_sink", record_intake_access)
    sink(actor_id=principal.actor_id, intake_id=intake_id, section="restricted_history")
    return result


@router.post(
    "/intakes/{intake_id}/follow-up-owners/query",
    response_model=FollowUpOwnersPage,
    response_model_exclude_unset=True,
)
def owners(
    intake_id: UUID,
    body: PageRequest,
    session: SessionDep,
    principal: PrincipalDep,
    directory: DirectoryDep,
):
    return query_follow_up_owners(
        session=session, principal=principal, directory=directory, intake_id=intake_id, request=body
    )


@router.post(
    "/work-interests/query", response_model=WorkInterestPage, response_model_exclude_unset=True
)
def interests(body: QueryWorkInterestsRequest, session: SessionDep, principal: PrincipalDep):
    return query_work_interests(session=session, principal=principal, request=body)


@router.post(
    "/work-interests", response_model=WorkInterestCommandResponse, response_model_exclude_unset=True
)
def create_interest(
    body: CreateWorkInterestRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_work_interest(
        session=session, principal=principal, command_id=command_id, request=body, clock=clock
    )
    return mutation_response(
        result,
        replayed,
        create_location=f"/api/staff/v1/work-interests/{result['current']['interest_id']}",
        intake=False,
    )


@router.post(
    "/work-interests/{interest_id}/revisions",
    response_model=WorkInterestCommandResponse,
    response_model_exclude_unset=True,
)
def revise_interest(
    interest_id: UUID,
    body: ReviseWorkInterestRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_work_interest(
        session=session,
        principal=principal,
        command_id=command_id,
        request=body,
        clock=clock,
        interest_id=interest_id,
    )
    return mutation_response(result, replayed, intake=False)
