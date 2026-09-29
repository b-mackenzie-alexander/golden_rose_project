from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from golden_rose.api.dependencies import get_db_session, get_identifier_factory, get_staff_principal
from golden_rose.api.staff import staff_accounts
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.staff_account_delegations import (
    StaffDelegationConflictError,
    StaffDelegationError,
    StaffDelegationNotFoundError,
    StaffDelegationResult,
)
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    StaffAccountLifecycleResult,
    StaffAccountNotFoundError,
    StaffAccountVersionConflictError,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.main import create_app
from golden_rose.persistence.staff_accounts import StaffAccountRecord, StaffDelegationRecord

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
STAFF_ID = UUID("22222222-2222-4222-8222-222222222222")
GENERATED_STAFF_ID = UUID("33333333-3333-4333-8333-333333333333")
DELEGATION_ID = UUID("44444444-4444-4444-8444-444444444444")


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
                "staff_account:read",
                "staff_account:recovery:record",
                "staff_account:session:revoke",
                "staff_account:delegation:grant",
                "staff_account:delegation:revoke",
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


def delegation_record(*, revoked: bool = False) -> StaffDelegationRecord:
    return StaffDelegationRecord(
        delegation_id=DELEGATION_ID,
        grantor_staff_id=ACTOR_ID,
        grantee_staff_id=STAFF_ID,
        permission_name="intake:read",
        scope_kind="global",
        scope_id=None,
        reason_text="Temporary coverage",
        starts_at=NOW,
        expires_at=datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
        revoked_at=NOW if revoked else None,
        revoked_by=ACTOR_ID if revoked else None,
        revocation_reason="Coverage ended" if revoked else None,
    )


def delegation_result(*, event_type: str, revoked: bool = False) -> StaffDelegationResult:
    return StaffDelegationResult(
        delegation=delegation_record(revoked=revoked),
        event_type=event_type,
        result_version=1,
    )


def command_headers() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid4())}


def test_list_staff_accounts_requires_read_permission_and_returns_no_store(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    listed = Mock(
        return_value=(
            account_record(status="active", version=2, mfa_enrolled=True),
            account_record(staff_id=GENERATED_STAFF_ID, status="suspended", version=1),
        )
    )
    monkeypatch.setattr(staff_accounts, "list_staff_accounts", listed)

    response = client.get("/api/staff/v1/staff-accounts")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert [item["staff_id"] for item in response.json()["items"]] == [
        str(STAFF_ID),
        str(GENERATED_STAFF_ID),
    ]
    listed.assert_called_once()


def test_get_staff_account_returns_exact_account_or_safe_not_found(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    reader = Mock(return_value=account_record(status="active", version=2, mfa_enrolled=True))
    monkeypatch.setattr(staff_accounts, "get_staff_account_by_id", reader)

    response = client.get(f"/api/staff/v1/staff-accounts/{STAFF_ID}")

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["staff_id"] == str(STAFF_ID)
    assert response.json()["lifecycle_status"] == "active"
    assert reader.call_args.kwargs["staff_id"] == STAFF_ID


def test_staff_account_read_routes_preserve_forbidden_and_missing_boundaries(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    listed = Mock()
    monkeypatch.setattr(staff_accounts, "list_staff_accounts", listed)
    cast(FastAPI, client.app).dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="operations_staff",
        permissions=frozenset(),
    )

    forbidden = client.get("/api/staff/v1/staff-accounts")

    cast(FastAPI, client.app).dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="owner",
        permissions=frozenset({"staff_account:read"}),
    )
    missing = Mock(side_effect=NoResultFound())
    monkeypatch.setattr(staff_accounts, "get_staff_account_by_id", missing)
    not_found = client.get(f"/api/staff/v1/staff-accounts/{STAFF_ID}")
    unavailable = Mock(side_effect=SQLAlchemyError("private database details"))
    monkeypatch.setattr(staff_accounts, "list_staff_accounts", unavailable)
    service_unavailable = client.get("/api/staff/v1/staff-accounts")

    assert forbidden.status_code == 403
    assert forbidden.headers["cache-control"] == "no-store"
    listed.assert_not_called()
    assert not_found.status_code == 404
    assert not_found.json()["type"] == "https://golden-rose.local/problems/staff-account-not-found"
    assert service_unavailable.status_code == 503
    assert service_unavailable.json()["type"] == (
        "https://golden-rose.local/problems/service-unavailable"
    )
    assert "private" not in service_unavailable.text


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
    ("path_suffix", "patch_name", "event_type", "reason_text"),
    [
        (
            "recovery-evidence",
            "record_staff_account_recovery_evidence",
            "staff_account.recovery_recorded",
            "Assisted MFA recovery completed",
        ),
        (
            "session-revocations",
            "record_staff_account_session_revocation_evidence",
            "staff_account.sessions_revoked",
            "Provider sessions revoked",
        ),
    ],
)
def test_staff_account_evidence_routes_record_current_version_without_status_change(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
    path_suffix: str,
    patch_name: str,
    event_type: str,
    reason_text: str,
) -> None:
    client, _ = http
    command = Mock(
        return_value=lifecycle_result(
            event_type=event_type,
            record=account_record(status="active", version=4, mfa_enrolled=True),
        )
    )
    monkeypatch.setattr(staff_accounts, patch_name, command)

    response = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/{path_suffix}",
        headers=command_headers(),
        json={"expected_version": 4, "reason_text": reason_text},
    )

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["idempotency-result-version"] == "4"
    assert response.json()["event_type"] == event_type
    assert response.json()["account"]["lifecycle_status"] == "active"
    assert response.json()["result_version"] == 4
    assert command.call_args.kwargs["staff_id"] == STAFF_ID
    assert command.call_args.kwargs["expected_version"] == 4
    assert command.call_args.kwargs["reason_text"] == reason_text


def test_staff_account_delegation_routes_list_and_grant_no_store(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    listed = Mock(return_value=(delegation_record(),))
    grant = Mock(return_value=delegation_result(event_type="staff_delegation.granted"))
    monkeypatch.setattr(staff_accounts, "list_delegations_for_staff", listed)
    monkeypatch.setattr(staff_accounts, "grant_staff_delegation", grant)

    list_response = client.get(f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations")
    grant_response = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations",
        headers={"Idempotency-Key": str(DELEGATION_ID)},
        json={
            "permission_name": " intake:read ",
            "scope_kind": "global",
            "expires_at": "2026-09-29T12:00:00Z",
            "reason_text": " Temporary coverage ",
        },
    )

    assert list_response.status_code == 200, list_response.text
    assert list_response.headers["cache-control"] == "no-store"
    assert list_response.headers["vary"] == "Authorization"
    assert list_response.json()["items"][0]["delegation_id"] == str(DELEGATION_ID)
    assert grant_response.status_code == 201, grant_response.text
    assert grant_response.headers["idempotency-result-version"] == "1"
    assert grant_response.json()["event_type"] == "staff_delegation.granted"
    assert grant.call_args.kwargs["delegation_id"] == DELEGATION_ID
    assert grant.call_args.kwargs["grantee_staff_id"] == STAFF_ID
    assert grant.call_args.kwargs["permission_name"] == "intake:read"
    assert grant.call_args.kwargs["scope_kind"] == "global"
    assert grant.call_args.kwargs["reason_text"] == "Temporary coverage"


def test_staff_account_delegation_revocation_route(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    revoke = Mock(
        return_value=delegation_result(event_type="staff_delegation.revoked", revoked=True)
    )
    monkeypatch.setattr(staff_accounts, "revoke_staff_account_delegation", revoke)

    response = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations/{DELEGATION_ID}/revoke",
        headers=command_headers(),
        json={"reason_text": " Coverage ended "},
    )

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["idempotency-result-version"] == "1"
    assert response.json()["delegation"]["revoked_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert response.json()["event_type"] == "staff_delegation.revoked"
    assert revoke.call_args.kwargs["delegation_id"] == DELEGATION_ID
    assert revoke.call_args.kwargs["grantee_staff_id"] == STAFF_ID
    assert revoke.call_args.kwargs["reason_text"] == "Coverage ended"


def test_staff_account_delegation_errors_are_value_safe(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    missing = Mock(side_effect=StaffDelegationNotFoundError("private delegation"))
    invalid = Mock(side_effect=StaffDelegationError("private invalid delegation"))
    monkeypatch.setattr(staff_accounts, "list_delegations_for_staff", missing)
    monkeypatch.setattr(staff_accounts, "grant_staff_delegation", invalid)

    not_found = client.get(f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations")
    bad_request = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations",
        headers=command_headers(),
        json={
            "permission_name": "intake:read",
            "scope_kind": "global",
            "expires_at": "2026-09-29T12:00:00Z",
            "reason_text": "Temporary coverage",
        },
    )

    assert not_found.status_code == 404
    assert (
        not_found.json()["type"] == "https://golden-rose.local/problems/staff-delegation-not-found"
    )
    assert "private" not in not_found.text
    assert bad_request.status_code == 422
    assert bad_request.json()["type"] == (
        "https://golden-rose.local/problems/staff-delegation-invalid"
    )
    assert "private" not in bad_request.text


def test_staff_account_delegation_routes_preserve_forbidden_and_service_boundaries(
    http: tuple[TestClient, FixedIdentifiers],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = http
    forbidden_list = Mock(side_effect=PermissionError("private delegation permission"))
    conflict_grant = Mock(side_effect=StaffDelegationConflictError("private delegation conflict"))
    unavailable_revoke = Mock(side_effect=SafePersistenceError("private database value"))
    monkeypatch.setattr(staff_accounts, "list_delegations_for_staff", forbidden_list)
    monkeypatch.setattr(staff_accounts, "grant_staff_delegation", conflict_grant)
    monkeypatch.setattr(staff_accounts, "revoke_staff_account_delegation", unavailable_revoke)

    forbidden = client.get(f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations")
    conflict = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations",
        headers=command_headers(),
        json={
            "permission_name": "intake:read",
            "scope_kind": "global",
            "expires_at": "2026-09-29T12:00:00Z",
            "reason_text": "Temporary coverage",
        },
    )
    service_unavailable = client.post(
        f"/api/staff/v1/staff-accounts/{STAFF_ID}/delegations/{DELEGATION_ID}/revoke",
        headers=command_headers(),
        json={"reason_text": "Coverage ended"},
    )

    assert forbidden.status_code == 403
    assert forbidden.headers["cache-control"] == "no-store"
    assert "private" not in forbidden.text
    assert conflict.status_code == 412
    assert conflict.json()["type"] == (
        "https://golden-rose.local/problems/staff-delegation-conflict"
    )
    assert "private" not in conflict.text
    assert service_unavailable.status_code == 503
    assert service_unavailable.json()["type"] == (
        "https://golden-rose.local/problems/service-unavailable"
    )
    assert "private" not in service_unavailable.text


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
