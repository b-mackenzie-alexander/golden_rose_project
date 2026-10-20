"""Google binding, access isolation and retry safety on disposable PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.application.staff_account_delegations import (
    StaffDelegationPermissionUnavailableError,
    grant_staff_delegation,
)
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    StaffAccountLifecycleResult,
    StaffAccountNotFoundError,
    StaffAccountVersionConflictError,
    activate_staff_account,
    correct_staff_account_onboarding,
    create_staff_account,
    resolve_staff_principal_from_claims,
    update_staff_account_google_email,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_accounts import StaffIdentityClaims
from golden_rose.main import create_app
from golden_rose.persistence.staff_accounts import StaffAccountRecord, get_staff_account_by_id
from tests.integration.test_intake_migrations import migrate
from tests.integration.test_intake_migrations import migration_database as migration_database

ACTOR = UUID(int=1)
NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)
GRANTS = frozenset(
    {
        "staff_account:create",
        "staff_account:activate",
        "staff_account:read",
        "staff_account:signin:reset",
        "intake:read",
    }
)
PRINCIPAL = StaffPrincipal(actor_id=ACTOR, role_name="owner", permissions=GRANTS)


class Clock:
    def now(self):
        return NOW


class Identifiers:
    def new_uuid4(self):
        return uuid4()


@pytest.fixture
def store(migration_database):
    migrate(migration_database, "head")
    with migration_database.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO staff_accounts(staff_id,provider_subject,display_name,role_name,
              lifecycle_status,mfa_enrolled,created_at,created_by,updated_at,updated_by,version)
            VALUES(:id,'operator-test-subject','Fictional operator','owner','active',true,
              :now,:id,:now,:id,1)
        """),
            {"id": ACTOR, "now": NOW},
        )
        connection.execute(
            text("""INSERT INTO staff_permission_grants(grant_id,staff_id,
          permission_name,scope_kind,granted_at,granted_by)
          VALUES(:grant,:id,'staff_account:signin:reset','global',:now,:id)"""),
            {"grant": uuid4(), "id": ACTOR, "now": NOW},
        )
    with Session(migration_database) as session:
        session.execute(text("SET ROLE golden_rose_runtime"))
        yield session


def create(session: Session, **overrides: Any) -> StaffAccountRecord:
    args: dict[str, Any] = {
        "session": session,
        "principal": PRINCIPAL,
        "command_id": uuid4(),
        "staff_id": uuid4(),
        "provider_subject": "",
        "provider_email": "owner@example.test",
        "display_name": "Fictional owner",
        "role_name": "owner",
        "permission_names": frozenset({"intake:read"}),
        "mfa_enrolled": False,
        "clock": Clock(),
        "identifiers": Identifiers(),
        "reason_text": "Fictional onboarding",
    }
    args.update(overrides)
    return create_staff_account(**args).account


def bind(
    session: Session, account: StaffAccountRecord, subject: str = "google-test-identity"
) -> StaffAccountRecord:
    with pytest.raises(ValueError, match="eligible"):
        resolve_staff_principal_from_claims(
            session=session,
            claims=StaffIdentityClaims(
                provider_subject=subject, provider_email=account.provider_email, mfa_verified=False
            ),
        )
    return get_staff_account_by_id(session=session, staff_id=account.staff_id)


def activate(session: Session, account: StaffAccountRecord) -> StaffAccountRecord:
    return activate_staff_account(
        session=session,
        principal=PRINCIPAL,
        command_id=uuid4(),
        staff_id=account.staff_id,
        expected_version=account.version,
        mfa_enrolled=True,
        clock=Clock(),
        identifiers=Identifiers(),
        reason_text="MFA confirmed for test",
    ).account


def restart_args(session: Session, account: StaffAccountRecord) -> dict[str, Any]:
    return {
        "session": session,
        "principal": PRINCIPAL,
        "command_id": uuid4(),
        "staff_id": account.staff_id,
        "expected_version": account.version,
        "provider_email": account.provider_email,
        "clock": Clock(),
        "identifiers": Identifiers(),
        "reason_text": "Restart fictional onboarding",
    }


def test_pending_google_proof_and_explicit_activation_are_separate(store):
    account = create(store)
    assert account.binding_status == "pending"
    with pytest.raises(StaffAccountLifecycleError, match="verified Google"):
        activate(store, account)
    bound = bind(store, account)
    assert bound.binding_status == "google_verified"
    assert bound.binding_verified_at is not None
    assert bound.lifecycle_status == "suspended" and not bound.mfa_enrolled
    active = activate(store, bound)
    principal = resolve_staff_principal_from_claims(
        session=store,
        claims=StaffIdentityClaims(provider_subject=active.provider_subject, mfa_verified=False),
    )
    assert principal.actor_id == account.staff_id
    assert principal.permissions == frozenset({"intake:read"})


def test_access_update_preserves_all_signin_and_mfa_fields(store):
    account = activate(store, bind(store, create(store)))
    changed = correct_staff_account_onboarding(
        session=store,
        principal=PRINCIPAL,
        command_id=uuid4(),
        staff_id=account.staff_id,
        expected_version=account.version,
        display_name="Updated fictional owner",
        role_name="owner",
        permission_names=frozenset({"intake:read", "worker:read"}),
        clock=Clock(),
        identifiers=Identifiers(),
        reason_text="Update durable access",
    ).account
    for name in (
        "provider_subject",
        "provider_email",
        "binding_status",
        "binding_verified_at",
        "mfa_enrolled",
    ):
        assert getattr(changed, name) == getattr(account, name)


def test_same_email_restart_replay_does_not_reset_a_subsequently_rebound_account(store):
    original = activate(store, bind(store, create(store)))
    args = restart_args(store, original)
    restarted = update_staff_account_google_email(**args)
    assert restarted.account.staff_id == original.staff_id
    assert restarted.account.binding_status == "pending"
    rebound = activate(store, bind(store, restarted.account, "replacement-google-test-identity"))
    replay = update_staff_account_google_email(**args)
    assert asdict(replay.account) == asdict(restarted.account)
    assert get_staff_account_by_id(session=store, staff_id=original.staff_id) == rebound
    with pytest.raises(StaffAccountLifecycleError, match="conflicts"):
        update_staff_account_google_email(**{**args, "reason_text": "Changed request"})
    assert get_staff_account_by_id(session=store, staff_id=original.staff_id) == rebound
    assert store.scalar(text("SELECT count(*) FROM staff_signin_restarts")) == 1
    stored = store.scalar(text("SELECT result::text FROM staff_signin_restarts"))
    assert "provider_subject" not in stored and original.provider_subject not in stored


@pytest.mark.parametrize("status", ["active", "suspended"])
def test_legacy_exact_subject_is_verified_without_changing_account_access(store, status):
    account = create(store)
    # Seed historical state as the disposable schema owner, not through the new ordinary API.
    store.execute(text("RESET ROLE"))
    store.execute(
        text("""UPDATE staff_accounts SET provider_subject='legacy-google-test-identity',
        binding_status='legacy_unverified', lifecycle_status=:status, mfa_enrolled=true
        WHERE staff_id=:id"""),
        {"id": account.staff_id, "status": status},
    )
    store.commit()
    store.execute(text("SET ROLE golden_rose_runtime"))
    claims = StaffIdentityClaims(provider_subject="legacy-google-test-identity", mfa_verified=False)
    if status == "suspended":
        with pytest.raises(ValueError, match="eligible"):
            resolve_staff_principal_from_claims(session=store, claims=claims)
    else:
        assert (
            resolve_staff_principal_from_claims(session=store, claims=claims).actor_id
            == account.staff_id
        )
    verified = get_staff_account_by_id(session=store, staff_id=account.staff_id)
    assert verified.binding_status == "google_verified" and verified.binding_verified_at
    assert verified.lifecycle_status == status and verified.mfa_enrolled


def test_email_match_cannot_take_over_an_active_bound_account(store):
    account = activate(store, bind(store, create(store)))
    with pytest.raises(StaffAccountNotFoundError):
        resolve_staff_principal_from_claims(
            session=store,
            claims=StaffIdentityClaims(
                provider_subject="different-google-test-identity",
                provider_email=account.provider_email,
                mfa_verified=True,
            ),
        )
    assert get_staff_account_by_id(session=store, staff_id=account.staff_id) == account


@pytest.mark.parametrize("case", ["permission", "self", "deprovisioned", "stale"])
def test_restart_denials_preserve_the_record_and_do_not_write_receipts(store, case):
    account = create(store)
    args = restart_args(store, account)
    error: type[Exception] = StaffAccountLifecycleError
    if case == "permission":
        args["principal"] = StaffPrincipal(
            actor_id=ACTOR, role_name="owner", permissions=frozenset({"staff_account:create"})
        )
        error = PermissionError
    elif case == "self":
        args["staff_id"] = ACTOR
    elif case == "deprovisioned":
        store.execute(
            text("UPDATE staff_accounts SET lifecycle_status='deprovisioned' WHERE staff_id=:id"),
            {"id": account.staff_id},
        )
        store.commit()
    else:
        args["expected_version"] = 99
        error = StaffAccountVersionConflictError
    before = get_staff_account_by_id(session=store, staff_id=account.staff_id)
    with pytest.raises(error):
        update_staff_account_google_email(**args)
    assert get_staff_account_by_id(session=store, staff_id=account.staff_id) == before
    assert store.scalar(text("SELECT count(*) FROM staff_signin_restarts")) == 0


def test_diagnostics_and_session_responses_never_expose_raw_subjects(store, migration_database):
    account = create(store)
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: PRINCIPAL
    with TestClient(app, raise_server_exceptions=False) as client:
        for path in (
            f"/api/staff/v1/staff-accounts/{account.staff_id}/diagnostics",
            "/api/staff/v1/staff-accounts",
            "/api/staff/v1/session",
        ):
            response = client.get(path)
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "no-store"
            assert "provider_subject" not in response.text
            assert account.provider_subject not in response.text


def test_delegated_recovery_authority_cannot_be_made_permanent_by_a_lesser_editor(store):
    account = create(store)
    store.execute(
        text("""INSERT INTO staff_delegations(delegation_id,grantor_staff_id,
        grantee_staff_id,permission_name,scope_kind,reason_text,starts_at,expires_at)
        VALUES(:id,:actor,:target,'staff_account:signin:reset','global','Fictional coverage',
          :now,:until)"""),
        {
            "id": uuid4(),
            "actor": ACTOR,
            "target": account.staff_id,
            "now": datetime(2020, 1, 1, tzinfo=UTC),
            "until": datetime(2099, 1, 1, tzinfo=UTC),
        },
    )
    store.commit()
    lesser = StaffPrincipal(
        actor_id=ACTOR, role_name="owner", permissions=frozenset({"staff_account:create"})
    )
    with pytest.raises(PermissionError, match="cannot provision"):
        correct_staff_account_onboarding(
            session=store,
            principal=lesser,
            command_id=uuid4(),
            staff_id=account.staff_id,
            expected_version=account.version,
            display_name=account.display_name,
            role_name="owner",
            permission_names=frozenset({"intake:read", "staff_account:signin:reset"}),
            clock=Clock(),
            identifiers=Identifiers(),
            reason_text="Attempt durable conversion",
        )
    assert get_staff_account_by_id(session=store, staff_id=account.staff_id) == account
    assert (
        store.scalar(
            text(
                "SELECT count(*) FROM staff_permission_grants WHERE staff_id=:id "
                "AND permission_name='staff_account:signin:reset'"
            ),
            {"id": account.staff_id},
        )
        == 0
    )


def test_existing_durable_recovery_grant_can_be_preserved_by_an_access_editor(store):
    account = create(store, permission_names=frozenset({"staff_account:signin:reset"}))
    lesser = StaffPrincipal(
        actor_id=ACTOR, role_name="owner", permissions=frozenset({"staff_account:create"})
    )
    changed = correct_staff_account_onboarding(
        session=store,
        principal=lesser,
        command_id=uuid4(),
        staff_id=account.staff_id,
        expected_version=account.version,
        display_name="Corrected display name",
        role_name="owner",
        permission_names=frozenset({"staff_account:signin:reset"}),
        clock=Clock(),
        identifiers=Identifiers(),
        reason_text="Preserve existing durable grant",
    ).account
    assert changed.provider_subject == account.provider_subject
    assert changed.display_name == "Corrected display name"


def test_restart_api_replay_keeps_original_grants_after_subsequent_access_edit(
    store, migration_database
):
    account = activate(store, bind(store, create(store)))
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: PRINCIPAL
    command_id = str(uuid4())
    payload = {
        "expected_version": account.version,
        "provider_email": account.provider_email,
        "reason_text": "Fictional recovery",
    }
    with TestClient(app, raise_server_exceptions=False) as client:
        path = f"/api/staff/v1/staff-accounts/{account.staff_id}/restart-google-signin"
        first = client.post(path, json=payload, headers={"Idempotency-Key": command_id})
        assert first.status_code == 200, first.text
        rebound = activate(
            store, bind(store, get_staff_account_by_id(session=store, staff_id=account.staff_id))
        )
        correct_staff_account_onboarding(
            session=store,
            principal=PRINCIPAL,
            command_id=uuid4(),
            staff_id=account.staff_id,
            expected_version=rebound.version,
            display_name=rebound.display_name,
            role_name="owner",
            permission_names=frozenset({"intake:read", "worker:read"}),
            clock=Clock(),
            identifiers=Identifiers(),
            reason_text="Intervening access edit",
        )
        replay = client.post(path, json=payload, headers={"Idempotency-Key": command_id})
        assert replay.status_code == 200, replay.text
        assert replay.json() == first.json()
        assert replay.json()["account"]["permission_names"] == ["intake:read"]


def test_concurrent_identical_restart_commands_have_one_result(store, migration_database):
    account = activate(store, bind(store, create(store)))
    args = restart_args(store, account)

    def run() -> StaffAccountLifecycleResult:
        with Session(migration_database) as session:
            session.execute(text("SET ROLE golden_rose_runtime"))
            return update_staff_account_google_email(**{**args, "session": session})

    # End this reader transaction before concurrent independent connections acquire row locks.
    store.commit()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(pool.map(lambda _: run(), range(2)))
    assert a == b
    assert (
        get_staff_account_by_id(session=store, staff_id=account.staff_id).version
        == account.version + 1
    )
    assert store.scalar(text("SELECT count(*) FROM staff_signin_restarts")) == 1


def test_migration_preserves_legacy_accounts_without_fabricating_google_proof(migration_database):
    migrate(migration_database, "0020_contact_email_fields")
    with migration_database.begin() as connection:
        connection.execute(
            text("""INSERT INTO staff_accounts(staff_id,provider_subject,
          display_name,role_name,lifecycle_status,mfa_enrolled,created_at,created_by,
          updated_at,updated_by,version) VALUES(:id,'historical-test-subject','Historical owner',
          'owner','active',true,:now,:id,:now,:id,1)"""),
            {"id": ACTOR, "now": NOW},
        )
    migrate(migration_database, "head")
    with migration_database.connect() as connection:
        assert connection.execute(
            text("SELECT lifecycle_status,binding_status,binding_verified_at FROM staff_accounts")
        ).one() == ("active", "legacy_unverified", None)


def test_active_pending_legacy_anomaly_stops_migration_before_schema_changes(migration_database):
    migrate(migration_database, "0020_contact_email_fields")
    with migration_database.begin() as connection:
        connection.execute(
            text("""INSERT INTO staff_accounts(staff_id,provider_subject,
          provider_email,display_name,role_name,lifecycle_status,mfa_enrolled,created_at,
          created_by,updated_at,updated_by,version) VALUES(:id,'pending-google-email:historical',
          'owner@example.test','Historical owner','owner','active',true,:now,:id,:now,:id,1)"""),
            {"id": ACTOR, "now": NOW},
        )
    with pytest.raises(RuntimeError, match="reviewed recovery"):
        migrate(migration_database, "head")
    with migration_database.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0020_contact_email_fields"
        )
        assert not connection.scalar(
            text(
                "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
                "WHERE table_name='staff_accounts' AND column_name='binding_status')"
            )
        )


def test_evidence_only_event_cannot_claim_a_lifecycle_transition(store):
    account = create(store)
    with pytest.raises(IntegrityError):
        store.execute(
            text("""INSERT INTO staff_account_lifecycle_events(event_id,command_id,
          staff_id,actor_id,event_type,previous_status,new_status,previous_version,new_version,
          occurred_at,reason_text) VALUES(:event,:command,:staff,:actor,
          'staff_account.recovery_recorded','suspended','active',1,1,:now,'Evidence only')"""),
            {
                "event": uuid4(),
                "command": uuid4(),
                "staff": account.staff_id,
                "actor": ACTOR,
                "now": NOW,
            },
        )
    store.rollback()


@pytest.mark.parametrize("operation", ["create", "access", "delegate"])
def test_temporary_recovery_grantor_cannot_provision_or_redelegate_authority(store, operation):
    account = create(store)
    store.execute(
        text(
            "UPDATE staff_permission_grants SET revoked_at=:now,revoked_by=:id,"
            "revocation_reason='Fictional revocation' WHERE staff_id=:id"
        ),
        {"id": ACTOR, "now": NOW},
    )
    store.commit()
    temporary = StaffPrincipal(
        actor_id=ACTOR, role_name="owner", permissions=GRANTS | {"staff_account:delegation:grant"}
    )
    with pytest.raises((PermissionError, StaffDelegationPermissionUnavailableError)):
        if operation == "create":
            create(
                store,
                principal=temporary,
                provider_email="second@example.test",
                permission_names=frozenset({"staff_account:signin:reset"}),
            )
        elif operation == "access":
            correct_staff_account_onboarding(
                session=store,
                principal=temporary,
                command_id=uuid4(),
                staff_id=account.staff_id,
                expected_version=account.version,
                display_name=account.display_name,
                role_name="owner",
                permission_names=frozenset({"staff_account:signin:reset"}),
                clock=Clock(),
                identifiers=Identifiers(),
                reason_text="Cannot make temporary authority durable",
            )
        else:
            grant_staff_delegation(
                session=store,
                principal=temporary,
                delegation_id=uuid4(),
                grantee_staff_id=account.staff_id,
                permission_name="staff_account:signin:reset",
                scope_kind="global",
                expires_at=datetime(2026, 10, 21, tzinfo=UTC),
                clock=Clock(),
                reason_text="Cannot extend temporary authority",
            )
    assert get_staff_account_by_id(session=store, staff_id=account.staff_id) == account


def test_downgrade_with_google_proof_refuses_before_ddl(store, migration_database):
    bind(store, create(store))
    store.commit()
    with pytest.raises(RuntimeError, match="reviewed downgrade"):
        migrate(migration_database, "0020_contact_email_fields", downgrade=True)
    with migration_database.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0021_staff_google_binding"
        )
        assert (
            connection.scalar(
                text("SELECT binding_status FROM staff_accounts WHERE staff_id<>:id"), {"id": ACTOR}
            )
            == "google_verified"
        )


def test_empty_binding_migration_can_downgrade_without_destroying_evidence(migration_database):
    migrate(migration_database, "head")
    migrate(migration_database, "0020_contact_email_fields", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.scalar(text("SELECT to_regclass('public.staff_signin_restarts')")) is None
    migrate(migration_database, "head")


def test_api_identity_injection_is_rejected_without_account_grant_or_event_writes(
    store, migration_database
):
    account = create(store)
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: PRINCIPAL
    base = {
        "display_name": account.display_name,
        "role_name": "owner",
        "permission_names": ["intake:read"],
        "reason_text": "Fictional access edit",
    }
    before = tuple(
        store.scalar(text(f"SELECT count(*) FROM {table}"))
        for table in ("staff_accounts", "staff_permission_grants", "staff_account_lifecycle_events")
    )
    store.commit()
    with TestClient(app, raise_server_exceptions=False) as client:
        for endpoint in ("access", "correct-onboarding"):
            for forbidden in (
                {"provider_subject": "manual-identity"},
                {"provider_email": "other@example.test"},
                {"mfa_enrolled": True},
            ):
                response = client.post(
                    f"/api/staff/v1/staff-accounts/{account.staff_id}/{endpoint}",
                    json={**base, "expected_version": account.version, **forbidden},
                    headers={"Idempotency-Key": str(uuid4())},
                )
                assert response.status_code == 422
        response = client.post(
            "/api/staff/v1/staff-accounts",
            json={
                **base,
                "provider_email": "new@example.test",
                "mfa_enrolled": False,
                "provider_subject": "manual-identity",
            },
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 422
    assert (
        tuple(
            store.scalar(text(f"SELECT count(*) FROM {table}"))
            for table in (
                "staff_accounts",
                "staff_permission_grants",
                "staff_account_lifecycle_events",
            )
        )
        == before
    )


def test_diagnostics_reports_current_capabilities_and_does_not_grant_authority(
    store, migration_database
):
    account = bind(store, create(store))
    store.commit()
    app = create_app(engine_factory=lambda: migration_database)
    with TestClient(app, raise_server_exceptions=False) as client:
        app.dependency_overrides[get_staff_principal] = lambda: PRINCIPAL
        response = client.get(f"/api/staff/v1/staff-accounts/{account.staff_id}/diagnostics")
        assert response.status_code == 200
        assert response.json()["can_restart_signin"] is True
        assert response.json()["can_activate"] is True
        assert response.json()["restart_unavailable_reason"] is None
        response = client.get(f"/api/staff/v1/staff-accounts/{ACTOR}/diagnostics")
        assert response.json()["restart_unavailable_reason"] == "self_reset"
        reader = StaffPrincipal(
            actor_id=ACTOR, role_name="owner", permissions=frozenset({"staff_account:read"})
        )
        app.dependency_overrides[get_staff_principal] = lambda: reader
        response = client.get(f"/api/staff/v1/staff-accounts/{account.staff_id}/diagnostics")
        assert response.json()["restart_unavailable_reason"] == "permission_required"
        assert response.json()["can_activate"] is False
        response = client.post(
            f"/api/staff/v1/staff-accounts/{account.staff_id}/google-email",
            json={
                "expected_version": account.version,
                "provider_email": account.provider_email,
                "reason_text": "No recovery grant",
            },
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 403
        app.dependency_overrides[get_staff_principal] = lambda: StaffPrincipal(
            actor_id=ACTOR, role_name="owner", permissions=frozenset()
        )
        response = client.get(f"/api/staff/v1/staff-accounts/{account.staff_id}/diagnostics")
        assert response.status_code == 403
        assert response.headers["cache-control"] == "no-store"
