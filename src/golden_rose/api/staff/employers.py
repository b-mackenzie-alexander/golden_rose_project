from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
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
from golden_rose.api.staff.schemas import (
    CreateDraftEmployerRequest,
    DraftEmployerResponse,
    EmployerContactCreateRequest,
    EmployerContactQueryPageResponse,
    EmployerContactQueryRequest,
    EmployerContactResponse,
    EmployerContactSummaryResponse,
    EmployerDetailResponse,
    EmployerSearchItemResponse,
    EmployerSearchPageResponse,
    ReviseDraftEmployerRequest,
    SearchEmployersRequest,
)
from golden_rose.application.create_draft_employer import create_draft_employer
from golden_rose.application.create_employer_contact import create_employer_contact
from golden_rose.application.errors import (
    EmployerNotFoundError,
    EmployerVersionConflictError,
    SafePersistenceError,
)
from golden_rose.application.get_employer import get_employer
from golden_rose.application.get_employer_contact import get_employer_contact
from golden_rose.application.query_employer_contacts import query_employer_contacts
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.application.search_employers import search_employers
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.config import Settings
from golden_rose.identifiers import IdentifierFactory

router = APIRouter(prefix="/api/staff/v1/employers", tags=["staff-employers"])


@router.post(
    "/{employer_id}/contacts",
    response_model=EmployerContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_staff_employer_contact(
    employer_id: UUID,
    request: EmployerContactCreateRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmployerContactResponse | Response:
    try:
        result = create_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            command_id=idempotency_key,
            full_name=request.full_name,
            clock=clock,
            identifiers=identifiers,
            environment=settings.environment,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except EmployerNotFoundError:
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="employer not found",
            type_="https://golden-rose.local/problems/employer-not-found",
        )
    except ValueError:
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="request validation failed",
            type_="https://golden-rose.local/problems/request-validation",
        )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Idempotency-Result-Version"] = str(result.result_record_version)
    if result.replayed:
        response.headers["Idempotency-Replayed"] = "true"
    return EmployerContactResponse.model_validate(result.contact)


@router.post(
    "/{employer_id}/contacts/query",
    response_model=EmployerContactQueryPageResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_employer_contact_query(
    employer_id: UUID,
    request: EmployerContactQueryRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> EmployerContactQueryPageResponse | Response:
    try:
        page = query_employer_contacts(
            session=session,
            principal=principal,
            employer_id=employer_id,
            page_size=request.page_size,
            cursor=request.cursor,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except EmployerNotFoundError:
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="employer not found",
            type_="https://golden-rose.local/problems/employer-not-found",
        )
    except ValueError:
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="request validation failed",
            type_="https://golden-rose.local/problems/request-validation",
        )
    except SafePersistenceError:
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    except Exception:
        return no_store_problem_response(
            status_code=500,
            title="Internal Server Error",
            detail="internal server error",
            type_="https://golden-rose.local/problems/internal-error",
        )
    response.headers["Cache-Control"] = "no-store"
    return EmployerContactQueryPageResponse(
        items=[EmployerContactSummaryResponse.model_validate(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    "/{employer_id}/contacts/{employer_contact_id}",
    response_model=EmployerContactResponse,
    status_code=status.HTTP_200_OK,
)
def get_staff_employer_contact(
    employer_id: UUID,
    employer_contact_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> EmployerContactResponse | Response:
    try:
        contact = get_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            employer_contact_id=employer_contact_id,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except EmployerNotFoundError:
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="employer contact not found",
            type_="https://golden-rose.local/problems/employer-contact-not-found",
        )
    except SafePersistenceError:
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    except Exception:
        return no_store_problem_response(
            status_code=500,
            title="Internal Server Error",
            detail="internal server error",
            type_="https://golden-rose.local/problems/internal-error",
        )
    response.headers["Cache-Control"] = "no-store"
    return EmployerContactResponse.model_validate(contact)


@router.post("", response_model=DraftEmployerResponse, status_code=status.HTTP_201_CREATED)
def post_staff_employer(
    request: CreateDraftEmployerRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    identifiers: Annotated[IdentifierFactory, Depends(get_identifier_factory)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DraftEmployerResponse:
    result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=idempotency_key,
        employer_type=request.employer_type,
        display_name=request.display_name,
        clock=clock,
        identifiers=identifiers,
        environment=settings.environment,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Idempotency-Result-Version"] = str(result.result_record_version)
    if result.replayed:
        response.headers["Idempotency-Replayed"] = "true"
    return DraftEmployerResponse.model_validate(result.employer)


@router.post("/search", response_model=EmployerSearchPageResponse, status_code=status.HTTP_200_OK)
def post_staff_employer_search(
    request: SearchEmployersRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> EmployerSearchPageResponse | Response:
    try:
        page = search_employers(
            session=session,
            principal=principal,
            request=request,
        )
    except PermissionError:
        return no_store_problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )
    except ValueError:
        return no_store_problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="request validation failed",
            type_="https://golden-rose.local/problems/request-validation",
        )
    except SafePersistenceError:
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    except Exception:
        return no_store_problem_response(
            status_code=500,
            title="Internal Server Error",
            detail="internal server error",
            type_="https://golden-rose.local/problems/internal-error",
        )
    response.headers["Cache-Control"] = "no-store"
    return EmployerSearchPageResponse(
        items=[EmployerSearchItemResponse.model_validate(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.post(
    "/{employer_id}/revisions",
    response_model=EmployerDetailResponse,
    status_code=status.HTTP_200_OK,
)
def post_staff_employer_revision(
    employer_id: UUID,
    request: ReviseDraftEmployerRequest,
    response: Response,
    idempotency_key: Annotated[UUID, Depends(get_idempotency_key)],
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    clock: Annotated[Clock, Depends(get_clock)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmployerDetailResponse | Response:
    try:
        result = revise_draft_employer(
            session=session,
            principal=principal,
            command_id=idempotency_key,
            employer_id=employer_id,
            expected_version=request.expected_version,
            employer_type=request.employer_type,
            display_name=request.display_name,
            clock=clock,
            environment=settings.environment,
        )
    except EmployerNotFoundError:
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="employer not found",
            type_="https://golden-rose.local/problems/employer-not-found",
        )
    except EmployerVersionConflictError:
        return no_store_problem_response(
            status_code=412,
            title="Precondition Failed",
            detail="employer version conflict",
            type_="https://golden-rose.local/problems/employer-version-conflict",
        )
    except SafePersistenceError:
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )
    except RuntimeError as exc:
        if str(exc) == "idempotency conflict":
            return no_store_problem_response(
                status_code=409,
                title="Conflict",
                detail="idempotency conflict",
                type_="https://golden-rose.local/problems/idempotency-conflict",
            )
        if str(exc) == "employer revision requires a change":
            return no_store_problem_response(
                status_code=422,
                title="Unprocessable Entity",
                detail="employer revision requires a change",
                type_="https://golden-rose.local/problems/employer-revision-noop",
            )
        raise
    response.headers["Cache-Control"] = "no-store"
    response.headers["Idempotency-Result-Version"] = str(result.result_record_version)
    if result.replayed:
        response.headers["Idempotency-Replayed"] = "true"
    return EmployerDetailResponse.model_validate(result.employer)


@router.get("/{employer_id}", response_model=EmployerDetailResponse, status_code=status.HTTP_200_OK)
def get_staff_employer(
    employer_id: UUID,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> EmployerDetailResponse | Response:
    try:
        employer = get_employer(
            session=session,
            principal=principal,
            employer_id=employer_id,
        )
    except EmployerNotFoundError:
        return no_store_problem_response(
            status_code=404,
            title="Not Found",
            detail="employer not found",
            type_="https://golden-rose.local/problems/employer-not-found",
        )
    response.headers["Cache-Control"] = "no-store"
    return EmployerDetailResponse.model_validate(employer)
