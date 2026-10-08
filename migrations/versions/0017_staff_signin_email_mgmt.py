# ruff: noqa: E501
"""Allow staff Google sign-in email management events."""

import sqlalchemy as sa
from alembic import op

revision = "0017_staff_signin_email_mgmt"
down_revision = "0016_staff_google_email"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    ALTER TABLE staff_account_lifecycle_events
      DROP CONSTRAINT IF EXISTS ck_staff_account_lifecycle_events_event_type,
      DROP CONSTRAINT IF EXISTS staff_account_lifecycle_events_event_type_check,
      DROP CONSTRAINT IF EXISTS ck_staff_account_lifecycle_events_version_shape,
      DROP CONSTRAINT IF EXISTS staff_account_lifecycle_events_check;
    ALTER TABLE staff_account_lifecycle_events
      ADD CONSTRAINT ck_staff_account_lifecycle_events_event_type
        CHECK(event_type IN (
          'staff_account.created',
          'staff_account.activated',
          'staff_account.suspended',
          'staff_account.deprovisioned',
          'staff_account.corrected',
          'staff_account.signin_email_updated',
          'staff_account.recovery_recorded',
          'staff_account.sessions_revoked'
        )),
      ADD CONSTRAINT ck_staff_account_lifecycle_events_version_shape
        CHECK(
          (
            event_type='staff_account.created'
            AND previous_status IS NULL
            AND previous_version IS NULL
            AND new_version=1
          )
          OR
          (
            event_type IN (
              'staff_account.activated',
              'staff_account.suspended',
              'staff_account.deprovisioned',
              'staff_account.corrected',
              'staff_account.signin_email_updated'
            )
            AND previous_status IS NOT NULL
            AND previous_version IS NOT NULL
            AND new_version=previous_version+1
          )
          OR
          (
            event_type IN (
              'staff_account.recovery_recorded',
              'staff_account.sessions_revoked'
            )
            AND previous_status IS NOT NULL
            AND previous_status=new_status
            AND previous_version IS NOT NULL
            AND new_version=previous_version
          )
        );
    """)


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            """
            SELECT EXISTS(
              SELECT 1 FROM staff_account_lifecycle_events
              WHERE event_type = 'staff_account.signin_email_updated'
            )
            """
        )
    ):
        raise RuntimeError("staff account sign-in email data blocks downgrade before DDL")
    execute("""
    ALTER TABLE staff_account_lifecycle_events
      DROP CONSTRAINT IF EXISTS ck_staff_account_lifecycle_events_event_type,
      DROP CONSTRAINT IF EXISTS staff_account_lifecycle_events_event_type_check,
      DROP CONSTRAINT IF EXISTS ck_staff_account_lifecycle_events_version_shape,
      DROP CONSTRAINT IF EXISTS staff_account_lifecycle_events_check;
    ALTER TABLE staff_account_lifecycle_events
      ADD CONSTRAINT ck_staff_account_lifecycle_events_event_type
        CHECK(event_type IN (
          'staff_account.created',
          'staff_account.activated',
          'staff_account.suspended',
          'staff_account.deprovisioned',
          'staff_account.corrected',
          'staff_account.recovery_recorded',
          'staff_account.sessions_revoked'
        )),
      ADD CONSTRAINT ck_staff_account_lifecycle_events_version_shape
        CHECK(
          (
            event_type='staff_account.created'
            AND previous_status IS NULL
            AND previous_version IS NULL
            AND new_version=1
          )
          OR
          (
            event_type IN (
              'staff_account.activated',
              'staff_account.suspended',
              'staff_account.deprovisioned',
              'staff_account.corrected'
            )
            AND previous_status IS NOT NULL
            AND previous_version IS NOT NULL
            AND new_version=previous_version+1
          )
          OR
          (
            event_type IN (
              'staff_account.recovery_recorded',
              'staff_account.sessions_revoked'
            )
            AND previous_status IS NOT NULL
            AND previous_status=new_status
            AND previous_version IS NOT NULL
            AND new_version=previous_version
          )
        );
    """)
