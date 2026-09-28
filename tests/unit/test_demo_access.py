import base64
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

import golden_rose.demo_access as demo_access_module
from golden_rose.api.dependencies import get_db_session
from golden_rose.main import create_app

_DEMO_USERNAME = "golden-rose-demo"
_DEMO_PASSWORD = base64.urlsafe_b64encode(b"d" * 32).decode("ascii").rstrip("=")
_CHALLENGE = 'Basic realm="Golden Rose synthetic develop", charset="UTF-8"'


class FakeEngine:
    def dispose(self) -> None:
        pass


class FakeScalarResult:
    def scalar_one(self) -> str:
        return "0011_staff_account_lifecycle"


class FakeConnection:
    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, statement: object) -> FakeScalarResult:
        return FakeScalarResult()


class ReadinessEngine(FakeEngine):
    def connect(self) -> FakeConnection:
        return FakeConnection()


class NoDatabaseSession:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"database access occurred through {name}")


def _basic(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


def _set_develop_env(
    monkeypatch: Any,
    static_assets_path: Path | None = None,
    *,
    expires_at: str | None = None,
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "develop")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv(
        "GOLDEN_ROSE_SYNTHETIC_STAFF_ID",
        "22222222-2222-4222-8222-222222222222",
    )
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYMENT_TARGET", "gcp-develop-private-synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL",
        "Non-production develop — fictional synthetic data only",
    )
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.setenv("GOLDEN_ROSE_DEMO_ACCESS_ENABLED", "true")
    monkeypatch.setenv("GOLDEN_ROSE_DEMO_ACCESS_PASSWORD", _DEMO_PASSWORD)
    monkeypatch.setenv(
        "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT",
        expires_at or (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    if static_assets_path is not None:
        monkeypatch.setenv("GOLDEN_ROSE_STATIC_ASSETS_PATH", str(static_assets_path))


def test_missing_credentials_protect_every_business_and_static_route(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    dist_path = tmp_path / "dist"
    (dist_path / "assets").mkdir(parents=True)
    (dist_path / "index.html").write_text("<main>business content</main>", encoding="utf-8")
    (dist_path / "assets" / "app.js").write_text("business asset", encoding="utf-8")
    _set_develop_env(monkeypatch, dist_path)
    engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        responses = [
            client.get("/"),
            client.get("/assets/app.js"),
            client.get("/api/staff/v1/environment"),
            client.post("/api/staff/v1/employers/search", json={"name_fragment": "Acme"}),
        ]

    for response in responses:
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == _CHALLENGE
        assert response.headers["Cache-Control"] == "no-store"
        assert response.content == b""
        assert "business" not in response.text


def test_wrong_or_malformed_credentials_return_the_same_secret_safe_denial(
    monkeypatch: Any,
    caplog: Any,
) -> None:
    _set_develop_env(monkeypatch)
    engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: engine)
    authorization_values = [
        "Bearer unrelated",
        "Basic",
        "Basic !!!!",
        "Basic " + base64.b64encode(b"missing-colon").decode("ascii"),
        "Basic " + base64.b64encode(b"\xff:\xff").decode("ascii"),
        _basic("wrong-user", _DEMO_PASSWORD),
        _basic(_DEMO_USERNAME, "wrong-password"),
    ]

    with TestClient(app) as client:
        responses = [
            client.get(
                "/api/staff/v1/environment",
                headers={"Authorization": authorization},
            )
            for authorization in authorization_values
        ]

    rendered_logs = "\n".join(record.getMessage() for record in caplog.records)
    for authorization, response in zip(authorization_values, responses, strict=True):
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == _CHALLENGE
        assert response.headers["Cache-Control"] == "no-store"
        assert response.content == b""
        assert authorization not in response.text
        assert authorization not in rendered_logs
    assert _DEMO_PASSWORD not in rendered_logs


def test_expired_access_returns_fixed_no_store_unavailable(monkeypatch: Any) -> None:
    expired_at = (datetime.now(UTC) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _set_develop_env(monkeypatch, expires_at=expired_at)
    engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        responses = [
            client.get("/api/staff/v1/environment"),
            client.get(
                "/api/staff/v1/environment",
                headers={"Authorization": _basic(_DEMO_USERNAME, _DEMO_PASSWORD)},
            ),
        ]

    for response in responses:
        assert response.status_code == 503
        assert response.headers["Cache-Control"] == "no-store"
        assert "WWW-Authenticate" not in response.headers
        assert response.content == b""
        assert expired_at not in response.text


def test_health_and_readiness_are_public_and_reveal_only_minimized_status(
    monkeypatch: Any,
) -> None:
    _set_develop_env(monkeypatch)
    engine: Any = ReadinessEngine()
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        health = client.get("/health")
        readiness = client.get("/readiness")

    assert health.status_code == 200
    assert health.headers["Cache-Control"] == "no-store"
    assert health.json() == {"status": "ok"}
    assert readiness.status_code == 200
    assert readiness.headers["Cache-Control"] == "no-store"
    assert readiness.json() == {"status": "ready"}


def test_correct_credentials_reach_protected_route_without_session_cookie(monkeypatch: Any) -> None:
    _set_develop_env(monkeypatch)
    engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        response = client.get(
            "/api/staff/v1/environment",
            headers={"Authorization": _basic(_DEMO_USERNAME, _DEMO_PASSWORD)},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "Set-Cookie" not in response.headers
    assert response.json() == {
        "environment": "develop",
        "label": "Non-production develop — fictional synthetic data only",
        "data_boundary": "fictional-synthetic-only",
    }


def test_correct_credentials_cannot_admit_plausible_live_values_in_develop(
    monkeypatch: Any,
) -> None:
    _set_develop_env(monkeypatch)
    engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: engine)

    def override_session():
        yield NoDatabaseSession()

    app.dependency_overrides[get_db_session] = override_session
    submitted_value = "Acme Staffing"

    with TestClient(app) as client:
        response = client.post(
            "/api/staff/v1/employers",
            headers={
                "Authorization": _basic(_DEMO_USERNAME, _DEMO_PASSWORD),
                "Idempotency-Key": "11111111-1111-4111-8111-111111111111",
            },
            json={"employer_type": "business", "display_name": submitted_value},
        )

    assert response.status_code == 422
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "type": "https://golden-rose.local/problems/synthetic-data-required",
        "title": "Unprocessable Entity",
        "detail": "fictional synthetic value required",
        "status": 422,
    }
    assert submitted_value not in response.text


def test_credentials_are_compared_through_constant_time_seam(monkeypatch: Any) -> None:
    comparisons: list[tuple[str, str]] = []

    def recording_compare(left: str, right: str) -> bool:
        comparisons.append((left, right))
        return left == right

    _set_develop_env(monkeypatch)
    monkeypatch.setattr(
        demo_access_module.hmac,  # type: ignore[attr-defined]
        "compare_digest",
        recording_compare,
    )
    engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: engine)

    with TestClient(app) as client:
        response = client.get(
            "/api/staff/v1/environment",
            headers={"Authorization": _basic(_DEMO_USERNAME, _DEMO_PASSWORD)},
        )

    assert response.status_code == 200
    assert comparisons == [
        (_DEMO_USERNAME, _DEMO_USERNAME),
        (_DEMO_PASSWORD, _DEMO_PASSWORD),
    ]
