import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from golden_rose.application.employer_text import (
    normalize_employer_text,
    validate_employer_display_name,
)


class CreateDraftEmployerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employer_type: Literal["household", "business"]
    display_name: str

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        return validate_employer_display_name(value)


class ReviseDraftEmployerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1, le=2_147_483_646, strict=True)
    employer_type: Literal["household", "business"]
    display_name: str

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        return validate_employer_display_name(value)


class DraftEmployerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employer_id: UUID
    employer_type: Literal["household", "business"]
    display_name: str
    lifecycle_status: Literal["draft"]
    source_channel: Literal["staff_entry"]
    version: int
    received_at: datetime
    created_at: datetime


class EmployerDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employer_id: UUID
    employer_type: Literal["household", "business"]
    display_name: str
    lifecycle_status: Literal["draft"]
    source_channel: Literal["staff_entry"]
    version: int
    received_at: datetime
    created_at: datetime
    updated_at: datetime


class EmployerSearchItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employer_id: UUID
    employer_type: Literal["household", "business"]
    display_name: str
    lifecycle_status: Literal["draft"]
    version: int
    received_at: datetime


class EmployerSearchPageResponse(BaseModel):
    items: list[EmployerSearchItemResponse]
    next_cursor: str | None


class SearchEmployersRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name_query: str
    employer_type: Literal["household", "business"] | None = None
    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=512)

    @field_validator("display_name_query")
    @classmethod
    def normalize_display_name_query(cls, value: str) -> str:
        normalized = normalize_employer_text(value)
        if len(normalized) < 2 or len(normalized) > 100:
            msg = "display_name_query must be between 2 and 100 characters"
            raise ValueError(msg)
        if any(unicodedata.category(character).startswith("C") for character in normalized):
            msg = "display_name_query must not contain control characters"
            raise ValueError(msg)
        return normalized
