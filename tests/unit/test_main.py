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
