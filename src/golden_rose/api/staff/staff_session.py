from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import get_db_session, get_settings, get_staff_principal
from golden_rose.api.errors import no_store_problem_response
from golden_rose.api.staff.schemas import (
    StaffAccountResponse,
    StaffDelegationResponse,
    StaffSessionResponse,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings
from golden_rose.persistence.staff_accounts import (
    get_staff_account_by_id,
    list_active_staff_permission_grants,
    list_staff_delegations,
)

router = APIRouter(prefix="/api/staff/v1/session", tags=["staff-session"])


def _read_response(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"


@router.get("", response_model=StaffSessionResponse)
def get_staff_session(
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StaffSessionResponse | Response:
    try:
        try:
            account = get_staff_account_by_id(session=session, staff_id=principal.actor_id)
        except NoResultFound:
            account = None
        delegations = (
            tuple(list_staff_delegations(session=session, staff_id=principal.actor_id))
            if account is not None
            else ()
        )
    except SQLAlchemyError:
        return no_store_problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )

    _read_response(response)
    return StaffSessionResponse(
        actor_id=principal.actor_id,
        role_name=principal.role_name,
        permission_names=tuple(sorted(principal.permissions)),
        auth_context=settings.auth_mode,
        account=StaffAccountResponse.model_validate(
            {
                **asdict(account),
                "permission_names": tuple(
                    sorted(
                        list_active_staff_permission_grants(
                            session=session, staff_id=account.staff_id
                        )
                    )
                ),
            }
        )
        if account is not None
        else None,
        delegations=tuple(StaffDelegationResponse.model_validate(item) for item in delegations),
    )
