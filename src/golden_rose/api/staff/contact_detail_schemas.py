"""Separate canonical phone and restricted household address projections."""

from uuid import UUID

from pydantic import Field

from golden_rose.application.intake_contracts import Address, IntakeValue, Phone


class ContactDetails(IntakeValue):
    contact_details_id: UUID
    employer_id: UUID
    employer_contact_id: UUID
    version: int = Field(ge=1, le=2147483647)
    phone: Phone


class ContactAddress(IntakeValue):
    contact_details_id: UUID
    version: int = Field(ge=1, le=2147483647)
    address: Address
