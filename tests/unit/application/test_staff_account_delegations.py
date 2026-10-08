from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

import golden_rose.application.staff_account_delegations as delegation_module
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.staff_account_delegations import (
    StaffDelegationError,
    StaffDelegationNotFoundError,
    grant_staff_delegation,
    list_delegations_for_staff,
    revoke_staff_account_delegation,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.staff_accounts import StaffAccountRecord, StaffDelegationRecord

NOW = datetime(2026, 9, 29, 2, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
GRANTEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_STAFF_ID = UUID("33333333-3333-4333-8333-333333333333")
DELEGATION_ID = UUID("44444444-4444-4444-8444-444444444444")


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _principal(*permissions: str, actor_id: UUID = ACTOR_ID) -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=actor_id,
        role_name="owner",
        permissions=frozenset(permissions),
    )


def _account(*, status: str = "active") -> StaffAccountRecord:
    return StaffAccountRecord(
        staff_id=GRANTEE_ID,
        provider_subject="oidc:staff:grantee",
        provider_email=None,
        display_name="Mariela Torres",
        role_name="operations_staff",
        lifecycle_status=status,  # type: ignore[arg-type]
        mfa_enrolled=True,
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=2,
    )


def _delegation(
    *,
    grantee_staff_id: UUID = GRANTEE_ID,
    revoked_at: datetime | None = None,
    revoked_by: UUID | None = None,
    revocation_reason: str | None = None,
) -> StaffDelegationRecord:
    return StaffDelegationRecord(
        delegation_id=DELEGATION_ID,
        grantor_staff_id=ACTOR_ID,
        grantee_staff_id=grantee_staff_id,
        permission_name="employer:read",
        scope_kind="global",
        scope_id=None,
        reason_text="Temporary coverage",
        starts_at=NOW,
        expires_at=NOW + timedelta(days=7),
        revoked_at=revoked_at,
        revoked_by=revoked_by,
        revocation_reason=revocation_reason,
    )


def test_list_delegations_allows_self_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, Any] = {}

    def get_account(**kwargs):
        observed["account_lookup"] = kwargs
        return _account()

    def list_delegations(**kwargs):
        observed["delegation_lookup"] = kwargs
        return (_delegation(),)

    monkeypatch.setattr(delegation_module, "get_staff_account_by_id", get_account)
    monkeypatch.setattr(delegation_module, "list_staff_delegations", list_delegations)

    delegations = list_delegations_for_staff(
        session=FakeSession(),  # type: ignore[arg-type]
        principal=_principal(actor_id=GRANTEE_ID),
        staff_id=GRANTEE_ID,
    )

    assert delegations == (_delegation(),)
    assert observed["account_lookup"]["staff_id"] == GRANTEE_ID
    assert observed["delegation_lookup"]["staff_id"] == GRANTEE_ID


def test_list_delegations_requires_admin_permission_for_other_account() -> None:
    with pytest.raises(PermissionError, match="staff_account:delegation:grant"):
        list_delegations_for_staff(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            staff_id=GRANTEE_ID,
        )


def test_list_delegations_reports_missing_account(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(delegation_module, "get_staff_account_by_id", missing_account)

    with pytest.raises(StaffDelegationNotFoundError, match="staff account not found"):
        list_delegations_for_staff(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:delegation:grant"),
            staff_id=GRANTEE_ID,
        )


def test_grant_staff_delegation_validates_and_inserts(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(delegation_module, "get_staff_account_by_id", lambda **_kwargs: _account())

    def insert_delegation(**kwargs):
        observed["delegation"] = kwargs
        return _delegation()

    monkeypatch.setattr(delegation_module, "insert_staff_delegation", insert_delegation)

    result = grant_staff_delegation(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:delegation:grant", "employer:read"),
        delegation_id=DELEGATION_ID,
        grantee_staff_id=GRANTEE_ID,
        permission_name=" employer:read ",
        scope_kind=" global ",
        expires_at=NOW + timedelta(days=7),
        clock=FixedClock(),
        reason_text=" Temporary coverage ",
    )

    assert result.event_type == "staff_delegation.granted"
    assert result.result_version == 1
    assert observed["delegation"]["permission_name"] == "employer:read"
    assert observed["delegation"]["scope_kind"] == "global"
    assert observed["delegation"]["reason_text"] == "Temporary coverage"
    assert observed["delegation"]["starts_at"] == NOW
    assert session.commits == 1
    assert session.rollbacks == 0


def test_grant_staff_delegation_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:delegation:grant"):
        grant_staff_delegation(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("employer:read"),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            permission_name="employer:read",
            scope_kind="global",
            expires_at=NOW + timedelta(days=7),
            clock=FixedClock(),
            reason_text="Temporary coverage",
        )


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"permission_name": " "}, "invalid permission_name"),
        ({"scope_kind": "case"}, "only global"),
        ({"permission_name": "worker:read"}, "does not hold"),
        ({"expires_at": NOW}, "expire in the future"),
        ({"expires_at": NOW + timedelta(days=367)}, "duration is too long"),
    ],
)
def test_grant_staff_delegation_rejects_invalid_input(
    kwargs: dict[str, object],
    match: str,
) -> None:
    values = {
        "permission_name": "employer:read",
        "scope_kind": "global",
        "expires_at": NOW + timedelta(days=7),
    } | kwargs

    with pytest.raises(StaffDelegationError, match=match):
        grant_staff_delegation(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:delegation:grant", "employer:read"),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            permission_name=values["permission_name"],  # type: ignore[arg-type]
            scope_kind=values["scope_kind"],  # type: ignore[arg-type]
            expires_at=values["expires_at"],  # type: ignore[arg-type]
            clock=FixedClock(),
            reason_text="Temporary coverage",
        )


def test_grant_staff_delegation_rejects_self_delegation() -> None:
    with pytest.raises(StaffDelegationError, match="delegate to itself"):
        grant_staff_delegation(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(
                "staff_account:delegation:grant",
                "employer:read",
                actor_id=GRANTEE_ID,
            ),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            permission_name="employer:read",
            scope_kind="global",
            expires_at=NOW + timedelta(days=7),
            clock=FixedClock(),
            reason_text="Temporary coverage",
        )


def test_grant_staff_delegation_rejects_deprovisioned_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        delegation_module,
        "get_staff_account_by_id",
        lambda **_kwargs: _account(status="deprovisioned"),
    )

    with pytest.raises(StaffDelegationError, match="deprovisioned"):
        grant_staff_delegation(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:delegation:grant", "employer:read"),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            permission_name="employer:read",
            scope_kind="global",
            expires_at=NOW + timedelta(days=7),
            clock=FixedClock(),
            reason_text="Temporary coverage",
        )


def test_grant_staff_delegation_database_failure_is_safe_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(delegation_module, "get_staff_account_by_id", lambda **_kwargs: _account())

    def raise_database_error(**_kwargs):
        raise SQLAlchemyError("synthetic delegation failure")

    monkeypatch.setattr(delegation_module, "insert_staff_delegation", raise_database_error)

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        grant_staff_delegation(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:delegation:grant", "employer:read"),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            permission_name="employer:read",
            scope_kind="global",
            expires_at=NOW + timedelta(days=7),
            clock=FixedClock(),
            reason_text="Temporary coverage",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_revoke_staff_delegation_updates_active_record(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        delegation_module,
        "get_staff_delegation_by_id",
        lambda **_kwargs: _delegation(),
    )

    def revoke_delegation(**kwargs):
        observed["revoke"] = kwargs
        return _delegation(
            revoked_at=kwargs["revoked_at"],
            revoked_by=kwargs["revoked_by"],
            revocation_reason=kwargs["revocation_reason"],
        )

    monkeypatch.setattr(delegation_module, "revoke_staff_delegation", revoke_delegation)

    result = revoke_staff_account_delegation(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:delegation:revoke"),
        delegation_id=DELEGATION_ID,
        grantee_staff_id=GRANTEE_ID,
        clock=FixedClock(),
        reason_text=" Coverage complete ",
    )

    assert result.event_type == "staff_delegation.revoked"
    assert result.delegation.revoked_at == NOW
    assert result.delegation.revoked_by == ACTOR_ID
    assert result.delegation.revocation_reason == "Coverage complete"
    assert observed["revoke"]["grantee_staff_id"] == GRANTEE_ID
    assert session.commits == 1
    assert session.rollbacks == 0


def test_revoke_staff_delegation_is_idempotent_for_already_revoked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    revoked = _delegation(
        revoked_at=NOW - timedelta(days=1),
        revoked_by=OTHER_STAFF_ID,
        revocation_reason="Previous revocation",
    )
    monkeypatch.setattr(
        delegation_module,
        "get_staff_delegation_by_id",
        lambda **_kwargs: revoked,
    )

    result = revoke_staff_account_delegation(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:delegation:revoke"),
        delegation_id=DELEGATION_ID,
        grantee_staff_id=GRANTEE_ID,
        clock=FixedClock(),
        reason_text="Coverage complete",
    )

    assert result.delegation == revoked
    assert session.commits == 1
    assert session.rollbacks == 0


def test_revoke_staff_delegation_hides_wrong_grantee(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        delegation_module,
        "get_staff_delegation_by_id",
        lambda **_kwargs: _delegation(grantee_staff_id=OTHER_STAFF_ID),
    )

    with pytest.raises(StaffDelegationNotFoundError, match="staff delegation not found"):
        revoke_staff_account_delegation(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:delegation:revoke"),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            clock=FixedClock(),
            reason_text="Coverage complete",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_revoke_staff_delegation_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:delegation:revoke"):
        revoke_staff_account_delegation(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            clock=FixedClock(),
            reason_text="Coverage complete",
        )


def test_revoke_staff_delegation_database_failure_is_safe_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        delegation_module,
        "get_staff_delegation_by_id",
        lambda **_kwargs: _delegation(),
    )

    def raise_database_error(**_kwargs):
        raise SQLAlchemyError("synthetic revocation failure")

    monkeypatch.setattr(delegation_module, "revoke_staff_delegation", raise_database_error)

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        revoke_staff_account_delegation(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:delegation:revoke"),
            delegation_id=DELEGATION_ID,
            grantee_staff_id=GRANTEE_ID,
            clock=FixedClock(),
            reason_text="Coverage complete",
        )

    assert session.rollbacks == 1
    assert session.commits == 0
