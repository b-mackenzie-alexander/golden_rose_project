from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StaffCalendarConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    connection_id: UUID
    staff_id: UUID
    provider_name: Literal["google_calendar"]
    calendar_alias: str
    granted_scopes: list[str]
    connection_status: Literal[
        "authorization_required",
        "connected",
        "disconnected",
        "unavailable",
    ]
    connected_at: datetime | None
    disconnected_at: datetime | None
    last_sync_status: Literal[
        "never_synced",
        "ready",
        "failed",
        "configuration_required",
    ]
    last_sync_error: str | None
    updated_at: datetime
    version: int


class ExternalCalendarImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    import_id: UUID
    connection_id: UUID
    provider_event_updated_at: datetime
    event_title: str
    starts_at: datetime
    ends_at: datetime
    time_zone: str
    location_review: str | None
    import_status: Literal[
        "candidate",
        "ignored",
        "marked_existing",
        "linked",
        "draft_started",
        "superseded",
        "unavailable",
    ]
    linked_entity_type: str | None
    linked_entity_id: UUID | None
    updated_at: datetime
    version: int


class CalendarImportSummaryResponse(BaseModel):
    connection: StaffCalendarConnectionResponse | None
    candidates: tuple[ExternalCalendarImportResponse, ...]
    oauth_configuration_required: bool
    oauth_connect_available: bool


class GoogleCalendarOAuthStartResponse(BaseModel):
    authorization_url: str


class StageExternalCalendarCandidateRequest(BaseModel):
    provider_event_uid: str = Field(min_length=1, max_length=200)
    provider_event_updated_at: datetime
    event_title: str = Field(min_length=1, max_length=200)
    starts_at: datetime
    ends_at: datetime
    time_zone: str = Field(min_length=1, max_length=64)
    location_review: str | None = Field(default=None, max_length=200)
    reason_text: str = Field(min_length=1, max_length=512)


class ExternalCalendarCandidateDispositionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason_text: str = Field(min_length=1, max_length=512)


class ExternalCalendarImportCommandResponse(BaseModel):
    candidate: ExternalCalendarImportResponse
    event_type: Literal[
        "external_calendar.candidate_imported",
        "external_calendar.candidate_deduplicated",
        "external_calendar.candidate_ignored",
        "external_calendar.candidate_marked_existing",
    ]
    result_version: int
    replayed: bool
