import base64
from typing import Any, cast
from uuid import uuid4

from fastapi import Response
from pydantic import SecretStr

from golden_rose.api.environment import get_environment_marker
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import Settings


def _principal() -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=uuid4(),
        role_name="staff_operator",
        permissions=frozenset(),
    )


def _valid_demo_password() -> str:
    return base64.urlsafe_b64encode(b"m" * 32).decode("ascii").rstrip("=")


def test_environment_marker_reports_live_data_staff_pilot_boundary_for_production() -> None:
    response = Response()
    settings = Settings(
        environment="production",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://accounts.example.test",
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://accounts.example.test/.well-known/jwks.json",
        public_environment_label="Controlled live-data staff pilot",
        deployed_image_digest="sha256:" + "a" * 64,
    )

    marker = get_environment_marker(response=response, settings=settings, principal=_principal())

    assert marker.model_dump() == {
        "environment": "production",
        "label": "Controlled live-data staff pilot",
        "data_boundary": "controlled-live-data-staff-pilot",
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Vary"] == "Authorization"


def test_environment_marker_preserves_develop_boundary() -> None:
    response = Response()
    settings = Settings(
        environment="develop",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
        deployment_target="gcp-develop-private-synthetic",
        public_environment_label="Non-production develop - fictional synthetic data only",
        deployed_image_digest="sha256:" + "b" * 64,
        demo_access_enabled=True,
        demo_access_password=SecretStr(_valid_demo_password()),
        demo_access_expires_at=cast(Any, "2026-10-02T00:00:00Z"),
    )

    marker = get_environment_marker(response=response, settings=settings, principal=_principal())

    assert marker.model_dump() == {
        "environment": "develop",
        "label": "Non-production develop - fictional synthetic data only",
        "data_boundary": "fictional-synthetic-only",
    }
