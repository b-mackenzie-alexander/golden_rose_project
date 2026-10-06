from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

import pytest
from sqlalchemy.exc import SQLAlchemyError

from golden_rose import bootstrap_staff_account
from golden_rose.bootstrap_staff_account import (
    BOOTSTRAP_PERMISSION_NAMES,
    SCHEMA_OWNER_ROLE,
    BootstrapConfigurationError,
    BootstrapStateError,
    FirstStaffBootstrapResult,
    bootstrap_first_staff_account,
)

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
STAFF_ID = UUID("11111111-1111-4111-8111-111111111111")
COMMAND_ID = UUID("22222222-2222-4222-8222-222222222222")
EVENT_ID = UUID("33333333-3333-4333-8333-333333333333")


class FakeResult:
    def __init__(self, *, scalar: int | None = None, row: tuple[object, ...] | None = None):
        self.scalar = scalar
        self.row = row

    def scalar_one(self) -> int:
        assert self.scalar is not None
        return self.scalar

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row


class FakeConnection:
    def __init__(self, results: list[FakeResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.calls.append((sql, parameters))
        if sql.lstrip().upper().startswith("SELECT") and self.results:
            return self.results.pop(0)
        return FakeResult()


class FixedUuids:
    def __init__(self) -> None:
        grant_ids = [
            UUID(f"44444444-4444-4444-8444-{index:012d}")
            for index in range(len(BOOTSTRAP_PERMISSION_NAMES))
        ]
        self.values = [STAFF_ID, COMMAND_ID, EVENT_ID, *grant_ids]

    def __call__(self) -> UUID:
        return self.values.pop(0)


class FakeEngine:
    def __init__(self) -> None:
        self.connection = object()

    def begin(self):
        return self

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback) -> Literal[False]:
        return False


def test_bootstrap_first_staff_account_creates_active_owner_and_global_grants() -> None:
    connection = FakeConnection(
        [
            FakeResult(scalar=0),
            FakeResult(row=None),
            FakeResult(scalar=len(BOOTSTRAP_PERMISSION_NAMES)),
        ]
    )

    result = bootstrap_first_staff_account(
        connection=connection,  # type: ignore[arg-type]
        provider_subject="  google-subject-123  ",
        display_name=" Initial   Owner ",
        occurred_at=NOW,
        uuid_factory=FixedUuids(),
    )

    assert result.created is True
    assert result.staff_id == STAFF_ID
    assert result.role_name == "owner"
    assert result.lifecycle_status == "active"
    assert result.mfa_enrolled is True
    assert result.requested_permission_count == len(BOOTSTRAP_PERMISSION_NAMES)
    assert result.active_permission_count == len(BOOTSTRAP_PERMISSION_NAMES)
    joined_sql = "\n".join(statement for statement, _ in connection.calls)
    assert "INSERT INTO staff_accounts" in joined_sql
    assert "INSERT INTO staff_account_lifecycle_events" in joined_sql
    assert joined_sql.count("INSERT INTO staff_permission_grants") == len(
        BOOTSTRAP_PERMISSION_NAMES
    )
    first_insert = next(
        parameters
        for statement, parameters in connection.calls
        if "INSERT INTO staff_accounts" in statement
    )
    assert first_insert == {
        "staff_id": STAFF_ID,
        "provider_subject": "google-subject-123",
        "display_name": "Initial Owner",
        "occurred_at": NOW,
    }


def test_bootstrap_existing_active_owner_is_idempotent_and_adds_missing_grants() -> None:
    connection = FakeConnection(
        [
            FakeResult(scalar=1),
            FakeResult(row=(STAFF_ID, "owner", "active", True, 1)),
            FakeResult(scalar=len(BOOTSTRAP_PERMISSION_NAMES)),
        ]
    )

    result = bootstrap_first_staff_account(
        connection=connection,  # type: ignore[arg-type]
        provider_subject="google-subject-123",
        display_name="Initial Owner",
        occurred_at=NOW,
        uuid_factory=FixedUuids(),
    )

    assert result.created is False
    joined_sql = "\n".join(statement for statement, _ in connection.calls)
    assert "INSERT INTO staff_accounts" not in joined_sql
    assert "INSERT INTO staff_account_lifecycle_events" not in joined_sql
    assert joined_sql.count("INSERT INTO staff_permission_grants") == len(
        BOOTSTRAP_PERMISSION_NAMES
    )


def test_bootstrap_rejects_email_as_provider_subject() -> None:
    connection = FakeConnection([])

    with pytest.raises(BootstrapConfigurationError, match="stable provider subject"):
        bootstrap_first_staff_account(
            connection=connection,  # type: ignore[arg-type]
            provider_subject="owner@example.com",
            display_name="Initial Owner",
            occurred_at=NOW,
            uuid_factory=FixedUuids(),
        )


def test_bootstrap_rejects_blank_display_name() -> None:
    connection = FakeConnection([])

    with pytest.raises(BootstrapConfigurationError, match="display_name is invalid"):
        bootstrap_first_staff_account(
            connection=connection,  # type: ignore[arg-type]
            provider_subject="google-subject-123",
            display_name="   ",
            occurred_at=NOW,
            uuid_factory=FixedUuids(),
        )


def test_bootstrap_rejects_creating_after_other_accounts_exist() -> None:
    connection = FakeConnection([FakeResult(scalar=1), FakeResult(row=None)])

    with pytest.raises(BootstrapStateError, match="cannot create after accounts exist"):
        bootstrap_first_staff_account(
            connection=connection,  # type: ignore[arg-type]
            provider_subject="google-subject-123",
            display_name="Initial Owner",
            occurred_at=NOW,
            uuid_factory=FixedUuids(),
        )


def test_bootstrap_rejects_existing_non_active_owner_state() -> None:
    connection = FakeConnection(
        [
            FakeResult(scalar=1),
            FakeResult(row=(STAFF_ID, "operations_staff", "suspended", False, 1)),
        ]
    )

    with pytest.raises(BootstrapStateError, match="active owner"):
        bootstrap_first_staff_account(
            connection=connection,  # type: ignore[arg-type]
            provider_subject="google-subject-123",
            display_name="Initial Owner",
            occurred_at=NOW,
            uuid_factory=FixedUuids(),
        )


def test_main_bootstraps_with_schema_owner_and_prints_value_safe_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    engine = FakeEngine()
    assumed_roles: list[str] = []

    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT", "google-subject-123")
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME", "Initial Owner")
    monkeypatch.delenv("GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE", raising=False)
    monkeypatch.setattr(bootstrap_staff_account, "create_database_engine", lambda: engine)
    monkeypatch.setattr(
        bootstrap_staff_account,
        "assume_database_role",
        lambda connection, role: assumed_roles.append(role),
    )

    def fake_bootstrap_first_staff_account(*, connection, provider_subject, display_name):
        assert connection is engine.connection
        assert provider_subject == "google-subject-123"
        assert display_name == "Initial Owner"
        return FirstStaffBootstrapResult(
            created=True,
            staff_id=STAFF_ID,
            provider_subject_sha256="provider-hash",
            staff_id_sha256="staff-id-hash",
            role_name="owner",
            lifecycle_status="active",
            mfa_enrolled=True,
            version=1,
            requested_permission_count=len(BOOTSTRAP_PERMISSION_NAMES),
            active_permission_count=len(BOOTSTRAP_PERMISSION_NAMES),
            occurred_at=NOW,
        )

    monkeypatch.setattr(
        bootstrap_staff_account,
        "bootstrap_first_staff_account",
        fake_bootstrap_first_staff_account,
    )

    assert bootstrap_staff_account.main() == 0

    captured = capsys.readouterr()
    assert assumed_roles == [SCHEMA_OWNER_ROLE]
    assert '"result": "success"' in captured.out
    assert "provider-hash" in captured.out
    assert "staff-id-hash" in captured.out
    assert "google-subject-123" not in captured.out
    assert str(STAFF_ID) not in captured.out
    assert captured.err == ""


def test_main_rejects_missing_provider_subject(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT", raising=False)
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME", "Initial Owner")

    assert bootstrap_staff_account.main() == bootstrap_staff_account.EX_CONFIG

    captured = capsys.readouterr()
    assert "GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT is required" in captured.err


def test_main_requires_schema_owner_role(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT", "google-subject-123")
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME", "Initial Owner")
    monkeypatch.setenv("GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE", "golden_rose_runtime")

    assert bootstrap_staff_account.main() == bootstrap_staff_account.EX_CONFIG

    captured = capsys.readouterr()
    assert "schema-owner role" in captured.err


def test_main_reports_bootstrap_state_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT", "google-subject-123")
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME", "Initial Owner")
    monkeypatch.setattr(bootstrap_staff_account, "create_database_engine", FakeEngine)
    monkeypatch.setattr(bootstrap_staff_account, "assume_database_role", lambda *_: None)

    def reject_bootstrap(**_kwargs):
        raise BootstrapStateError("first staff bootstrap cannot create after accounts exist")

    monkeypatch.setattr(
        bootstrap_staff_account,
        "bootstrap_first_staff_account",
        reject_bootstrap,
    )

    assert bootstrap_staff_account.main() == bootstrap_staff_account.EX_CONFIG

    captured = capsys.readouterr()
    assert "bootstrap state rejected" in captured.err


def test_main_reports_persistence_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT", "google-subject-123")
    monkeypatch.setenv("GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME", "Initial Owner")
    monkeypatch.setattr(bootstrap_staff_account, "create_database_engine", FakeEngine)

    def fail_assume_database_role(*_args):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(bootstrap_staff_account, "assume_database_role", fail_assume_database_role)

    assert bootstrap_staff_account.main() == bootstrap_staff_account.EX_TEMPFAIL

    captured = capsys.readouterr()
    assert "bootstrap persistence operation failed" in captured.err
