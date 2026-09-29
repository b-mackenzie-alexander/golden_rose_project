"""Canonical exact-read DTOs, with address values isolated from ordinary details."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from golden_rose.api.staff.intake_schemas import OfferSummary
from golden_rose.application.intake_contracts import (
    Address,
    IntakeValue,
    Offer,
    Schedule,
    Text100,
    Text200,
    Text500,
    Text1000,
)


class QueryEmployerOutputsRequest(IntakeValue):
    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=1024)


class EmployerAddressSummary(IntakeValue):
    employer_address_id: UUID
    employer_id: UUID
    version: int = Field(ge=1, le=2147483647)
    purpose: Literal["business"]


class EmployerAddressDetail(EmployerAddressSummary):
    address: Address


class WorksiteIdentity(IntakeValue):
    worksite_id: UUID
    employer_id: UUID
    version: int = Field(ge=1, le=2147483647)


class WorksiteDetail(WorksiteIdentity):
    location_verification_status: Literal["supplied"]
    service_area_status: Literal["unassigned"]
    map_area_status: Literal["pending"]


class WorksiteAddress(WorksiteIdentity):
    address: Address


class StaffingRequestSummary(IntakeValue):
    staffing_request_id: UUID
    employer_id: UUID
    version: int = Field(ge=1, le=2147483647)
    request_status: Literal["draft"]
    role_title: Text200
    worker_count: int = Field(ge=1, le=1000)
    offer: OfferSummary


class EmployerAddressPage(IntakeValue):
    items: list[EmployerAddressSummary]
    next_cursor: str | None


class WorksitePage(IntakeValue):
    items: list[WorksiteIdentity]
    next_cursor: str | None


class StaffingRequestPage(IntakeValue):
    items: list[StaffingRequestSummary]
    next_cursor: str | None


class StaffingRequestDetail(IntakeValue):
    staffing_request_id: UUID
    employer_id: UUID
    version: int = Field(ge=1, le=2147483647)
    employer_contact_id: UUID
    worksite_id: UUID
    employer_address_id: UUID | None
    request_type: Literal["household", "general_labor"]
    request_status: Literal["draft"]
    source_channel: Literal["staff_entry"]
    role_title: Text200
    duties_summary: Text1000
    worker_count: int = Field(ge=1, le=1000)
    schedule: Schedule
    offer: Offer
    created_at: datetime
    received_at: datetime
    updated_at: datetime


class QueryShiftNeedsRequest(IntakeValue):
    page_size: int = Field(default=25, ge=1, le=50)


class CreateShiftNeedRequest(IntakeValue):
    expected_request_version: int = Field(ge=1, le=2147483647)
    role_title: Text200
    worker_count: int = Field(ge=1, le=1000)
    starts_at: datetime
    ends_at: datetime
    time_zone: Text100
    reason_text: Text500
    notes: Text1000 | None = None

    @field_validator("starts_at", "ends_at", mode="before")
    @classmethod
    def parse_json_datetime(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class ShiftNeedDetail(IntakeValue):
    shift_need_id: UUID
    employer_id: UUID
    staffing_request_id: UUID
    request_version_at_creation: int = Field(ge=1, le=2147483647)
    shift_status: Literal["draft"]
    role_title: Text200
    worker_count: int = Field(ge=1, le=1000)
    starts_at: datetime
    ends_at: datetime
    time_zone: Text100
    notes: Text1000 | None = None
    version: int = Field(ge=1, le=2147483647)
    created_at: datetime
    updated_at: datetime


class ShiftNeedPage(IntakeValue):
    items: list[ShiftNeedDetail]


class ShiftNeedCommandResponse(IntakeValue):
    command_id: UUID
    result_record_version: int = Field(ge=1, le=2147483647)
    event_type: Literal["shift_need.created"]
    current: ShiftNeedDetail
