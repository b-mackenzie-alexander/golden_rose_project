from datetime import UTC, datetime
from uuid import UUID

from golden_rose.persistence.staff_accounts import (
    get_staff_account_by_id,
    get_staff_account_by_id_for_update,
    get_staff_account_by_provider_subject,
    get_staff_delegation_by_id,
    insert_lifecycle_event,
    insert_staff_account,
    insert_staff_delegation,
    insert_staff_permission_grants,
    list_active_staff_permissions,
    list_staff_account_lifecycle_events,
    list_staff_accounts,
    list_staff_delegations,
    revoke_staff_delegation,
    update_staff_account_lifecycle,
)

NOW = datetime(2026, 9, 27, 20, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
STAFF_ID = UUID("22222222-2222-4222-8222-222222222222")
COMMAND_ID = UUID("33333333-3333-4333-8333-333333333333")
EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
DELEGATION_ID = UUID("66666666-6666-4666-8666-666666666666")
GRANTEE_ID = UUID("77777777-7777-4777-8777-777777777777")


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


class FakeRowsResult:
    def __init__(self, rows: tuple[tuple[object, ...], ...]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeSession:
    def __init__(self, result: object | None = None) -> None:
        self.result = result
        self.calls: list[tuple[object, object | None]] = []

    def execute(self, statement, parameters=None):
        self.calls.append((statement, parameters))
        if isinstance(self.result, list):
            return self.result.pop(0)
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


def _delegation_row(
    *,
    revoked_at: datetime | None = None,
    revoked_by: UUID | None = None,
    revocation_reason: str | None = None,
) -> tuple[object, ...]:
    return (
        DELEGATION_ID,
        ACTOR_ID,
        GRANTEE_ID,
        "intake:read",
        "global",
        None,
        "Temporary coverage",
        NOW,
        datetime(2026, 9, 28, 20, 0, tzinfo=UTC),
        revoked_at,
        revoked_by,
        revocation_reason,
    )


def _event_row() -> tuple[object, ...]:
    return (
        EVENT_ID,
        COMMAND_ID,
        STAFF_ID,
        ACTOR_ID,
        "staff_account.created",
        None,
        "suspended",
        None,
        1,
        NOW,
        "Initial staff onboarding",
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


def test_get_staff_account_by_id_maps_row() -> None:
    session = FakeSession(FakeOneResult(_row(status="active", version=2)))

    record = get_staff_account_by_id(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
    )

    assert len(session.calls) == 1
    assert record.staff_id == STAFF_ID
    assert record.lifecycle_status == "active"
    assert record.version == 2


def test_list_staff_accounts_maps_rows() -> None:
    session = FakeSession(
        FakeRowsResult(
            (
                _row(status="active", version=2),
                _row(status="suspended", version=1),
            )
        )
    )

    records = list_staff_accounts(
        session=session,  # type: ignore[arg-type]
        limit=2,
    )

    assert len(session.calls) == 1
    assert [record.lifecycle_status for record in records] == ["active", "suspended"]


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
    session = FakeSession(
        [
            FakeScalarResult(("intake:read",)),
            FakeScalarResult(("worker:read",)),
        ]
    )

    permissions = list_active_staff_permissions(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
    )

    assert permissions == frozenset({"intake:read", "worker:read"})
    assert len(session.calls) == 2


def test_staff_delegation_persistence_helpers_map_rows() -> None:
    session = FakeSession(FakeOneResult(_delegation_row()))

    inserted = insert_staff_delegation(
        session=session,  # type: ignore[arg-type]
        delegation_id=DELEGATION_ID,
        grantor_staff_id=ACTOR_ID,
        grantee_staff_id=GRANTEE_ID,
        permission_name="intake:read",
        scope_kind="global",
        scope_id=None,
        reason_text="Temporary coverage",
        starts_at=NOW,
        expires_at=datetime(2026, 9, 28, 20, 0, tzinfo=UTC),
    )
    fetched = get_staff_delegation_by_id(
        session=session,  # type: ignore[arg-type]
        delegation_id=DELEGATION_ID,
    )

    assert inserted.delegation_id == DELEGATION_ID
    assert inserted.revoked_at is None
    assert fetched.delegation_id == DELEGATION_ID
    assert fetched.grantee_staff_id == GRANTEE_ID
    assert len(session.calls) == 2


def test_list_and_revoke_staff_delegations_map_rows() -> None:
    revoked_at = datetime(2026, 9, 27, 21, 0, tzinfo=UTC)
    session = FakeSession(
        [
            FakeRowsResult((_delegation_row(),)),
            FakeOneResult(
                _delegation_row(
                    revoked_at=revoked_at,
                    revoked_by=ACTOR_ID,
                    revocation_reason="Coverage ended",
                )
            ),
        ]
    )

    delegations = list_staff_delegations(
        session=session,  # type: ignore[arg-type]
        staff_id=GRANTEE_ID,
    )
    revoked = revoke_staff_delegation(
        session=session,  # type: ignore[arg-type]
        delegation_id=DELEGATION_ID,
        grantee_staff_id=GRANTEE_ID,
        revoked_at=revoked_at,
        revoked_by=ACTOR_ID,
        revocation_reason="Coverage ended",
    )

    assert delegations == (delegations[0],)
    assert delegations[0].delegation_id == DELEGATION_ID
    assert revoked.revoked_at == revoked_at
    assert revoked.revoked_by == ACTOR_ID
    assert revoked.revocation_reason == "Coverage ended"
    assert len(session.calls) == 2


def test_list_staff_account_lifecycle_events_maps_rows() -> None:
    session = FakeSession(FakeRowsResult((_event_row(),)))

    events = list_staff_account_lifecycle_events(
        session=session,  # type: ignore[arg-type]
        staff_id=STAFF_ID,
        limit=1,
    )

    assert len(session.calls) == 1
    assert events[0].event_id == EVENT_ID
    assert events[0].event_type == "staff_account.created"
    assert events[0].new_status == "suspended"
    assert events[0].new_version == 1
    assert events[0].reason_text == "Initial staff onboarding"


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
