from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.permissions import can_manage_calendar_imports
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.identifiers import IdentifierFactory
from golden_rose.persistence.external_calendar_imports import (
    ExternalCalendarImportRecord,
    StaffCalendarConnectionRecord,
    get_external_calendar_import_by_id,
    get_external_calendar_import_by_id_for_update,
    get_external_calendar_import_by_source_for_update,
    get_external_calendar_import_event_by_command,
    get_staff_calendar_connection,
    insert_external_calendar_import,
    insert_external_calendar_import_event,
    insert_staff_calendar_connection,
    list_external_calendar_imports,
    update_external_calendar_import_status,
    upsert_staff_calendar_connection_after_import,
)

DEFAULT_GOOGLE_CALENDAR_ALIAS = "primary"
GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.events.readonly"


@dataclass(frozen=True, slots=True)
class CalendarImportSummary:
    connection: StaffCalendarConnectionRecord | None
    candidates: tuple[ExternalCalendarImportRecord, ...]


@dataclass(frozen=True, slots=True)
class CalendarImportCommandResult:
    candidate: ExternalCalendarImportRecord
    event_type: str
    result_version: int
    replayed: bool


@dataclass(frozen=True, slots=True)
class GoogleCalendarEventImport:
    provider_event_uid: str
    provider_event_updated_at: datetime
    event_title: str
    starts_at: datetime
    ends_at: datetime
    time_zone: str
    location_review: str | None


@dataclass(frozen=True, slots=True)
class GoogleCalendarImportResult:
    connection: StaffCalendarConnectionRecord
    staged_count: int
    deduplicated_count: int


class CalendarImportError(RuntimeError):
    pass


class CalendarImportNotFoundError(CalendarImportError):
    pass


class CalendarImportVersionConflictError(CalendarImportError):
    pass


def get_calendar_import_summary(
    *,
    session: Session,
    principal: StaffPrincipal,
) -> CalendarImportSummary:
    _require_calendar_permission(principal)
    try:
        connection = get_staff_calendar_connection(
            session=session,
            staff_id=principal.actor_id,
            calendar_alias=DEFAULT_GOOGLE_CALENDAR_ALIAS,
        )
        candidates = (
            list_external_calendar_imports(session=session, connection_id=connection.connection_id)
            if connection is not None
            else ()
        )
    except SQLAlchemyError as exc:
        raise SafePersistenceError("persistence operation failed") from exc
    return CalendarImportSummary(connection=connection, candidates=candidates)


def stage_external_calendar_candidate(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    provider_event_uid: str,
    provider_event_updated_at: datetime,
    event_title: str,
    starts_at: datetime,
    ends_at: datetime,
    time_zone: str,
    location_review: str | None,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> CalendarImportCommandResult:
    _require_calendar_permission(principal)
    provider_event_uid = _require_text("provider_event_uid", provider_event_uid, 200)
    event_title = _require_text("event_title", event_title, 200)
    time_zone = _require_text("time_zone", time_zone, 64)
    location_review = _optional_text(location_review, 200)
    reason_text = _require_text("reason_text", reason_text, 512)
    if ends_at <= starts_at:
        raise CalendarImportError("external event interval is invalid")
    now = clock.now()
    try:
        replayed = get_external_calendar_import_event_by_command(
            session=session,
            command_id=command_id,
        )
        if replayed is not None:
            candidate = get_external_calendar_import_by_id(
                session=session,
                import_id=replayed.import_id,
            )
            return CalendarImportCommandResult(
                candidate=candidate,
                event_type=replayed.event_type,
                result_version=replayed.new_version,
                replayed=True,
            )
        connection = _ensure_connection(
            session=session,
            principal=principal,
            clock_value=now,
            identifiers=identifiers,
        )
        existing = get_external_calendar_import_by_source_for_update(
            session=session,
            connection_id=connection.connection_id,
            provider_event_uid=provider_event_uid,
        )
        if existing is None:
            candidate = insert_external_calendar_import(
                session=session,
                import_id=identifiers.new_uuid4(),
                connection_id=connection.connection_id,
                provider_event_uid=provider_event_uid,
                provider_event_updated_at=provider_event_updated_at,
                event_title=event_title,
                starts_at=starts_at,
                ends_at=ends_at,
                time_zone=time_zone,
                location_review=location_review,
                created_at=now,
                actor_id=principal.actor_id,
            )
            event_type = "external_calendar.candidate_imported"
            previous_status = None
            previous_version = None
        else:
            candidate = existing
            event_type = "external_calendar.candidate_deduplicated"
            previous_status = existing.import_status
            previous_version = existing.version
        event = insert_external_calendar_import_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            import_id=candidate.import_id,
            connection_id=candidate.connection_id,
            actor_id=principal.actor_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=candidate.import_status,
            previous_version=previous_version,
            new_version=candidate.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return CalendarImportCommandResult(
        candidate=candidate,
        event_type=event.event_type,
        result_version=event.new_version,
        replayed=False,
    )


def dispose_external_calendar_candidate(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    import_id: UUID,
    expected_version: int,
    disposition: str,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> CalendarImportCommandResult:
    _require_calendar_permission(principal)
    if disposition not in {"ignored", "marked_existing"}:
        raise CalendarImportError("unsupported external calendar disposition")
    reason_text = _require_text("reason_text", reason_text, 512)
    now = clock.now()
    try:
        replayed = get_external_calendar_import_event_by_command(
            session=session,
            command_id=command_id,
        )
        if replayed is not None:
            candidate = get_external_calendar_import_by_id(
                session=session,
                import_id=replayed.import_id,
            )
            return CalendarImportCommandResult(
                candidate=candidate,
                event_type=replayed.event_type,
                result_version=replayed.new_version,
                replayed=True,
            )
        existing = get_external_calendar_import_by_id_for_update(
            session=session,
            import_id=import_id,
        )
        if existing.version != expected_version:
            raise CalendarImportVersionConflictError("external calendar candidate version conflict")
        if existing.import_status != "candidate":
            raise CalendarImportError("only candidate imports can be disposed")
        updated = update_external_calendar_import_status(
            session=session,
            import_id=import_id,
            status=disposition,  # type: ignore[arg-type]
            expected_version=expected_version,
            updated_at=now,
            actor_id=principal.actor_id,
        )
        event_type = (
            "external_calendar.candidate_ignored"
            if disposition == "ignored"
            else "external_calendar.candidate_marked_existing"
        )
        event = insert_external_calendar_import_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            import_id=updated.import_id,
            connection_id=updated.connection_id,
            actor_id=principal.actor_id,
            event_type=event_type,
            previous_status=existing.import_status,
            new_status=updated.import_status,
            previous_version=existing.version,
            new_version=updated.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except NoResultFound as exc:
        session.rollback()
        raise CalendarImportNotFoundError("external calendar candidate not found") from exc
    except (CalendarImportError, CalendarImportVersionConflictError):
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return CalendarImportCommandResult(
        candidate=updated,
        event_type=event.event_type,
        result_version=event.new_version,
        replayed=False,
    )


def import_google_calendar_events(
    *,
    session: Session,
    principal: StaffPrincipal,
    events: tuple[GoogleCalendarEventImport, ...],
    granted_scopes: tuple[str, ...],
    clock: Clock,
    identifiers: IdentifierFactory,
) -> GoogleCalendarImportResult:
    _require_calendar_permission(principal)
    cleaned_scopes = _clean_granted_scopes(granted_scopes)
    if GOOGLE_CALENDAR_EVENTS_READONLY_SCOPE not in cleaned_scopes:
        raise CalendarImportError("Google Calendar OAuth scope is insufficient")
    now = clock.now()
    staged_count = 0
    deduplicated_count = 0
    try:
        connection = upsert_staff_calendar_connection_after_import(
            session=session,
            connection_id=identifiers.new_uuid4(),
            staff_id=principal.actor_id,
            calendar_alias=DEFAULT_GOOGLE_CALENDAR_ALIAS,
            granted_scopes=cleaned_scopes,
            connected_at=now,
            actor_id=principal.actor_id,
        )
        for source_event in events:
            event = _clean_google_calendar_event(source_event)
            existing = get_external_calendar_import_by_source_for_update(
                session=session,
                connection_id=connection.connection_id,
                provider_event_uid=event.provider_event_uid,
            )
            if existing is None:
                candidate = insert_external_calendar_import(
                    session=session,
                    import_id=identifiers.new_uuid4(),
                    connection_id=connection.connection_id,
                    provider_event_uid=event.provider_event_uid,
                    provider_event_updated_at=event.provider_event_updated_at,
                    event_title=event.event_title,
                    starts_at=event.starts_at,
                    ends_at=event.ends_at,
                    time_zone=event.time_zone,
                    location_review=event.location_review,
                    created_at=now,
                    actor_id=principal.actor_id,
                )
                event_type: Literal[
                    "external_calendar.candidate_imported",
                    "external_calendar.candidate_deduplicated",
                ] = "external_calendar.candidate_imported"
                previous_status = None
                previous_version = None
                staged_count += 1
            else:
                candidate = existing
                event_type = "external_calendar.candidate_deduplicated"
                previous_status = existing.import_status
                previous_version = existing.version
                deduplicated_count += 1
            insert_external_calendar_import_event(
                session=session,
                event_id=identifiers.new_uuid4(),
                command_id=identifiers.new_uuid4(),
                import_id=candidate.import_id,
                connection_id=candidate.connection_id,
                actor_id=principal.actor_id,
                event_type=event_type,
                previous_status=previous_status,
                new_status=candidate.import_status,
                previous_version=previous_version,
                new_version=candidate.version,
                occurred_at=now,
                reason_text="Staff connected Google Calendar for one-time migration import.",
            )
        session.commit()
    except CalendarImportError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return GoogleCalendarImportResult(
        connection=connection,
        staged_count=staged_count,
        deduplicated_count=deduplicated_count,
    )


def _ensure_connection(
    *,
    session: Session,
    principal: StaffPrincipal,
    clock_value: datetime,
    identifiers: IdentifierFactory,
) -> StaffCalendarConnectionRecord:
    connection = get_staff_calendar_connection(
        session=session,
        staff_id=principal.actor_id,
        calendar_alias=DEFAULT_GOOGLE_CALENDAR_ALIAS,
    )
    if connection is not None:
        return connection
    return insert_staff_calendar_connection(
        session=session,
        connection_id=identifiers.new_uuid4(),
        staff_id=principal.actor_id,
        calendar_alias=DEFAULT_GOOGLE_CALENDAR_ALIAS,
        created_at=clock_value,
        actor_id=principal.actor_id,
    )


def _require_calendar_permission(principal: StaffPrincipal) -> None:
    if not can_manage_calendar_imports(principal):
        msg = "principal lacks calendar_import:manage"
        raise PermissionError(msg)


def _require_text(name: str, value: str, max_length: int) -> str:
    cleaned = value.strip()
    if cleaned == "" or len(cleaned) > max_length:
        raise CalendarImportError(f"{name} is invalid")
    return cleaned


def _optional_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    if len(cleaned) > max_length:
        raise CalendarImportError("optional text is invalid")
    return cleaned


def _clean_granted_scopes(scopes: tuple[str, ...]) -> list[str]:
    cleaned: list[str] = []
    for scope in scopes:
        value = scope.strip()
        if value == "" or len(value) > 200 or any(ch.isspace() for ch in value):
            raise CalendarImportError("Google Calendar OAuth scope is invalid")
        if value not in cleaned:
            cleaned.append(value)
    return cleaned


def _clean_google_calendar_event(event: GoogleCalendarEventImport) -> GoogleCalendarEventImport:
    provider_event_uid = _require_text("provider_event_uid", event.provider_event_uid, 200)
    event_title = _require_text("event_title", event.event_title, 200)
    time_zone = _require_text("time_zone", event.time_zone, 64)
    location_review = _optional_text(event.location_review, 200)
    if event.ends_at <= event.starts_at:
        raise CalendarImportError("external event interval is invalid")
    return GoogleCalendarEventImport(
        provider_event_uid=provider_event_uid,
        provider_event_updated_at=event.provider_event_updated_at,
        event_title=event_title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        time_zone=time_zone,
        location_review=location_review,
    )
