from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

import golden_rose.application.staff_account_lifecycle as lifecycle_module
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    activate_staff_account,
    create_staff_account,
    deprovision_staff_account,
    resolve_staff_principal_from_claims,
    suspend_staff_account,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_accounts import StaffIdentityClaims
from golden_rose.persistence.staff_accounts import StaffAccountRecord

NOW = datetime(2026, 9, 27, 20, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
STAFF_ID = UUID("22222222-2222-4222-8222-222222222222")
COMMAND_ID = UUID("33333333-3333-4333-8333-333333333333")
EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FixedIdentifiers:
    def __init__(self) -> None:
        self.values = [GRANT_ID, EVENT_ID]

    def new_uuid4(self) -> UUID:
        return self.values.pop(0)


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


def _record(
    *,
    status: str = "suspended",
    version: int = 1,
    mfa_enrolled: bool = False,
) -> StaffAccountRecord:
    return StaffAccountRecord(
        staff_id=STAFF_ID,
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


def test_create_staff_account_records_grants_and_lifecycle_event(monkeypatch: pytest.MonkeyPatch):
    session = FakeSession()
    observed: dict[str, Any] = {}

    def insert_account(**kwargs):
        observed["account"] = kwargs
        return _record()

    def insert_grants(**kwargs) -> None:
        observed["grants"] = kwargs

    def insert_event(**kwargs) -> None:
        observed["event"] = kwargs

    monkeypatch.setattr(lifecycle_module, "insert_staff_account", insert_account)
    monkeypatch.setattr(lifecycle_module, "insert_staff_permission_grants", insert_grants)
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", insert_event)

    result = create_staff_account(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:create", "intake:read"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        provider_subject=" oidc:staff:123 ",
        display_name=" Mariela   Torres ",
        role_name="operations_staff",
        permission_names=frozenset({"intake:read"}),
        mfa_enrolled=False,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text=" Initial staff onboarding ",
    )

    assert result.event_type == "staff_account.created"
    assert observed["account"]["provider_subject"] == "oidc:staff:123"
    assert observed["account"]["display_name"] == "Mariela Torres"
    assert observed["account"]["lifecycle_status"] == "suspended"
    assert observed["grants"]["grants"] == ((GRANT_ID, "intake:read"),)
    assert observed["event"]["event_id"] == EVENT_ID
    assert observed["event"]["new_status"] == "suspended"
    assert observed["event"]["reason_text"] == "Initial staff onboarding"
    assert session.commits == 1
    assert session.rollbacks == 0


def test_create_staff_account_denies_platform_admin_operational_data() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="platform administrator"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Platform Admin",
            role_name="platform_administrator",
            permission_names=frozenset({"employer:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Admin setup",
        )


def test_create_staff_account_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:create"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"intake:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )


def test_create_staff_account_rejects_invalid_role() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="invalid staff role"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Mariela Torres",
            role_name="shadow_admin",
            permission_names=frozenset({"intake:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )


def test_create_staff_account_requires_text_and_permissions() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="invalid provider_subject"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject=" ",
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"intake:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )
    with pytest.raises(StaffAccountLifecycleError, match="requires named permissions"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset(),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )
    with pytest.raises(StaffAccountLifecycleError, match="duplicate"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"intake:read", " intake:read "}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )


def test_create_staff_account_denies_self_escalation() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="cannot grant itself"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create", actor_id=STAFF_ID),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"staff_account:create", "intake:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Self setup",
        )


def test_activate_staff_account_requires_mfa() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="mfa"):
        activate_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:activate"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="MFA not ready",
        )


def test_activate_staff_account_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:activate"):
        activate_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            mfa_enrolled=True,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="MFA complete",
        )


def test_activate_staff_account_transitions_and_records_evidence(monkeypatch: pytest.MonkeyPatch):
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="suspended", version=1, mfa_enrolled=False),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_lifecycle",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )

    def insert_event(**kwargs) -> None:
        observed["event"] = kwargs

    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", insert_event)

    result = activate_staff_account(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:activate"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=1,
        mfa_enrolled=True,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="MFA complete",
    )

    assert result.account.lifecycle_status == "active"
    assert result.result_version == 2
    assert observed["event"]["event_type"] == "staff_account.activated"
    assert observed["event"]["previous_status"] == "suspended"
    assert observed["event"]["new_status"] == "active"
    assert session.commits == 1


def test_suspend_staff_account_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:suspend"):
        suspend_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=2,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Account review",
        )


def test_suspend_staff_account_denies_self_suspend() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="cannot suspend itself"):
        suspend_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:suspend", actor_id=STAFF_ID),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Stepping away",
        )


def test_suspend_staff_account_transitions_and_records_evidence(monkeypatch: pytest.MonkeyPatch):
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_lifecycle",
        lambda **_kwargs: _record(status="suspended", version=3, mfa_enrolled=False),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_lifecycle_event",
        lambda **kwargs: observed.setdefault("event", kwargs),
    )

    result = suspend_staff_account(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:suspend"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=2,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Account review",
    )

    assert result.account.lifecycle_status == "suspended"
    assert result.result_version == 3
    assert observed["event"]["event_type"] == "staff_account.suspended"
    assert observed["event"]["previous_version"] == 2
    assert observed["event"]["new_version"] == 3
    assert session.commits == 1


def test_deprovision_staff_account_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:deprovision"):
        deprovision_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=2,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Leaving",
        )


def test_deprovision_staff_account_denies_self_deprovision() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="cannot deprovision itself"):
        deprovision_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:deprovision", actor_id=STAFF_ID),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Leaving",
        )


def test_deprovision_staff_account_transitions_and_records_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    session = FakeSession()

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_lifecycle",
        lambda **_kwargs: _record(status="deprovisioned", version=3, mfa_enrolled=False),
    )
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", lambda **_kwargs: None)

    result = deprovision_staff_account(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:deprovision"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=2,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Leaving",
    )

    assert result.event_type == "staff_account.deprovisioned"
    assert result.account.lifecycle_status == "deprovisioned"
    assert session.commits == 1


def test_transition_staff_account_reports_missing_account(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()

    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_id_for_update", missing_account)

    with pytest.raises(lifecycle_module.StaffAccountNotFoundError, match="not found"):
        suspend_staff_account(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:suspend"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Account review",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_transition_staff_account_rejects_stale_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=3, mfa_enrolled=True),
    )

    with pytest.raises(lifecycle_module.StaffAccountVersionConflictError, match="version conflict"):
        suspend_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:suspend"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=2,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Account review",
        )


def test_transition_staff_account_rejects_deprovisioned_reactivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="deprovisioned", version=3, mfa_enrolled=False),
    )

    with pytest.raises(StaffAccountLifecycleError, match="cannot be reactivated"):
        activate_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:activate"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=3,
            mfa_enrolled=True,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Return attempt",
        )


def test_transition_staff_account_rejects_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="suspended", version=2, mfa_enrolled=False),
    )

    with pytest.raises(StaffAccountLifecycleError, match="requires a change"):
        suspend_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:suspend"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=2,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="No change",
        )


def test_transition_staff_account_database_failure_is_safe_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )

    def raise_database_error(**_kwargs):
        raise SQLAlchemyError("synthetic transition failure")

    monkeypatch.setattr(lifecycle_module, "update_staff_account_lifecycle", raise_database_error)

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        suspend_staff_account(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:suspend"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=2,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Account review",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_transition_staff_account_unexpected_failure_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_lifecycle",
        lambda **_kwargs: _record(status="suspended", version=3, mfa_enrolled=False),
    )

    def raise_unexpected(**_kwargs):
        raise RuntimeError("synthetic event failure")

    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", raise_unexpected)

    with pytest.raises(RuntimeError, match="synthetic event failure"):
        suspend_staff_account(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:suspend"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=2,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Account review",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_resolve_staff_principal_from_claims_requires_mfa() -> None:
    with pytest.raises(PermissionError, match="mfa"):
        resolve_staff_principal_from_claims(
            session=FakeSession(),  # type: ignore[arg-type]
            claims=StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=False),
        )


def test_resolve_staff_principal_from_claims_reports_missing_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", missing_account)

    with pytest.raises(lifecycle_module.StaffAccountNotFoundError, match="not found"):
        resolve_staff_principal_from_claims(
            session=FakeSession(),  # type: ignore[arg-type]
            claims=StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=True),
        )


def test_resolve_staff_principal_from_claims_returns_active_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_provider_subject",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "list_active_staff_permissions",
        lambda **_kwargs: frozenset({"intake:read"}),
    )

    principal = resolve_staff_principal_from_claims(
        session=FakeSession(),  # type: ignore[arg-type]
        claims=StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=True),
    )

    assert principal.actor_id == STAFF_ID
    assert principal.role_name == "operations_staff"
    assert principal.permissions == frozenset({"intake:read"})


def test_staff_account_lifecycle_database_failure_is_safe_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def raise_database_error(**_kwargs):
        raise SQLAlchemyError("synthetic staff account failure")

    monkeypatch.setattr(lifecycle_module, "insert_staff_account", raise_database_error)

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        create_staff_account(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="oidc:staff:123",
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"intake:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )

    assert session.rollbacks == 1
    assert session.commits == 0
