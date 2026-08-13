from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict

from golden_rose.api.dependencies import get_settings
from golden_rose.config import Settings

router = APIRouter(prefix="/api/staff/v1", tags=["staff-environment"])


class EnvironmentMarkerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["develop"]
    label: str
    data_boundary: Literal["fictional-synthetic-only"]


@router.get("/environment", response_model=EnvironmentMarkerResponse)
def get_environment_marker(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> EnvironmentMarkerResponse:
    response.headers["Cache-Control"] = "no-store"
    return EnvironmentMarkerResponse(
        environment="develop",
        label=settings.public_environment_label or "",
        data_boundary="fictional-synthetic-only",
    )
