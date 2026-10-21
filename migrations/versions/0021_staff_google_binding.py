"""Separate Google binding proof from access administration."""

import sqlalchemy as sa
from alembic import op

revision = "0021_staff_google_binding"
down_revision = "0020_contact_email_fields"
branch_labels = None
depends_on = None

EVENTS = (
    "created",
    "activated",
    "suspended",
    "deprovisioned",
    "corrected",
    "signin_email_updated",
    "recovery_recorded",
    "sessions_revoked",
    "access_updated",
    "binding_restarted",
    "binding_verified",
)


def upgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM staff_accounts "
            "WHERE lifecycle_status='active' AND provider_subject LIKE 'pending-google-email:%')"
        )
    ):
        raise RuntimeError(
            "active pending identity requires reviewed recovery before binding migration"
        )
    op.execute(
        sa.text("""
        ALTER TABLE staff_accounts
          ADD COLUMN binding_status varchar(32) NOT NULL DEFAULT 'legacy_unverified',
          ADD COLUMN binding_verified_at timestamptz;
        UPDATE staff_accounts SET binding_status='pending'
          WHERE provider_subject LIKE 'pending-google-email:%';
        ALTER TABLE staff_accounts ADD CONSTRAINT ck_staff_binding_proof CHECK (
          (binding_status='pending' AND binding_verified_at IS NULL
            AND provider_subject LIKE 'pending-google-email:%'
            AND provider_email IS NOT NULL AND lifecycle_status<>'active')
          OR (binding_status='legacy_unverified' AND binding_verified_at IS NULL
            AND provider_subject NOT LIKE 'pending-google-email:%')
          OR (binding_status='google_verified' AND binding_verified_at IS NOT NULL
            AND provider_subject NOT LIKE 'pending-google-email:%')
        );
        GRANT UPDATE(binding_status,binding_verified_at) ON staff_accounts TO golden_rose_runtime;
        CREATE TABLE staff_signin_restarts (
          command_id uuid PRIMARY KEY,
          staff_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
          actor_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
          request_fingerprint varchar(64) NOT NULL CHECK(length(request_fingerprint)=64),
          result jsonb NOT NULL CHECK(jsonb_typeof(result)='object')
        );
        ALTER TABLE staff_signin_restarts OWNER TO golden_rose_schema_owner;
        GRANT SELECT,INSERT ON staff_signin_restarts TO golden_rose_runtime;
        ALTER TABLE staff_account_lifecycle_events
          DROP CONSTRAINT IF EXISTS ck_staff_account_lifecycle_events_event_type,
          DROP CONSTRAINT IF EXISTS staff_account_lifecycle_events_event_type_check,
          DROP CONSTRAINT IF EXISTS ck_staff_account_lifecycle_events_version_shape,
          DROP CONSTRAINT IF EXISTS staff_account_lifecycle_events_check;
    """)
    )
    events = ",".join("'staff_account." + name + "'" for name in EVENTS)
    op.execute(
        sa.text(f"""
        ALTER TABLE staff_account_lifecycle_events
          ADD CONSTRAINT ck_staff_account_lifecycle_events_event_type
            CHECK(event_type IN ({events})),
          ADD CONSTRAINT ck_staff_account_lifecycle_events_version_shape CHECK (
            (event_type='staff_account.created' AND previous_status IS NULL
              AND previous_version IS NULL AND new_version=1)
            OR (event_type IN ('staff_account.recovery_recorded','staff_account.sessions_revoked')
              AND previous_status IS NOT NULL AND previous_version IS NOT NULL
              AND previous_status=new_status AND new_version=previous_version)
            OR (event_type NOT IN ('staff_account.created','staff_account.recovery_recorded',
                'staff_account.sessions_revoked') AND previous_status IS NOT NULL
              AND previous_version IS NOT NULL AND new_version=previous_version+1)
          );
    """)
    )


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text("""
        SELECT EXISTS(SELECT 1 FROM staff_signin_restarts)
          OR EXISTS(SELECT 1 FROM staff_accounts WHERE binding_status='google_verified')
          OR EXISTS(SELECT 1 FROM staff_account_lifecycle_events
            WHERE event_type IN ('staff_account.access_updated','staff_account.binding_verified',
                                 'staff_account.binding_restarted'))
    """)
    ):
        raise RuntimeError("staff binding evidence requires a separately reviewed downgrade")
    old_events = ",".join("'staff_account." + name + "'" for name in EVENTS[:8])
    op.execute(
        sa.text(f"""
        DROP TABLE staff_signin_restarts;
        ALTER TABLE staff_accounts DROP CONSTRAINT ck_staff_binding_proof,
          DROP COLUMN binding_status, DROP COLUMN binding_verified_at;
        ALTER TABLE staff_account_lifecycle_events
          DROP CONSTRAINT ck_staff_account_lifecycle_events_event_type,
          DROP CONSTRAINT ck_staff_account_lifecycle_events_version_shape,
          ADD CONSTRAINT ck_staff_account_lifecycle_events_event_type
            CHECK(event_type IN ({old_events})),
          ADD CONSTRAINT ck_staff_account_lifecycle_events_version_shape CHECK (
            (event_type='staff_account.created' AND previous_status IS NULL
              AND previous_version IS NULL AND new_version=1)
            OR (event_type IN ('staff_account.recovery_recorded','staff_account.sessions_revoked')
              AND previous_status IS NOT NULL AND previous_version IS NOT NULL
              AND previous_status=new_status AND new_version=previous_version)
            OR (event_type NOT IN ('staff_account.created','staff_account.recovery_recorded',
                'staff_account.sessions_revoked') AND previous_status IS NOT NULL
              AND previous_version IS NOT NULL AND new_version=previous_version+1)
          );
    """)
    )
