from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.main import create_app


def test_create_app_rejects_production_synthetic_auth_before_serving(monkeypatch) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "production")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))

    with pytest.raises(ValidationError, match="synthetic auth_mode is not allowed"):
        create_app()
