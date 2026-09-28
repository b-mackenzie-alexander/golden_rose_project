# ruff: noqa: E501
"""Add staff account lifecycle evidence and write grants."""

import sqlalchemy as sa
from alembic import op

revision = "0011_staff_account_lifecycle"
down_revision = "0010_staff_accounts"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    CREATE TABLE staff_account_lifecycle_events (
      event_id uuid PRIMARY KEY,
      command_id uuid NOT NULL UNIQUE,
      staff_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
      actor_id uuid NOT NULL,
      event_type varchar(64) NOT NULL CHECK(event_type IN (
        'staff_account.created','staff_account.activated','staff_account.suspended','staff_account.deprovisioned'
      )),
      previous_status varchar(32) CHECK(previous_status IS NULL OR previous_status IN ('active','suspended','deprovisioned')),
      new_status varchar(32) NOT NULL CHECK(new_status IN ('active','suspended','deprovisioned')),
      previous_version integer CHECK(previous_version IS NULL OR previous_version>=1),
      new_version integer NOT NULL CHECK(new_version>=1),
      occurred_at timestamptz NOT NULL,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text)<>''),
      CHECK(
        (event_type='staff_account.created' AND previous_status IS NULL AND previous_version IS NULL AND new_version=1)
        OR
        (event_type<>'staff_account.created' AND previous_status IS NOT NULL AND previous_version IS NOT NULL AND new_version=previous_version+1)
      )
    );
    CREATE INDEX ix_staff_account_lifecycle_events_staff
      ON staff_account_lifecycle_events(staff_id,occurred_at);
    """)
    execute("ALTER TABLE staff_account_lifecycle_events OWNER TO golden_rose_schema_owner")
    execute(
        "REVOKE ALL ON staff_account_lifecycle_events FROM PUBLIC,golden_rose_runtime,golden_rose_migrator"
    )
    execute("GRANT SELECT,INSERT ON staff_account_lifecycle_events TO golden_rose_runtime")
    execute("GRANT SELECT,INSERT ON staff_accounts TO golden_rose_runtime")
    execute(
        "GRANT UPDATE(lifecycle_status,mfa_enrolled,updated_at,updated_by,version) ON staff_accounts TO golden_rose_runtime"
    )
    execute("GRANT SELECT,INSERT ON staff_permission_grants TO golden_rose_runtime")
    execute(
        "GRANT UPDATE(revoked_at,revoked_by,revocation_reason) ON staff_permission_grants TO golden_rose_runtime"
    )
    execute("GRANT SELECT,INSERT ON staff_delegations TO golden_rose_runtime")
    execute(
        "GRANT UPDATE(revoked_at,revoked_by,revocation_reason) ON staff_delegations TO golden_rose_runtime"
    )


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT EXISTS(SELECT 1 FROM staff_account_lifecycle_events)")):
        raise RuntimeError("staff account lifecycle data blocks downgrade before DDL")
    op.drop_table("staff_account_lifecycle_events")
    for table in ("staff_accounts", "staff_permission_grants", "staff_delegations"):
        execute(f"REVOKE ALL ON {table} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator")
        execute(f"GRANT SELECT ON {table} TO golden_rose_runtime")
