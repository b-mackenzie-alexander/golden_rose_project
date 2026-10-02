from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict

from golden_rose.api.dependencies import get_settings, get_staff_principal
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings

router = APIRouter(prefix="/api/staff/v1", tags=["staff-environment"])


class EnvironmentMarkerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["develop", "production"]
    label: str
    data_boundary: Literal["fictional-synthetic-only", "controlled-live-data-staff-pilot"]


@router.get("/environment", response_model=EnvironmentMarkerResponse)
def get_environment_marker(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> EnvironmentMarkerResponse:
    del principal
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"
    return EnvironmentMarkerResponse(
        environment=settings.environment if settings.environment == "production" else "develop",
        label=settings.public_environment_label or "",
        data_boundary=(
            "controlled-live-data-staff-pilot"
            if settings.environment == "production"
            else "fictional-synthetic-only"
        ),
    )
