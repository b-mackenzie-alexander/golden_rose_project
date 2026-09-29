from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from golden_rose.persistence.models import (
    staff_account_lifecycle_events,
    staff_accounts,
    staff_permission_grants,
)

StaffAccountStatus = Literal["active", "suspended", "deprovisioned"]


@dataclass(frozen=True, slots=True)
class StaffAccountRecord:
    staff_id: UUID
    provider_subject: str
    display_name: str
    role_name: str
    lifecycle_status: StaffAccountStatus
    mfa_enrolled: bool
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    version: int


def insert_staff_account(
    *,
    session: Session,
    staff_id: UUID,
    provider_subject: str,
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


def get_staff_account_by_id(*, session: Session, staff_id: UUID) -> StaffAccountRecord:
    row = session.execute(
        select(
            staff_accounts.c.staff_id,
            staff_accounts.c.provider_subject,
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
    rows = session.execute(
        select(staff_permission_grants.c.permission_name).where(
            staff_permission_grants.c.staff_id == staff_id,
            staff_permission_grants.c.scope_kind == "global",
            staff_permission_grants.c.revoked_at.is_(None),
        )
    ).scalars()
    return frozenset(rows)


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
