"""Intake draft command/query transport contracts."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from golden_rose.application.intake_contracts import (
    Address,
    EmployerCreateContent,
    EmployerDraftContent,
    IntakeValue,
    Money,
    Offer,
    Text3,
    Text100,
    Text200,
    WorkerCreateContent,
    WorkerDraftContent,
    has_substantive_content,
    validate_content,
)


class CreateIntakeRequest(IntakeValue):
    kind: Literal["worker", "employer"]
    content: WorkerCreateContent | EmployerCreateContent

    @model_validator(mode="before")
    @classmethod
    def select_content(cls, value: Any) -> Any:
        if isinstance(value, dict) and "kind" in value and "content" in value:
            value = dict(value)
            value["content"] = validate_content(
                value["kind"], value["content"], include_addresses=True
            )
        return value

    @model_validator(mode="after")
    def require_substantive(self) -> "CreateIntakeRequest":
        if not has_substantive_content(self.content.to_content()):
            raise ValueError("At least one substantive content field is required")
        return self


class ReviseIntakeRequest(IntakeValue):
    expected_version: int = Field(ge=1, le=2_147_483_646)
    content: WorkerDraftContent | EmployerDraftContent


class ReviseIntakeAddressRequest(IntakeValue):
    expected_version: int = Field(ge=1, le=2_147_483_646)
    address: Address | None


class QueryIntakesRequest(IntakeValue):
    kind: Literal["worker", "employer"]
    lifecycle: Literal["draft", "finalized"] = "draft"
    name_query: Text100 | None = Field(default=None, min_length=2)
    reference: UUID | None = None
    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=1024)

    @field_validator("reference", mode="before")
    @classmethod
    def parse_reference(cls, value: Any) -> Any:
        if isinstance(value, str):
            parsed = UUID(value)
            if str(parsed) != value.lower():
                raise ValueError("Full UUID required")
            return parsed
        return value

    @model_validator(mode="after")
    def exclusive_filters(self) -> "QueryIntakesRequest":
        if self.name_query is not None and self.reference is not None:
            raise ValueError("Name and reference filters are exclusive")
        return self


# PR A response contracts expose no future review/link/finalization authority.
MissingIntakeField = Literal[
    "full_name",
    "phone",
    "interests",
    "availability",
    "worker_residence",
    "employer_type",
    "display_name",
    "representative_name",
    "role_title",
    "duties_summary",
    "worker_count",
    "schedule",
    "offer",
    "party_address",
    "worksite_address",
]


class OfferSummary(IntakeValue):
    minimum: Money | None = None
    maximum: Money | None = None
    currency: Text3 | None = None
    basis: Literal["hour", "day", "week", "month", "year", "task"] | None = None
    per_worker: bool | None = None
    negotiable: bool = False

    @model_validator(mode="after")
    def valid_offer_values(self) -> "OfferSummary":
        Offer.model_validate(self.to_content())
        return self


class IntakeResponseValue(IntakeValue):
    @field_validator("intake_id", "command_id", mode="before", check_fields=False)
    @classmethod
    def parse_output_uuid(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)


class IntakeSummary(IntakeResponseValue):
    intake_id: UUID
    kind: Literal["worker", "employer"]
    version: int = Field(ge=1, le=2_147_483_647)
    lifecycle: Literal["draft"]
    display_name: Text200 | None = None
    complete: bool
    missing_fields: list[MissingIntakeField] = Field(max_length=15)
    review_status: Literal["unreviewed"]
    updated_at: datetime
    offer: OfferSummary | None = None

    @field_validator("updated_at", mode="before")
    @classmethod
    def parse_output_time(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if isinstance(value, datetime) and value.utcoffset() is None:
            raise ValueError("Response instant must be offset aware")
        return value


class IntakeDetail(IntakeResponseValue):
    summary: IntakeSummary
    content_version: int = Field(ge=1, le=2_147_483_647)
    candidate: WorkerDraftContent | EmployerDraftContent
    resolved: dict[str, Any] = Field(max_length=0)
    links: dict[str, Any] = Field(max_length=0)
    dependency_stale: bool

    @model_validator(mode="after")
    def validate_pr_a_detail(self) -> "IntakeDetail":
        validate_content(self.summary.kind, self.candidate.to_content())
        if self.dependency_stale:
            raise ValueError("Draft-only response cannot contain linked dependencies")
        return self


class IntakeAddressDetail(IntakeResponseValue):
    intake_id: UUID
    version: int = Field(ge=1, le=2_147_483_647)
    section: Literal["worker_residence", "party_address", "worksite_address"]
    candidate: Address | None
    resolved: None


class IntakeCommandResponse(IntakeResponseValue):
    command_id: UUID
    result_record_version: int = Field(ge=1, le=2_147_483_647)
    current: IntakeDetail

    @model_validator(mode="after")
    def current_covers_result(self) -> "IntakeCommandResponse":
        if self.current.summary.version < self.result_record_version:
            raise ValueError("Current version precedes command result")
        return self


class IntakeQueryPageResponse(IntakeResponseValue):
    items: list[IntakeSummary] = Field(max_length=50)
    next_cursor: str | None = Field(max_length=1024)
