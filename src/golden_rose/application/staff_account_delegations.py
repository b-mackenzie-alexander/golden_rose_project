from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.permissions import (
    can_grant_staff_account_delegation,
    can_revoke_staff_account_delegation,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.clock import Clock
from golden_rose.persistence.staff_accounts import (
    StaffDelegationRecord,
    get_staff_account_by_id,
    get_staff_delegation_by_id,
    insert_staff_delegation,
    list_staff_delegations,
    revoke_staff_delegation,
)


@dataclass(frozen=True, slots=True)
class StaffDelegationResult:
    delegation: StaffDelegationRecord
    event_type: str
    result_version: int


class StaffDelegationError(RuntimeError):
    pass


class StaffDelegationNotFoundError(StaffDelegationError):
    pass


class StaffDelegationConflictError(StaffDelegationError):
    pass


class StaffDelegationExpiryError(StaffDelegationError):
    pass


class StaffDelegationPermissionUnavailableError(StaffDelegationError):
    pass


class StaffDelegationSelfGrantError(StaffDelegationError):
    pass


class StaffDelegationTargetUnavailableError(StaffDelegationError):
    pass


def list_delegations_for_staff(
    *,
    session: Session,
    principal: StaffPrincipal,
    staff_id: UUID,
) -> tuple[StaffDelegationRecord, ...]:
    if staff_id != principal.actor_id and not can_grant_staff_account_delegation(principal):
        msg = "principal lacks staff_account:delegation:grant"
        raise PermissionError(msg)
    try:
        get_staff_account_by_id(session=session, staff_id=staff_id)
        return list_staff_delegations(session=session, staff_id=staff_id)
    except NoResultFound as exc:
        raise StaffDelegationNotFoundError("staff account not found") from exc
    except SQLAlchemyError as exc:
        raise SafePersistenceError("persistence operation failed") from exc


def grant_staff_delegation(
    *,
    session: Session,
    principal: StaffPrincipal,
    delegation_id: UUID,
    grantee_staff_id: UUID,
    permission_name: str,
    scope_kind: str,
    expires_at: datetime,
    clock: Clock,
    reason_text: str,
) -> StaffDelegationResult:
    if not can_grant_staff_account_delegation(principal):
        msg = "principal lacks staff_account:delegation:grant"
        raise PermissionError(msg)
    permission_name = _require_text("permission_name", permission_name, 120)
    scope_kind = _require_text("scope_kind", scope_kind, 40)
    reason_text = _require_text("reason_text", reason_text, 512)
    if scope_kind != "global":
        raise StaffDelegationError("only global staff delegations are supported")
    if grantee_staff_id == principal.actor_id:
        raise StaffDelegationSelfGrantError("staff account cannot delegate to itself")
    if permission_name not in principal.permissions:
        raise StaffDelegationPermissionUnavailableError(
            "staff account cannot delegate permission it does not hold"
        )
    now = clock.now()
    if expires_at <= now:
        raise StaffDelegationExpiryError("staff delegation must expire in the future")
    if expires_at > now + timedelta(days=366):
        raise StaffDelegationExpiryError("staff delegation duration is too long")
    try:
        try:
            target = get_staff_account_by_id(session=session, staff_id=grantee_staff_id)
        except NoResultFound as exc:
            raise StaffDelegationNotFoundError("staff account not found") from exc
        if target.lifecycle_status == "deprovisioned":
            raise StaffDelegationTargetUnavailableError(
                "deprovisioned staff account cannot receive delegation"
            )
        delegation = insert_staff_delegation(
            session=session,
            delegation_id=delegation_id,
            grantor_staff_id=principal.actor_id,
            grantee_staff_id=grantee_staff_id,
            permission_name=permission_name,
            scope_kind=scope_kind,
            scope_id=None,
            reason_text=reason_text,
            starts_at=now,
            expires_at=expires_at,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return StaffDelegationResult(
        delegation=delegation,
        event_type="staff_delegation.granted",
        result_version=1,
    )


def revoke_staff_account_delegation(
    *,
    session: Session,
    principal: StaffPrincipal,
    delegation_id: UUID,
    grantee_staff_id: UUID,
    clock: Clock,
    reason_text: str,
) -> StaffDelegationResult:
    if not can_revoke_staff_account_delegation(principal):
        msg = "principal lacks staff_account:delegation:revoke"
        raise PermissionError(msg)
    reason_text = _require_text("reason_text", reason_text, 512)
    now = clock.now()
    try:
        try:
            delegation = get_staff_delegation_by_id(session=session, delegation_id=delegation_id)
        except NoResultFound as exc:
            raise StaffDelegationNotFoundError("staff delegation not found") from exc
        if delegation.grantee_staff_id != grantee_staff_id:
            raise StaffDelegationNotFoundError("staff delegation not found")
        if delegation.revoked_at is not None:
            session.commit()
            return StaffDelegationResult(
                delegation=delegation,
                event_type="staff_delegation.revoked",
                result_version=1,
            )
        revoked = revoke_staff_delegation(
            session=session,
            delegation_id=delegation_id,
            grantee_staff_id=grantee_staff_id,
            revoked_at=now,
            revoked_by=principal.actor_id,
            revocation_reason=reason_text,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return StaffDelegationResult(
        delegation=revoked,
        event_type="staff_delegation.revoked",
        result_version=1,
    )


def _require_text(field: str, value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > max_length:
        raise StaffDelegationError(f"invalid {field}")
    return normalized
