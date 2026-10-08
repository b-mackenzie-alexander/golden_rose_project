from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import Select, insert, or_, select, update
from sqlalchemy.orm import Session

from golden_rose.persistence.models import (
    staff_account_lifecycle_events,
    staff_accounts,
    staff_delegations,
    staff_permission_grants,
)

StaffAccountStatus = Literal["active", "suspended", "deprovisioned"]


@dataclass(frozen=True, slots=True)
class StaffAccountRecord:
    staff_id: UUID
    provider_subject: str
    provider_email: str | None
    display_name: str
    role_name: str
    lifecycle_status: StaffAccountStatus
    mfa_enrolled: bool
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    version: int


@dataclass(frozen=True, slots=True)
class StaffDelegationRecord:
    delegation_id: UUID
    grantor_staff_id: UUID
    grantee_staff_id: UUID
    permission_name: str
    scope_kind: str
    scope_id: UUID | None
    reason_text: str
    starts_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revoked_by: UUID | None
    revocation_reason: str | None


@dataclass(frozen=True, slots=True)
class StaffAccountLifecycleEventRecord:
    event_id: UUID
    command_id: UUID
    staff_id: UUID
    actor_id: UUID
    event_type: str
    previous_status: str | None
    new_status: StaffAccountStatus
    previous_version: int | None
    new_version: int
    occurred_at: datetime
    reason_text: str


def insert_staff_account(
    *,
    session: Session,
    staff_id: UUID,
    provider_subject: str,
    provider_email: str | None,
    display_name: str,
    role_name: str,
    lifecycle_status: StaffAccountStatus,
    mfa_enrolled: bool,
    created_at: datetime,
    actor_id: UUID,
) -> StaffAccountRecord:
    session.execute(
        insert(staff_accounts).values(
            staff_id=staff_id,
            provider_subject=provider_subject,
            provider_email=provider_email,
            display_name=display_name,
            role_name=role_name,
            lifecycle_status=lifecycle_status,
            mfa_enrolled=mfa_enrolled,
            created_at=created_at,
            created_by=actor_id,
            updated_at=created_at,
            updated_by=actor_id,
            version=1,
        )
    )
    return StaffAccountRecord(
        staff_id=staff_id,
        provider_subject=provider_subject,
        provider_email=provider_email,
        display_name=display_name,
        role_name=role_name,
        lifecycle_status=lifecycle_status,
        mfa_enrolled=mfa_enrolled,
        created_at=created_at,
        created_by=actor_id,
        updated_at=created_at,
        updated_by=actor_id,
        version=1,
    )


def get_staff_account_by_id_for_update(*, session: Session, staff_id: UUID) -> StaffAccountRecord:
    row = session.execute(
        select(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        )
        .where(staff_accounts.c.staff_id == staff_id)
        .with_for_update()
    ).one()
    return StaffAccountRecord(*row)


def get_staff_account_by_provider_subject(
    *,
    session: Session,
    provider_subject: str,
) -> StaffAccountRecord:
    row = session.execute(
        select(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        ).where(staff_accounts.c.provider_subject == provider_subject)
    ).one()
    return StaffAccountRecord(*row)


def get_pending_staff_account_by_provider_email_for_update(
    *,
    session: Session,
    provider_email: str,
    pending_subject_prefix: str,
) -> StaffAccountRecord:
    row = session.execute(
        select(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        )
        .where(
            staff_accounts.c.provider_email == provider_email,
            staff_accounts.c.lifecycle_status == "suspended",
            staff_accounts.c.provider_subject.startswith(pending_subject_prefix),
        )
        .with_for_update()
    ).one()
    return StaffAccountRecord(*row)


def get_staff_account_by_id(*, session: Session, staff_id: UUID) -> StaffAccountRecord:
    row = session.execute(
        select(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        ).where(staff_accounts.c.staff_id == staff_id)
    ).one()
    return StaffAccountRecord(*row)


def list_staff_accounts(*, session: Session, limit: int = 50) -> tuple[StaffAccountRecord, ...]:
    rows = session.execute(
        select(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        )
        .order_by(staff_accounts.c.updated_at.desc(), staff_accounts.c.staff_id.asc())
        .limit(limit)
    )
    return tuple(StaffAccountRecord(*row) for row in rows)


def update_staff_account_lifecycle(
    *,
    session: Session,
    staff_id: UUID,
    expected_version: int,
    lifecycle_status: StaffAccountStatus,
    mfa_enrolled: bool,
    updated_at: datetime,
    actor_id: UUID,
) -> StaffAccountRecord:
    row = session.execute(
        update(staff_accounts)
        .where(
            staff_accounts.c.staff_id == staff_id,
            staff_accounts.c.version == expected_version,
        )
        .values(
            lifecycle_status=lifecycle_status,
            mfa_enrolled=mfa_enrolled,
            updated_at=updated_at,
            updated_by=actor_id,
            version=expected_version + 1,
        )
        .returning(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        )
    ).one()
    return StaffAccountRecord(*row)


def update_staff_account_onboarding(
    *,
    session: Session,
    staff_id: UUID,
    expected_version: int,
    provider_subject: str,
    provider_email: str | None,
    display_name: str,
    role_name: str,
    mfa_enrolled: bool,
    updated_at: datetime,
    actor_id: UUID,
) -> StaffAccountRecord:
    row = session.execute(
        update(staff_accounts)
        .where(
            staff_accounts.c.staff_id == staff_id,
            staff_accounts.c.version == expected_version,
        )
        .values(
            provider_subject=provider_subject,
            provider_email=provider_email,
            display_name=display_name,
            role_name=role_name,
            mfa_enrolled=mfa_enrolled,
            updated_at=updated_at,
            updated_by=actor_id,
            version=expected_version + 1,
        )
        .returning(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        )
    ).one()
    return StaffAccountRecord(*row)


def update_staff_account_provider_binding(
    *,
    session: Session,
    staff_id: UUID,
    expected_version: int,
    provider_subject: str,
    mfa_enrolled: bool,
    updated_at: datetime,
) -> StaffAccountRecord:
    row = session.execute(
        update(staff_accounts)
        .where(
            staff_accounts.c.staff_id == staff_id,
            staff_accounts.c.version == expected_version,
        )
        .values(
            provider_subject=provider_subject,
            mfa_enrolled=mfa_enrolled,
            updated_at=updated_at,
            updated_by=staff_id,
            version=expected_version + 1,
        )
        .returning(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
            staff_accounts.c.provider_email,
            staff_accounts.c.display_name,
            staff_accounts.c.role_name,
            staff_accounts.c.lifecycle_status,
            staff_accounts.c.mfa_enrolled,
            staff_accounts.c.created_at,
            staff_accounts.c.created_by,
            staff_accounts.c.updated_at,
            staff_accounts.c.updated_by,
            staff_accounts.c.version,
        )
    ).one()
    return StaffAccountRecord(*row)


def revoke_active_staff_permission_grants(
    *,
    session: Session,
    staff_id: UUID,
    revoked_at: datetime,
    actor_id: UUID,
    reason_text: str,
) -> None:
    session.execute(
        update(staff_permission_grants)
        .where(
            staff_permission_grants.c.staff_id == staff_id,
            staff_permission_grants.c.revoked_at.is_(None),
        )
        .values(
            revoked_at=revoked_at,
            revoked_by=actor_id,
            revocation_reason=reason_text,
        )
    )


def insert_staff_permission_grants(
    *,
    session: Session,
    grants: tuple[tuple[UUID, str], ...],
    staff_id: UUID,
    granted_at: datetime,
    actor_id: UUID,
) -> None:
    if not grants:
        return
    session.execute(
        insert(staff_permission_grants),
        [
            {
                "grant_id": grant_id,
                "staff_id": staff_id,
                "permission_name": permission_name,
                "scope_kind": "global",
                "scope_id": None,
                "granted_at": granted_at,
                "granted_by": actor_id,
            }
            for grant_id, permission_name in grants
        ],
    )


def list_active_staff_permissions(*, session: Session, staff_id: UUID) -> frozenset[str]:
    direct_permissions = session.execute(
        select(staff_permission_grants.c.permission_name).where(
            staff_permission_grants.c.staff_id == staff_id,
            staff_permission_grants.c.scope_kind == "global",
            staff_permission_grants.c.revoked_at.is_(None),
        )
    ).scalars()
    now = datetime.now(UTC)
    delegated_permissions = session.execute(
        select(staff_delegations.c.permission_name).where(
            staff_delegations.c.grantee_staff_id == staff_id,
            staff_delegations.c.scope_kind == "global",
            staff_delegations.c.revoked_at.is_(None),
            staff_delegations.c.starts_at <= now,
            staff_delegations.c.expires_at > now,
        )
    ).scalars()
    return frozenset(direct_permissions) | frozenset(delegated_permissions)


def insert_staff_delegation(
    *,
    session: Session,
    delegation_id: UUID,
    grantor_staff_id: UUID,
    grantee_staff_id: UUID,
    permission_name: str,
    scope_kind: str,
    scope_id: UUID | None,
    reason_text: str,
    starts_at: datetime,
    expires_at: datetime,
) -> StaffDelegationRecord:
    session.execute(
        insert(staff_delegations).values(
            delegation_id=delegation_id,
            grantor_staff_id=grantor_staff_id,
            grantee_staff_id=grantee_staff_id,
            permission_name=permission_name,
            scope_kind=scope_kind,
            scope_id=scope_id,
            reason_text=reason_text,
            starts_at=starts_at,
            expires_at=expires_at,
        )
    )
    return StaffDelegationRecord(
        delegation_id=delegation_id,
        grantor_staff_id=grantor_staff_id,
        grantee_staff_id=grantee_staff_id,
        permission_name=permission_name,
        scope_kind=scope_kind,
        scope_id=scope_id,
        reason_text=reason_text,
        starts_at=starts_at,
        expires_at=expires_at,
        revoked_at=None,
        revoked_by=None,
        revocation_reason=None,
    )


def _delegation_select() -> Select[
    tuple[
        UUID,
        UUID,
        UUID,
        str,
        str,
        UUID | None,
        str,
        datetime,
        datetime,
        datetime | None,
        UUID | None,
        str | None,
    ]
]:
    return select(
        staff_delegations.c.delegation_id,
        staff_delegations.c.grantor_staff_id,
        staff_delegations.c.grantee_staff_id,
        staff_delegations.c.permission_name,
        staff_delegations.c.scope_kind,
        staff_delegations.c.scope_id,
        staff_delegations.c.reason_text,
        staff_delegations.c.starts_at,
        staff_delegations.c.expires_at,
        staff_delegations.c.revoked_at,
        staff_delegations.c.revoked_by,
        staff_delegations.c.revocation_reason,
    )


def get_staff_delegation_by_id(*, session: Session, delegation_id: UUID) -> StaffDelegationRecord:
    row = session.execute(
        _delegation_select().where(staff_delegations.c.delegation_id == delegation_id)
    ).one()
    return StaffDelegationRecord(*row)


def list_staff_delegations(
    *,
    session: Session,
    staff_id: UUID,
    limit: int = 50,
) -> tuple[StaffDelegationRecord, ...]:
    rows = session.execute(
        _delegation_select()
        .where(
            or_(
                staff_delegations.c.grantee_staff_id == staff_id,
                staff_delegations.c.grantor_staff_id == staff_id,
            )
        )
        .order_by(staff_delegations.c.starts_at.desc(), staff_delegations.c.delegation_id.asc())
        .limit(limit)
    )
    return tuple(StaffDelegationRecord(*row) for row in rows)


def list_staff_account_lifecycle_events(
    *,
    session: Session,
    staff_id: UUID,
    limit: int = 50,
) -> tuple[StaffAccountLifecycleEventRecord, ...]:
    rows = session.execute(
        select(
            staff_account_lifecycle_events.c.event_id,
            staff_account_lifecycle_events.c.command_id,
            staff_account_lifecycle_events.c.staff_id,
            staff_account_lifecycle_events.c.actor_id,
            staff_account_lifecycle_events.c.event_type,
            staff_account_lifecycle_events.c.previous_status,
            staff_account_lifecycle_events.c.new_status,
            staff_account_lifecycle_events.c.previous_version,
            staff_account_lifecycle_events.c.new_version,
            staff_account_lifecycle_events.c.occurred_at,
            staff_account_lifecycle_events.c.reason_text,
        )
        .where(staff_account_lifecycle_events.c.staff_id == staff_id)
        .order_by(
            staff_account_lifecycle_events.c.occurred_at.desc(),
            staff_account_lifecycle_events.c.event_id.asc(),
        )
        .limit(limit)
    )
    return tuple(StaffAccountLifecycleEventRecord(*row) for row in rows)


def revoke_staff_delegation(
    *,
    session: Session,
    delegation_id: UUID,
    grantee_staff_id: UUID,
    revoked_at: datetime,
    revoked_by: UUID,
    revocation_reason: str,
) -> StaffDelegationRecord:
    row = session.execute(
        update(staff_delegations)
        .where(
            staff_delegations.c.delegation_id == delegation_id,
            staff_delegations.c.grantee_staff_id == grantee_staff_id,
            staff_delegations.c.revoked_at.is_(None),
        )
        .values(
            revoked_at=revoked_at,
            revoked_by=revoked_by,
            revocation_reason=revocation_reason,
        )
        .returning(
            staff_delegations.c.delegation_id,
            staff_delegations.c.grantor_staff_id,
            staff_delegations.c.grantee_staff_id,
            staff_delegations.c.permission_name,
            staff_delegations.c.scope_kind,
            staff_delegations.c.scope_id,
            staff_delegations.c.reason_text,
            staff_delegations.c.starts_at,
            staff_delegations.c.expires_at,
            staff_delegations.c.revoked_at,
            staff_delegations.c.revoked_by,
            staff_delegations.c.revocation_reason,
        )
    ).one()
    return StaffDelegationRecord(*row)


def insert_lifecycle_event(
    *,
    session: Session,
    event_id: UUID,
    command_id: UUID,
    staff_id: UUID,
    actor_id: UUID,
    event_type: str,
    previous_status: str | None,
    new_status: StaffAccountStatus,
    previous_version: int | None,
    new_version: int,
    occurred_at: datetime,
    reason_text: str,
) -> None:
    session.execute(
        insert(staff_account_lifecycle_events).values(
            event_id=event_id,
            command_id=command_id,
            staff_id=staff_id,
            actor_id=actor_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            previous_version=previous_version,
            new_version=new_version,
            occurred_at=occurred_at,
            reason_text=reason_text,
        )
    )
