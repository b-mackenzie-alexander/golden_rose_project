"""Canonical exact-read DTOs, with address values isolated from ordinary details."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from golden_rose.api.staff.intake_schemas import OfferSummary
from golden_rose.application.intake_contracts import (
    Address,
    IntakeValue,
    Offer,
    Schedule,
    Text200,
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
