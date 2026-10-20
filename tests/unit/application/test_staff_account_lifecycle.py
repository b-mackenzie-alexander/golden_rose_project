from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

import golden_rose.application.staff_account_lifecycle as lifecycle_module
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    StaffAccountNotFoundError,
    StaffAccountVersionConflictError,
    activate_staff_account,
    correct_staff_account_onboarding,
    create_staff_account,
    deprovision_staff_account,
    record_staff_account_recovery_evidence,
    record_staff_account_session_revocation_evidence,
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
    staff_id: UUID = STAFF_ID,
    status: str = "suspended",
    version: int = 1,
    mfa_enrolled: bool = False,
    provider_subject: str = "oidc:staff:123",
    provider_email: str | None = None,
) -> StaffAccountRecord:
    return StaffAccountRecord(
        staff_id=staff_id,
        provider_subject=provider_subject,
        provider_email=provider_email,
        display_name="Mariela Torres",
        role_name="operations_staff",
        lifecycle_status=status,  # type: ignore[arg-type]
        mfa_enrolled=mfa_enrolled,
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=version,
        binding_status="pending"
        if provider_subject.startswith("pending-google-email:")
        else "google_verified",
        binding_verified_at=None if provider_subject.startswith("pending-google-email:") else NOW,
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
        provider_subject="",
        provider_email="staff@example.test",
        display_name=" Mariela   Torres ",
        role_name="operations_staff",
        permission_names=frozenset({"intake:read"}),
        mfa_enrolled=False,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text=" Initial staff onboarding ",
    )

    assert result.event_type == "staff_account.created"
    assert observed["account"]["provider_subject"].startswith("pending-google-email:")
    assert observed["account"]["provider_email"] == "staff@example.test"
    assert observed["account"]["display_name"] == "Mariela Torres"
    assert observed["account"]["lifecycle_status"] == "suspended"
    assert observed["grants"]["grants"] == ((GRANT_ID, "intake:read"),)
    assert observed["event"]["event_id"] == EVENT_ID
    assert observed["event"]["new_status"] == "suspended"
    assert observed["event"]["reason_text"] == "Initial staff onboarding"
    assert session.commits == 1
    assert session.rollbacks == 0


def test_create_staff_account_accepts_google_email_without_provider_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    def insert_account(**kwargs):
        observed["account"] = kwargs
        return _record(
            provider_subject=kwargs["provider_subject"],
            provider_email=kwargs["provider_email"],
        )

    monkeypatch.setattr(lifecycle_module, "insert_staff_account", insert_account)
    monkeypatch.setattr(lifecycle_module, "insert_staff_permission_grants", lambda **_kwargs: None)
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", lambda **_kwargs: None)

    result = create_staff_account(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:create", "intake:read"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        provider_subject="",
        provider_email=" Mariela.Torres@Example.Test ",
        display_name="Mariela Torres",
        role_name="operations_staff",
        permission_names=frozenset({"intake:read"}),
        mfa_enrolled=False,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Initial staff onboarding",
    )

    assert result.account.provider_subject.startswith("pending-google-email:")
    assert observed["account"]["provider_email"] == "mariela.torres@example.test"
    assert session.commits == 1


def test_correct_staff_account_onboarding_replaces_details_grants_and_records_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    class CorrectionIdentifiers:
        def __init__(self) -> None:
            self.values = [
                UUID("66666666-6666-4666-8666-666666666666"),
                UUID("77777777-7777-4777-8777-777777777777"),
                EVENT_ID,
            ]

        def new_uuid4(self) -> UUID:
            return self.values.pop(0)

    def get_existing(**kwargs):
        observed["get"] = kwargs
        return _record()

    def update_account(**kwargs):
        observed["account"] = kwargs
        return _record(version=2, mfa_enrolled=True)

    def revoke_grants(**kwargs) -> None:
        observed["revoked_grants"] = kwargs

    def insert_grants(**kwargs) -> None:
        observed["grants"] = kwargs

    def insert_event(**kwargs) -> None:
        observed["event"] = kwargs

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_id_for_update", get_existing)
    monkeypatch.setattr(lifecycle_module, "update_staff_account_onboarding", update_account)
    monkeypatch.setattr(lifecycle_module, "revoke_active_staff_permission_grants", revoke_grants)
    monkeypatch.setattr(lifecycle_module, "insert_staff_permission_grants", insert_grants)
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", insert_event)

    result = correct_staff_account_onboarding(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:create", "intake:read"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=1,
        display_name=" Mariela   Rivera ",
        role_name="operations_staff",
        permission_names=frozenset({"intake:read", "staff_account:read"}),
        clock=FixedClock(),
        identifiers=CorrectionIdentifiers(),
        reason_text=" Corrected onboarding record ",
    )

    assert result.event_type == "staff_account.access_updated"
    assert observed["get"]["staff_id"] == STAFF_ID
    assert "provider_subject" not in observed["account"]
    assert "provider_email" not in observed["account"]
    assert observed["account"]["display_name"] == "Mariela Rivera"
    assert observed["account"]["expected_version"] == 1
    assert observed["revoked_grants"]["reason_text"] == "Corrected onboarding record"
    assert observed["grants"]["grants"] == (
        (UUID("66666666-6666-4666-8666-666666666666"), "intake:read"),
        (UUID("77777777-7777-4777-8777-777777777777"), "staff_account:read"),
    )
    assert observed["event"]["event_type"] == "staff_account.access_updated"
    assert observed["event"]["previous_status"] == "suspended"
    assert observed["event"]["new_status"] == "suspended"
    assert observed["event"]["previous_version"] == 1
    assert observed["event"]["new_version"] == 2
    assert session.commits == 1
    assert session.rollbacks == 0


def test_correct_staff_account_onboarding_allows_active_account_access_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    class CorrectionIdentifiers:
        def __init__(self) -> None:
            self.values = [
                UUID("66666666-6666-4666-8666-666666666666"),
                UUID("77777777-7777-4777-8777-777777777777"),
                EVENT_ID,
            ]

        def new_uuid4(self) -> UUID:
            return self.values.pop(0)

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_: _record(status="active", version=3, mfa_enrolled=True),
    )

    def update_account(**kwargs):
        observed["account"] = kwargs
        return _record(status="active", version=4, mfa_enrolled=True)

    monkeypatch.setattr(lifecycle_module, "update_staff_account_onboarding", update_account)
    monkeypatch.setattr(
        lifecycle_module,
        "revoke_active_staff_permission_grants",
        lambda **kwargs: observed.setdefault("revoked_grants", kwargs),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_staff_permission_grants",
        lambda **kwargs: observed.setdefault("grants", kwargs),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_lifecycle_event",
        lambda **kwargs: observed.setdefault("event", kwargs),
    )

    result = correct_staff_account_onboarding(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:create", "intake:read"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=3,
        display_name="Mariela Torres",
        role_name="operations_staff",
        permission_names=frozenset({"staff_account:read", "intake:read"}),
        clock=FixedClock(),
        identifiers=CorrectionIdentifiers(),
        reason_text="Correct active account permissions",
    )

    assert result.account.lifecycle_status == "active"
    assert observed["account"]["expected_version"] == 3
    assert observed["grants"]["grants"] == (
        (UUID("66666666-6666-4666-8666-666666666666"), "intake:read"),
        (UUID("77777777-7777-4777-8777-777777777777"), "staff_account:read"),
    )
    assert observed["event"]["event_type"] == "staff_account.access_updated"
    assert observed["event"]["previous_status"] == "active"
    assert observed["event"]["new_status"] == "active"
    assert session.commits == 1
    assert session.rollbacks == 0


def test_correct_staff_account_onboarding_rejects_deprovisioned_accounts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_: _record(status="deprovisioned", version=3, mfa_enrolled=True),
    )

    with pytest.raises(StaffAccountLifecycleError, match="only active or suspended"):
        correct_staff_account_onboarding(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=3,
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"staff_account:read"}),
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="No deprovisioned correction",
        )

    assert session.rollbacks == 1


def test_correct_staff_account_onboarding_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:create"):
        correct_staff_account_onboarding(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"staff_account:read"}),
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Correct onboarding",
        )


def test_correct_staff_account_onboarding_rejects_invalid_role() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="invalid staff role"):
        correct_staff_account_onboarding(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            display_name="Mariela Torres",
            role_name="shadow_admin",
            permission_names=frozenset({"staff_account:read"}),
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Correct onboarding",
        )


def test_correct_staff_account_onboarding_rejects_self_correction() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="cannot correct itself"):
        correct_staff_account_onboarding(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create", "staff_account:read", actor_id=STAFF_ID),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"staff_account:read"}),
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Correct onboarding",
        )


@pytest.mark.parametrize(
    ("reader", "expected_error"),
    [
        (
            lambda **_: _record(status="suspended", version=2),
            StaffAccountVersionConflictError,
        ),
        (
            lambda **_: (_ for _ in ()).throw(NoResultFound()),
            StaffAccountNotFoundError,
        ),
    ],
)
def test_correct_staff_account_onboarding_rolls_back_recoverable_read_errors(
    monkeypatch: pytest.MonkeyPatch,
    reader,
    expected_error: type[Exception],
) -> None:
    session = FakeSession()
    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_id_for_update", reader)

    with pytest.raises(expected_error):
        correct_staff_account_onboarding(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"staff_account:read"}),
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Recoverable correction failure",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_correct_staff_account_onboarding_wraps_persistence_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_: _record(status="suspended", version=1),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_onboarding",
        Mock(side_effect=SQLAlchemyError("database details")),
    )

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        correct_staff_account_onboarding(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            display_name="Mariela Torres",
            role_name="operations_staff",
            permission_names=frozenset({"staff_account:read"}),
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Persistence correction failure",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_create_staff_account_unexpected_failure_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def raise_unexpected(**_kwargs):
        raise RuntimeError("synthetic account event failure")

    monkeypatch.setattr(
        lifecycle_module,
        "insert_staff_account",
        lambda **_kwargs: _record(status="suspended", version=1),
    )
    monkeypatch.setattr(lifecycle_module, "insert_staff_permission_grants", lambda **_kwargs: None)
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", raise_unexpected)

    with pytest.raises(RuntimeError, match="synthetic account event failure"):
        create_staff_account(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="",
            provider_email="staff@example.test",
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


def test_create_staff_account_denies_platform_admin_operational_data() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="platform administrator"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="",
            provider_email="staff@example.test",
            display_name="Platform Admin",
            role_name="platform_administrator",
            permission_names=frozenset({"calendar_import:manage"}),
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
            provider_subject="",
            provider_email="staff@example.test",
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
            provider_subject="",
            provider_email="staff@example.test",
            display_name="Mariela Torres",
            role_name="shadow_admin",
            permission_names=frozenset({"intake:read"}),
            mfa_enrolled=False,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Initial staff onboarding",
        )


def test_create_staff_account_requires_text_and_permissions() -> None:
    with pytest.raises(StaffAccountLifecycleError, match="requires provider subject or email"):
        create_staff_account(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:create"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            provider_subject="",
            provider_email=None,
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
            provider_subject="",
            provider_email="staff@example.test",
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
            provider_subject="",
            provider_email="staff@example.test",
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
            provider_subject="",
            provider_email="staff@example.test",
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


def test_activate_staff_account_rejects_pending_google_email_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(
            status="suspended",
            version=1,
            provider_subject="pending-google-email:abc123",
            provider_email="mariela.torres@example.test",
        ),
    )
    update = Mock()
    monkeypatch.setattr(lifecycle_module, "update_staff_account_lifecycle", update)

    with pytest.raises(StaffAccountLifecycleError, match="verified Google sign-in"):
        activate_staff_account(
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

    update.assert_not_called()
    assert session.rollbacks == 1


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


def test_record_staff_account_recovery_evidence_records_current_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=4, mfa_enrolled=True),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_lifecycle_event",
        lambda **kwargs: observed.setdefault("event", kwargs),
    )

    result = record_staff_account_recovery_evidence(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:recovery:record"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=4,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Assisted MFA recovery completed",
    )

    assert result.event_type == "staff_account.recovery_recorded"
    assert result.result_version == 4
    assert observed["event"]["event_type"] == "staff_account.recovery_recorded"
    assert observed["event"]["previous_status"] == "active"
    assert observed["event"]["new_status"] == "active"
    assert observed["event"]["previous_version"] == 4
    assert observed["event"]["new_version"] == 4
    assert observed["event"]["reason_text"] == "Assisted MFA recovery completed"
    assert session.commits == 1


def test_record_staff_account_session_revocation_evidence_allows_deprovisioned_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="deprovisioned", version=5, mfa_enrolled=False),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_lifecycle_event",
        lambda **kwargs: observed.setdefault("event", kwargs),
    )

    result = record_staff_account_session_revocation_evidence(
        session=session,  # type: ignore[arg-type]
        principal=_principal("staff_account:session:revoke"),
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        expected_version=5,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Provider sessions revoked",
    )

    assert result.event_type == "staff_account.sessions_revoked"
    assert result.result_version == 5
    assert observed["event"]["event_type"] == "staff_account.sessions_revoked"
    assert observed["event"]["previous_status"] == "deprovisioned"
    assert observed["event"]["new_status"] == "deprovisioned"
    assert observed["event"]["previous_version"] == 5
    assert observed["event"]["new_version"] == 5
    assert session.commits == 1


def test_staff_account_recovery_evidence_reports_missing_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_id_for_update", missing_account)

    with pytest.raises(StaffAccountNotFoundError, match="not found"):
        record_staff_account_recovery_evidence(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:recovery:record"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Recovery",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_staff_account_recovery_evidence_rejects_stale_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=True),
    )

    with pytest.raises(StaffAccountVersionConflictError, match="version conflict"):
        record_staff_account_recovery_evidence(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:recovery:record"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Recovery",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_staff_account_recovery_evidence_database_failure_is_safe_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="active", version=1, mfa_enrolled=True),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_lifecycle_event",
        Mock(side_effect=SQLAlchemyError("private recovery detail")),
    )

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        record_staff_account_recovery_evidence(
            session=session,  # type: ignore[arg-type]
            principal=_principal("staff_account:recovery:record"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Recovery",
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_staff_account_recovery_evidence_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:recovery:record"):
        record_staff_account_recovery_evidence(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Recovery",
        )


def test_staff_account_session_revocation_evidence_requires_permission() -> None:
    with pytest.raises(PermissionError, match="staff_account:session:revoke"):
        record_staff_account_session_revocation_evidence(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal(),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=1,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Session revoke",
        )


def test_staff_account_recovery_evidence_rejects_deprovisioned_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_id_for_update",
        lambda **_kwargs: _record(status="deprovisioned", version=5, mfa_enrolled=False),
    )

    with pytest.raises(StaffAccountLifecycleError, match="cannot be recovered"):
        record_staff_account_recovery_evidence(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("staff_account:recovery:record"),
            command_id=COMMAND_ID,
            staff_id=STAFF_ID,
            expected_version=5,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Recovery",
        )


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


def test_resolve_staff_principal_from_claims_accepts_missing_token_mfa_when_account_enrolled(
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
        claims=StaffIdentityClaims(provider_subject="oidc:staff:123", mfa_verified=False),
    )

    assert principal.actor_id == STAFF_ID
    assert principal.permissions == frozenset({"intake:read"})


def test_resolve_staff_principal_from_claims_requires_account_mfa_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle_module,
        "get_staff_account_by_provider_subject",
        lambda **_kwargs: _record(status="active", version=2, mfa_enrolled=False),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "list_active_staff_permissions",
        lambda **_kwargs: frozenset({"intake:read"}),
    )

    with pytest.raises(ValueError, match="eligible"):
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


def test_resolve_staff_principal_from_claims_reports_missing_pending_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", missing_account)

    with pytest.raises(StaffAccountNotFoundError, match="not found"):
        resolve_staff_principal_from_claims(
            session=session,  # type: ignore[arg-type]
            claims=StaffIdentityClaims(
                provider_subject="oidc:staff:missing",
                provider_email=None,
                mfa_verified=True,
            ),
        )

    assert session.rollbacks == 0


def test_resolve_staff_principal_from_claims_reports_missing_pending_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", missing_account)
    monkeypatch.setattr(
        lifecycle_module,
        "get_pending_staff_account_by_provider_email_for_update",
        missing_account,
    )

    with pytest.raises(StaffAccountNotFoundError, match="not found"):
        resolve_staff_principal_from_claims(
            session=session,  # type: ignore[arg-type]
            claims=StaffIdentityClaims(
                provider_subject="oidc:staff:missing",
                provider_email="mariela.torres@example.test",
                mfa_verified=True,
            ),
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_resolve_staff_principal_from_claims_wraps_pending_binding_database_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", missing_account)
    monkeypatch.setattr(
        lifecycle_module,
        "get_pending_staff_account_by_provider_email_for_update",
        lambda **_kwargs: _record(
            status="suspended",
            version=1,
            provider_subject="pending-google-email:abc123",
            provider_email="mariela.torres@example.test",
        ),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_provider_binding",
        Mock(side_effect=SQLAlchemyError("private binding details")),
    )

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        resolve_staff_principal_from_claims(
            session=session,  # type: ignore[arg-type]
            claims=StaffIdentityClaims(
                provider_subject="oidc:staff:bound",
                provider_email="mariela.torres@example.test",
                mfa_verified=True,
            ),
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_resolve_staff_principal_from_claims_pending_binding_unexpected_failure_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def missing_account(**_kwargs):
        raise NoResultFound()

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", missing_account)
    monkeypatch.setattr(
        lifecycle_module,
        "get_pending_staff_account_by_provider_email_for_update",
        lambda **_kwargs: _record(
            status="suspended",
            version=1,
            provider_subject="pending-google-email:abc123",
            provider_email="mariela.torres@example.test",
        ),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "update_staff_account_provider_binding",
        lambda **_kwargs: _record(
            status="suspended",
            version=2,
            provider_subject="oidc:staff:bound",
            provider_email="mariela.torres@example.test",
        ),
    )
    monkeypatch.setattr(
        lifecycle_module,
        "insert_lifecycle_event",
        Mock(side_effect=RuntimeError("synthetic binding event failure")),
    )

    with pytest.raises(RuntimeError, match="synthetic binding event failure"):
        resolve_staff_principal_from_claims(
            session=session,  # type: ignore[arg-type]
            claims=StaffIdentityClaims(
                provider_subject="oidc:staff:bound",
                provider_email="mariela.torres@example.test",
                mfa_verified=True,
            ),
        )

    assert session.rollbacks == 1
    assert session.commits == 0


def test_resolve_staff_principal_binds_pending_google_email_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    def missing_account(**_kwargs):
        raise NoResultFound()

    def pending_account(**kwargs):
        observed["pending"] = kwargs
        return _record(
            status="suspended",
            version=1,
            provider_subject="pending-google-email:abc123",
            provider_email="mariela.torres@example.test",
        )

    def update_binding(**kwargs):
        observed["binding"] = kwargs
        return _record(
            status="suspended",
            version=2,
            mfa_enrolled=True,
            provider_subject=kwargs["provider_subject"],
            provider_email="mariela.torres@example.test",
        )

    def insert_event(**kwargs) -> None:
        observed["event"] = kwargs

    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", missing_account)
    monkeypatch.setattr(
        lifecycle_module,
        "get_pending_staff_account_by_provider_email_for_update",
        pending_account,
    )
    monkeypatch.setattr(lifecycle_module, "update_staff_account_provider_binding", update_binding)
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", insert_event)
    monkeypatch.setattr(
        lifecycle_module,
        "list_active_staff_permissions",
        lambda **_kwargs: frozenset({"intake:read"}),
    )

    with pytest.raises(ValueError, match="eligible"):
        resolve_staff_principal_from_claims(
            session=session,  # type: ignore[arg-type]
            claims=StaffIdentityClaims(
                provider_subject="oidc:staff:bound",
                provider_email=" Mariela.Torres@Example.Test ",
                mfa_verified=True,
            ),
        )

    assert observed["pending"]["provider_email"] == "mariela.torres@example.test"
    assert observed["binding"]["provider_subject"] == "oidc:staff:bound"
    assert observed["binding"]["mfa_enrolled"] is True
    assert observed["event"]["event_type"] == "staff_account.binding_verified"
    assert session.commits == 1


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
            provider_subject="",
            provider_email="staff@example.test",
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


@pytest.mark.parametrize("stage", ["lock", "update", "audit", "commit"])
def test_legacy_verification_database_failure_is_safe_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    account = replace(
        _record(status="active", mfa_enrolled=True),
        binding_status="legacy_unverified",
        binding_verified_at=None,
    )
    session = Mock()
    failure = SQLAlchemyError("private legacy storage detail")
    lookup = Mock(return_value=account)
    lock = Mock(return_value=account)
    audit = Mock()
    permissions = Mock(return_value=frozenset({"intake:read"}))
    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_provider_subject", lookup)
    monkeypatch.setattr(lifecycle_module, "get_staff_account_by_id_for_update", lock)
    monkeypatch.setattr(lifecycle_module, "insert_lifecycle_event", audit)
    monkeypatch.setattr(lifecycle_module, "list_active_staff_permissions", permissions)
    {"lock": lock, "update": session.execute, "audit": audit, "commit": session.commit}[
        stage
    ].side_effect = failure
    with pytest.raises(SafePersistenceError, match="^persistence operation failed$") as caught:
        resolve_staff_principal_from_claims(
            session=session,
            claims=StaffIdentityClaims(
                provider_subject=account.provider_subject, mfa_verified=False
            ),
        )
    assert caught.value.__cause__ is failure
    session.rollback.assert_called_once_with()
    permissions.assert_not_called()
