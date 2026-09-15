"""Explicit canonical correction routes; no default permission activation."""

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from golden_rose.api.staff import canonical_correction_schemas as schemas
from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import ClockDep, KeyDep, PrincipalDep, SessionDep
from golden_rose.application.canonical_history import read_correction_history
from golden_rose.application.correct_canonical_records import execute_correction

router = APIRouter(prefix="/api/staff/v1", tags=["staff-canonical-corrections"])


@router.post("/workers/{worker_id}/corrections", response_model=schemas.CanonicalCorrectionResponse)
def correct_worker(
    worker_id: UUID,
    body: schemas.CorrectWorkerRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_worker",
        parent_id=worker_id,
        target_id=worker_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/workers/{worker_id}/contact/corrections", response_model=schemas.CanonicalCorrectionResponse
)
def correct_worker_contact(
    worker_id: UUID,
    body: schemas.CorrectWorkerContactRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_worker_contact",
        parent_id=worker_id,
        target_id=worker_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/workers/{worker_id}/residence/corrections", response_model=schemas.CanonicalCorrectionResponse
)
def correct_worker_residence(
    worker_id: UUID,
    body: schemas.CorrectWorkerResidenceRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_worker_residence",
        parent_id=worker_id,
        target_id=worker_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/workers/{worker_id}/preferences/corrections",
    response_model=schemas.CanonicalCorrectionResponse,
)
def correct_worker_preferences(
    worker_id: UUID,
    body: schemas.CorrectWorkerPreferencesRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_worker_preferences",
        parent_id=worker_id,
        target_id=worker_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/employers/{employer_id}/contacts/{contact_id}/details/corrections",
    response_model=schemas.CanonicalCorrectionResponse,
)
def correct_contact_details(
    employer_id: UUID,
    contact_id: UUID,
    body: schemas.CorrectContactDetailsRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_contact_details",
        parent_id=employer_id,
        target_id=contact_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/employers/{employer_id}/contacts/{contact_id}/details/address/corrections",
    response_model=schemas.CanonicalCorrectionResponse,
)
def correct_contact_address(
    employer_id: UUID,
    contact_id: UUID,
    body: schemas.CorrectContactAddressRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_contact_address",
        parent_id=employer_id,
        target_id=contact_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/employers/{employer_id}/addresses/{address_id}/corrections",
    response_model=schemas.CanonicalCorrectionResponse,
)
def correct_employer_address(
    employer_id: UUID,
    address_id: UUID,
    body: schemas.CorrectEmployerAddressRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_employer_address",
        parent_id=employer_id,
        target_id=address_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/employers/{employer_id}/worksites/{worksite_id}/address/corrections",
    response_model=schemas.CanonicalCorrectionResponse,
)
def correct_worksite_address(
    employer_id: UUID,
    worksite_id: UUID,
    body: schemas.CorrectWorksiteAddressRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_worksite_address",
        parent_id=employer_id,
        target_id=worksite_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.post(
    "/employers/{employer_id}/requests/{request_id}/corrections",
    response_model=schemas.CanonicalCorrectionResponse,
)
def correct_staffing_request(
    employer_id: UUID,
    request_id: UUID,
    body: schemas.CorrectStaffingRequestRequest,
    session: SessionDep,
    principal: PrincipalDep,
    command_id: KeyDep,
    clock: ClockDep,
    settings: SettingsDep,
):
    local_only(settings)
    result, replayed = execute_correction(
        session=session,
        principal=principal,
        command_id=command_id,
        command_type="correct_staffing_request",
        parent_id=employer_id,
        target_id=request_id,
        request=body,
        clock=clock,
    )
    return JSONResponse(
        result,
        headers={
            "Idempotency-Replayed": str(replayed).lower(),
            "Idempotency-Result-Version": str(result["result_record_version"]),
        },
    )


@router.get("/canonical-corrections/{event_id}")
def history(event_id: UUID, session: SessionDep, principal: PrincipalDep, settings: SettingsDep):
    local_only(settings)
    return read_correction_history(session=session, principal=principal, event_id=event_id)
