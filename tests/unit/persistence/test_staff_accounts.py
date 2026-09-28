from datetime import UTC, datetime
from uuid import UUID

from golden_rose.persistence.staff_accounts import (
    get_staff_account_by_id_for_update,
    get_staff_account_by_provider_subject,
    insert_lifecycle_event,
    insert_staff_account,
    insert_staff_permission_grants,
    list_active_staff_permissions,
    update_staff_account_lifecycle,
)

NOW = datetime(2026, 9, 27, 20, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
STAFF_ID = UUID("22222222-2222-4222-8222-222222222222")
COMMAND_ID = UUID("33333333-3333-4333-8333-333333333333")
EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")


class FakeOneResult:
    def __init__(self, row: tuple[object, ...]) -> None:
        self.row = row

    def one(self) -> tuple[object, ...]:
        return self.row


class FakeScalarResult:
    def __init__(self, values: tuple[str, ...]) -> None:
        self.values = values

    def scalars(self) -> tuple[str, ...]:
        return self.values


class FakeSession:
    def __init__(self, result: object | None = None) -> None:
        self.result = result
        self.calls: list[tuple[object, object | None]] = []

    def execute(self, statement, parameters=None):
        self.calls.append((statement, parameters))
        return self.result


def _row(*, status: str = "suspended", version: int = 1) -> tuple[object, ...]:
    return (
        STAFF_ID,
        "oidc:staff:123",
        "Mariela Torres",
        "operations_staff",
        status,
        False,
        NOW,
        ACTOR_ID,
        NOW,
        ACTOR_ID,
        version,
    )


def test_insert_staff_account_executes_insert_and_returns_record() -> None:
    session = FakeSession()

    record = insert_staff_account(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
        provider_subject="oidc:staff:123",
        display_name="Mariela Torres",
        role_name="operations_staff",
        lifecycle_status="suspended",
        mfa_enrolled=False,
        created_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.calls) == 1
    assert record.staff_id == STAFF_ID
    assert record.lifecycle_status == "suspended"
    assert record.version == 1
    assert record.updated_by == ACTOR_ID


def test_get_staff_account_by_id_for_update_maps_row() -> None:
    session = FakeSession(FakeOneResult(_row(status="active", version=2)))

    record = get_staff_account_by_id_for_update(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
    )

    assert len(session.calls) == 1
    assert record.staff_id == STAFF_ID
    assert record.lifecycle_status == "active"
    assert record.version == 2


def test_get_staff_account_by_provider_subject_maps_row() -> None:
    session = FakeSession(FakeOneResult(_row(status="active", version=2)))

    record = get_staff_account_by_provider_subject(
        session=session,  # type: ignore[arg-type]
        provider_subject="oidc:staff:123",
    )

    assert len(session.calls) == 1
    assert record.provider_subject == "oidc:staff:123"
    assert record.lifecycle_status == "active"


def test_update_staff_account_lifecycle_maps_returning_row() -> None:
    session = FakeSession(FakeOneResult(_row(status="active", version=2)))

    record = update_staff_account_lifecycle(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
        expected_version=1,
        lifecycle_status="active",
        mfa_enrolled=True,
        updated_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.calls) == 1
    assert record.lifecycle_status == "active"
    assert record.version == 2


def test_insert_staff_permission_grants_skips_empty_grants() -> None:
    session = FakeSession()

    insert_staff_permission_grants(
        session=session,  # type: ignore[arg-type]
        grants=(),
        staff_id=STAFF_ID,
        granted_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert session.calls == []


def test_insert_staff_permission_grants_executes_bulk_insert() -> None:
    session = FakeSession()

    insert_staff_permission_grants(
        session=session,  # type: ignore[arg-type]
        grants=((GRANT_ID, "intake:read"),),
        staff_id=STAFF_ID,
        granted_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.calls) == 1
    assert session.calls[0][1] == [
        {
            "grant_id": GRANT_ID,
            "staff_id": STAFF_ID,
            "permission_name": "intake:read",
            "scope_kind": "global",
            "scope_id": None,
            "granted_at": NOW,
            "granted_by": ACTOR_ID,
        }
    ]


def test_list_active_staff_permissions_returns_frozenset() -> None:
    session = FakeSession(FakeScalarResult(("intake:read", "worker:read")))

    permissions = list_active_staff_permissions(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
    )

    assert permissions == frozenset({"intake:read", "worker:read"})


def test_insert_lifecycle_event_executes_insert() -> None:
    session = FakeSession()

    insert_lifecycle_event(
        session=session,  # type: ignore[arg-type]
        event_id=EVENT_ID,
        command_id=COMMAND_ID,
        staff_id=STAFF_ID,
        actor_id=ACTOR_ID,
        event_type="staff_account.created",
        previous_status=None,
        new_status="suspended",
        previous_version=None,
        new_version=1,
        occurred_at=NOW,
        reason_text="Initial staff onboarding",
    )

    assert len(session.calls) == 1
