from datetime import UTC, datetime
from uuid import UUID

import pytest

from golden_rose.bootstrap_staff_account import (
    BOOTSTRAP_PERMISSION_NAMES,
    BootstrapConfigurationError,
    BootstrapStateError,
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
