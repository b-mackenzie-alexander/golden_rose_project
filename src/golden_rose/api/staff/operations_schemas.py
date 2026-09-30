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


class OperationsProjectionResponse(IntakeValue):
    request_items: list[OperationsStaffingRequestItem]
    shift_items: list[OperationsShiftNeedItem]
