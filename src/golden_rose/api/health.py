from typing import Literal

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from golden_rose.config import Settings

router = APIRouter(tags=["runtime-health"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready"]


EXPECTED_SCHEMA_REVISION = "0013_shift_need_foundation"


@router.get("/health", response_model=HealthResponse)
def get_health(response: Response) -> HealthResponse:
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse(status="ok")


@router.get("/readiness", response_model=ReadinessResponse)
def get_readiness(request: Request, response: Response) -> ReadinessResponse | JSONResponse:
    try:
        Settings()  # type: ignore[call-arg]
        engine = request.app.state.db_engine
        with engine.connect() as connection:
            schema_revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
    except Exception:
        return JSONResponse(
            status_code=503,
            headers={"Cache-Control": "no-store"},
            content={
                "status": "not_ready",
                "reason": "database_schema_unavailable",
            },
        )

    if schema_revision != EXPECTED_SCHEMA_REVISION:
        return JSONResponse(
            status_code=503,
            headers={"Cache-Control": "no-store"},
            content={
                "status": "not_ready",
                "reason": "database_schema_unavailable",
            },
        )

    response.headers["Cache-Control"] = "no-store"
    return ReadinessResponse(status="ready")
