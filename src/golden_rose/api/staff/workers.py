"""Local/test canonical worker reads; permissions are not activated here."""

from uuid import UUID

from fastapi import APIRouter, Request

from golden_rose.api.staff.intake_workflows import SettingsDep, local_only
from golden_rose.api.staff.intakes import PrincipalDep, SessionDep
from golden_rose.api.staff.worker_schemas import (
    QueryWorkersRequest,
    WorkerContactDetail,
    WorkerDetail,
    WorkerPreferencesDetail,
    WorkerQueryPage,
    WorkerResidenceDetail,
)
from golden_rose.application.intake_access import record_worker_access
from golden_rose.application.query_workers import query_workers
from golden_rose.application.read_worker import read_worker

router = APIRouter(prefix="/api/staff/v1/workers", tags=["staff-workers"])


@router.post("/query", response_model=WorkerQueryPage)
def query(
    body: QueryWorkersRequest, session: SessionDep, principal: PrincipalDep, settings: SettingsDep
):
    local_only(settings)
    return query_workers(session=session, principal=principal, request=body)


@router.get("/{worker_id}", response_model=WorkerDetail)
def identity(worker_id: UUID, session: SessionDep, principal: PrincipalDep, settings: SettingsDep):
    local_only(settings)
    return read_worker(
        session=session, principal=principal, worker_id=worker_id, section="identity"
    )


@router.get("/{worker_id}/contact", response_model=WorkerContactDetail)
def contact(worker_id: UUID, session: SessionDep, principal: PrincipalDep, settings: SettingsDep):
    local_only(settings)
    return read_worker(session=session, principal=principal, worker_id=worker_id, section="contact")


@router.get(
    "/{worker_id}/residence", response_model=WorkerResidenceDetail, response_model_exclude_none=True
)
def residence(
    worker_id: UUID,
    session: SessionDep,
    principal: PrincipalDep,
    settings: SettingsDep,
    request: Request,
):
    local_only(settings)
    result = WorkerResidenceDetail.model_validate(
        read_worker(
            session=session,
            principal=principal,
            worker_id=worker_id,
            section="residence",
        )
    )
    sink = getattr(request.app.state, "worker_access_sink", record_worker_access)
    sink(actor_id=principal.actor_id, worker_id=worker_id)
    return result


@router.get(
    "/{worker_id}/preferences",
    response_model=WorkerPreferencesDetail,
    response_model_exclude_none=True,
)
def preferences(
    worker_id: UUID, session: SessionDep, principal: PrincipalDep, settings: SettingsDep
):
    local_only(settings)
    return read_worker(
        session=session, principal=principal, worker_id=worker_id, section="preferences"
    )
