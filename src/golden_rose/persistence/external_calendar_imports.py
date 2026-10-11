from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from golden_rose.persistence.models import (
    external_calendar_import_events,
    external_calendar_imports,
    staff_calendar_connections,
)

CalendarConnectionStatus = Literal[
    "authorization_required",
    "connected",
    "disconnected",
    "unavailable",
]
CalendarSyncStatus = Literal[
    "never_synced",
    "ready",
    "failed",
    "configuration_required",
]
ExternalCalendarImportStatus = Literal[
    "candidate",
    "ignored",
    "marked_existing",
    "linked",
    "draft_started",
    "superseded",
    "unavailable",
]


@dataclass(frozen=True, slots=True)
class StaffCalendarConnectionRecord:
    connection_id: UUID
    staff_id: UUID
    provider_name: str
    calendar_alias: str
    token_material_ref: str | None
    granted_scopes: list[str]
    connection_status: CalendarConnectionStatus
    connected_at: datetime | None
    disconnected_at: datetime | None
    last_sync_status: CalendarSyncStatus
    last_sync_error: str | None
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    version: int


@dataclass(frozen=True, slots=True)
class ExternalCalendarImportRecord:
    import_id: UUID
    connection_id: UUID
    provider_event_uid: str
    provider_event_updated_at: datetime
    event_title: str
    starts_at: datetime
    ends_at: datetime
    time_zone: str
    location_review: str | None
    import_status: ExternalCalendarImportStatus
    linked_entity_type: str | None
    linked_entity_id: UUID | None
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    version: int


@dataclass(frozen=True, slots=True)
class ExternalCalendarImportEventRecord:
    event_id: UUID
    command_id: UUID
    import_id: UUID
    connection_id: UUID
    actor_id: UUID
    event_type: str
    previous_status: ExternalCalendarImportStatus | None
    new_status: ExternalCalendarImportStatus
    previous_version: int | None
    new_version: int
    occurred_at: datetime
    reason_text: str


def _connection_from_row(row) -> StaffCalendarConnectionRecord:
    scopes = row.granted_scopes
    if not isinstance(scopes, list):
        scopes = []
    return StaffCalendarConnectionRecord(
        connection_id=row.connection_id,
        staff_id=row.staff_id,
        provider_name=row.provider_name,
        calendar_alias=row.calendar_alias,
        token_material_ref=row.token_material_ref,
        granted_scopes=[str(scope) for scope in scopes],
        connection_status=row.connection_status,
        connected_at=row.connected_at,
        disconnected_at=row.disconnected_at,
        last_sync_status=row.last_sync_status,
        last_sync_error=row.last_sync_error,
        created_at=row.created_at,
        created_by=row.created_by,
        updated_at=row.updated_at,
        updated_by=row.updated_by,
        version=row.version,
    )


def _import_from_row(row) -> ExternalCalendarImportRecord:
    return ExternalCalendarImportRecord(
        import_id=row.import_id,
        connection_id=row.connection_id,
        provider_event_uid=row.provider_event_uid,
        provider_event_updated_at=row.provider_event_updated_at,
        event_title=row.event_title,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        time_zone=row.time_zone,
        location_review=row.location_review,
        import_status=row.import_status,
        linked_entity_type=row.linked_entity_type,
        linked_entity_id=row.linked_entity_id,
        created_at=row.created_at,
        created_by=row.created_by,
        updated_at=row.updated_at,
        updated_by=row.updated_by,
        version=row.version,
    )


def _event_from_row(row) -> ExternalCalendarImportEventRecord:
    return ExternalCalendarImportEventRecord(
        event_id=row.event_id,
        command_id=row.command_id,
        import_id=row.import_id,
        connection_id=row.connection_id,
        actor_id=row.actor_id,
        event_type=row.event_type,
        previous_status=row.previous_status,
        new_status=row.new_status,
        previous_version=row.previous_version,
        new_version=row.new_version,
        occurred_at=row.occurred_at,
        reason_text=row.reason_text,
    )


def get_staff_calendar_connection(
    *,
    session: Session,
    staff_id: UUID,
    provider_name: str = "google_calendar",
    calendar_alias: str = "primary",
) -> StaffCalendarConnectionRecord | None:
    row = (
        session.execute(
            select(staff_calendar_connections).where(
                staff_calendar_connections.c.staff_id == staff_id,
                staff_calendar_connections.c.provider_name == provider_name,
                staff_calendar_connections.c.calendar_alias == calendar_alias,
            )
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _connection_from_row(row)


def insert_staff_calendar_connection(
    *,
    session: Session,
    connection_id: UUID,
    staff_id: UUID,
    calendar_alias: str,
    created_at: datetime,
    actor_id: UUID,
) -> StaffCalendarConnectionRecord:
    pending_provider_reference: str | None = None
    values = {
        "connection_id": connection_id,
        "staff_id": staff_id,
        "provider_name": "google_calendar",
        "calendar_alias": calendar_alias,
        "token_material_ref": pending_provider_reference,
        "granted_scopes": [],
        "connection_status": "authorization_required",
        "connected_at": None,
        "disconnected_at": None,
        "last_sync_status": "configuration_required",
        "last_sync_error": "oauth_configuration_pending",
        "created_at": created_at,
        "created_by": actor_id,
        "updated_at": created_at,
        "updated_by": actor_id,
        "version": 1,
    }
    session.execute(insert(staff_calendar_connections).values(**values))
    return StaffCalendarConnectionRecord(
        connection_id=connection_id,
        staff_id=staff_id,
        provider_name="google_calendar",
        calendar_alias=calendar_alias,
        token_material_ref=None,
        granted_scopes=[],
        connection_status="authorization_required",
        connected_at=None,
        disconnected_at=None,
        last_sync_status="configuration_required",
        last_sync_error="oauth_configuration_pending",
        created_at=created_at,
        created_by=actor_id,
        updated_at=created_at,
        updated_by=actor_id,
        version=1,
    )


def list_external_calendar_imports(
    *,
    session: Session,
    connection_id: UUID,
    limit: int = 50,
) -> tuple[ExternalCalendarImportRecord, ...]:
    rows = session.execute(
        select(external_calendar_imports)
        .where(external_calendar_imports.c.connection_id == connection_id)
        .order_by(
            external_calendar_imports.c.starts_at.asc(),
            external_calendar_imports.c.import_id.asc(),
        )
        .limit(limit)
    ).mappings()
    return tuple(_import_from_row(row) for row in rows)


def get_external_calendar_import_by_id_for_update(
    *,
    session: Session,
    import_id: UUID,
) -> ExternalCalendarImportRecord:
    row = (
        session.execute(
            select(external_calendar_imports)
            .where(external_calendar_imports.c.import_id == import_id)
            .with_for_update()
        )
        .mappings()
        .one()
    )
    return _import_from_row(row)


def get_external_calendar_import_by_source_for_update(
    *,
    session: Session,
    connection_id: UUID,
    provider_event_uid: str,
) -> ExternalCalendarImportRecord | None:
    row = (
        session.execute(
            select(external_calendar_imports)
            .where(
                external_calendar_imports.c.connection_id == connection_id,
                external_calendar_imports.c.provider_event_uid == provider_event_uid,
            )
            .with_for_update()
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _import_from_row(row)


def insert_external_calendar_import(
    *,
    session: Session,
    import_id: UUID,
    connection_id: UUID,
    provider_event_uid: str,
    provider_event_updated_at: datetime,
    event_title: str,
    starts_at: datetime,
    ends_at: datetime,
    time_zone: str,
    location_review: str | None,
    created_at: datetime,
    actor_id: UUID,
) -> ExternalCalendarImportRecord:
    values = {
        "import_id": import_id,
        "connection_id": connection_id,
        "provider_event_uid": provider_event_uid,
        "provider_event_updated_at": provider_event_updated_at,
        "event_title": event_title,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "time_zone": time_zone,
        "location_review": location_review,
        "import_status": "candidate",
        "linked_entity_type": None,
        "linked_entity_id": None,
        "created_at": created_at,
        "created_by": actor_id,
        "updated_at": created_at,
        "updated_by": actor_id,
        "version": 1,
    }
    session.execute(insert(external_calendar_imports).values(**values))
    return ExternalCalendarImportRecord(
        import_id=import_id,
        connection_id=connection_id,
        provider_event_uid=provider_event_uid,
        provider_event_updated_at=provider_event_updated_at,
        event_title=event_title,
        starts_at=starts_at,
        ends_at=ends_at,
        time_zone=time_zone,
        location_review=location_review,
        import_status="candidate",
        linked_entity_type=None,
        linked_entity_id=None,
        created_at=created_at,
        created_by=actor_id,
        updated_at=created_at,
        updated_by=actor_id,
        version=1,
    )


def update_external_calendar_import_status(
    *,
    session: Session,
    import_id: UUID,
    status: ExternalCalendarImportStatus,
    expected_version: int,
    updated_at: datetime,
    actor_id: UUID,
) -> ExternalCalendarImportRecord:
    result = session.execute(
        update(external_calendar_imports)
        .where(
            external_calendar_imports.c.import_id == import_id,
            external_calendar_imports.c.version == expected_version,
        )
        .values(
            import_status=status,
            updated_at=updated_at,
            updated_by=actor_id,
            version=expected_version + 1,
        )
    )
    if cast(Any, result).rowcount != 1:
        raise NoResultFound("external calendar import version mismatch")
    row = (
        session.execute(
            select(external_calendar_imports).where(
                external_calendar_imports.c.import_id == import_id
            )
        )
        .mappings()
        .one()
    )
    return _import_from_row(row)


def insert_external_calendar_import_event(
    *,
    session: Session,
    event_id: UUID,
    command_id: UUID,
    import_id: UUID,
    connection_id: UUID,
    actor_id: UUID,
    event_type: str,
    previous_status: ExternalCalendarImportStatus | None,
    new_status: ExternalCalendarImportStatus,
    previous_version: int | None,
    new_version: int,
    occurred_at: datetime,
    reason_text: str,
) -> ExternalCalendarImportEventRecord:
    values = {
        "event_id": event_id,
        "command_id": command_id,
        "import_id": import_id,
        "connection_id": connection_id,
        "actor_id": actor_id,
        "event_type": event_type,
        "previous_status": previous_status,
        "new_status": new_status,
        "previous_version": previous_version,
        "new_version": new_version,
        "occurred_at": occurred_at,
        "reason_text": reason_text,
    }
    session.execute(insert(external_calendar_import_events).values(**values))
    return ExternalCalendarImportEventRecord(
        event_id=event_id,
        command_id=command_id,
        import_id=import_id,
        connection_id=connection_id,
        actor_id=actor_id,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        previous_version=previous_version,
        new_version=new_version,
        occurred_at=occurred_at,
        reason_text=reason_text,
    )


def get_external_calendar_import_event_by_command(
    *,
    session: Session,
    command_id: UUID,
) -> ExternalCalendarImportEventRecord | None:
    row = (
        session.execute(
            select(external_calendar_import_events).where(
                external_calendar_import_events.c.command_id == command_id
            )
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _event_from_row(row)


def get_external_calendar_import_by_id(
    *,
    session: Session,
    import_id: UUID,
) -> ExternalCalendarImportRecord:
    row = (
        session.execute(
            select(external_calendar_imports).where(
                external_calendar_imports.c.import_id == import_id
            )
        )
        .mappings()
        .one()
    )
    return _import_from_row(row)
