from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import (
    get_clock,
    get_db_session,
    get_idempotency_key,
    get_identifier_factory,
    get_staff_principal,
)
from golden_rose.api.errors import no_store_problem_response
from golden_rose.api.staff.schemas import (
    ActivateStaffAccountRequest,
    CorrectStaffAccountRequest,
    CreateStaffAccountRequest,
    StaffAccountLifecycleEventListResponse,
    StaffAccountLifecycleEventResponse,
    StaffAccountLifecycleResponse,
    StaffAccountListResponse,
    StaffAccountResponse,
    StaffAccountTransitionRequest,
    StaffDelegationCommandResponse,
    StaffDelegationGrantRequest,
    StaffDelegationListResponse,
    StaffDelegationResponse,
    StaffDelegationRevokeRequest,
    UpdateStaffAccountGoogleEmailRequest,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.staff_account_delegations import (
    StaffDelegationConflictError,
    StaffDelegationError,
    StaffDelegationExpiryError,
    StaffDelegationNotFoundError,
    StaffDelegationPermissionUnavailableError,
    StaffDelegationResult,
    StaffDelegationSelfGrantError,
    StaffDelegationTargetUnavailableError,
    grant_staff_delegation,
    list_delegations_for_staff,
    revoke_staff_account_delegation,
)
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    StaffAccountLifecycleResult,
    StaffAccountNotFoundError,
    StaffAccountVersionConflictError,
    activate_staff_account,
    correct_staff_account_onboarding,
    create_staff_account,
    deprovision_staff_account,
    record_staff_account_recovery_evidence,
    record_staff_account_session_revocation_evidence,
    suspend_staff_account,
    update_staff_account_google_email,
)
from golden_rose.auth.permissions import can_read_staff_account
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.identifiers import IdentifierFactory
from golden_rose.persistence.staff_accounts import (
    StaffAccountRecord,
    get_staff_account_by_id,
    list_active_staff_permission_grants,
    list_staff_account_lifecycle_events,
    list_staff_accounts,
)

router = APIRouter(prefix="/api/staff/v1/staff-accounts", tags=["staff-accounts"])


def _lifecycle_response(result: StaffAccountLifecycleResult, response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"
    response.headers["Idempotency-Result-Version"] = str(result.result_version)
    return response


def _account_response(session: Session, account: StaffAccountRecord) -> StaffAccountResponse:
    return StaffAccountResponse.model_validate(
        {
            **asdict(account),
            "permission_names": tuple(
                sorted(
                    list_active_staff_permission_grants(session=session, staff_id=account.staff_id)
                )
            ),
        }
    )


def _lifecycle_body(
    session: Session, result: StaffAccountLifecycleResult
) -> StaffAccountLifecycleResponse:
    return StaffAccountLifecycleResponse(
        account=_account_response(session, result.account),
        event_type=result.event_type,  # type: ignore[arg-type]
        result_version=result.result_version,
    )


def _problem_for_lifecycle_error(exc: Exception) -> Response:
    if isinstance(exc, StaffAccountNotFoundError):
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="staff account not found",
            type_="https://golden-rose.local/problems/staff-account-not-found",
        )
    if isinstance(exc, StaffAccountVersionConflictError):
        return no_store_problem_response(
            status_code=412,
            title="Precondition Failed",
            detail="staff account version conflict",
            type_="https://golden-rose.local/problems/staff-account-version-conflict",
        )
    if isinstance(exc, StaffAccountLifecycleError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="staff account lifecycle request is invalid",
            type_="https://golden-rose.local/problems/staff-account-lifecycle-invalid",
        )
    if isinstance(exc, SafePersistenceError):
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    raise exc


def _delegation_response(result: StaffDelegationResult, response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"
    response.headers["Idempotency-Result-Version"] = str(result.result_version)
    return response


def _delegation_body(result: StaffDelegationResult) -> StaffDelegationCommandResponse:
    return StaffDelegationCommandResponse(
        delegation=StaffDelegationResponse.model_validate(result.delegation),
        event_type=result.event_type,  # type: ignore[arg-type]
        result_version=result.result_version,
    )


def _problem_for_delegation_error(exc: Exception) -> Response:
    if isinstance(exc, StaffDelegationNotFoundError):
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="staff delegation not found",
            type_="https://golden-rose.local/problems/staff-delegation-not-found",
        )
    if isinstance(exc, StaffDelegationConflictError):
        return no_store_problem_response(
            status_code=412,
            title="Precondition Failed",
            detail="staff delegation conflict",
            type_="https://golden-rose.local/problems/staff-delegation-conflict",
        )
    if isinstance(exc, StaffDelegationSelfGrantError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="staff delegation cannot target the current account",
            type_="https://golden-rose.local/problems/staff-delegation-self-grant",
        )
    if isinstance(exc, StaffDelegationPermissionUnavailableError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="delegated permission is not available to this session",
            type_="https://golden-rose.local/problems/staff-delegation-permission-unavailable",
        )
    if isinstance(exc, StaffDelegationTargetUnavailableError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="target staff account cannot receive delegation",
            type_="https://golden-rose.local/problems/staff-delegation-target-unavailable",
        )
    if isinstance(exc, StaffDelegationExpiryError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="staff delegation expiration is invalid",
            type_="https://golden-rose.local/problems/staff-delegation-expiration-invalid",
        )
    if isinstance(exc, StaffDelegationError):
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="staff delegation request is invalid",
            type_="https://golden-rose.local/problems/staff-delegation-invalid",
        )
    if isinstance(exc, SafePersistenceError):
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    raise exc


def _read_response(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"


def _require_read_permission(principal: StaffPrincipal) -> Response | None:
    if can_read_staff_account(principal):
        return None
    return no_store_problem_response(
        status_code=403,
        title="Forbidden",
        detail="forbidden",
        type_="https://golden-rose.local/problems/forbidden",
    )


@router.get("", response_model=StaffAccountListResponse)
def get_staff_accounts(
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> StaffAccountListResponse | Response:
    denied = _require_read_permission(principal)
    if denied is not None:
        return denied
    try:
        accounts = list_staff_accounts(session=session)
    except SQLAlchemyError:
        return _problem_for_lifecycle_error(SafePersistenceError("persistence operation failed"))
    _read_response(response)
    return StaffAccountListResponse(
        items=tuple(_account_response(session, account) for account in accounts),
    )


@router.get("/{staff_id}", response_model=StaffAccountResponse)
def get_staff_account(
    staff_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> StaffAccountResponse | Response:
    denied = _require_read_permission(principal)
    if denied is not None:
        return denied
    try:
        account = get_staff_account_by_id(session=session, staff_id=staff_id)
    except NoResultFound:
        return _problem_for_lifecycle_error(StaffAccountNotFoundError("staff account not found"))
    except SQLAlchemyError:
        return _problem_for_lifecycle_error(SafePersistenceError("persistence operation failed"))
    _read_response(response)
    return _account_response(session, account)


@router.get("/{staff_id}/delegations", response_model=StaffDelegationListResponse)
def get_staff_account_delegations(
    staff_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> StaffDelegationListResponse | Response:
    try:
        delegations = list_delegations_for_staff(
            session=session,
            principal=principal,
            staff_id=staff_id,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except (StaffDelegationError, SafePersistenceError) as exc:
        return _problem_for_delegation_error(exc)
    _read_response(response)
    return StaffDelegationListResponse(
        items=tuple(StaffDelegationResponse.model_validate(item) for item in delegations),
    )


@router.get("/{staff_id}/events", response_model=StaffAccountLifecycleEventListResponse)
def get_staff_account_events(
    staff_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> StaffAccountLifecycleEventListResponse | Response:
    denied = _require_read_permission(principal)
    if denied is not None:
        return denied
    try:
        get_staff_account_by_id(session=session, staff_id=staff_id)
        events = list_staff_account_lifecycle_events(session=session, staff_id=staff_id)
    except NoResultFound:
        return _problem_for_lifecycle_error(StaffAccountNotFoundError("staff account not found"))
    except SQLAlchemyError:
        return _problem_for_lifecycle_error(SafePersistenceError("persistence operation failed"))
    _read_response(response)
    return StaffAccountLifecycleEventListResponse(
        items=tuple(StaffAccountLifecycleEventResponse.model_validate(item) for item in events),
    )


@router.post(
    "/{staff_id}/delegations",
    response_model=StaffDelegationCommandResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_staff_account_delegation(
    staff_id: UUID,
    request: StaffDelegationGrantRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StaffDelegationCommandResponse | Response:
    try:
        result = grant_staff_delegation(
            session=session,
            principal=principal,
            delegation_id=idempotency_key,
            grantee_staff_id=staff_id,
            permission_name=request.permission_name,
            scope_kind=request.scope_kind,
            expires_at=request.expires_at,
            clock=clock,
            reason_text=request.reason_text,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except (StaffDelegationError, SafePersistenceError) as exc:
        return _problem_for_delegation_error(exc)
    _delegation_response(result, response)
    return _delegation_body(result)


@router.post(
    "/{staff_id}/delegations/{delegation_id}/revoke",
    response_model=StaffDelegationCommandResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_delegation_revocation(
    staff_id: UUID,
    delegation_id: UUID,
    request: StaffDelegationRevokeRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StaffDelegationCommandResponse | Response:
    del idempotency_key
    try:
        result = revoke_staff_account_delegation(
            session=session,
            principal=principal,
            delegation_id=delegation_id,
            grantee_staff_id=staff_id,
            clock=clock,
            reason_text=request.reason_text,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except (StaffDelegationError, SafePersistenceError) as exc:
        return _problem_for_delegation_error(exc)
    _delegation_response(result, response)
    return _delegation_body(result)


@router.post(
    "",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_staff_account(
    request: CreateStaffAccountRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = create_staff_account(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=identifiers.new_uuid4(),
            provider_subject=request.provider_subject,
            provider_email=request.provider_email,
            display_name=request.display_name,
            role_name=request.role_name,
            permission_names=frozenset(request.permission_names),
            mfa_enrolled=request.mfa_enrolled,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (StaffAccountLifecycleError, SafePersistenceError) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/activate",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_activation(
    staff_id: UUID,
    request: ActivateStaffAccountRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = activate_staff_account(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            mfa_enrolled=request.mfa_enrolled,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/correct-onboarding",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_onboarding_correction(
    staff_id: UUID,
    request: CorrectStaffAccountRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = correct_staff_account_onboarding(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            provider_subject=request.provider_subject,
            provider_email=request.provider_email,
            display_name=request.display_name,
            role_name=request.role_name,
            permission_names=frozenset(request.permission_names),
            mfa_enrolled=request.mfa_enrolled,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/google-email",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_google_email_update(
    staff_id: UUID,
    request: UpdateStaffAccountGoogleEmailRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = update_staff_account_google_email(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            provider_email=request.provider_email,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/suspend",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_suspension(
    staff_id: UUID,
    request: StaffAccountTransitionRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = suspend_staff_account(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/deprovision",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_deprovisioning(
    staff_id: UUID,
    request: StaffAccountTransitionRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = deprovision_staff_account(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/recovery-evidence",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_recovery_evidence(
    staff_id: UUID,
    request: StaffAccountTransitionRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = record_staff_account_recovery_evidence(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)


@router.post(
    "/{staff_id}/session-revocations",
    response_model=StaffAccountLifecycleResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_account_session_revocation(
    staff_id: UUID,
    request: StaffAccountTransitionRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
) -> StaffAccountLifecycleResponse | Response:
    try:
        result = record_staff_account_session_revocation_evidence(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            staff_id=staff_id,
            expected_version=request.expected_version,
            clock=clock,
            identifiers=identifiers,
            reason_text=request.reason_text,
        )
    except (
        StaffAccountLifecycleError,
        StaffAccountNotFoundError,
        StaffAccountVersionConflictError,
        SafePersistenceError,
    ) as exc:
        return _problem_for_lifecycle_error(exc)
    _lifecycle_response(result, response)
    return _lifecycle_body(session, result)
