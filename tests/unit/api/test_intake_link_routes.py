"""Link transport contract; database authority is exercised separately."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_settings
from golden_rose.api.staff import intake_workflows
from golden_rose.application.intake_errors import IntakeError
from golden_rose.main import create_app
from tests.unit.api.test_intake_schemas import response_detail


@pytest.fixture
def http(monkeypatch) -> Iterator[Any]:
    app = create_app(engine_factory=lambda: Mock())
    session = object()
    app.dependency_overrides[get_db_session] = lambda: session
    execute = Mock()
    monkeypatch.setattr(intake_workflows, "execute_link_intake", execute)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, execute, session


def body() -> dict[str, Any]:
    return {"expected_version": 2, "party": None}


def safe(response) -> None:
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "etag" not in response.headers and "last-modified" not in response.headers
    assert "private" not in response.text


@pytest.mark.parametrize("replayed", [False, True])
def test_command_response_and_original_identity(http, replayed):
    client, execute, session = http
    target, key = uuid4(), uuid4()
    detail = response_detail()
    detail["summary"].update(intake_id=str(target), version=5 if replayed else 3)
    result = {"command_id": str(key), "result_record_version": 3, "current": detail}
    execute.return_value = result, replayed
    response = client.post(
        f"/api/staff/v1/intakes/{target}/links",
        json=body(),
        headers={"Idempotency-Key": str(key)},
    )
    assert response.status_code == 200, response.text
    assert response.json() == result
    safe(response)
    assert response.headers["idempotency-replayed"] == str(replayed).lower()
    assert response.headers["idempotency-result-version"] == "3"
    assert "location" not in response.headers
    args = execute.call_args.kwargs
    assert args["session"] is session and args["intake_id"] == target
    assert args["command_id"] == key
    assert args["request"].model_dump(mode="json", exclude_unset=True) == body()


@pytest.mark.parametrize("environment", ["develop", "production"])
def test_local_test_only(http, environment):
    client, execute, _ = http
    client.app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"environment": environment}
    )
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/links",
        json=body(),
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 403
    safe(response)
    execute.assert_not_called()


@pytest.mark.parametrize(
    "patch",
    [
        {"expected_version": True},
        {"party": {"id": "private", "version": 1}},
        {"contact": {"id": str(uuid4()), "version": 1}},
        {"content": "private"},
    ],
)
def test_invalid_body(http, patch):
    client, execute, _ = http
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/links",
        json={**body(), **patch},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 422
    safe(response)
    execute.assert_not_called()


@pytest.mark.parametrize(
    "case,status",
    [
        ("key", 422),
        ("media", 415),
        ("size", 413),
        ("method", 405),
    ],
)
def test_transport_rejections(http, case, status):
    client, execute, _ = http
    path = f"/api/staff/v1/intakes/{uuid4()}/links"
    if case == "method":
        response = client.get(path)
    elif case == "key":
        response = client.post(path, json=body())
    else:
        response = client.post(
            path,
            content="private" * (5000 if case == "size" else 1),
            headers={
                "Content-Type": "application/json" if case == "size" else "text/plain",
                "Idempotency-Key": str(uuid4()),
            },
        )
    assert response.status_code == status
    safe(response)
    execute.assert_not_called()


@pytest.mark.parametrize(
    "code,status",
    [
        ("forbidden", 403),
        ("not_found", 404),
        ("version_conflict", 409),
        ("dependency_changed", 409),
        ("no_change", 409),
        ("idempotency_conflict", 409),
        ("already_finalized", 409),
        ("persistence_unavailable", 503),
    ],
)
def test_safe_errors(http, code, status):
    client, execute, _ = http
    execute.side_effect = IntakeError(code, status)
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/links",
        json=body(),
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == status and response.json()["code"] == code
    safe(response)
    if status == 503:
        assert response.headers["retry-after"] == "1"
