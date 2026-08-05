import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CreateDraftEmployerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employer_type: Literal["household", "business"]
    display_name: str

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = unicodedata.normalize("NFC", value).strip()
        if not normalized:
            msg = "display_name must not be blank"
            raise ValueError(msg)
        if len(normalized) > 200:
            msg = "display_name must be 200 characters or fewer"
            raise ValueError(msg)
        if any(unicodedata.category(character).startswith("C") for character in normalized):
            msg = "display_name must not contain control characters"
            raise ValueError(msg)
        return normalized


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
