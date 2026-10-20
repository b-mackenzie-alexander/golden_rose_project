"""Intake draft command/query transport contracts."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from golden_rose.application.intake_contracts import (
    Address,
    Email,
    EmployerCreateContent,
    EmployerDraftContent,
    IntakeValue,
    Money,
    Offer,
    Phone,
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


class FollowUpSummary(IntakeResponseValue):
    owner_staff_id: UUID
    next_follow_up_at: datetime
    overdue: bool

    @field_validator("owner_staff_id", mode="before")
    @classmethod
    def owner_id(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)

    @field_validator("next_follow_up_at", mode="before")
    @classmethod
    def instant(cls, value: Any) -> Any:
        return datetime.fromisoformat(value) if isinstance(value, str) else value


class LatestIntakeReview(IntakeResponseValue):
    review_id: UUID
    reviewed_record_version: int = Field(ge=1)
    reviewed_content_version: int = Field(ge=1)
    outcome: Literal["intake_reviewed", "needs_follow_up"]
    actor_id: UUID
    actor_display_name: Text200
    occurred_at: datetime


class IntakeSummary(IntakeResponseValue):
    intake_id: UUID
    kind: Literal["worker", "employer"]
    version: int = Field(ge=1, le=2_147_483_647)
    lifecycle: Literal["draft", "finalized"]
    display_name: Text200 | None = None
    # None means linked canonical completeness is unavailable to this reader.
    complete: bool | None
    missing_fields: list[MissingIntakeField] = Field(max_length=15)
    review_status: Literal["unreviewed", "needs_follow_up", "current", "stale"]
    follow_up: FollowUpSummary | None = None
    updated_at: datetime
    offer: OfferSummary | None = None

    @model_validator(mode="after")
    def unavailable_summary_has_no_facts(self) -> "IntakeSummary":
        if self.complete is None and (self.display_name is not None or self.missing_fields):
            raise ValueError("Unavailable completeness cannot claim canonical facts")
        return self

    @field_validator("updated_at", mode="before")
    @classmethod
    def parse_output_time(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if isinstance(value, datetime) and value.utcoffset() is None:
            raise ValueError("Response instant must be offset aware")
        return value


class CreatedCanonicalReference(IntakeValue):
    id: UUID
    version: int = Field(ge=1, le=1)
    disposition: Literal["created"]

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)


class CanonicalLinkReference(IntakeValue):
    id: UUID
    version: int = Field(ge=1, le=2147483647)

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)


class ResolvedEmployerContent(IntakeValue):
    employer_type: Literal["household", "business"] | None = None
    display_name: Text200 | None = None
    representative_name: Text200 | None = None
    phone: Phone | None = None
    email: Email | None = None


LinkEntity = Literal[
    "worker",
    "worker_contact",
    "worker_residence",
    "worker_preferences",
    "employer",
    "employer_contact",
    "employer_contact_details",
    "worksite",
    "employer_address",
]


class WorkerFinalizationOutputs(IntakeValue):
    kind: Literal["worker"]
    worker: "CanonicalOutputReference"
    contact: "CanonicalOutputReference"
    residence: "CanonicalOutputReference"
    preferences: "CanonicalOutputReference"

    @model_validator(mode="after")
    def whole_group_disposition(self) -> "WorkerFinalizationOutputs":
        if (
            len(
                {
                    ref.disposition
                    for ref in (self.worker, self.contact, self.residence, self.preferences)
                }
            )
            != 1
        ):
            raise ValueError("Worker outputs must all be created or all reused")
        return self


class CanonicalOutputReference(CanonicalLinkReference):
    disposition: Literal["created", "reused"]

    @model_validator(mode="after")
    def created_version(self) -> "CanonicalOutputReference":
        if self.disposition == "created" and self.version != 1:
            raise ValueError("Created output must start at version one")
        return self


class EmployerFinalizationOutputs(IntakeValue):
    kind: Literal["employer"]
    employer: CanonicalOutputReference
    contact: CanonicalOutputReference
    contact_details: CanonicalOutputReference
    worksite: CanonicalOutputReference
    request: CreatedCanonicalReference
    business_address: CanonicalOutputReference | None

    @model_validator(mode="after")
    def consistent_reuse(self) -> "EmployerFinalizationOutputs":
        if self.contact.disposition != self.contact_details.disposition:
            raise ValueError("Contact and details must be created or reused together")
        children = (self.contact, self.contact_details, self.worksite, self.business_address)
        if self.employer.disposition == "created" and any(
            child is not None and child.disposition == "reused" for child in children
        ):
            raise ValueError("A new employer cannot reuse another employer's children")
        return self


class IntakeDetail(IntakeResponseValue):
    latest_review: LatestIntakeReview | None = None
    summary: IntakeSummary
    content_version: int = Field(ge=1, le=2_147_483_647)
    candidate: WorkerDraftContent | EmployerDraftContent
    resolved: WorkerDraftContent | ResolvedEmployerContent
    links: dict[LinkEntity, CanonicalLinkReference] = Field(max_length=5)
    dependency_stale: bool
    finalization: WorkerFinalizationOutputs | EmployerFinalizationOutputs | None = None

    @model_validator(mode="before")
    @classmethod
    def select_resolved_kind(cls, value: Any) -> Any:
        if isinstance(value, dict) and "resolved" in value:
            summary = value.get("summary")
            kind = (
                summary.get("kind") if isinstance(summary, dict) else getattr(summary, "kind", None)
            )
            model = WorkerDraftContent if kind == "worker" else ResolvedEmployerContent
            value = dict(value)
            value["resolved"] = model.model_validate(value["resolved"])
        return value

    @model_validator(mode="after")
    def validate_detail(self) -> "IntakeDetail":
        if self.summary.complete is None:
            raise ValueError("Full detail requires authorized completeness")
        validate_content(self.summary.kind, self.candidate.to_content())
        names = set(self.links)
        resolved = self.resolved.model_dump(exclude_unset=True)
        if not names:
            if resolved or self.dependency_stale:
                raise ValueError(
                    "Unlinked detail cannot contain resolved facts or stale dependencies"
                )
        elif self.summary.kind == "worker":
            if names != {"worker", "worker_contact", "worker_residence", "worker_preferences"}:
                raise ValueError("Worker links require the complete canonical group")
            if not isinstance(self.resolved, WorkerDraftContent):
                raise ValueError("Worker detail requires worker resolved facts")
        else:
            allowed = {
                "employer",
                "employer_contact",
                "employer_contact_details",
                "worksite",
                "employer_address",
            }
            if "employer" not in names or not names <= allowed:
                raise ValueError("Employer links require a matching parent")
            if ("employer_contact" in names) != ("employer_contact_details" in names):
                raise ValueError("Selected contact requires details")
            if not isinstance(self.resolved, ResolvedEmployerContent):
                raise ValueError("Employer detail requires employer resolved facts")
            if "employer_contact" not in names and {"representative_name", "phone"} & set(resolved):
                raise ValueError("Unselected contact facts cannot be resolved")
            if (
                self.resolved.employer_type == "household"
                and "employer_address" in names
                and not self.dependency_stale
            ):
                raise ValueError("Household cannot select a business address")
        if self.summary.lifecycle == "finalized":
            if self.finalization is None or self.finalization.kind != self.summary.kind:
                raise ValueError("Finalized intake requires kind-matching output references")
        elif self.finalization is not None:
            raise ValueError("Draft cannot contain finalization outputs")
        return self


class IntakeAddressDetail(IntakeResponseValue):
    intake_id: UUID
    version: int = Field(ge=1, le=2_147_483_647)
    section: Literal["worker_residence", "party_address", "worksite_address"]
    candidate: Address | None
    resolved: Address | None
    source_ref: CanonicalLinkReference | None = None

    @model_validator(mode="after")
    def resolved_requires_source(self) -> "IntakeAddressDetail":
        if self.resolved is not None and self.source_ref is None:
            raise ValueError("Resolved address requires a canonical source reference")
        return self


class IntakeCommandResponse(IntakeResponseValue):
    command_id: UUID
    result_record_version: int = Field(ge=1, le=2_147_483_647)
    current: IntakeDetail
    finalization: WorkerFinalizationOutputs | EmployerFinalizationOutputs | None = None

    @model_validator(mode="after")
    def current_covers_result(self) -> "IntakeCommandResponse":
        if self.current.summary.version < self.result_record_version:
            raise ValueError("Current version precedes command result")
        if self.finalization is not None and self.finalization != self.current.finalization:
            raise ValueError("Finalization references differ from current intake")
        return self


class IntakeQueryPageResponse(IntakeResponseValue):
    items: list[IntakeSummary] = Field(max_length=50)
    next_cursor: str | None = Field(max_length=1024)
