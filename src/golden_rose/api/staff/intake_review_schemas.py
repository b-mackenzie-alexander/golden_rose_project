"""Strict review, follow-up, history and governed catalog contracts."""

import re
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import AfterValidator, Field, field_validator, model_validator

from golden_rose.api.staff.intake_schemas import (
    IntakeResponseValue,
    IntakeSummary,
    QueryIntakesRequest,
)
from golden_rose.application.intake_contracts import (
    Address,
    EmployerDraftContent,
    IntakeValue,
    Text100,
    Text200,
    WorkerDraftContent,
    normalize_text,
    validate_content,
)

Text512 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=512)]
ReasonCode = Literal["missing_information", "clarification", "other"]
ReviewOutcome = Literal["intake_reviewed", "needs_follow_up"]
AttemptMethod = Literal["phone", "email", "in_person", "other"]
AttemptOutcome = Literal[
    "no_answer",
    "voicemail_left",
    "callback_requested",
    "contact_reached_information_pending",
    "invalid_contact_information",
    "information_received",
    "other",
]


class FollowUpValues(IntakeValue):
    owner_staff_id: UUID | None = None
    next_follow_up_at: datetime | None = None
    time_zone: Text100 | None = None

    @field_validator("owner_staff_id", mode="before")
    @classmethod
    def owner_uuid(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)

    @field_validator("next_follow_up_at", mode="before")
    @classmethod
    def instant(cls, value: Any) -> Any:
        if isinstance(value, str):
            if not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value
            ):
                raise ValueError("RFC3339 instant required")
            value = datetime.fromisoformat(value)
        if value is not None and (not isinstance(value, datetime) or value.utcoffset() is None):
            raise ValueError("Offset required")
        return value

    @model_validator(mode="after")
    def valid_zone(self) -> "FollowUpValues":
        if self.time_zone is not None:
            try:
                zone = ZoneInfo(self.time_zone)
                if (
                    self.next_follow_up_at is not None
                    and self.next_follow_up_at.astimezone(zone).utcoffset()
                    != self.next_follow_up_at.utcoffset()
                ):
                    raise ValueError("Offset mismatch")
            except (KeyError, OverflowError) as exc:
                raise ValueError("Invalid time zone") from exc
        return self


class ReviewIntakeRequest(FollowUpValues):
    expected_version: int = Field(ge=1, le=2147483646)
    outcome: ReviewOutcome
    note: Text512 | None = None
    reason_code: ReasonCode | None = None
    reason_text: Text512 | None = None

    @model_validator(mode="after")
    def disposition_shape(self) -> "ReviewIntakeRequest":
        fields = ("reason_code", "reason_text", "owner_staff_id", "next_follow_up_at", "time_zone")
        if self.outcome == "needs_follow_up":
            if any(getattr(self, field) is None for field in fields):
                raise ValueError("Follow-up responsibility required")
        elif any(field in self.model_fields_set for field in fields):
            raise ValueError("Reviewed disposition rejects follow-up fields")
        return self


class FollowUpIntakeRequest(FollowUpValues):
    expected_version: int = Field(ge=1, le=2147483646)
    action: Literal["reschedule", "reassign", "attempt"]
    reason_text: Text512
    owner_staff_id: UUID
    next_follow_up_at: datetime
    time_zone: Text100
    method: AttemptMethod | None = None
    outcome: AttemptOutcome | None = None
    note: Text512 | None = None

    @model_validator(mode="after")
    def attempt_shape(self) -> "FollowUpIntakeRequest":
        if self.action == "attempt":
            if self.method is None or self.outcome is None:
                raise ValueError("Attempt method and outcome required")
        elif self.method is not None or self.outcome is not None:
            raise ValueError("Only attempts have method and outcome")
        return self


class PageRequest(IntakeValue):
    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=1024)


class QueryWorkInterestsRequest(PageRequest):
    include_retired: bool = False


class CreateWorkInterestRequest(IntakeValue):
    code: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")]
    label_en: Text100
    label_es: Text100


class ReviseWorkInterestRequest(IntakeValue):
    expected_version: int = Field(ge=1, le=2147483646)
    label_en: Text100
    label_es: Text100
    active: bool


# Explicit response projections keep protected payloads out of ordinary history.


class WorkflowResponse(IntakeResponseValue):
    @field_validator(
        "event_id",
        "review_id",
        "actor_id",
        "owner_staff_id",
        "staff_id",
        "interest_id",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def response_uuid(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)

    @field_validator("occurred_at", "next_follow_up_at", mode="before", check_fields=False)
    @classmethod
    def response_time(cls, value: Any) -> Any:
        return IntakeSummary.parse_output_time(value)


class IntakeHistoryItem(WorkflowResponse):
    event_id: UUID
    version: int = Field(ge=1, le=2147483647)
    content_version: int = Field(ge=1, le=2147483647)
    event_type: Literal[
        "intake.created", "intake.revised", "intake.reviewed", "intake.follow_up_recorded"
    ]
    actor_id: UUID
    actor_display_name: Text200
    occurred_at: datetime
    review_id: UUID | None = None
    outcome: ReviewOutcome | None = None
    owner_staff_id: UUID | None = None
    next_follow_up_at: datetime | None = None


class IntakeHistoryPage(WorkflowResponse):
    items: list[IntakeHistoryItem] = Field(max_length=50)
    next_cursor: str | None = Field(max_length=1024)


class ReviewedSnapshot(IntakeValue):
    kind: Literal["worker", "employer"]
    content: WorkerDraftContent | EmployerDraftContent
    addresses: dict[
        Literal["worker_residence", "party_address", "worksite_address"], Address | None
    ]

    @model_validator(mode="after")
    def snapshot_kind(self) -> "ReviewedSnapshot":
        validate_content(self.kind, self.content.to_content())
        expected = (
            {"worker_residence"} if self.kind == "worker" else {"party_address", "worksite_address"}
        )
        if set(self.addresses) != expected:
            raise ValueError("Snapshot address sections must match intake kind")
        return self


class ProtectedFollowUp(IntakeValue):
    action: Literal["needs_follow_up", "reschedule", "reassign", "attempt"]
    reason_code: ReasonCode | None = None
    reason_text: Text512
    method: AttemptMethod | None = None
    outcome: AttemptOutcome | None = None
    time_zone: Text100


class RestrictedHistoryResponse(WorkflowResponse):
    event_id: UUID
    note: Text512 | None = None
    reviewed_content: ReviewedSnapshot | None = None
    follow_up: ProtectedFollowUp | None = None


class FollowUpOwner(WorkflowResponse):
    staff_id: UUID
    display_name: Text200


class FollowUpOwnersPage(WorkflowResponse):
    items: list[FollowUpOwner] = Field(max_length=50)
    next_cursor: str | None = Field(max_length=1024)


class WorkInterestResponse(WorkflowResponse):
    interest_id: UUID
    code: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")]
    version: int = Field(ge=1, le=2147483647)
    label_en: Text100
    label_es: Text100
    active: bool


class WorkInterestPage(WorkflowResponse):
    items: list[WorkInterestResponse] = Field(max_length=50)
    next_cursor: str | None = Field(max_length=1024)


class WorkInterestCommandResponse(WorkflowResponse):
    command_id: UUID
    result_record_version: int = Field(ge=1, le=2147483647)
    current: WorkInterestResponse

    @model_validator(mode="after")
    def current_covers_result(self) -> "WorkInterestCommandResponse":
        if self.current.version < self.result_record_version:
            raise ValueError("Current version precedes the saved result")
        return self
