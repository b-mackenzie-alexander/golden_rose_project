from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from golden_rose.auth.principal import StaffPrincipal

StaffAccountStatus = Literal["active", "suspended", "deprovisioned"]
StaffAccountRole = Literal[
    "owner",
    "delegated_manager",
    "operations_staff",
    "platform_administrator",
]

STAFF_ACCOUNT_STATUSES: frozenset[str] = frozenset({"active", "suspended", "deprovisioned"})
STAFF_ACCOUNT_ROLES: frozenset[str] = frozenset(
    {
        "owner",
        "delegated_manager",
        "operations_staff",
        "platform_administrator",
    }
)


@dataclass(frozen=True, slots=True)
class StaffAccount:
    staff_id: UUID
    provider_subject: str
    display_name: str
    role_name: StaffAccountRole
    status: StaffAccountStatus
    permissions: frozenset[str]
    mfa_enrolled: bool
    intake_scope: frozenset[UUID] | None = None
    worker_scope: frozenset[UUID] | None = None

    @property
    def active(self) -> bool:
        return self.status == "active"

    @property
    def can_start_session(self) -> bool:
        return self.active and self.mfa_enrolled

    def to_principal(self) -> StaffPrincipal:
        if not self.can_start_session:
            msg = "staff account is not eligible for a session"
            raise ValueError(msg)
        return StaffPrincipal(
            actor_id=self.staff_id,
            role_name=self.role_name,
            permissions=self.permissions,
            intake_scope=self.intake_scope,
            worker_scope=self.worker_scope,
        )


@dataclass(frozen=True, slots=True)
class StaffDelegation:
    delegation_id: UUID
    grantor_staff_id: UUID
    grantee_staff_id: UUID
    permission_name: str
    scope_kind: str
    scope_id: UUID | None
    active: bool

    def applies_to(self, permission_name: str, scope_kind: str, scope_id: UUID | None) -> bool:
        return (
            self.active
            and self.permission_name == permission_name
            and self.scope_kind == scope_kind
            and self.scope_id == scope_id
        )
