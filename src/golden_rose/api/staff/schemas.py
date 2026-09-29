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


class EmployerContactCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str


class EmployerContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    employer_contact_id: UUID
    employer_id: UUID
    full_name: str
    version: int
    created_at: datetime
    updated_at: datetime


class EmployerContactSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    employer_contact_id: UUID
    employer_id: UUID
    full_name: str
    version: int
    created_at: datetime
    updated_at: datetime


class EmployerContactQueryPageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EmployerContactSummaryResponse]
    next_cursor: str | None


class EmployerContactQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=512)


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


StaffAccountRoleName = Literal[
    "owner",
    "delegated_manager",
    "operations_staff",
    "platform_administrator",
]
StaffAccountLifecycleStatus = Literal["active", "suspended", "deprovisioned"]


def _normalize_staff_text(field_name: str, value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > max_length:
        msg = f"{field_name} must be between 1 and {max_length} characters"
        raise ValueError(msg)
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        msg = f"{field_name} must not contain control characters"
        raise ValueError(msg)
    return normalized


class CreateStaffAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_subject: str
    display_name: str
    role_name: StaffAccountRoleName
    permission_names: tuple[str, ...]
    mfa_enrolled: bool = False
    reason_text: str

    @field_validator("provider_subject")
    @classmethod
    def validate_provider_subject(cls, value: str) -> str:
        return _normalize_staff_text("provider_subject", value, 256)

    @field_validator("display_name")
    @classmethod
    def validate_staff_display_name(cls, value: str) -> str:
        return _normalize_staff_text("display_name", value, 160)

    @field_validator("permission_names")
    @classmethod
    def validate_permission_names(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            msg = "permission_names must contain at least one permission"
            raise ValueError(msg)
        normalized = tuple(_normalize_staff_text("permission_name", item, 120) for item in value)
        if len(set(normalized)) != len(normalized):
            msg = "permission_names must not contain duplicates"
            raise ValueError(msg)
        return normalized

    @field_validator("reason_text")
    @classmethod
    def validate_staff_reason_text(cls, value: str) -> str:
        return _normalize_staff_text("reason_text", value, 512)


class StaffAccountTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1, le=2_147_483_646, strict=True)
    reason_text: str

    @field_validator("reason_text")
    @classmethod
    def validate_staff_reason_text(cls, value: str) -> str:
        return _normalize_staff_text("reason_text", value, 512)


class ActivateStaffAccountRequest(StaffAccountTransitionRequest):
    mfa_enrolled: bool


class StaffAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    staff_id: UUID
    provider_subject: str
    display_name: str
    role_name: StaffAccountRoleName
    lifecycle_status: StaffAccountLifecycleStatus
    mfa_enrolled: bool
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    version: int


class StaffAccountListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: tuple[StaffAccountResponse, ...]


class StaffDelegationGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_name: str
    scope_kind: Literal["global"] = "global"
    expires_at: datetime
    reason_text: str

    @field_validator("permission_name")
    @classmethod
    def validate_staff_permission_name(cls, value: str) -> str:
        return _normalize_staff_text("permission_name", value, 120)

    @field_validator("reason_text")
    @classmethod
    def validate_staff_delegation_reason_text(cls, value: str) -> str:
        return _normalize_staff_text("reason_text", value, 512)


class StaffDelegationRevokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_text: str

    @field_validator("reason_text")
    @classmethod
    def validate_staff_delegation_revocation_reason_text(cls, value: str) -> str:
        return _normalize_staff_text("reason_text", value, 512)


class StaffDelegationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    delegation_id: UUID
    grantor_staff_id: UUID
    grantee_staff_id: UUID
    permission_name: str
    scope_kind: Literal["global"]
    scope_id: UUID | None
    reason_text: str
    starts_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revoked_by: UUID | None
    revocation_reason: str | None


class StaffDelegationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: tuple[StaffDelegationResponse, ...]


class StaffDelegationCommandResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delegation: StaffDelegationResponse
    event_type: Literal["staff_delegation.granted", "staff_delegation.revoked"]
    result_version: int


class StaffAccountLifecycleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account: StaffAccountResponse
    event_type: Literal[
        "staff_account.created",
        "staff_account.activated",
        "staff_account.suspended",
        "staff_account.deprovisioned",
        "staff_account.recovery_recorded",
        "staff_account.sessions_revoked",
    ]
    result_version: int
