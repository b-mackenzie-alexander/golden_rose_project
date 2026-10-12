from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_settings, get_staff_principal
from golden_rose.api.staff import intakes
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.config import CONTROLLED_LIVE_DATA_STAFF_PILOT_TARGET, Settings
from golden_rose.main import create_app
from tests.unit.api.test_intake_schemas import response_detail


def controlled_staff_pilot_settings() -> Settings:
    return Settings(
        environment="production",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://accounts.example.test",
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://accounts.example.test/.well-known/jwks.json",
        deployment_target=CONTROLLED_LIVE_DATA_STAFF_PILOT_TARGET,
    )


def pilot_principal() -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset(
            {
                "intake:read",
                "intake:draft:create",
                "intake:draft:revise",
                "worker_residence:read",
                "worker_residence:write",
                "party_address:read",
                "party_address:write",
                "worksite_address:read",
                "worksite_address:write",
            }
        ),
    )


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, Mock, object]]:
    app = create_app(engine_factory=lambda: Mock())
    session = object()
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_staff_principal] = pilot_principal
    execute = Mock()
    monkeypatch.setattr(intakes, "execute_intake", execute)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, execute, session


def create_body() -> dict[str, Any]:
    return {"kind": "worker", "content": {"full_name": "Fictional Worker"}}


def command_result(command_id) -> dict[str, Any]:
    return {
        "command_id": str(command_id),
        "result_record_version": 1,
        "current": response_detail(),
    }


def test_create_intake_is_open_in_controlled_staff_pilot(http) -> None:
    client, execute, session = http
    key = uuid4()
    execute.return_value = command_result(key), False
    client.app.dependency_overrides[get_settings] = controlled_staff_pilot_settings

    response = client.post(
        "/api/staff/v1/intakes",
        json=create_body(),
        headers={"Idempotency-Key": str(key)},
    )

    assert response.status_code == 201, response.text
    assert response.headers["idempotency-replayed"] == "false"
    assert response.headers["cache-control"] == "no-store"
    args = execute.call_args.kwargs
    assert args["session"] is session
    assert args["command_id"] == key
    assert args["intake_id"] is None
    assert args["request"].model_dump(mode="json", exclude_unset=True) == create_body()


@pytest.mark.parametrize("environment", ["develop", "production"])
def test_create_intake_remains_closed_outside_local_test_and_controlled_pilot(
    http,
    environment: str,
) -> None:
    client, execute, _ = http
    client.app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"environment": environment}
    )

    response = client.post(
        "/api/staff/v1/intakes",
        json=create_body(),
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    execute.assert_not_called()
