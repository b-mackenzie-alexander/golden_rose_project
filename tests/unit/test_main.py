from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
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


def test_create_app_rejects_production_synthetic_auth_before_opening_database_engine(
    monkeypatch,
) -> None:
    engine_factory_calls = 0

    def engine_factory():
        nonlocal engine_factory_calls
        engine_factory_calls += 1
        raise AssertionError("engine factory should not be called")

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "production")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))

    with pytest.raises(ValidationError, match="synthetic auth_mode is not allowed"):
        create_app(engine_factory=engine_factory)

    assert engine_factory_calls == 0


def test_application_lifespan_creates_engine_once_and_disposes_once(monkeypatch) -> None:
    class FakeEngine:
        def __init__(self) -> None:
            self.dispose_calls = 0

        def dispose(self) -> None:
            self.dispose_calls += 1

    engine_factory_calls = 0
    fake_engine = FakeEngine()

    def engine_factory():
        nonlocal engine_factory_calls
        engine_factory_calls += 1
        return fake_engine

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))

    app = create_app(engine_factory=engine_factory)

    with TestClient(app):
        assert engine_factory_calls == 1
        assert app.state.db_engine is fake_engine
        assert fake_engine.dispose_calls == 0

    assert fake_engine.dispose_calls == 1


def test_lifespan_shutdown_disposes_engine_for_container_termination(monkeypatch) -> None:
    class FakeEngine:
        def __init__(self) -> None:
            self.dispose_calls = 0

        def dispose(self) -> None:
            self.dispose_calls += 1

    fake_engine = FakeEngine()

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))

    fake_engine_typed: Any = fake_engine
    app = create_app(engine_factory=lambda: fake_engine_typed)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert fake_engine.dispose_calls == 0

    assert fake_engine.dispose_calls == 1
    assert app.state.db_engine is fake_engine


def test_develop_app_exposes_value_safe_non_production_marker(monkeypatch) -> None:
    class FakeEngine:
        def dispose(self) -> None:
            pass

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "develop")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://sensitive-user:sensitive-pass@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYMENT_TARGET", "gcp-develop-private-synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.setenv(
        "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL",
        "Non-production develop — fictional synthetic data only",
    )

    fake_engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: fake_engine)

    with TestClient(app) as client:
        response = client.get("/api/staff/v1/environment")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "environment": "develop",
        "label": "Non-production develop — fictional synthetic data only",
        "data_boundary": "fictional-synthetic-only",
    }
    serialized_response = response.text
    assert "sensitive-user" not in serialized_response
    assert "sensitive-pass" not in serialized_response
    assert "gcp-develop-private-synthetic" not in serialized_response


@pytest.mark.parametrize("environment", ["local", "test"])
def test_environment_marker_is_not_registered_outside_develop(
    monkeypatch,
    environment: str,
) -> None:
    class FakeEngine:
        def dispose(self) -> None:
            pass

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", environment)
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))

    fake_engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: fake_engine)

    with TestClient(app) as client:
        response = client.get("/api/staff/v1/environment")

    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
    assert "develop" not in response.text
    assert "fictional-synthetic-only" not in response.text


def test_startup_engine_factory_failure_prevents_serving_without_partial_app_state(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))

    app = create_app(engine_factory=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError, match="boom"), TestClient(app):
        pass

    assert not hasattr(app.state, "db_engine")
