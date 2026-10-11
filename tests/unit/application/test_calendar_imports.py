from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

import golden_rose.application.calendar_imports as calendar_import_module
from golden_rose.application.calendar_imports import (
    CalendarImportError,
    CalendarImportNotFoundError,
    CalendarImportVersionConflictError,
    dispose_external_calendar_candidate,
    get_calendar_import_summary,
    stage_external_calendar_candidate,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.external_calendar_imports import (
    ExternalCalendarImportEventRecord,
    ExternalCalendarImportRecord,
    StaffCalendarConnectionRecord,
)

NOW = datetime(2026, 10, 9, 14, 0, tzinfo=UTC)
ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
COMMAND_ID = UUID("22222222-2222-4222-8222-222222222222")
CONNECTION_ID = UUID("33333333-3333-4333-8333-333333333333")
IMPORT_ID = UUID("44444444-4444-4444-8444-444444444444")
EVENT_ID = UUID("55555555-5555-4555-8555-555555555555")


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FixedIdentifiers:
    def __init__(self, *values: UUID) -> None:
        self.values = list(values)

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


def _principal(*permissions: str) -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=ACTOR_ID,
        role_name="owner",
        permissions=frozenset(permissions),
    )


def connection_record() -> StaffCalendarConnectionRecord:
    return StaffCalendarConnectionRecord(
        connection_id=CONNECTION_ID,
        staff_id=ACTOR_ID,
        provider_name="google_calendar",
        calendar_alias="primary",
        token_material_ref=None,
        granted_scopes=[],
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


def candidate_record(
    *,
    status: str = "candidate",
    version: int = 1,
) -> ExternalCalendarImportRecord:
    return ExternalCalendarImportRecord(
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        provider_event_uid="google-private-event-uid",
        provider_event_updated_at=NOW,
        event_title="Owner calendar note",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone="America/New_York",
        location_review="Queens",
        import_status=status,  # type: ignore[arg-type]
        linked_entity_type=None,
        linked_entity_id=None,
        created_at=NOW,
        created_by=ACTOR_ID,
        updated_at=NOW,
        updated_by=ACTOR_ID,
        version=version,
    )


def event_record(*, event_type: str, new_version: int) -> ExternalCalendarImportEventRecord:
    return ExternalCalendarImportEventRecord(
        event_id=EVENT_ID,
        command_id=COMMAND_ID,
        import_id=IMPORT_ID,
        connection_id=CONNECTION_ID,
        actor_id=ACTOR_ID,
        event_type=event_type,
        previous_status=None,
        new_status="candidate",
        previous_version=None,
        new_version=new_version,
        occurred_at=NOW,
        reason_text="Staff reviewed owner calendar import preview",
    )


def test_stage_calendar_candidate_creates_authorization_placeholder_and_audit_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_staff_calendar_connection",
        lambda **_kwargs: None,
    )

    def insert_connection(**kwargs):
        observed["connection"] = kwargs
        return connection_record()

    def get_by_source(**kwargs):
        observed["lookup"] = kwargs
        return None

    def insert_candidate(**kwargs):
        observed["candidate"] = kwargs
        return candidate_record()

    def insert_event(**kwargs):
        observed["event"] = kwargs
        return event_record(event_type=kwargs["event_type"], new_version=kwargs["new_version"])

    monkeypatch.setattr(
        calendar_import_module,
        "insert_staff_calendar_connection",
        insert_connection,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_source_for_update",
        get_by_source,
    )
    monkeypatch.setattr(calendar_import_module, "insert_external_calendar_import", insert_candidate)
    monkeypatch.setattr(
        calendar_import_module,
        "insert_external_calendar_import_event",
        insert_event,
    )

    result = stage_external_calendar_candidate(
        session=session,  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
        command_id=COMMAND_ID,
        provider_event_uid=" google-private-event-uid ",
        provider_event_updated_at=NOW,
        event_title=" Owner   calendar note ",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone=" America/New_York ",
        location_review=" Queens ",
        clock=FixedClock(),
        identifiers=FixedIdentifiers(CONNECTION_ID, IMPORT_ID, EVENT_ID),
        reason_text=" Staff reviewed owner calendar import preview ",
    )

    assert result.event_type == "external_calendar.candidate_imported"
    assert observed["connection"]["staff_id"] == ACTOR_ID
    assert observed["candidate"]["provider_event_uid"] == "google-private-event-uid"
    assert observed["candidate"]["event_title"] == "Owner   calendar note"
    assert observed["candidate"]["location_review"] == "Queens"
    assert observed["event"]["previous_status"] is None
    assert session.commits == 1
    assert session.rollbacks == 0


def test_stage_calendar_candidate_deduplicates_existing_source_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_staff_calendar_connection",
        lambda **_kwargs: connection_record(),
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_source_for_update",
        lambda **_kwargs: candidate_record(version=3),
    )

    def insert_event(**kwargs):
        observed["event"] = kwargs
        return event_record(event_type=kwargs["event_type"], new_version=kwargs["new_version"])

    monkeypatch.setattr(
        calendar_import_module,
        "insert_external_calendar_import_event",
        insert_event,
    )

    result = stage_external_calendar_candidate(
        session=session,  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
        command_id=COMMAND_ID,
        provider_event_uid="google-private-event-uid",
        provider_event_updated_at=NOW,
        event_title="Owner calendar note",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone="America/New_York",
        location_review=None,
        clock=FixedClock(),
        identifiers=FixedIdentifiers(EVENT_ID),
        reason_text="Staff reviewed owner calendar import preview",
    )

    assert result.event_type == "external_calendar.candidate_deduplicated"
    assert observed["event"]["previous_status"] == "candidate"
    assert observed["event"]["previous_version"] == 3
    assert observed["event"]["new_version"] == 3
    assert session.commits == 1


def test_get_calendar_import_summary_reads_existing_connection_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}

    def get_connection(**kwargs):
        observed["connection"] = kwargs
        return connection_record()

    def list_candidates(**kwargs):
        observed["candidates"] = kwargs
        return (candidate_record(),)

    monkeypatch.setattr(calendar_import_module, "get_staff_calendar_connection", get_connection)
    monkeypatch.setattr(calendar_import_module, "list_external_calendar_imports", list_candidates)

    summary = get_calendar_import_summary(
        session=FakeSession(),  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
    )

    assert summary.connection == connection_record()
    assert summary.candidates == (candidate_record(),)
    assert observed["connection"]["calendar_alias"] == "primary"
    assert observed["candidates"]["connection_id"] == CONNECTION_ID


def test_get_calendar_import_summary_skips_candidates_without_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    list_candidates = pytest.fail
    monkeypatch.setattr(
        calendar_import_module,
        "get_staff_calendar_connection",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(calendar_import_module, "list_external_calendar_imports", list_candidates)

    summary = get_calendar_import_summary(
        session=FakeSession(),  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
    )

    assert summary.connection is None
    assert summary.candidates == ()


def test_get_calendar_import_summary_maps_sqlalchemy_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_sqlalchemy(**_kwargs):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(calendar_import_module, "get_staff_calendar_connection", raise_sqlalchemy)

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        get_calendar_import_summary(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
        )


def test_stage_calendar_candidate_replays_existing_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: event_record(
            event_type="external_calendar.candidate_imported",
            new_version=4,
        ),
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_id",
        lambda **_kwargs: candidate_record(version=4),
    )

    result = stage_external_calendar_candidate(
        session=session,  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
        command_id=COMMAND_ID,
        provider_event_uid="google-private-event-uid",
        provider_event_updated_at=NOW,
        event_title="Owner calendar note",
        starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
        ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
        time_zone="America/New_York",
        location_review=" ",
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Staff reviewed owner calendar import preview",
    )

    assert result.replayed is True
    assert result.result_version == 4
    assert session.commits == 0
    assert session.rollbacks == 0


def test_stage_calendar_candidate_rejects_invalid_interval() -> None:
    with pytest.raises(CalendarImportError, match="interval is invalid"):
        stage_external_calendar_candidate(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            provider_event_uid="google-private-event-uid",
            provider_event_updated_at=NOW,
            event_title="Owner calendar note",
            starts_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
            ends_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
            time_zone="America/New_York",
            location_review=None,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Staff reviewed owner calendar import preview",
        )


def test_stage_calendar_candidate_rolls_back_on_persistence_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    def raise_sqlalchemy(**_kwargs):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(
        calendar_import_module, "get_external_calendar_import_event_by_command", raise_sqlalchemy
    )

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        stage_external_calendar_candidate(
            session=session,  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            provider_event_uid="google-private-event-uid",
            provider_event_updated_at=NOW,
            event_title="Owner calendar note",
            starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
            ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
            time_zone="America/New_York",
            location_review=None,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Staff reviewed owner calendar import preview",
        )

    assert session.commits == 0
    assert session.rollbacks == 1


def test_dispose_calendar_candidate_records_status_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_id_for_update",
        lambda **_kwargs: candidate_record(version=1),
    )

    def update_status(**kwargs):
        observed["update"] = kwargs
        return candidate_record(status="ignored", version=2)

    def insert_event(**kwargs):
        observed["event"] = kwargs
        return event_record(event_type=kwargs["event_type"], new_version=kwargs["new_version"])

    monkeypatch.setattr(
        calendar_import_module,
        "update_external_calendar_import_status",
        update_status,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "insert_external_calendar_import_event",
        insert_event,
    )

    result = dispose_external_calendar_candidate(
        session=session,  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
        command_id=COMMAND_ID,
        import_id=IMPORT_ID,
        expected_version=1,
        disposition="ignored",
        clock=FixedClock(),
        identifiers=FixedIdentifiers(EVENT_ID),
        reason_text="Duplicate of an existing Golden Rose item",
    )

    assert result.event_type == "external_calendar.candidate_ignored"
    assert observed["update"]["status"] == "ignored"
    assert observed["update"]["expected_version"] == 1
    assert observed["event"]["previous_status"] == "candidate"
    assert observed["event"]["new_status"] == "ignored"
    assert session.commits == 1
    assert session.rollbacks == 0


def test_dispose_calendar_candidate_records_marked_existing_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_id_for_update",
        lambda **_kwargs: candidate_record(version=1),
    )
    monkeypatch.setattr(
        calendar_import_module,
        "update_external_calendar_import_status",
        lambda **_kwargs: candidate_record(status="marked_existing", version=2),
    )

    def insert_event(**kwargs):
        observed["event"] = kwargs
        return event_record(event_type=kwargs["event_type"], new_version=kwargs["new_version"])

    monkeypatch.setattr(
        calendar_import_module,
        "insert_external_calendar_import_event",
        insert_event,
    )

    result = dispose_external_calendar_candidate(
        session=session,  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
        command_id=COMMAND_ID,
        import_id=IMPORT_ID,
        expected_version=1,
        disposition="marked_existing",
        clock=FixedClock(),
        identifiers=FixedIdentifiers(EVENT_ID),
        reason_text="Already represented in Golden Rose",
    )

    assert result.event_type == "external_calendar.candidate_marked_existing"
    assert observed["event"]["new_status"] == "marked_existing"
    assert session.commits == 1


def test_dispose_calendar_candidate_replays_existing_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: event_record(
            event_type="external_calendar.candidate_ignored",
            new_version=2,
        ),
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_id",
        lambda **_kwargs: candidate_record(status="ignored", version=2),
    )

    result = dispose_external_calendar_candidate(
        session=session,  # type: ignore[arg-type]
        principal=_principal("calendar_import:manage"),
        command_id=COMMAND_ID,
        import_id=IMPORT_ID,
        expected_version=1,
        disposition="ignored",
        clock=FixedClock(),
        identifiers=FixedIdentifiers(),
        reason_text="Duplicate of an existing Golden Rose item",
    )

    assert result.replayed is True
    assert result.result_version == 2
    assert session.commits == 0
    assert session.rollbacks == 0


def test_dispose_calendar_candidate_rolls_back_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )

    def raise_missing(**_kwargs):
        raise NoResultFound("missing")

    monkeypatch.setattr(
        calendar_import_module, "get_external_calendar_import_by_id_for_update", raise_missing
    )

    with pytest.raises(CalendarImportNotFoundError, match="not found"):
        dispose_external_calendar_candidate(
            session=session,  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            import_id=IMPORT_ID,
            expected_version=1,
            disposition="ignored",
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Duplicate of an existing Golden Rose item",
        )

    assert session.commits == 0
    assert session.rollbacks == 1


def test_dispose_calendar_candidate_rejects_non_candidate_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_id_for_update",
        lambda **_kwargs: candidate_record(status="ignored", version=1),
    )

    with pytest.raises(CalendarImportError, match="only candidate"):
        dispose_external_calendar_candidate(
            session=session,  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            import_id=IMPORT_ID,
            expected_version=1,
            disposition="ignored",
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Duplicate of an existing Golden Rose item",
        )

    assert session.commits == 0
    assert session.rollbacks == 1


def test_dispose_calendar_candidate_rejects_unsupported_disposition() -> None:
    with pytest.raises(CalendarImportError, match="unsupported"):
        dispose_external_calendar_candidate(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            import_id=IMPORT_ID,
            expected_version=1,
            disposition="linked",
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Duplicate of an existing Golden Rose item",
        )


def test_dispose_calendar_candidate_rolls_back_on_persistence_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )

    def raise_sqlalchemy(**_kwargs):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(
        calendar_import_module, "get_external_calendar_import_by_id_for_update", raise_sqlalchemy
    )

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        dispose_external_calendar_candidate(
            session=session,  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            import_id=IMPORT_ID,
            expected_version=1,
            disposition="ignored",
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Duplicate of an existing Golden Rose item",
        )

    assert session.commits == 0
    assert session.rollbacks == 1


def test_dispose_calendar_candidate_rolls_back_on_version_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_event_by_command",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        calendar_import_module,
        "get_external_calendar_import_by_id_for_update",
        lambda **_kwargs: candidate_record(version=2),
    )

    with pytest.raises(CalendarImportVersionConflictError, match="version conflict"):
        dispose_external_calendar_candidate(
            session=session,  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            import_id=IMPORT_ID,
            expected_version=1,
            disposition="ignored",
            clock=FixedClock(),
            identifiers=FixedIdentifiers(EVENT_ID),
            reason_text="Duplicate of an existing Golden Rose item",
        )

    assert session.commits == 0
    assert session.rollbacks == 1


def test_stage_calendar_candidate_rejects_overlong_optional_text() -> None:
    with pytest.raises(CalendarImportError, match="optional text is invalid"):
        stage_external_calendar_candidate(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("calendar_import:manage"),
            command_id=COMMAND_ID,
            provider_event_uid="google-private-event-uid",
            provider_event_updated_at=NOW,
            event_title="Owner calendar note",
            starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
            ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
            time_zone="America/New_York",
            location_review="x" * 201,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Staff reviewed owner calendar import preview",
        )


def test_stage_calendar_candidate_requires_named_permission() -> None:
    with pytest.raises(PermissionError, match="calendar_import:manage"):
        stage_external_calendar_candidate(
            session=FakeSession(),  # type: ignore[arg-type]
            principal=_principal("intake:read"),
            command_id=COMMAND_ID,
            provider_event_uid="google-private-event-uid",
            provider_event_updated_at=NOW,
            event_title="Owner calendar note",
            starts_at=datetime(2026, 10, 12, 13, 30, tzinfo=UTC),
            ends_at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
            time_zone="America/New_York",
            location_review=None,
            clock=FixedClock(),
            identifiers=FixedIdentifiers(),
            reason_text="Staff reviewed owner calendar import preview",
        )
