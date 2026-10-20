"""Complete section replacements for canonical current facts (intake contract §9).

These values confer no permission and perform no writes. Catalog currency and
same-target correction references are checked under locks by the command.
"""

from typing import Annotated, Any
from uuid import UUID

from pydantic import AfterValidator, Field, field_validator, model_validator

from golden_rose.application.intake_contracts import (
    Address,
    Availability,
    Email,
    IntakeValue,
    Interests,
    Offer,
    Phone,
    Schedule,
    Text200,
    Text1000,
    normalize_text,
)

Text512 = Annotated[str, Field(strict=True), AfterValidator(normalize_text), Field(max_length=512)]


class CorrectionRequest(IntakeValue):
    expected_version: int = Field(ge=1, le=2147483646)
    reason_text: Text512
    corrects_event_id: UUID | None = None

    @field_validator("corrects_event_id", mode="before")
    @classmethod
    def parse_event_id(cls, value: Any) -> Any:
        if isinstance(value, str):
            parsed = UUID(value)
            if str(parsed) != value.lower():
                raise ValueError("Full UUID required")
            return parsed
        return value

    def section_values(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json",
            exclude={"expected_version", "reason_text", "corrects_event_id"},
            exclude_none=True,
            exclude_unset=True,
        )


class CorrectWorkerRequest(CorrectionRequest):
    full_name: Text200


class CorrectWorkerContactRequest(CorrectionRequest):
    phone: Phone
    email: Email | None = None

    def section_values(self) -> dict[str, Any]:
        return {"phone": self.phone, "email": self.email}


class CompleteAddress(Address):
    line1: Text200

    # Other required values retain the exact base field bounds.
    @model_validator(mode="after")
    def require_complete_address(self) -> "CompleteAddress":
        required = {"line1", "locality", "country"}
        if self.country == "US":
            required |= {"region", "postal_code"}
        if any(getattr(self, name) is None for name in required):
            raise ValueError("Complete address required")
        return self


class CorrectWorkerResidenceRequest(CorrectionRequest):
    address: CompleteAddress


class CorrectWorkerPreferencesRequest(CorrectionRequest):
    interests: Interests
    availability: Availability

    @model_validator(mode="after")
    def require_complete_preferences(self) -> "CorrectWorkerPreferencesRequest":
        if not self.interests.selections and not self.interests.other_description:
            raise ValueError("Work interests required")
        if self.availability.mode == "unknown":
            raise ValueError("Availability required")
        return self


class CorrectContactDetailsRequest(CorrectionRequest):
    representative_name: Text200
    phone: Phone
    email: Email | None = None

    def section_values(self) -> dict[str, Any]:
        return {
            "representative_name": self.representative_name,
            "phone": self.phone,
            "email": self.email,
        }


class CorrectContactAddressRequest(CorrectionRequest):
    address: CompleteAddress


class CorrectEmployerAddressRequest(CorrectionRequest):
    address: CompleteAddress


class CorrectWorksiteAddressRequest(CorrectionRequest):
    address: CompleteAddress


class CorrectStaffingRequestRequest(CorrectionRequest):
    role_title: Text200
    duties_summary: Text1000
    worker_count: int = Field(ge=1, le=1000)
    schedule: Schedule
    offer: Offer

    @model_validator(mode="after")
    def require_complete_request(self) -> "CorrectStaffingRequestRequest":
        if self.schedule.mode == "unknown":
            raise ValueError("Schedule required")
        if any(
            getattr(self.offer, field) is None
            for field in ("minimum", "currency", "basis", "per_worker")
        ):
            raise ValueError("Complete offer required")
        return self
