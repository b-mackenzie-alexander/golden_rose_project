"""Read-only staff operations projections."""

from typing import Annotated

from fastapi import APIRouter, Query

from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import PrincipalDep, SessionDep
from golden_rose.api.staff.operations_schemas import OperationsProjectionResponse
from golden_rose.application.operations_projection import query_operations_projection

router = APIRouter(prefix="/api/staff/v1/operations", tags=["staff-operations"])


@router.get("/projection", response_model=OperationsProjectionResponse)
def operations_projection(
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
    page_size: Annotated[int, Query(ge=1, le=50)] = 50,
):
    local_only(settings)
    return query_operations_projection(session=session, principal=principal, page_size=page_size)
