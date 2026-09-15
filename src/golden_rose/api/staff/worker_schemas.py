"""Minimized canonical worker read projections."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from golden_rose.api.staff.intake_schemas import QueryIntakesRequest
from golden_rose.application.intake_contracts import (
    Address,
    Availability,
    IntakeValue,
    Interests,
    Phone,
    Text100,
    Text200,
)


class QueryWorkersRequest(IntakeValue):
    name_query: Text100 | None = Field(default=None, min_length=2)
    reference: UUID | None = None
    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=1024)

    @field_validator("reference", mode="before")
    @classmethod
    def parse_reference(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)

    @model_validator(mode="after")
    def identifying_filter(self) -> "QueryWorkersRequest":
        if (self.name_query is None) == (self.reference is None):
            raise ValueError("Exactly one identifying filter is required")
        return self


class WorkerSummary(IntakeValue):
    worker_id: UUID
    full_name: Text200
    version: int = Field(ge=1, le=2147483647)


class WorkerQueryPage(IntakeValue):
    items: list[WorkerSummary]
    next_cursor: str | None


class WorkerDetail(IntakeValue):
    worker_id: UUID
    full_name: Text200
    version: int = Field(ge=1, le=2147483647)
    contact_id: UUID
    residence_id: UUID
    preferences_id: UUID
    created_at: datetime
    updated_at: datetime


class WorkerContactDetail(IntakeValue):
    worker_contact_id: UUID
    worker_id: UUID
    version: int = Field(ge=1, le=2147483647)
    phone: Phone


class WorkerResidenceDetail(IntakeValue):
    worker_residence_id: UUID
    worker_id: UUID
    version: int = Field(ge=1, le=2147483647)
    address: Address


class WorkerPreferencesDetail(IntakeValue):
    worker_preferences_id: UUID
    worker_id: UUID
    version: int = Field(ge=1, le=2147483647)
    interests: Interests
    availability: Availability
    self_reported: Literal[True]
