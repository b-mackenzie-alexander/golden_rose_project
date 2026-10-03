from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_settings
from golden_rose.api.staff.auth_config import router
from golden_rose.config import Settings


def client_for(settings: Settings) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_staff_auth_config_reports_synthetic_without_provider_values() -> None:
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=UUID("22222222-2222-4222-8222-222222222222"),
    )

    with client_for(settings) as client:
        response = client.get("/api/staff/v1/staff-auth-config")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "auth_mode": "synthetic",
        "provider": "synthetic",
        "google_client_id": None,
    }


def test_staff_auth_config_exposes_only_google_client_id_for_google_oidc() -> None:
    settings = Settings(
        environment="production",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://accounts.google.com",
        staff_oidc_audience="google-client-id.apps.googleusercontent.com",
        staff_oidc_jwks_url="https://www.googleapis.com/oauth2/v3/certs",
    )

    with client_for(settings) as client:
        response = client.get("/api/staff/v1/staff-auth-config")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "auth_mode": "staff_oidc",
        "provider": "google",
        "google_client_id": "google-client-id.apps.googleusercontent.com",
    }
    assert "staff_oidc_issuer" not in response.text
    assert "staff_oidc_jwks_url" not in response.text


def test_staff_auth_config_fails_closed_for_unsupported_oidc_provider() -> None:
    settings = Settings(
        environment="production",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://golden_rose_app:test@localhost/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://identity.example.test",
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
    )

    with client_for(settings) as client:
        response = client.get("/api/staff/v1/staff-auth-config")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "auth_mode": "staff_oidc",
        "provider": "unsupported",
        "google_client_id": None,
    }
