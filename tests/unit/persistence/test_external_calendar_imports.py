from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound

import golden_rose.persistence.external_calendar_imports as store

NOW = datetime(2026, 10, 9, 14, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
CONNECTION_ID = UUID("22222222-2222-4222-8222-222222222222")
IMPORT_ID = UUID("33333333-3333-4333-8333-333333333333")
EVENT_ID = UUID("44444444-4444-4444-8444-444444444444")
COMMAND_ID = UUID("55555555-5555-4555-8555-555555555555")
_MISSING = object()


class FakeResult:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        one: Any = _MISSING,
        one_or_none: Any = _MISSING,
        rowcount: int = 1,
    ) -> None:
        self.rows = rows
        self._one = one
        self._one_or_none = one_or_none
        self.rowcount = rowcount

    def mappings(self) -> "FakeResult":
        return self

    def one(self) -> Any:
        if self._one is not _MISSING:
            return self._one
        if not self.rows:
            raise NoResultFound("missing row")
        return self.rows[0]

    def one_or_none(self) -> Any:
        if self._one_or_none is not _MISSING:
            return self._one_or_none
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)


class FakeSession:
    def __init__(self, *results: FakeResult) -> None:
        self.results = list(results)
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> FakeResult:
        self.statements.append(statement)
        if self.results:
            return self.results.pop(0)
        return FakeResult()


def connection_row(*, scopes: Any = None) -> SimpleNamespace:
    return SimpleNamespace(
        connection_id=CONNECTION_ID,
        staff_id=ACTOR_ID,
        provider_name="google_calendar",
        calendar_alias="primary",
        token_material_ref=None,
        granted_scopes=[] if scopes is None else scopes,
        connection_status="authorization_required",
        connected_at=None,
        disconnected_at=None,
        last_sync_status="configuration_required",
        last_sync_error="oauth_configuration_pending",
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=1,
    )


def import_row(*, status: str = "candidate", version: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        provider_event_uid="google-private-event-uid",
        provider_event_updated_at=NOW,
        event_title="Owner calendar note",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone="America/New_York",
        location_review="Queens",
        import_status=status,
        linked_entity_type=None,
        linked_entity_id=None,
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=version,
    )


def event_row() -> SimpleNamespace:
    return SimpleNamespace(
        event_id=EVENT_ID,
        command_id=COMMAND_ID,
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        actor_id=ACTOR_ID,
        event_type="external_calendar.candidate_imported",
        previous_status=None,
        new_status="candidate",
        previous_version=None,
        new_version=1,
        occurred_at=NOW,
        reason_text="Staff reviewed owner calendar import preview",
    )


def test_get_staff_calendar_connection_converts_scope_values() -> None:
    session = FakeSession(FakeResult(one_or_none=connection_row(scopes=[1, "calendar"])))

    record = store.get_staff_calendar_connection(
        session=session,  # type: ignore[arg-type]
        staff_id=ACTOR_ID,
    )

    assert record is not None
    assert record.granted_scopes == ["1", "calendar"]
    assert record.connection_status == "authorization_required"


def test_get_staff_calendar_connection_treats_non_list_scopes_as_empty() -> None:
    session = FakeSession(FakeResult(one_or_none=connection_row(scopes=("calendar",))))

    record = store.get_staff_calendar_connection(
        session=session,  # type: ignore[arg-type]
        staff_id=ACTOR_ID,
    )

    assert record is not None
    assert record.granted_scopes == []


def test_get_staff_calendar_connection_returns_none_when_missing() -> None:
    session = FakeSession(FakeResult(one_or_none=None))

    record = store.get_staff_calendar_connection(
        session=session,  # type: ignore[arg-type]
        staff_id=ACTOR_ID,
    )

    assert record is None


def test_insert_staff_calendar_connection_returns_authorization_placeholder() -> None:
    session = FakeSession()

    record = store.insert_staff_calendar_connection(
        session=session,  # type: ignore[arg-type]
        connection_id=CONNECTION_ID,
        staff_id=ACTOR_ID,
        calendar_alias="primary",
        created_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.statements) == 1
    assert record.provider_name == "google_calendar"
    assert record.token_material_ref is None
    assert record.last_sync_status == "configuration_required"
    assert record.last_sync_error == "oauth_configuration_pending"


def test_upsert_staff_calendar_connection_after_import_inserts_connected_record() -> None:
    session = FakeSession()

    record = store.upsert_staff_calendar_connection_after_import(
        session=session,  # type: ignore[arg-type]
        connection_id=CONNECTION_ID,
        staff_id=ACTOR_ID,
        calendar_alias="primary",
        granted_scopes=["https://www.googleapis.com/auth/calendar.events.readonly"],
        connected_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.statements) == 2
    assert record.connection_status == "connected"
    assert record.token_material_ref == "one_time_import_no_token_material"
    assert record.last_sync_status == "ready"


def test_upsert_staff_calendar_connection_after_import_updates_existing_record() -> None:
    session = FakeSession(
        FakeResult(one_or_none=connection_row()),
        FakeResult(),
        FakeResult(one=connection_row()),
    )

    record = store.upsert_staff_calendar_connection_after_import(
        session=session,  # type: ignore[arg-type]
        connection_id=UUID("99999999-9999-4999-8999-999999999999"),
        staff_id=ACTOR_ID,
        calendar_alias="primary",
        granted_scopes=["https://www.googleapis.com/auth/calendar.events.readonly"],
        connected_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.statements) == 3
    assert record.connection_id == CONNECTION_ID


def test_list_external_calendar_imports_converts_ordered_rows() -> None:
    session = FakeSession(FakeResult(rows=(import_row(version=1), import_row(version=2))))

    records = store.list_external_calendar_imports(
        session=session,  # type: ignore[arg-type]
        connection_id=CONNECTION_ID,
    )

    assert [record.version for record in records] == [1, 2]
    assert records[0].provider_event_uid == "google-private-event-uid"


def test_get_external_calendar_import_by_id_for_update_reads_one_row() -> None:
    session = FakeSession(FakeResult(one=import_row(version=3)))

    record = store.get_external_calendar_import_by_id_for_update(
        session=session,  # type: ignore[arg-type]
        import_id=IMPORT_ID,
    )

    assert record.import_id == IMPORT_ID
    assert record.version == 3


def test_get_external_calendar_import_by_source_for_update_returns_optional_record() -> None:
    found = FakeSession(FakeResult(one_or_none=import_row()))
    missing = FakeSession(FakeResult(one_or_none=None))

    assert (
        store.get_external_calendar_import_by_source_for_update(
            session=found,  # type: ignore[arg-type]
            connection_id=CONNECTION_ID,
            provider_event_uid="google-private-event-uid",
        )
        is not None
    )
    assert (
        store.get_external_calendar_import_by_source_for_update(
            session=missing,  # type: ignore[arg-type]
            connection_id=CONNECTION_ID,
            provider_event_uid="google-private-event-uid",
        )
        is None
    )


def test_insert_external_calendar_import_returns_candidate_defaults() -> None:
    session = FakeSession()

    record = store.insert_external_calendar_import(
        session=session,  # type: ignore[arg-type]
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        provider_event_uid="google-private-event-uid",
        provider_event_updated_at=NOW,
        event_title="Owner calendar note",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone="America/New_York",
        location_review=None,
        created_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert len(session.statements) == 1
    assert record.import_status == "candidate"
    assert record.linked_entity_type is None
    assert record.version == 1


def test_update_external_calendar_import_status_reads_updated_row() -> None:
    session = FakeSession(
        FakeResult(rowcount=1),
        FakeResult(one=import_row(status="ignored", version=2)),
    )

    record = store.update_external_calendar_import_status(
        session=session,  # type: ignore[arg-type]
        import_id=IMPORT_ID,
        status="ignored",
        expected_version=1,
        updated_at=NOW,
        actor_id=ACTOR_ID,
    )

    assert record.import_status == "ignored"
    assert record.version == 2
    assert len(session.statements) == 2


def test_update_external_calendar_import_status_rejects_stale_version() -> None:
    session = FakeSession(FakeResult(rowcount=0))

    with pytest.raises(NoResultFound, match="version mismatch"):
        store.update_external_calendar_import_status(
            session=session,  # type: ignore[arg-type]
            import_id=IMPORT_ID,
            status="ignored",
            expected_version=1,
            updated_at=NOW,
            actor_id=ACTOR_ID,
        )


def test_insert_external_calendar_import_event_returns_audit_record() -> None:
    session = FakeSession()

    record = store.insert_external_calendar_import_event(
        session=session,  # type: ignore[arg-type]
        event_id=EVENT_ID,
        command_id=COMMAND_ID,
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        actor_id=ACTOR_ID,
        event_type="external_calendar.candidate_imported",
        previous_status=None,
        new_status="candidate",
        previous_version=None,
        new_version=1,
        occurred_at=NOW,
        reason_text="Staff reviewed owner calendar import preview",
    )

    assert len(session.statements) == 1
    assert record.command_id == COMMAND_ID
    assert record.reason_text == "Staff reviewed owner calendar import preview"


def test_get_external_calendar_import_event_by_command_returns_optional_record() -> None:
    found = FakeSession(FakeResult(one_or_none=event_row()))
    missing = FakeSession(FakeResult(one_or_none=None))

    assert (
        store.get_external_calendar_import_event_by_command(
            session=found,  # type: ignore[arg-type]
            command_id=COMMAND_ID,
        )
        is not None
    )
    assert (
        store.get_external_calendar_import_event_by_command(
            session=missing,  # type: ignore[arg-type]
            command_id=COMMAND_ID,
        )
        is None
    )


def test_get_external_calendar_import_by_id_reads_one_row() -> None:
    session = FakeSession(FakeResult(one=import_row(version=5)))

    record = store.get_external_calendar_import_by_id(
        session=session,  # type: ignore[arg-type]
        import_id=IMPORT_ID,
    )

    assert record.import_id == IMPORT_ID
    assert record.version == 5
