"""Current-facts review is separate from original intake review and finalization."""

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from golden_rose.api.staff.canonical_correction_schemas import (
    CanonicalReviewResponse,
    CanonicalReviewState,
    ReviewCanonicalOutputsRequest,
)
from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import ClockDep, KeyDep, PrincipalDep, SessionDep
from golden_rose.application.canonical_history import read_current_review_history
from golden_rose.application.review_canonical_outputs import (
    execute_current_review,
    read_current_review,
)

router = APIRouter(prefix="/api/staff/v1/intake-finalizations", tags=["staff-canonical-review"])


@router.get("/{intake_id}/current-review", response_model=CanonicalReviewState)
def state(intake_id: UUID, session: SessionDep, principal: PrincipalDep, settings: SettingsDep):
    local_only(settings)
    return read_current_review(session=session, principal=principal, intake_id=intake_id)


@router.post("/{intake_id}/current-reviews", response_model=CanonicalReviewResponse)
def review(
    intake_id: UUID,
    body: ReviewCanonicalOutputsRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_current_review(
        session=session,
        principal=principal,
        intake_id=intake_id,
        command_id=command_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        status_code=200 if replayed else 201,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.get("/{intake_id}/current-reviews/{review_id}/restricted")
def history(
    intake_id: UUID,
    review_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
):
    local_only(settings)
    return read_current_review_history(
        session=session, principal=principal, intake_id=intake_id, review_id=review_id
    )
