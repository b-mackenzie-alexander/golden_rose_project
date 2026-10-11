from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import (
    get_clock,
    get_db_session,
    get_idempotency_key,
    get_identifier_factory,
    get_staff_principal,
)
from golden_rose.api.errors import no_store_problem_response
from golden_rose.api.staff.calendar_import_schemas import (
    CalendarImportSummaryResponse,
    ExternalCalendarCandidateDispositionRequest,
    ExternalCalendarImportCommandResponse,
    ExternalCalendarImportResponse,
    StaffCalendarConnectionResponse,
    StageExternalCalendarCandidateRequest,
)
from golden_rose.application.calendar_imports import (
    CalendarImportError,
    CalendarImportNotFoundError,
    CalendarImportVersionConflictError,
    dispose_external_calendar_candidate,
    get_calendar_import_summary,
    stage_external_calendar_candidate,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.identifiers import IdentifierFactory

router = APIRouter(prefix="/api/staff/v1/calendar-imports", tags=["staff-calendar-imports"])


def _read_response(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"


def _command_response(result, response: Response) -> Response:
    _read_response(response)
    response.headers["Idempotency-Result-Version"] = str(result.result_version)
    return response


def _problem_for_calendar_error(exc: Exception) -> Response:
    if isinstance(exc, PermissionError):
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    if isinstance(exc, CalendarImportNotFoundError):
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="calendar import candidate not found",
            type_="https://golden-rose.local/problems/calendar-import-not-found",
        )
    if isinstance(exc, CalendarImportVersionConflictError):
        return no_store_problem_response(
            status_code=412,
            title="Precondition Failed",
            detail="calendar import candidate version conflict",
            type_="https://golden-rose.local/problems/calendar-import-version-conflict",
        )
    if isinstance(exc, CalendarImportError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="calendar import request is invalid",
            type_="https://golden-rose.local/problems/calendar-import-invalid",
        )
    if isinstance(exc, SafePersistenceError):
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    raise exc


@router.get("", response_model=CalendarImportSummaryResponse)
def get_calendar_imports(
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> CalendarImportSummaryResponse | Response:
    try:
        summary = get_calendar_import_summary(session=session, principal=principal)
    except (PermissionError, SafePersistenceError) as exc:
        return _problem_for_calendar_error(exc)
    _read_response(response)
    return CalendarImportSummaryResponse(
        connection=(
            StaffCalendarConnectionResponse.model_validate(summary.connection)
            if summary.connection is not None
            else None
        ),
        candidates=tuple(
            ExternalCalendarImportResponse.model_validate(candidate)
            for candidate in summary.candidates
        ),
        oauth_configuration_required=(
            summary.connection is None
            or summary.connection.connection_status == "authorization_required"
            or summary.connection.last_sync_status == "configuration_required"
        ),
    )


@router.post("/candidates", response_model=ExternalCalendarImportCommandResponse)
def stage_calendar_import_candidate(
    request: StageExternalCalendarCandidateRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    command_id: Annotated[UUID, Depends(get_idempotency_key)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> ExternalCalendarImportCommandResponse | Response:
    try:
        result = stage_external_calendar_candidate(
            session=session,
            principal=principal,
            command_id=command_id,
            provider_event_uid=request.provider_event_uid,
            provider_event_updated_at=request.provider_event_updated_at,
            event_title=request.event_title,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            time_zone=request.time_zone,
            location_review=request.location_review,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (PermissionError, CalendarImportError, SafePersistenceError) as exc:
        return _problem_for_calendar_error(exc)
    _command_response(result, response)
    return ExternalCalendarImportCommandResponse(
        candidate=ExternalCalendarImportResponse.model_validate(result.candidate),
        event_type=result.event_type,  # type: ignore[arg-type]
        result_version=result.result_version,
        replayed=result.replayed,
    )


@router.post("/candidates/{import_id}/ignore", response_model=ExternalCalendarImportCommandResponse)
def ignore_calendar_import_candidate(
    import_id: UUID,
    request: ExternalCalendarCandidateDispositionRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    command_id: Annotated[UUID, Depends(get_idempotency_key)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> ExternalCalendarImportCommandResponse | Response:
    return _dispose_candidate(
        import_id=import_id,
        request=request,
        response=response,
        session=session,
        principal=principal,
        command_id=command_id,
        clock=clock,
        identifiers=identifiers,
        disposition="ignored",
    )


@router.post(
    "/candidates/{import_id}/mark-existing",
    response_model=ExternalCalendarImportCommandResponse,
)
def mark_calendar_import_candidate_existing(
    import_id: UUID,
    request: ExternalCalendarCandidateDispositionRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    command_id: Annotated[UUID, Depends(get_idempotency_key)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> ExternalCalendarImportCommandResponse | Response:
    return _dispose_candidate(
        import_id=import_id,
        request=request,
        response=response,
        session=session,
        principal=principal,
        command_id=command_id,
        clock=clock,
        identifiers=identifiers,
        disposition="marked_existing",
    )


def _dispose_candidate(
    *,
    import_id: UUID,
    request: ExternalCalendarCandidateDispositionRequest,
    response: Response,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    clock: Clock,
    identifiers: IdentifierFactory,
    disposition: str,
) -> ExternalCalendarImportCommandResponse | Response:
    try:
        result = dispose_external_calendar_candidate(
            session=session,
            principal=principal,
            command_id=command_id,
            import_id=import_id,
            expected_version=request.expected_version,
            disposition=disposition,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (
        PermissionError,
        CalendarImportError,
        CalendarImportNotFoundError,
        CalendarImportVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_calendar_error(exc)
    _command_response(result, response)
    return ExternalCalendarImportCommandResponse(
        candidate=ExternalCalendarImportResponse.model_validate(result.candidate),
        event_type=result.event_type,  # type: ignore[arg-type]
        result_version=result.result_version,
        replayed=result.replayed,
    )
