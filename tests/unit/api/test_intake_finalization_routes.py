"""HTTP contract checks without a database; transaction proof lives in integration tests."""

from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_settings
from golden_rose.api.staff import intake_workflows
from golden_rose.application.intake_errors import IntakeError
from golden_rose.main import create_app
from tests.unit.api.test_intake_finalization_schemas import output_refs
from tests.unit.api.test_intake_schemas import response_detail


@pytest.fixture
def http(monkeypatch):
    engine: Any = Mock()
    app = create_app(engine_factory=lambda: engine)
    session = object()
    app.dependency_overrides[get_db_session] = lambda: session
    execute = Mock()
    monkeypatch.setattr(intake_workflows, "execute_new_intake_finalization", execute)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, execute, session


def request_body() -> dict[str, Any]:
    return {"expected_version": 2, "review_id": str(uuid4())}


@pytest.mark.parametrize("replayed", [False, True])
def test_finalization_response_and_exact_command_forwarding(http, replayed):
    client, execute, session = http
    target, key = uuid4(), uuid4()
    body = request_body()
    detail = response_detail()
    detail["summary"].update(
        intake_id=str(target), lifecycle="finalized", version=4 if replayed else 3
    )
    detail["finalization"] = output_refs()
    result = {
        "command_id": str(key),
        "result_record_version": 3,
        "current": detail,
        "finalization": detail["finalization"],
    }
    execute.return_value = result, replayed
    response = client.post(
        f"/api/staff/v1/intakes/{target}/finalizations",
        json=body,
        headers={"Idempotency-Key": str(key)},
    )
    assert response.status_code == (200 if replayed else 201), response.text
    assert response.json() == result
    assert response.headers["idempotency-replayed"] == str(replayed).lower()
    assert response.headers["idempotency-result-version"] == "3"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    if replayed:
        assert "location" not in response.headers
    else:
        assert response.headers["location"] == f"/api/staff/v1/intakes/{target}"
    execute.assert_called_once()
    args = execute.call_args.kwargs
    assert args["session"] is session
    assert args["intake_id"] == target
    assert args["command_id"] == key
    assert args["request"].model_dump(mode="json") == body


@pytest.mark.parametrize("environment", ["develop", "production"])
def test_finalization_is_blocked_outside_local_test(http, environment):
    client, execute, _ = http
    settings = get_settings().model_copy(update={"environment": environment})
    client.app.dependency_overrides[get_settings] = lambda: settings
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/finalizations",
        json=request_body(),
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    execute.assert_not_called()


@pytest.mark.parametrize(
    "patch",
    [
        {"expected_version": True},
        {"review_id": "private-invalid"},
        {"content": "private-value"},
        {"actor_id": str(uuid4())},
    ],
)
def test_invalid_body_is_rejected_without_echo_or_execution(http, patch):
    client, execute, _ = http
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/finalizations",
        json={**request_body(), **patch},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 422
    assert "private-" not in response.text
    execute.assert_not_called()


@pytest.mark.parametrize("key", [None, "invalid", "00000000-0000-0000-0000-000000000000"])
def test_finalization_requires_valid_command_key(http, key):
    client, execute, _ = http
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/finalizations",
        json=request_body(),
        headers={} if key is None else {"Idempotency-Key": key},
    )
    assert response.status_code == 422
    execute.assert_not_called()


def test_finalization_requires_json(http):
    client, execute, _ = http
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/finalizations",
        content="private-value",
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 415
    assert "private-value" not in response.text
    execute.assert_not_called()


@pytest.mark.parametrize(
    "code,status",
    [
        ("forbidden", 403),
        ("review_required", 409),
        ("already_finalized", 409),
        ("persistence_unavailable", 503),
    ],
)
def test_finalization_preserves_safe_application_errors(http, code, status):
    client, execute, _ = http
    execute.side_effect = IntakeError(code, status)
    response = client.post(
        f"/api/staff/v1/intakes/{uuid4()}/finalizations",
        json=request_body(),
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == status
    assert response.json()["code"] == code
    assert response.headers["cache-control"] == "no-store"
    if status == 503:
        assert response.headers["retry-after"] == "1"
