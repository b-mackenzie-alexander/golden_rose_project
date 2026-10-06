from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from golden_rose.database import assume_database_role, create_database_engine

EX_CONFIG = 78
EX_TEMPFAIL = 75
SCHEMA_OWNER_ROLE = "golden_rose_schema_owner"
BOOTSTRAP_REASON = (
    "Operator-approved first staff pilot bootstrap; Google provider subject captured privately."
)
BOOTSTRAP_PERMISSION_NAMES = (
    "canonical:review",
    "employer:draft:create",
    "employer:draft:revise",
    "employer:read",
    "employer_contact:draft:create",
    "employer_contact:read",
    "intake:draft:create",
    "intake:draft:revise",
    "intake:finalize",
    "intake:follow_up",
    "intake:link",
    "intake:read",
    "intake:restricted_history:read",
    "intake:review",
    "shift_need:create",
    "shift_need:read",
    "shift_need:submit_review",
    "staff_account:activate",
    "staff_account:create",
    "staff_account:delegation:grant",
    "staff_account:delegation:revoke",
    "staff_account:deprovision",
    "staff_account:read",
    "staff_account:recovery:record",
    "staff_account:session:revoke",
    "staff_account:suspend",
    "staffing_request:submit_review",
    "worker:read",
    "worker_contact:read",
    "worker_residence:read",
    "worker_residence:write",
    "work_interest:read",
)


class UuidFactory(Protocol):
    def __call__(self) -> UUID: ...


@dataclass(frozen=True, slots=True)
class FirstStaffBootstrapResult:
    created: bool
    staff_id: UUID
    provider_subject_sha256: str
    staff_id_sha256: str
    role_name: str
    lifecycle_status: str
    mfa_enrolled: bool
    version: int
    requested_permission_count: int
    active_permission_count: int
    occurred_at: datetime

    def to_value_safe_dict(self) -> dict[str, object]:
        return {
            "result": "success",
            "created": self.created,
            "provider_subject_sha256": self.provider_subject_sha256,
            "staff_id_sha256": self.staff_id_sha256,
            "role_name": self.role_name,
            "lifecycle_status": self.lifecycle_status,
            "mfa_enrolled": self.mfa_enrolled,
            "version": self.version,
            "requested_permission_count": self.requested_permission_count,
            "active_permission_count": self.active_permission_count,
            "occurred_at": self.occurred_at.isoformat(),
        }


class BootstrapConfigurationError(RuntimeError):
    pass


class BootstrapStateError(RuntimeError):
    pass


def bootstrap_first_staff_account(
    *,
    connection: Connection,
    provider_subject: str,
    display_name: str,
    occurred_at: datetime | None = None,
    uuid_factory: UuidFactory = uuid4,
) -> FirstStaffBootstrapResult:
    provider_subject = _require_provider_subject(provider_subject)
    display_name = _require_text("display_name", display_name, max_length=160)
    occurred_at = occurred_at or datetime.now(UTC)

    existing_count = connection.execute(text("SELECT count(*) FROM staff_accounts")).scalar_one()
    existing = connection.execute(
        text(
            """
            SELECT staff_id, role_name, lifecycle_status, mfa_enrolled, version
            FROM staff_accounts
            WHERE provider_subject=:provider_subject
            FOR UPDATE
            """
        ),
        {"provider_subject": provider_subject},
    ).fetchone()

    created = False
    if existing is None:
        if existing_count:
            raise BootstrapStateError("first staff bootstrap cannot create after accounts exist")
        staff_id = uuid_factory()
        command_id = uuid_factory()
        connection.execute(
            text(
                """
                INSERT INTO staff_accounts (
                    staff_id, provider_subject, display_name, role_name,
                    lifecycle_status, mfa_enrolled, created_at, created_by,
                    updated_at, updated_by, version
                ) VALUES (
                    :staff_id, :provider_subject, :display_name, 'owner',
                    'active', true, :occurred_at, :staff_id,
                    :occurred_at, :staff_id, 1
                )
                """
            ),
            {
                "staff_id": staff_id,
                "provider_subject": provider_subject,
                "display_name": display_name,
                "occurred_at": occurred_at,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO staff_account_lifecycle_events (
                    event_id, command_id, staff_id, actor_id, event_type,
                    previous_status, new_status, previous_version, new_version,
                    occurred_at, reason_text
                ) VALUES (
                    :event_id, :command_id, :staff_id, :staff_id,
                    'staff_account.created', NULL, 'active', NULL, 1,
                    :occurred_at, :reason_text
                )
                """
            ),
            {
                "event_id": uuid_factory(),
                "command_id": command_id,
                "staff_id": staff_id,
                "occurred_at": occurred_at,
                "reason_text": BOOTSTRAP_REASON,
            },
        )
        role_name = "owner"
        lifecycle_status = "active"
        mfa_enrolled = True
        version = 1
        created = True
    else:
        staff_id, role_name, lifecycle_status, mfa_enrolled, version = existing
        if role_name != "owner" or lifecycle_status != "active" or not mfa_enrolled:
            raise BootstrapStateError(
                "existing staff account is not an active owner with MFA enrollment"
            )

    for permission_name in BOOTSTRAP_PERMISSION_NAMES:
        connection.execute(
            text(
                """
                INSERT INTO staff_permission_grants (
                    grant_id, staff_id, permission_name, scope_kind, scope_id,
                    granted_at, granted_by, revoked_at, revoked_by, revocation_reason
                ) VALUES (
                    :grant_id, :staff_id, :permission_name, 'global', NULL,
                    :occurred_at, :staff_id, NULL, NULL, NULL
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "grant_id": uuid_factory(),
                "staff_id": staff_id,
                "permission_name": permission_name,
                "occurred_at": occurred_at,
            },
        )

    active_permission_count = connection.execute(
        text(
            """
            SELECT count(*)
            FROM staff_permission_grants
            WHERE staff_id=:staff_id AND revoked_at IS NULL
            """
        ),
        {"staff_id": staff_id},
    ).scalar_one()
    return FirstStaffBootstrapResult(
        created=created,
        staff_id=staff_id,
        provider_subject_sha256=_sha256(provider_subject),
        staff_id_sha256=_sha256(str(staff_id)),
        role_name=str(role_name),
        lifecycle_status=str(lifecycle_status),
        mfa_enrolled=bool(mfa_enrolled),
        version=int(version),
        requested_permission_count=len(BOOTSTRAP_PERMISSION_NAMES),
        active_permission_count=int(active_permission_count),
        occurred_at=occurred_at,
    )


def main() -> int:
    try:
        provider_subject = _read_env("GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT")
        display_name = _read_env("GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME")
        assumed_role = os.environ.get("GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE", SCHEMA_OWNER_ROLE)
        if assumed_role != SCHEMA_OWNER_ROLE:
            raise BootstrapConfigurationError("bootstrap must assume the schema-owner role")
        engine = create_database_engine()
        with engine.begin() as connection:
            assume_database_role(connection, assumed_role)
            result = bootstrap_first_staff_account(
                connection=connection,
                provider_subject=provider_subject,
                display_name=display_name,
            )
    except BootstrapConfigurationError as exc:
        print(f"bootstrap configuration rejected: {exc}", file=sys.stderr)
        return EX_CONFIG
    except BootstrapStateError as exc:
        print(f"bootstrap state rejected: {exc}", file=sys.stderr)
        return EX_CONFIG
    except SQLAlchemyError:
        print("bootstrap persistence operation failed", file=sys.stderr)
        return EX_TEMPFAIL

    print(json.dumps(result.to_value_safe_dict(), sort_keys=True))
    return 0


def _read_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise BootstrapConfigurationError(f"{name} is required")
    return value


def _require_provider_subject(value: str) -> str:
    provider_subject = _require_text("provider_subject", value, max_length=256)
    if "@" in provider_subject:
        raise BootstrapConfigurationError("provider_subject must be a stable provider subject")
    return provider_subject


def _require_text(name: str, value: str, *, max_length: int) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > max_length:
        raise BootstrapConfigurationError(f"{name} is invalid")
    return normalized


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
