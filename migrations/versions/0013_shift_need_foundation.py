# ruff: noqa: E501
"""Add governed draft shift needs under staffing requests."""

import sqlalchemy as sa
from alembic import op

revision = "0013_shift_need_foundation"
down_revision = "0012_staff_account_evidence"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    CREATE TABLE shift_needs (
      shift_need_id uuid PRIMARY KEY,
      employer_id uuid NOT NULL,
      staffing_request_id uuid NOT NULL,
      request_version_at_creation integer NOT NULL CHECK(request_version_at_creation >= 1),
      shift_status varchar(32) NOT NULL CHECK(shift_status = 'draft'),
      role_title varchar(200) NOT NULL CHECK(btrim(role_title) <> ''),
      worker_count integer NOT NULL CHECK(worker_count BETWEEN 1 AND 1000),
      starts_at timestamptz NOT NULL,
      ends_at timestamptz NOT NULL,
      time_zone varchar(64) NOT NULL CHECK(btrim(time_zone) <> ''),
      notes varchar(1000),
      version integer NOT NULL CHECK(version = 1),
      created_at timestamptz NOT NULL,
      updated_at timestamptz NOT NULL,
      created_by uuid NOT NULL,
      updated_by uuid NOT NULL,
      CHECK(starts_at < ends_at),
      CHECK(created_at = updated_at AND created_by = updated_by),
      FOREIGN KEY(employer_id, staffing_request_id)
        REFERENCES staffing_requests(employer_id, staffing_request_id),
      UNIQUE(employer_id, shift_need_id)
    );
    CREATE INDEX ix_shift_needs_request_schedule
      ON shift_needs(employer_id, staffing_request_id, starts_at, shift_need_id);

    CREATE TABLE shift_need_events (
      event_id uuid PRIMARY KEY,
      command_id uuid NOT NULL UNIQUE,
      shift_need_id uuid NOT NULL,
      employer_id uuid NOT NULL,
      staffing_request_id uuid NOT NULL,
      actor_id uuid NOT NULL,
      event_type varchar(64) NOT NULL CHECK(event_type = 'shift_need.created'),
      previous_status varchar(32),
      new_status varchar(32) NOT NULL CHECK(new_status = 'draft'),
      previous_version integer,
      new_version integer NOT NULL CHECK(new_version = 1),
      request_version integer NOT NULL CHECK(request_version >= 1),
      occurred_at timestamptz NOT NULL,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text) <> ''),
      CHECK(previous_status IS NULL AND previous_version IS NULL),
      FOREIGN KEY(employer_id, shift_need_id)
        REFERENCES shift_needs(employer_id, shift_need_id),
      FOREIGN KEY(employer_id, staffing_request_id)
        REFERENCES staffing_requests(employer_id, staffing_request_id)
    );

    CREATE TRIGGER deny_mutation_shift_need_events
      BEFORE UPDATE OR DELETE OR TRUNCATE ON shift_need_events
      FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables();

    ALTER TABLE shift_needs OWNER TO golden_rose_schema_owner;
    ALTER TABLE shift_need_events OWNER TO golden_rose_schema_owner;
    REVOKE ALL ON TABLE shift_needs, shift_need_events
      FROM PUBLIC, golden_rose_runtime, golden_rose_migrator;
    GRANT SELECT, INSERT ON TABLE shift_needs, shift_need_events TO golden_rose_runtime;
    """)


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT EXISTS(SELECT 1 FROM shift_need_events)")):
        raise RuntimeError("shift need evidence blocks downgrade before DDL")
    execute("""
    DROP TRIGGER IF EXISTS deny_mutation_shift_need_events ON shift_need_events;
    DROP TABLE IF EXISTS shift_need_events;
    DROP TABLE IF EXISTS shift_needs;
    """)
