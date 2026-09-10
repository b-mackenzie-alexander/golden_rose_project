import base64
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from golden_rose.config import Settings


def _valid_demo_password() -> str:
    return base64.urlsafe_b64encode(b"f" * 32).decode("ascii").rstrip("=")


def _future_demo_expiry() -> str:
    return (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _model_input(value: object) -> Any:
    """Keep runtime coercion probes explicit to the static type checker."""
    return value


@pytest.mark.parametrize(
    "password",
    [
        base64.urlsafe_b64encode(b"f" * 31).decode("ascii").rstrip("="),
        base64.urlsafe_b64encode(b"f" * 32).decode("ascii"),
        "!" * 43,
    ],
)
def test_develop_rejects_noncanonical_or_short_demo_password(password: str) -> None:
    with pytest.raises(ValidationError, match="canonical unpadded base64url"):
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Non-production develop — fictional synthetic data only",
            deployed_image_digest="sha256:" + "a" * 64,
            demo_access_password=_model_input(password),
            demo_access_expires_at=_model_input(_future_demo_expiry()),
        )


@pytest.mark.parametrize(
    "expires_at",
    [
        "2030-01-01T00:00:00+00:00",
        "2030-01-01T00:00:00.000Z",
        "2030-01-01",
    ],
)
def test_demo_access_expiry_requires_strict_utc_rfc3339(expires_at: str) -> None:
    with pytest.raises(ValidationError, match="strict UTC RFC 3339"):
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Non-production develop — fictional synthetic data only",
            deployed_image_digest="sha256:" + "a" * 64,
            demo_access_password=_model_input(_valid_demo_password()),
            demo_access_expires_at=_model_input(expires_at),
        )


def test_develop_rejects_demo_access_expiry_more_than_seven_days_away() -> None:
    expires_at = (datetime.now(UTC) + timedelta(days=7, minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    with pytest.raises(ValidationError, match="no more than seven days"):
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Non-production develop — fictional synthetic data only",
            deployed_image_digest="sha256:" + "a" * 64,
            demo_access_enabled=True,
            demo_access_password=_model_input(_valid_demo_password()),
            demo_access_expires_at=_model_input(expires_at),
        )


def test_develop_requires_secret_shared_access_configuration() -> None:
    develop_settings = {
        "environment": "develop",
        "auth_mode": "synthetic",
        "database_url": "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        "synthetic_staff_id": uuid4(),
        "deployment_target": "gcp-develop-private-synthetic",
        "public_environment_label": "Non-production develop — fictional synthetic data only",
        "deployed_image_digest": "sha256:" + "a" * 64,
        "demo_access_enabled": True,
    }

    with pytest.raises(ValidationError, match="demo access"):
        Settings(**develop_settings)  # type: ignore[arg-type]

    settings = Settings(
        **develop_settings,  # type: ignore[arg-type]
        demo_access_password=_model_input(_valid_demo_password()),
        demo_access_expires_at=_model_input(_future_demo_expiry()),
    )

    assert isinstance(settings.demo_access_password, SecretStr)
    assert _valid_demo_password() not in repr(settings)


def test_develop_rejects_demo_credentials_without_enabled_shared_gate() -> None:
    with pytest.raises(ValidationError, match="demo access gate must be enabled"):
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Non-production develop — fictional synthetic data only",
            deployed_image_digest="sha256:" + "a" * 64,
            demo_access_password=_model_input(_valid_demo_password()),
            demo_access_expires_at=_model_input(_future_demo_expiry()),
        )


def test_production_forbids_demo_access_configuration() -> None:
    with pytest.raises(ValidationError, match="demo access.*forbidden in production"):
        Settings(
            environment="production",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            demo_access_enabled=True,
            demo_access_password=_model_input(_valid_demo_password()),
            demo_access_expires_at=_model_input(_future_demo_expiry()),
        )


def test_production_rejects_synthetic_auth() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment="production",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
        )

    assert "synthetic" in str(exc_info.value)


@pytest.mark.parametrize("environment", ["local", "test"])
def test_local_and_test_allow_synthetic_auth(
    environment: Literal["local", "test"],
) -> None:
    settings = Settings(
        environment=environment,
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
    )

    assert settings.environment == environment
    assert settings.auth_mode == "synthetic"


def test_develop_requires_explicit_private_synthetic_cloud_posture() -> None:
    with pytest.raises(ValidationError) as missing_posture:
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
        )

    missing_message = str(missing_posture.value)
    assert "develop deployment target" in missing_message
    assert "synthetic" in missing_message

    settings = Settings(
        environment="develop",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
        deployment_target="gcp-develop-private-synthetic",
        public_environment_label="Non-production develop — fictional synthetic data only",
        deployed_image_digest="sha256:" + "a" * 64,
        demo_access_enabled=True,
        demo_access_password=_model_input(_valid_demo_password()),
        demo_access_expires_at=_model_input(_future_demo_expiry()),
    )

    assert settings.environment == "develop"
    assert settings.deployment_target == "gcp-develop-private-synthetic"
    assert settings.public_environment_label == (
        "Non-production develop — fictional synthetic data only"
    )

    for unsafe_target in ["", "local", "gcp-develop-public", "production"]:
        with pytest.raises(ValidationError) as unsafe_posture:
            Settings(
                environment="develop",
                auth_mode="synthetic",
                database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
                synthetic_staff_id=uuid4(),
                deployment_target=unsafe_target,
                public_environment_label="Non-production develop — fictional synthetic data only",
                deployed_image_digest="sha256:" + "a" * 64,
            )

        assert "develop deployment target" in str(unsafe_posture.value)

    with pytest.raises(ValidationError) as unlabeled_posture:
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Production",
            deployed_image_digest="sha256:" + "a" * 64,
        )

    unlabeled_message = str(unlabeled_posture.value)
    assert "non-production" in unlabeled_message
    assert "synthetic" in unlabeled_message

    with pytest.raises(ValidationError, match="deployed_image_digest"):
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Non-production develop — fictional synthetic data only",
        )

    with pytest.raises(ValidationError, match="immutable sha256"):
        Settings(
            environment="develop",
            auth_mode="synthetic",
            database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
            synthetic_staff_id=uuid4(),
            deployment_target="gcp-develop-private-synthetic",
            public_environment_label="Non-production develop — fictional synthetic data only",
            deployed_image_digest="staff-tracer:latest",
            demo_access_enabled=True,
            demo_access_password=_model_input(_valid_demo_password()),
            demo_access_expires_at=_model_input(_future_demo_expiry()),
        )


def test_settings_repr_redacts_database_url() -> None:
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://sensitive-user:sensitive-pass@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
    )

    assert "sensitive-user" not in repr(settings)
    assert "sensitive-pass" not in repr(settings)
