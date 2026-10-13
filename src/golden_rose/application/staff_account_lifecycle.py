import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from golden_rose.application.errors import SafePersistenceError
from golden_rose.auth.permissions import (
    can_activate_staff_account,
    can_create_staff_account,
    can_deprovision_staff_account,
    can_record_staff_account_recovery,
    can_revoke_staff_account_sessions,
    can_suspend_staff_account,
)
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.auth.staff_accounts import STAFF_ACCOUNT_ROLES, StaffAccount, StaffIdentityClaims
from golden_rose.auth.staff_accounts import StaffAccountRole as AuthStaffAccountRole
from golden_rose.clock import Clock
from golden_rose.identifiers import IdentifierFactory
from golden_rose.persistence.staff_accounts import (
    StaffAccountRecord,
    StaffAccountStatus,
    get_pending_staff_account_by_provider_email_for_update,
    get_staff_account_by_id_for_update,
    get_staff_account_by_provider_email,
    get_staff_account_by_provider_subject,
    insert_lifecycle_event,
    insert_staff_account,
    insert_staff_permission_grants,
    list_active_staff_permissions,
    revoke_active_staff_permission_grants,
    update_staff_account_lifecycle,
    update_staff_account_onboarding,
    update_staff_account_provider_binding,
    update_staff_account_signin_email,
)

PENDING_PROVIDER_SUBJECT_PREFIX = "pending-google-email:"


@dataclass(frozen=True, slots=True)
class StaffAccountLifecycleResult:
    account: StaffAccountRecord
    event_type: str
    result_version: int


class StaffAccountLifecycleError(RuntimeError):
    pass


class StaffAccountNotFoundError(StaffAccountLifecycleError):
    pass


class StaffAccountVersionConflictError(StaffAccountLifecycleError):
    pass


def create_staff_account(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    provider_subject: str,
    provider_email: str | None,
    display_name: str,
    role_name: str,
    permission_names: frozenset[str],
    mfa_enrolled: bool,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_create_staff_account(principal):
        msg = "principal lacks staff_account:create"
        raise PermissionError(msg)

    provider_email = _normalize_provider_email(provider_email)
    provider_subject = _normalize_provider_subject(provider_subject, provider_email)
    display_name = _require_text("display_name", display_name, 160)
    reason_text = _require_text("reason_text", reason_text, 512)
    permissions = _validate_permission_names(permission_names)
    _validate_role_permissions(role_name=role_name, permissions=permissions)
    _deny_self_escalation(
        principal=principal,
        target_staff_id=staff_id,
        requested_permissions=permissions,
    )
    if role_name not in STAFF_ACCOUNT_ROLES:
        raise StaffAccountLifecycleError("invalid staff role")

    now = clock.now()
    try:
        account = insert_staff_account(
            session=session,
            staff_id=staff_id,
            provider_subject=provider_subject,
            provider_email=provider_email,
            display_name=display_name,
            role_name=role_name,
            lifecycle_status="suspended",
            mfa_enrolled=mfa_enrolled,
            created_at=now,
            actor_id=principal.actor_id,
        )
        grants = tuple((identifiers.new_uuid4(), item) for item in sorted(permissions))
        insert_staff_permission_grants(
            session=session,
            grants=grants,
            staff_id=staff_id,
            granted_at=now,
            actor_id=principal.actor_id,
        )
        insert_lifecycle_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            staff_id=staff_id,
            actor_id=principal.actor_id,
            event_type="staff_account.created",
            previous_status=None,
            new_status=account.lifecycle_status,
            previous_version=None,
            new_version=account.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise

    return StaffAccountLifecycleResult(
        account=account,
        event_type="staff_account.created",
        result_version=account.version,
    )


def correct_staff_account_onboarding(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    provider_subject: str,
    provider_email: str | None,
    display_name: str,
    role_name: str,
    permission_names: frozenset[str],
    mfa_enrolled: bool,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_create_staff_account(principal):
        msg = "principal lacks staff_account:create"
        raise PermissionError(msg)

    provider_email = _normalize_provider_email(provider_email)
    provider_subject = _normalize_provider_subject(provider_subject, provider_email)
    display_name = _require_text("display_name", display_name, 160)
    reason_text = _require_text("reason_text", reason_text, 512)
    permissions = _validate_permission_names(permission_names)
    _validate_role_permissions(role_name=role_name, permissions=permissions)
    _deny_self_escalation(
        principal=principal,
        target_staff_id=staff_id,
        requested_permissions=permissions,
    )
    if role_name not in STAFF_ACCOUNT_ROLES:
        raise StaffAccountLifecycleError("invalid staff role")
    if staff_id == principal.actor_id:
        raise StaffAccountLifecycleError("staff account cannot correct itself")

    now = clock.now()
    try:
        existing = get_staff_account_by_id_for_update(session=session, staff_id=staff_id)
        if existing.version != expected_version:
            raise StaffAccountVersionConflictError("staff account version conflict")
        if existing.lifecycle_status not in {"active", "suspended"}:
            raise StaffAccountLifecycleError(
                "only active or suspended staff accounts can be corrected"
            )
        account = update_staff_account_onboarding(
            session=session,
            staff_id=staff_id,
            expected_version=expected_version,
            provider_subject=provider_subject,
            provider_email=provider_email,
            display_name=display_name,
            role_name=role_name,
            mfa_enrolled=mfa_enrolled,
            updated_at=now,
            actor_id=principal.actor_id,
        )
        revoke_active_staff_permission_grants(
            session=session,
            staff_id=staff_id,
            revoked_at=now,
            actor_id=principal.actor_id,
            reason_text=reason_text,
        )
        grants = tuple((identifiers.new_uuid4(), item) for item in sorted(permissions))
        insert_staff_permission_grants(
            session=session,
            grants=grants,
            staff_id=staff_id,
            granted_at=now,
            actor_id=principal.actor_id,
        )
        insert_lifecycle_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            staff_id=staff_id,
            actor_id=principal.actor_id,
            event_type="staff_account.corrected",
            previous_status=existing.lifecycle_status,
            new_status=account.lifecycle_status,
            previous_version=existing.version,
            new_version=account.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except NoResultFound as exc:
        session.rollback()
        raise StaffAccountNotFoundError("staff account not found") from exc
    except StaffAccountVersionConflictError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise

    return StaffAccountLifecycleResult(
        account=account,
        event_type="staff_account.corrected",
        result_version=account.version,
    )


def update_staff_account_google_email(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    provider_email: str,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_create_staff_account(principal):
        msg = "principal lacks staff_account:create"
        raise PermissionError(msg)

    normalized_email = _normalize_provider_email(provider_email)
    if normalized_email is None:
        raise StaffAccountLifecycleError("staff account requires provider_email")
    reason_text = _require_text("reason_text", reason_text, 512)
    now = clock.now()
    try:
        existing = get_staff_account_by_id_for_update(session=session, staff_id=staff_id)
        if existing.version != expected_version:
            raise StaffAccountVersionConflictError("staff account version conflict")
        if existing.lifecycle_status == "deprovisioned":
            raise StaffAccountLifecycleError("deprovisioned staff account cannot update sign-in")
        if existing.provider_email == normalized_email:
            raise StaffAccountLifecycleError("staff account email update requires a change")
        duplicate = get_staff_account_by_provider_email(
            session=session,
            provider_email=normalized_email,
        )
        if duplicate is not None and duplicate.staff_id != staff_id:
            raise StaffAccountLifecycleError("staff account email is already assigned")
        reset_binding = existing.provider_email is not None or _is_pending_provider_subject(
            existing.provider_subject
        )
        if reset_binding and staff_id == principal.actor_id:
            raise StaffAccountLifecycleError("staff account cannot reset its own sign-in binding")
        next_subject = (
            _normalize_provider_subject("", normalized_email)
            if reset_binding
            else existing.provider_subject
        )
        next_status = "suspended" if reset_binding else existing.lifecycle_status
        next_mfa = False if reset_binding else existing.mfa_enrolled
        account = update_staff_account_signin_email(
            session=session,
            staff_id=staff_id,
            expected_version=expected_version,
            provider_subject=next_subject,
            provider_email=normalized_email,
            lifecycle_status=cast(StaffAccountStatus, next_status),
            mfa_enrolled=next_mfa,
            updated_at=now,
            actor_id=principal.actor_id,
        )
        insert_lifecycle_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            staff_id=staff_id,
            actor_id=principal.actor_id,
            event_type="staff_account.signin_email_updated",
            previous_status=existing.lifecycle_status,
            new_status=account.lifecycle_status,
            previous_version=existing.version,
            new_version=account.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except NoResultFound as exc:
        session.rollback()
        raise StaffAccountNotFoundError("staff account not found") from exc
    except StaffAccountVersionConflictError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise

    return StaffAccountLifecycleResult(
        account=account,
        event_type="staff_account.signin_email_updated",
        result_version=account.version,
    )


def activate_staff_account(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    mfa_enrolled: bool,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_activate_staff_account(principal):
        msg = "principal lacks staff_account:activate"
        raise PermissionError(msg)
    if not mfa_enrolled:
        raise StaffAccountLifecycleError("active staff account requires mfa enrollment")
    return _transition_staff_account(
        session=session,
        principal=principal,
        command_id=command_id,
        staff_id=staff_id,
        expected_version=expected_version,
        new_status="active",
        mfa_enrolled=True,
        clock=clock,
        identifiers=identifiers,
        reason_text=reason_text,
        event_type="staff_account.activated",
    )


def suspend_staff_account(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_suspend_staff_account(principal):
        msg = "principal lacks staff_account:suspend"
        raise PermissionError(msg)
    if staff_id == principal.actor_id:
        raise StaffAccountLifecycleError("staff account cannot suspend itself")
    return _transition_staff_account(
        session=session,
        principal=principal,
        command_id=command_id,
        staff_id=staff_id,
        expected_version=expected_version,
        new_status="suspended",
        mfa_enrolled=False,
        clock=clock,
        identifiers=identifiers,
        reason_text=reason_text,
        event_type="staff_account.suspended",
    )


def deprovision_staff_account(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_deprovision_staff_account(principal):
        msg = "principal lacks staff_account:deprovision"
        raise PermissionError(msg)
    if staff_id == principal.actor_id:
        raise StaffAccountLifecycleError("staff account cannot deprovision itself")
    return _transition_staff_account(
        session=session,
        principal=principal,
        command_id=command_id,
        staff_id=staff_id,
        expected_version=expected_version,
        new_status="deprovisioned",
        mfa_enrolled=False,
        clock=clock,
        identifiers=identifiers,
        reason_text=reason_text,
        event_type="staff_account.deprovisioned",
    )


def record_staff_account_recovery_evidence(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_record_staff_account_recovery(principal):
        msg = "principal lacks staff_account:recovery:record"
        raise PermissionError(msg)
    return _record_staff_account_evidence(
        session=session,
        principal=principal,
        command_id=command_id,
        staff_id=staff_id,
        expected_version=expected_version,
        clock=clock,
        identifiers=identifiers,
        reason_text=reason_text,
        event_type="staff_account.recovery_recorded",
        allow_deprovisioned=False,
    )


def record_staff_account_session_revocation_evidence(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
) -> StaffAccountLifecycleResult:
    if not can_revoke_staff_account_sessions(principal):
        msg = "principal lacks staff_account:session:revoke"
        raise PermissionError(msg)
    return _record_staff_account_evidence(
        session=session,
        principal=principal,
        command_id=command_id,
        staff_id=staff_id,
        expected_version=expected_version,
        clock=clock,
        identifiers=identifiers,
        reason_text=reason_text,
        event_type="staff_account.sessions_revoked",
        allow_deprovisioned=True,
    )


def resolve_staff_principal_from_claims(
    *,
    session: Session,
    claims: StaffIdentityClaims,
) -> StaffPrincipal:
    try:
        account = get_staff_account_by_provider_subject(
            session=session,
            provider_subject=_require_text("provider_subject", claims.provider_subject, 256),
        )
    except NoResultFound as exc:
        if claims.provider_email is None:
            raise StaffAccountNotFoundError("staff account not found") from exc
        account = _bind_pending_google_email_account(session=session, claims=claims)
    permissions = list_active_staff_permissions(session=session, staff_id=account.staff_id)
    return StaffAccount(
        staff_id=account.staff_id,
        provider_subject=account.provider_subject,
        display_name=account.display_name,
        role_name=cast(AuthStaffAccountRole, account.role_name),
        status=account.lifecycle_status,
        permissions=permissions,
        mfa_enrolled=account.mfa_enrolled,
    ).to_principal()


def _bind_pending_google_email_account(
    *,
    session: Session,
    claims: StaffIdentityClaims,
) -> StaffAccountRecord:
    provider_email = _normalize_provider_email(claims.provider_email)
    if provider_email is None:
        raise StaffAccountNotFoundError("staff account not found")
    provider_subject = _require_text("provider_subject", claims.provider_subject, 256)
    now = datetime.now(UTC)
    try:
        pending = get_pending_staff_account_by_provider_email_for_update(
            session=session,
            provider_email=provider_email,
            pending_subject_prefix=PENDING_PROVIDER_SUBJECT_PREFIX,
        )
        updated = update_staff_account_provider_binding(
            session=session,
            staff_id=pending.staff_id,
            expected_version=pending.version,
            provider_subject=provider_subject,
            mfa_enrolled=pending.mfa_enrolled or claims.mfa_verified,
            updated_at=now,
        )
        insert_lifecycle_event(
            session=session,
            event_id=uuid4(),
            command_id=uuid4(),
            staff_id=pending.staff_id,
            actor_id=pending.staff_id,
            event_type="staff_account.corrected",
            previous_status=pending.lifecycle_status,
            new_status=updated.lifecycle_status,
            previous_version=pending.version,
            new_version=updated.version,
            occurred_at=now,
            reason_text="Verified Google sign-in bound the pending staff account email.",
        )
        session.commit()
    except NoResultFound as exc:
        session.rollback()
        raise StaffAccountNotFoundError("staff account not found") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return updated


def _record_staff_account_evidence(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
    event_type: str,
    allow_deprovisioned: bool,
) -> StaffAccountLifecycleResult:
    reason_text = _require_text("reason_text", reason_text, 512)
    now = clock.now()
    try:
        try:
            current = get_staff_account_by_id_for_update(session=session, staff_id=staff_id)
        except NoResultFound as exc:
            raise StaffAccountNotFoundError("staff account not found") from exc
        if current.version != expected_version:
            raise StaffAccountVersionConflictError("staff account version conflict")
        if current.lifecycle_status == "deprovisioned" and not allow_deprovisioned:
            raise StaffAccountLifecycleError("deprovisioned staff account cannot be recovered")
        insert_lifecycle_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            staff_id=staff_id,
            actor_id=principal.actor_id,
            event_type=event_type,
            previous_status=current.lifecycle_status,
            new_status=current.lifecycle_status,
            previous_version=current.version,
            new_version=current.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return StaffAccountLifecycleResult(
        account=current,
        event_type=event_type,
        result_version=current.version,
    )


def _transition_staff_account(
    *,
    session: Session,
    principal: StaffPrincipal,
    command_id: UUID,
    staff_id: UUID,
    expected_version: int,
    new_status: str,
    mfa_enrolled: bool,
    clock: Clock,
    identifiers: IdentifierFactory,
    reason_text: str,
    event_type: str,
) -> StaffAccountLifecycleResult:
    reason_text = _require_text("reason_text", reason_text, 512)
    now = clock.now()
    try:
        try:
            current = get_staff_account_by_id_for_update(session=session, staff_id=staff_id)
        except NoResultFound as exc:
            raise StaffAccountNotFoundError("staff account not found") from exc
        if current.version != expected_version:
            raise StaffAccountVersionConflictError("staff account version conflict")
        if current.lifecycle_status == "deprovisioned" and new_status != "deprovisioned":
            raise StaffAccountLifecycleError("deprovisioned staff account cannot be reactivated")
        if event_type == "staff_account.activated" and _is_pending_provider_subject(
            current.provider_subject
        ):
            raise StaffAccountLifecycleError(
                "staff account requires verified Google sign-in binding"
            )
        if current.lifecycle_status == new_status and current.mfa_enrolled == mfa_enrolled:
            raise StaffAccountLifecycleError("staff account transition requires a change")
        updated = update_staff_account_lifecycle(
            session=session,
            staff_id=staff_id,
            expected_version=expected_version,
            lifecycle_status=cast(StaffAccountStatus, new_status),
            mfa_enrolled=mfa_enrolled,
            updated_at=now,
            actor_id=principal.actor_id,
        )
        insert_lifecycle_event(
            session=session,
            event_id=identifiers.new_uuid4(),
            command_id=command_id,
            staff_id=staff_id,
            actor_id=principal.actor_id,
            event_type=event_type,
            previous_status=current.lifecycle_status,
            new_status=updated.lifecycle_status,
            previous_version=current.version,
            new_version=updated.version,
            occurred_at=now,
            reason_text=reason_text,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise SafePersistenceError("persistence operation failed") from exc
    except Exception:
        session.rollback()
        raise
    return StaffAccountLifecycleResult(
        account=updated,
        event_type=event_type,
        result_version=updated.version,
    )


def _require_text(field: str, value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > max_length:
        raise StaffAccountLifecycleError(f"invalid {field}")
    return normalized


def _normalize_provider_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if (
        not normalized
        or len(normalized) > 320
        or normalized.count("@") != 1
        or any(ch.isspace() for ch in normalized)
    ):
        raise StaffAccountLifecycleError("invalid provider_email")
    local, domain = normalized.split("@", 1)
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise StaffAccountLifecycleError("invalid provider_email")
    return normalized


def _normalize_provider_subject(provider_subject: str, provider_email: str | None) -> str:
    if provider_subject.strip():
        return _require_text("provider_subject", provider_subject, 256)
    if provider_email is None:
        raise StaffAccountLifecycleError("staff account requires provider subject or email")
    digest = hashlib.sha256(provider_email.encode("utf-8")).hexdigest()
    return PENDING_PROVIDER_SUBJECT_PREFIX + digest


def _is_pending_provider_subject(provider_subject: str) -> bool:
    return provider_subject.startswith(PENDING_PROVIDER_SUBJECT_PREFIX)


def _validate_permission_names(permission_names: frozenset[str]) -> frozenset[str]:
    if not permission_names:
        raise StaffAccountLifecycleError("staff account requires named permissions")
    normalized = frozenset(_require_text("permission_name", item, 120) for item in permission_names)
    if len(normalized) != len(permission_names):
        raise StaffAccountLifecycleError("duplicate staff account permission")
    return normalized


def _validate_role_permissions(*, role_name: str, permissions: frozenset[str]) -> None:
    if role_name == "platform_administrator" and any(
        _is_operational_data_permission(permission) for permission in permissions
    ):
        raise StaffAccountLifecycleError("platform administrator cannot receive operational data")


def _deny_self_escalation(
    *,
    principal: StaffPrincipal,
    target_staff_id: UUID,
    requested_permissions: frozenset[str],
) -> None:
    if target_staff_id == principal.actor_id and not requested_permissions <= principal.permissions:
        raise StaffAccountLifecycleError("staff account cannot grant itself new permissions")


def _is_operational_data_permission(permission: str) -> bool:
    return permission.startswith(
        (
            "employer",
            "employer_contact",
            "intake",
            "worker",
            "worker_residence",
            "party_address",
            "worksite_address",
            "work_interest",
            "canonical",
            "calendar_import",
        )
    )
