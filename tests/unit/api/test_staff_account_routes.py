from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_identifier_factory, get_staff_principal
from golden_rose.api.staff import staff_accounts
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    StaffAccountLifecycleResult,
    StaffAccountNotFoundError,
    StaffAccountVersionConflictError,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.main import create_app
from golden_rose.persistence.staff_accounts import StaffAccountRecord

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
STAFF_ID = UUID("22222222-2222-4222-8222-222222222222")
GENERATED_STAFF_ID = UUID("33333333-3333-4333-8333-333333333333")


class FixedIdentifiers:
    def __init__(self) -> None:
        self.generated: list[UUID] = []

    def new_uuid4(self) -> UUID:
        self.generated.append(GENERATED_STAFF_ID)
        return GENERATED_STAFF_ID


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, FixedIdentifiers]]:
    app = create_app(engine_factory=lambda: Mock())
    app.dependency_overrides[get_db_session] = lambda: object()
    app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="owner",
        permissions=frozenset(
            {
                "staff_account:create",
                "staff_account:activate",
                "staff_account:suspend",
                "staff_account:deprovision",
            }
        ),
    )
    identifiers = FixedIdentifiers()
    app.dependency_overrides[get_identifier_factory] = lambda: identifiers
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, identifiers


def account_record(
    *,
    staff_id: UUID = STAFF_ID,
    status: str = "suspended",
    version: int = 1,
    mfa_enrolled: bool = False,
) -> StaffAccountRecord:
    return StaffAccountRecord(
        staff_id=staff_id,
        provider_subject="oidc:staff:123",
        display_name="Mariela Torres",
        role_name="operations_staff",
        lifecycle_status=status,  # type: ignore[arg-type]
        mfa_enrolled=mfa_enrolled,
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=version,
    )


def lifecycle_result(
    *,
    event_type: str,
    record: StaffAccountRecord,
) -> StaffAccountLifecycleResult:
    return StaffAccountLifecycleResult(
        account=record,
        event_type=event_type,
        result_version=record.version,
    )


def command_headers() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid4())}


def test_create_staff_account_routes_normalized_admin_request(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, identifiers = http
    create = Mock(
        return_value=lifecycle_result(
            event_type="staff_account.created",
            record=account_record(staff_id=GENERATED_STAFF_ID),
        )
    )
    monkeypatch.setattr(staff_accounts, "create_staff_account", create)

    response = client.post(
        "/api/staff/v1/staff-accounts",
        headers=command_headers(),
        json={
            "provider_subject": " oidc:staff:123 ",
            "display_name": " Mariela   Torres ",
            "role_name": "operations_staff",
            "permission_names": ["intake:read", "worker:read"],
            "mfa_enrolled": False,
            "reason_text": " Initial onboarding ",
        },
    )

    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["idempotency-result-version"] == "1"
    assert response.json()["account"]["staff_id"] == str(GENERATED_STAFF_ID)
    assert response.json()["event_type"] == "staff_account.created"
    assert identifiers.generated == [GENERATED_STAFF_ID]
    assert create.call_args.kwargs["staff_id"] == GENERATED_STAFF_ID
    assert create.call_args.kwargs["provider_subject"] == "oidc:staff:123"
    assert create.call_args.kwargs["display_name"] == "Mariela Torres"
    assert create.call_args.kwargs["permission_names"] == frozenset({"intake:read", "worker:read"})
    assert create.call_args.kwargs["reason_text"] == "Initial onboarding"


def test_activate_staff_account_routes_mfa_confirmation(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    activate = Mock(
        return_value=lifecycle_result(
            event_type="staff_account.activated",
            record=account_record(status="active", version=2, mfa_enrolled=True),
        )
    )
    monkeypatch.setattr(staff_accounts, "activate_staff_account", activate)

    response = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/activate",
        headers=command_headers(),
        json={"expected_version": 1, "mfa_enrolled": True, "reason_text": "MFA complete"},
    )

    assert response.status_code == 200, response.text
    assert response.headers["idempotency-result-version"] == "2"
    assert response.json()["account"]["lifecycle_status"] == "active"
    assert response.json()["account"]["mfa_enrolled"] is True
    assert activate.call_args.kwargs["staff_id"] == STAFF_ID
    assert activate.call_args.kwargs["expected_version"] == 1
    assert activate.call_args.kwargs["mfa_enrolled"] is True


@pytest.mark.parametrize(
    ("path_suffix", "patch_name", "event_type", "status"),
    [
        ("suspend", "suspend_staff_account", "staff_account.suspended", "suspended"),
        (
            "deprovision",
            "deprovision_staff_account",
            "staff_account.deprovisioned",
            "deprovisioned",
        ),
    ],
)
def test_terminal_staff_account_lifecycle_routes(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
    path_suffix: str,
    patch_name: str,
    event_type: str,
    status: str,
) -> None:
    client, _ = http
    command = Mock(
        return_value=lifecycle_result(
            event_type=event_type,
            record=account_record(status=status, version=3),
        )
    )
    monkeypatch.setattr(staff_accounts, patch_name, command)

    response = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/{path_suffix}",
        headers=command_headers(),
        json={"expected_version": 2, "reason_text": "Access review"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["event_type"] == event_type
    assert response.json()["account"]["lifecycle_status"] == status
    assert command.call_args.kwargs["expected_version"] == 2


@pytest.mark.parametrize(
    ("error", "status", "problem_type"),
    [
        (
            StaffAccountNotFoundError("missing private subject"),
            404,
            "https://golden-rose.local/problems/staff-account-not-found",
        ),
        (
            StaffAccountVersionConflictError("private version"),
            412,
            "https://golden-rose.local/problems/staff-account-version-conflict",
        ),
        (
            StaffAccountLifecycleError("private invalid transition"),
            422,
            "https://golden-rose.local/problems/staff-account-lifecycle-invalid",
        ),
        (
            SafePersistenceError("private database value"),
            503,
            "https://golden-rose.local/problems/service-unavailable",
        ),
    ],
)
def test_lifecycle_route_errors_are_value_safe(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    status: int,
    problem_type: str,
) -> None:
    client, _ = http
    suspend = Mock(side_effect=error)
    monkeypatch.setattr(staff_accounts, "suspend_staff_account", suspend)

    response = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/suspend",
        headers=command_headers(),
        json={"expected_version": 2, "reason_text": "Access review"},
    )

    assert response.status_code == status
    assert response.json()["type"] == problem_type
    assert response.headers["cache-control"] == "no-store"
    assert "private" not in response.text


def test_staff_account_routes_preserve_forbidden_and_validation_boundaries(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    create = Mock(side_effect=PermissionError("private permission detail"))
    monkeypatch.setattr(staff_accounts, "create_staff_account", create)
    cast(FastAPI, client.app).dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="operations_staff",
        permissions=frozenset(),
    )

    forbidden = client.post(
        "/api/staff/v1/staff-accounts",
        headers=command_headers(),
        json={
            "provider_subject": "oidc:staff:123",
            "display_name": "Mariela Torres",
            "role_name": "operations_staff",
            "permission_names": ["intake:read"],
            "reason_text": "Initial onboarding",
        },
    )
    invalid = client.post(
        "/api/staff/v1/staff-accounts",
        headers=command_headers(),
        json={
            "provider_subject": "oidc:staff:123",
            "display_name": "Bad\nName",
            "role_name": "operations_staff",
            "permission_names": ["intake:read", " intake:read "],
            "reason_text": "Initial onboarding",
            "private_extra": "secret",
        },
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "forbidden"
    assert invalid.status_code == 422
    assert "secret" not in invalid.text
    assert create.call_count == 1
