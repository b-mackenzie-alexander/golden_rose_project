"""Minimized correction results and separately versioned current-facts review."""

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from golden_rose.api.staff.intake_schemas import CanonicalLinkReference, QueryIntakesRequest
from golden_rose.application.canonical_correction_contracts import (
    CorrectContactAddressRequest as CorrectContactAddressRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectContactDetailsRequest as CorrectContactDetailsRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectEmployerAddressRequest as CorrectEmployerAddressRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectStaffingRequestRequest as CorrectStaffingRequestRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectWorkerContactRequest as CorrectWorkerContactRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectWorkerPreferencesRequest as CorrectWorkerPreferencesRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectWorkerRequest as CorrectWorkerRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectWorkerResidenceRequest as CorrectWorkerResidenceRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    CorrectWorksiteAddressRequest as CorrectWorksiteAddressRequest,
)
from golden_rose.application.canonical_correction_contracts import (
    Text512,
)
from golden_rose.application.intake_contracts import IntakeValue

TargetEntity = Literal[
    "worker",
    "worker_contact",
    "worker_residence",
    "worker_preferences",
    "employer_contact_details",
    "employer_address",
    "worksite",
    "staffing_request",
]


class CanonicalResponseValue(IntakeValue):
    @field_validator(
        "command_id", "event_id", "review_id", "latest_review_id", mode="before", check_fields=False
    )
    @classmethod
    def parse_uuid(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)


class CanonicalTarget(IntakeValue):
    entity_type: TargetEntity
    id: UUID
    current_version: int = Field(ge=1, le=2147483647)

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)


class CanonicalCorrectionResponse(CanonicalResponseValue):
    command_id: UUID
    result_record_version: int = Field(ge=2, le=2147483647)
    target: CanonicalTarget
    event_id: UUID

    @model_validator(mode="after")
    def covers_result(self) -> "CanonicalCorrectionResponse":
        if self.target.current_version < self.result_record_version:
            raise ValueError("Current version precedes correction")
        return self


class CurrentOutputReference(CanonicalLinkReference):
    # Disposition describes the original finalization, version describes current facts.
    disposition: Literal["created", "reused"]


class WorkerCurrentOutputs(IntakeValue):
    kind: Literal["worker"]
    worker: CurrentOutputReference
    contact: CurrentOutputReference
    residence: CurrentOutputReference
    preferences: CurrentOutputReference

    @model_validator(mode="after")
    def consistent_disposition(self) -> "WorkerCurrentOutputs":
        if (
            len(
                {
                    self.worker.disposition,
                    self.contact.disposition,
                    self.residence.disposition,
                    self.preferences.disposition,
                }
            )
            != 1
        ):
            raise ValueError("Worker group must share original disposition")
        return self


class CreatedCurrentReference(CurrentOutputReference):
    disposition: Literal["created"]


class EmployerCurrentOutputs(IntakeValue):
    kind: Literal["employer"]
    employer: CurrentOutputReference
    contact: CurrentOutputReference
    contact_details: CurrentOutputReference
    worksite: CurrentOutputReference
    request: CreatedCurrentReference
    business_address: CurrentOutputReference | None

    @model_validator(mode="after")
    def consistent_disposition(self) -> "EmployerCurrentOutputs":
        if self.contact.disposition != self.contact_details.disposition:
            raise ValueError("Contact and details must share original disposition")
        if self.employer.disposition == "created" and any(
            child is not None and child.disposition == "reused"
            for child in (self.contact, self.contact_details, self.worksite, self.business_address)
        ):
            raise ValueError("Created parent cannot reuse children")
        return self


CurrentOutputs = Annotated[
    WorkerCurrentOutputs | EmployerCurrentOutputs, Field(discriminator="kind")
]


class ReviewCanonicalOutputsRequest(IntakeValue):
    expected_review_version: int = Field(ge=0, le=2147483646)
    expected_versions: CurrentOutputs
    note: Text512 | None = None


class CanonicalReviewState(CanonicalResponseValue):
    review_version: int = Field(ge=0, le=2147483647)
    latest_review_id: UUID | None
    status: Literal["unreviewed", "current", "stale"]
    dependencies: CurrentOutputs

    @model_validator(mode="after")
    def consistent_head(self) -> "CanonicalReviewState":
        if self.review_version == 0:
            if self.latest_review_id is not None or self.status != "unreviewed":
                raise ValueError("Unreviewed head must be empty")
        elif self.latest_review_id is None or self.status == "unreviewed":
            raise ValueError("Reviewed head requires a review")
        return self


class CanonicalReviewResponse(CanonicalResponseValue):
    command_id: UUID
    review_id: UUID
    result_record_version: int = Field(ge=1, le=2147483647)
    current: CanonicalReviewState

    @model_validator(mode="after")
    def covers_result(self) -> "CanonicalReviewResponse":
        if self.current.review_version < self.result_record_version:
            raise ValueError("Current head precedes review result")
        return self
