from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict

from golden_rose.api.dependencies import get_settings
from golden_rose.config import Settings

router = APIRouter(prefix="/api/staff/v1", tags=["staff-auth"])

GOOGLE_OIDC_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


class StaffAuthConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auth_mode: Literal["synthetic", "staff_oidc"]
    provider: Literal["synthetic", "google", "unsupported"]
    google_client_id: str | None


@router.get("/staff-auth-config", response_model=StaffAuthConfigResponse)
def get_staff_auth_config(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> StaffAuthConfigResponse:
    response.headers["Cache-Control"] = "no-store"

    if settings.auth_mode == "synthetic":
        return StaffAuthConfigResponse(
            auth_mode="synthetic",
            provider="synthetic",
            google_client_id=None,
        )

    if settings.staff_oidc_issuer in GOOGLE_OIDC_ISSUERS and settings.staff_oidc_audience:
        return StaffAuthConfigResponse(
            auth_mode="staff_oidc",
            provider="google",
            google_client_id=settings.staff_oidc_audience,
        )

    return StaffAuthConfigResponse(
        auth_mode="staff_oidc",
        provider="unsupported",
        google_client_id=None,
    )
