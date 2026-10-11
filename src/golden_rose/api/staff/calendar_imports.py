from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import (
    get_clock,
    get_db_session,
    get_idempotency_key,
    get_identifier_factory,
    get_settings,
    get_staff_principal,
)
from golden_rose.api.errors import no_store_problem_response
from golden_rose.api.staff.calendar_import_schemas import (
    CalendarImportSummaryResponse,
    ExternalCalendarCandidateDispositionRequest,
    ExternalCalendarImportCommandResponse,
    ExternalCalendarImportResponse,
    GoogleCalendarOAuthStartResponse,
    StaffCalendarConnectionResponse,
    StageExternalCalendarCandidateRequest,
)
from golden_rose.application.calendar_imports import (
    CalendarImportError,
    CalendarImportNotFoundError,
    CalendarImportVersionConflictError,
    dispose_external_calendar_candidate,
    get_calendar_import_summary,
    import_google_calendar_events,
    stage_external_calendar_candidate,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.google_calendar_oauth import (
    GOOGLE_CALENDAR_OAUTH_STATE_TTL_SECONDS,
    GoogleCalendarOAuthError,
    build_google_calendar_oauth_start,
    exchange_google_calendar_code,
    fetch_google_calendar_events,
    validate_google_calendar_oauth_state,
)
from golden_rose.auth.permissions import can_manage_calendar_imports
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.config import Settings
from golden_rose.identifiers import IdentifierFactory
from golden_rose.persistence.staff_accounts import (
    get_staff_account_by_id,
    list_active_staff_permissions,
)

router = APIRouter(prefix="/api/staff/v1/calendar-imports", tags=["staff-calendar-imports"])
GOOGLE_CALENDAR_OAUTH_COOKIE = "golden_rose_google_calendar_oauth_state"
STAFF_CALENDAR_RETURN_PATH = "/staff/calendar"


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


def _set_oauth_cookie(response: Response, *, state: str, settings: Settings) -> None:
    response.set_cookie(
        GOOGLE_CALENDAR_OAUTH_COOKIE,
        state,
        max_age=GOOGLE_CALENDAR_OAUTH_STATE_TTL_SECONDS,
        httponly=True,
        secure=settings.environment != "local",
        samesite="lax",
        path="/api/staff/v1/calendar-imports/oauth",
    )


def _clear_oauth_cookie(response: Response, *, settings: Settings) -> None:
    response.delete_cookie(
        GOOGLE_CALENDAR_OAUTH_COOKIE,
        secure=settings.environment != "local",
        samesite="lax",
        path="/api/staff/v1/calendar-imports/oauth",
    )


def _oauth_redirect(status: str, *, settings: Settings) -> RedirectResponse:
    response = RedirectResponse(
        f"{STAFF_CALENDAR_RETURN_PATH}?calendar_import={status}",
        status_code=303,
    )
    response.headers["Cache-Control"] = "no-store"
    _clear_oauth_cookie(response, settings=settings)
    return response


def _staff_principal_for_oauth_callback(*, session: Session, staff_id: UUID) -> StaffPrincipal:
    try:
        account = get_staff_account_by_id(session=session, staff_id=staff_id)
        permissions = list_active_staff_permissions(session=session, staff_id=staff_id)
    except (NoResultFound, SQLAlchemyError) as exc:
        raise SafePersistenceError("persistence operation failed") from exc
    if account.lifecycle_status != "active" or not account.mfa_enrolled:
        raise PermissionError("staff account is not active for calendar import")
    principal = StaffPrincipal(
        actor_id=account.staff_id,
        role_name=account.role_name,
        permissions=permissions,
    )
    if not can_manage_calendar_imports(principal):
        raise PermissionError("calendar_import:manage")
    return principal


@router.get("", response_model=CalendarImportSummaryResponse)
def get_calendar_imports(
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CalendarImportSummaryResponse | Response:
    try:
        summary = get_calendar_import_summary(session=session, principal=principal)
    except (PermissionError, SafePersistenceError) as exc:
        return _problem_for_calendar_error(exc)
    _read_response(response)
    oauth_configured = settings.google_calendar_oauth_configured
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
        oauth_configuration_required=not oauth_configured,
        oauth_connect_available=oauth_configured,
    )


@router.post("/oauth/start", response_model=GoogleCalendarOAuthStartResponse)
def start_google_calendar_oauth(
    response: Response,
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> GoogleCalendarOAuthStartResponse | Response:
    if not can_manage_calendar_imports(principal):
        return _problem_for_calendar_error(PermissionError("calendar_import:manage"))
    try:
        start = build_google_calendar_oauth_start(
            settings=settings,
            staff_id=principal.actor_id,
            now=clock.now(),
        )
    except GoogleCalendarOAuthError:
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="Google Calendar OAuth is not configured",
            type_="https://golden-rose.local/problems/google-calendar-oauth-unavailable",
        )
    _read_response(response)
    _set_oauth_cookie(response, state=start.state, settings=settings)
    return GoogleCalendarOAuthStartResponse(authorization_url=start.authorization_url)


@router.get("/oauth/callback")
def complete_google_calendar_oauth(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
    code: Annotated[str | None, Query(max_length=2048)] = None,
    state: Annotated[str | None, Query(max_length=4096)] = None,
    error: Annotated[str | None, Query(max_length=256)] = None,
) -> RedirectResponse:
    if error is not None or code is None:
        return _oauth_redirect("failed", settings=settings)
    now = clock.now()
    try:
        oauth_state = validate_google_calendar_oauth_state(
            settings=settings,
            state=state,
            cookie_state=request.cookies.get(GOOGLE_CALENDAR_OAUTH_COOKIE),
            now=now,
        )
        token = exchange_google_calendar_code(settings=settings, code=code)
        events = fetch_google_calendar_events(
            access_token=token.access_token,
            now=now,
            window_days=settings.google_calendar_import_window_days,
        )
        principal = _staff_principal_for_oauth_callback(
            session=session,
            staff_id=oauth_state.staff_id,
        )
        import_google_calendar_events(
            session=session,
            principal=principal,
            events=events,
            granted_scopes=token.granted_scopes,
            clock=clock,
            identifiers=identifiers,
        )
    except (GoogleCalendarOAuthError, CalendarImportError, PermissionError, SafePersistenceError):
        return _oauth_redirect("failed", settings=settings)
    return _oauth_redirect("connected", settings=settings)


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
