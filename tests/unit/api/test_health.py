import base64
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

import golden_rose.application.create_draft_employer as create_draft_employer_module
import golden_rose.application.create_employer_contact as create_employer_contact_module
import golden_rose.application.get_employer as get_employer_module
import golden_rose.application.get_employer_contact as get_employer_contact_module
import golden_rose.application.query_employer_contacts as query_employer_contacts_module
import golden_rose.application.revise_draft_employer as revise_draft_employer_module
import golden_rose.application.search_employers as search_employers_module
from golden_rose.main import create_app


class FakeEngine:
    def __init__(self) -> None:
        self.dispose_calls = 0

    def dispose(self) -> None:
        self.dispose_calls += 1


class FakeScalarResult:
    def __init__(self, value: str) -> None:
        self.value = value

    def scalar_one(self) -> str:
        return self.value


class FakeConnection:
    def __init__(self, revision: str = "0011_staff_account_lifecycle") -> None:
        self.revision = revision
        self.statements: list[str] = []

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, statement: object) -> FakeScalarResult:
        statement_text = str(statement)
        self.statements.append(statement_text)
        return FakeScalarResult(self.revision)


class ReadinessEngine(FakeEngine):
    def __init__(self, connection: FakeConnection) -> None:
        super().__init__()
        self.connection = connection

    def connect(self) -> FakeConnection:
        return self.connection


def _set_local_env(monkeypatch) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))


def _set_develop_env(monkeypatch) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "develop")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", str(uuid4()))
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYMENT_TARGET", "gcp-develop-private-synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL",
        "Non-production develop — fictional synthetic data only",
    )
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.setenv("GOLDEN_ROSE_DEMO_ACCESS_ENABLED", "true")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD",
        base64.urlsafe_b64encode(b"h" * 32).decode("ascii").rstrip("="),
    )
    monkeypatch.setenv(
        "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT",
        (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def test_health_is_database_independent_and_value_safe(monkeypatch) -> None:
    _set_local_env(monkeypatch)
    fake_engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: fake_engine)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {"status": "ok"}
    assert "postgresql" not in response.text
    assert "synthetic" not in response.text


def test_readiness_checks_database_schema_without_business_mutation(monkeypatch) -> None:
    _set_develop_env(monkeypatch)
    connection = FakeConnection()
    engine: Any = ReadinessEngine(connection)
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        response = client.get("/readiness")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {"status": "ready"}
    assert len(connection.statements) == 1
    statement = connection.statements[0].lower()
    assert "alembic_version" in statement
    assert "insert" not in statement
    assert "update" not in statement
    assert "delete" not in statement
    assert "command_receipts" not in statement
    assert "audit_events" not in statement
    assert "employers" not in statement


def test_readiness_failure_is_static_and_value_safe(monkeypatch) -> None:
    class BrokenEngine(FakeEngine):
        def connect(self) -> FakeConnection:
            raise RuntimeError(
                "psycopg postgresql+psycopg://sensitive-user:sensitive-pass@db/sensitive"
            )

    _set_develop_env(monkeypatch)
    engine: Any = BrokenEngine()
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/readiness")

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "status": "not_ready",
        "reason": "database_schema_unavailable",
    }
    assert "psycopg" not in response.text
    assert "postgresql" not in response.text
    assert "sensitive-user" not in response.text
    assert "sensitive-pass" not in response.text


def test_health_and_readiness_do_not_run_synthetic_qualification(monkeypatch) -> None:
    def explode_if_qualification_runs(*args: object, **kwargs: object) -> None:
        raise AssertionError("health/readiness must not run synthetic qualification")

    monkeypatch.setattr(
        create_draft_employer_module,
        "create_draft_employer",
        explode_if_qualification_runs,
    )
    monkeypatch.setattr(
        create_employer_contact_module,
        "create_employer_contact",
        explode_if_qualification_runs,
    )
    monkeypatch.setattr(get_employer_module, "get_employer", explode_if_qualification_runs)
    monkeypatch.setattr(
        get_employer_contact_module,
        "get_employer_contact",
        explode_if_qualification_runs,
    )
    monkeypatch.setattr(
        query_employer_contacts_module,
        "query_employer_contacts",
        explode_if_qualification_runs,
    )
    monkeypatch.setattr(
        revise_draft_employer_module,
        "revise_draft_employer",
        explode_if_qualification_runs,
    )
    monkeypatch.setattr(search_employers_module, "search_employers", explode_if_qualification_runs)

    _set_develop_env(monkeypatch)
    connection = FakeConnection()
    engine: Any = ReadinessEngine(connection)
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        health_response = client.get("/health")
        readiness_response = client.get("/readiness")

    assert health_response.status_code == 200
    assert readiness_response.status_code == 200
    assert connection.statements == ["SELECT version_num FROM alembic_version"]
