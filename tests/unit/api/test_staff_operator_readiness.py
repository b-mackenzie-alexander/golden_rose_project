from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from golden_rose.api.dependencies import get_settings, get_staff_principal
from golden_rose.api.staff.operator_readiness import router
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings

ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
SYNTHETIC_STAFF_ID = UUID("22222222-2222-4222-8222-222222222222")


def client_for(settings: Settings) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="owner",
        permissions=frozenset({"staff_account:read"}),
    )
    return TestClient(app)


def local_synthetic_settings() -> Settings:
    return Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=SYNTHETIC_STAFF_ID,
    )


def develop_synthetic_settings() -> Settings:
    expires_at: Any = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return Settings(
        environment="develop",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=SYNTHETIC_STAFF_ID,
        deployment_target="gcp-develop-private-synthetic",
        public_environment_label="Non-production develop - fictional synthetic data only",
        deployed_image_digest="sha256:" + ("a" * 64),
        demo_access_enabled=True,
        demo_access_password=SecretStr("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
        demo_access_expires_at=expires_at,
    )


def production_oidc_settings() -> Settings:
    return Settings(
        environment="production",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://identity.example.test",
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
    )


def test_local_synthetic_staff_identity_readiness_is_no_store_and_not_production_ready() -> None:
    with client_for(local_synthetic_settings()) as client:
        response = client.get("/api/staff/v1/staff-identity-readiness")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.json() == {
        "environment": "local",
        "auth_mode": "synthetic",
        "staff_identity_boundary": "synthetic_local_or_test",
        "production_staff_auth_ready": False,
        "synthetic_staff_runtime_allowed": True,
        "recovery_and_session_revocation_evidence_only": True,
        "required_operator_actions": [
            "use_only_for_local_or_test",
            "configure_staff_oidc_for_production",
            "create_staff_accounts_before_live_use",
        ],
    }


def test_develop_synthetic_staff_identity_readiness_names_private_develop_boundary() -> None:
    with client_for(develop_synthetic_settings()) as client:
        response = client.get("/api/staff/v1/staff-identity-readiness")

    assert response.status_code == 200, response.text
    assert response.json()["staff_identity_boundary"] == "synthetic_private_develop"
    assert response.json()["production_staff_auth_ready"] is False
    assert response.json()["synthetic_staff_runtime_allowed"] is True
    assert response.json()["required_operator_actions"] == [
        "replace_synthetic_staff_auth_before_production",
        "configure_staff_oidc_issuer_audience_and_jwks",
        "create_staff_accounts_before_live_use",
    ]


def test_production_oidc_staff_identity_readiness_omits_provider_values() -> None:
    with client_for(production_oidc_settings()) as client:
        response = client.get("/api/staff/v1/staff-identity-readiness")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload == {
        "environment": "production",
        "auth_mode": "staff_oidc",
        "staff_identity_boundary": "production_oidc_configured",
        "production_staff_auth_ready": True,
        "synthetic_staff_runtime_allowed": False,
        "recovery_and_session_revocation_evidence_only": True,
        "required_operator_actions": [
            "create_staff_accounts_before_live_use",
            "confirm_mfa_claim_mapping",
            "record_recovery_and_session_revocation_provider_runbook",
        ],
    }
    assert "staff_oidc_issuer" not in payload
    assert "staff_oidc_audience" not in payload
    assert "staff_oidc_jwks_url" not in payload
