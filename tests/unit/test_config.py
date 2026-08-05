from typing import Literal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.config import Settings


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


def test_settings_repr_redacts_database_url() -> None:
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://sensitive-user:sensitive-pass@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
    )

    assert "sensitive-user" not in repr(settings)
    assert "sensitive-pass" not in repr(settings)
