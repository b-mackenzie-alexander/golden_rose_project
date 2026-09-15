"""Strict commands for explicit canonical links and reviewed finalization."""

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from golden_rose.api.staff.intake_schemas import (
    CanonicalLinkReference as CanonicalLinkReference,
)
from golden_rose.api.staff.intake_schemas import (
    QueryIntakesRequest,
)
from golden_rose.application.intake_contracts import IntakeValue


class LinkIntakeRequest(IntakeValue):
    expected_version: int = Field(ge=1, le=2147483646)
    party: CanonicalLinkReference | None
    contact: CanonicalLinkReference | None = None
    worksite: CanonicalLinkReference | None = None
    business_address: CanonicalLinkReference | None = None

    @model_validator(mode="after")
    def require_parent(self) -> "LinkIntakeRequest":
        if self.party is None and any(
            reference is not None
            for reference in (self.contact, self.worksite, self.business_address)
        ):
            raise ValueError("Sublinks require a party")
        return self


class FinalizeIntakeRequest(IntakeValue):
    expected_version: int = Field(ge=1, le=2147483646)
    review_id: UUID

    @field_validator("review_id", mode="before")
    @classmethod
    def parse_review_id(cls, value: Any) -> Any:
        return QueryIntakesRequest.parse_reference(value)
