from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict

from golden_rose.api.dependencies import get_settings, get_staff_principal
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings

router = APIRouter(prefix="/api/staff/v1", tags=["staff-environment"])


class StaffIdentityReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["local", "test", "develop", "production"]
    auth_mode: Literal["synthetic", "staff_oidc"]
    staff_identity_boundary: Literal[
        "synthetic_local_or_test",
        "synthetic_private_develop",
        "production_oidc_configured",
    ]
    production_staff_auth_ready: bool
    synthetic_staff_runtime_allowed: bool
    recovery_and_session_revocation_evidence_only: bool
    required_operator_actions: tuple[str, ...]


@router.get("/staff-identity-readiness", response_model=StaffIdentityReadinessResponse)
def get_staff_identity_readiness(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[StaffPrincipal, Depends(get_staff_principal)],
) -> StaffIdentityReadinessResponse:
    del principal
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"

    if settings.auth_mode == "staff_oidc":
        return StaffIdentityReadinessResponse(
            environment=settings.environment,
            auth_mode=settings.auth_mode,
            staff_identity_boundary="production_oidc_configured",
            production_staff_auth_ready=settings.environment == "production",
            synthetic_staff_runtime_allowed=False,
            recovery_and_session_revocation_evidence_only=True,
            required_operator_actions=(
                "create_staff_accounts_before_live_use",
                "confirm_mfa_claim_mapping",
                "record_recovery_and_session_revocation_provider_runbook",
            ),
        )

    if settings.environment == "develop":
        return StaffIdentityReadinessResponse(
            environment=settings.environment,
            auth_mode=settings.auth_mode,
            staff_identity_boundary="synthetic_private_develop",
            production_staff_auth_ready=False,
            synthetic_staff_runtime_allowed=True,
            recovery_and_session_revocation_evidence_only=True,
            required_operator_actions=(
                "replace_synthetic_staff_auth_before_production",
                "configure_staff_oidc_issuer_audience_and_jwks",
                "create_staff_accounts_before_live_use",
            ),
        )

    return StaffIdentityReadinessResponse(
        environment=settings.environment,
        auth_mode=settings.auth_mode,
        staff_identity_boundary="synthetic_local_or_test",
        production_staff_auth_ready=False,
        synthetic_staff_runtime_allowed=True,
        recovery_and_session_revocation_evidence_only=True,
        required_operator_actions=(
            "use_only_for_local_or_test",
            "configure_staff_oidc_for_production",
            "create_staff_accounts_before_live_use",
        ),
    )
