"""Staff operations projection DTOs for dashboard surfaces."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from golden_rose.application.intake_contracts import IntakeValue, Text200


class OperationsStaffingRequestItem(IntakeValue):
    item_type: Literal["staffing_request"]
    source_intake_id: UUID | None = None
    employer_id: UUID
    employer_name: Text200
    staffing_request_id: UUID
    request_status: Literal["draft", "pending_review"]
    role_title: Text200
    worker_count: int = Field(ge=1, le=1000)
    version: int = Field(ge=1, le=2147483647)
    received_at: datetime
    updated_at: datetime


class OperationsShiftNeedItem(IntakeValue):
    item_type: Literal["shift_need"]
    source_intake_id: UUID | None = None
    employer_id: UUID
    employer_name: Text200
    staffing_request_id: UUID
    shift_need_id: UUID
    request_status: Literal["draft", "pending_review"]
    shift_status: Literal["draft", "pending_review"]
    role_title: Text200
    worker_count: int = Field(ge=1, le=1000)
    starts_at: datetime
    ends_at: datetime
    time_zone: Text200
    version: int = Field(ge=1, le=2147483647)
    updated_at: datetime


class OperationsAreaSummaryItem(IntakeValue):
    area_key: Literal["bronx", "brooklyn", "manhattan", "queens", "staten_island"]
    area_label: Literal["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
    request_count: int = Field(ge=0, le=2147483647)
    shift_count: int = Field(ge=0, le=2147483647)
    worker_slots: int = Field(ge=0, le=2147483647)
    pending_review_count: int = Field(ge=0, le=2147483647)


class OperationsReportSummary(IntakeValue):
    request_count: int = Field(ge=0, le=2147483647)
    shift_count: int = Field(ge=0, le=2147483647)
    worker_slots: int = Field(ge=0, le=2147483647)
    pending_review_count: int = Field(ge=0, le=2147483647)
    active_area_count: int = Field(ge=0, le=5)
    unmapped_request_count: int = Field(ge=0, le=2147483647)


class OperationsCalendarSummary(IntakeValue):
    projected_shift_count: int = Field(ge=0, le=2147483647)
    worker_slots: int = Field(ge=0, le=2147483647)
    pending_review_shift_count: int = Field(ge=0, le=2147483647)
    coverage_day_count: int = Field(ge=0, le=366)
    first_shift_starts_at: datetime | None = None
    last_shift_ends_at: datetime | None = None


class OperationsQueueSummary(IntakeValue):
    open_item_count: int = Field(ge=0, le=2147483647)
    draft_count: int = Field(ge=0, le=2147483647)
    pending_review_count: int = Field(ge=0, le=2147483647)
    high_priority_count: int = Field(ge=0, le=2147483647)
    oldest_item_updated_at: datetime | None = None
    newest_item_updated_at: datetime | None = None


class OperationsProjectionResponse(IntakeValue):
    request_items: list[OperationsStaffingRequestItem]
    shift_items: list[OperationsShiftNeedItem]
    area_summary: list[OperationsAreaSummaryItem]
    report_summary: OperationsReportSummary
    calendar_summary: OperationsCalendarSummary
    queue_summary: OperationsQueueSummary
