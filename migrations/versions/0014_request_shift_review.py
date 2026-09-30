# ruff: noqa: E501
"""Add request and shift review lifecycle evidence."""

import sqlalchemy as sa
from alembic import op

revision = "0014_request_shift_review"
down_revision = "0013_shift_need_foundation"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    ALTER TABLE staffing_requests
      DROP CONSTRAINT staffing_requests_request_status_check,
      ADD CONSTRAINT staffing_requests_request_status_check
        CHECK (request_status IN ('draft', 'pending_review'));

    ALTER TABLE shift_needs
      DROP CONSTRAINT IF EXISTS ck_shift_needs_status_draft,
      DROP CONSTRAINT IF EXISTS shift_needs_shift_status_check,
      DROP CONSTRAINT IF EXISTS ck_shift_needs_version_one,
      DROP CONSTRAINT IF EXISTS shift_needs_version_check,
      DROP CONSTRAINT IF EXISTS ck_shift_needs_creation_attribution,
      DROP CONSTRAINT IF EXISTS shift_needs_check1,
      ADD CONSTRAINT ck_shift_needs_status_review_lifecycle
        CHECK (shift_status IN ('draft', 'pending_review')),
      ADD CONSTRAINT ck_shift_needs_version_positive CHECK (version >= 1);

    ALTER TABLE shift_need_events
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_type,
      DROP CONSTRAINT IF EXISTS shift_need_events_event_type_check,
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_new_status,
      DROP CONSTRAINT IF EXISTS shift_need_events_new_status_check,
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_new_version_one,
      DROP CONSTRAINT IF EXISTS shift_need_events_new_version_check,
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_create_shape,
      DROP CONSTRAINT IF EXISTS shift_need_events_check,
      ADD CONSTRAINT ck_shift_need_events_type
        CHECK (event_type IN ('shift_need.created', 'shift_need.submitted_for_review')),
      ADD CONSTRAINT ck_shift_need_events_new_status
        CHECK (new_status IN ('draft', 'pending_review')),
      ADD CONSTRAINT ck_shift_need_events_new_version_positive CHECK (new_version >= 1),
      ADD CONSTRAINT ck_shift_need_events_lifecycle_shape CHECK (
        (
          event_type = 'shift_need.created'
          AND previous_status IS NULL
          AND previous_version IS NULL
          AND new_status = 'draft'
          AND new_version = 1
        )
        OR
        (
          event_type = 'shift_need.submitted_for_review'
          AND previous_status = 'draft'
          AND previous_version >= 1
          AND new_status = 'pending_review'
          AND new_version = previous_version + 1
        )
      );

    CREATE TABLE staffing_request_events (
      event_id uuid PRIMARY KEY,
      command_id uuid NOT NULL UNIQUE,
      staffing_request_id uuid NOT NULL,
      employer_id uuid NOT NULL,
      actor_id uuid NOT NULL,
      event_type varchar(64) NOT NULL CHECK(event_type = 'staffing_request.submitted_for_review'),
      previous_status varchar(32) NOT NULL CHECK(previous_status = 'draft'),
      new_status varchar(32) NOT NULL CHECK(new_status = 'pending_review'),
      previous_version integer NOT NULL CHECK(previous_version >= 1),
      new_version integer NOT NULL CHECK(new_version = previous_version + 1),
      occurred_at timestamptz NOT NULL,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text) <> ''),
      FOREIGN KEY(employer_id, staffing_request_id)
        REFERENCES staffing_requests(employer_id, staffing_request_id)
    );

    CREATE TRIGGER deny_mutation_staffing_request_events
      BEFORE UPDATE OR DELETE OR TRUNCATE ON staffing_request_events
      FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables();

    ALTER TABLE staffing_request_events OWNER TO golden_rose_schema_owner;
    REVOKE ALL ON TABLE staffing_request_events FROM PUBLIC, golden_rose_runtime, golden_rose_migrator;
    GRANT SELECT, INSERT ON TABLE staffing_request_events TO golden_rose_runtime;
    GRANT UPDATE(request_status, version, updated_at, updated_by) ON TABLE staffing_requests
      TO golden_rose_runtime;
    GRANT UPDATE(shift_status, version, updated_at, updated_by) ON TABLE shift_needs
      TO golden_rose_runtime;
    """)


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT EXISTS(SELECT 1 FROM staffing_request_events)")):
        raise RuntimeError("staffing request evidence blocks downgrade before DDL")
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM shift_need_events WHERE event_type <> 'shift_need.created')"
        )
    ):
        raise RuntimeError("shift need lifecycle evidence blocks downgrade before DDL")
    execute("""
    DROP TRIGGER IF EXISTS deny_mutation_staffing_request_events ON staffing_request_events;
    DROP TABLE IF EXISTS staffing_request_events;

    REVOKE UPDATE(request_status, version, updated_at, updated_by) ON TABLE staffing_requests
      FROM golden_rose_runtime;
    REVOKE UPDATE(shift_status, version, updated_at, updated_by) ON TABLE shift_needs
      FROM golden_rose_runtime;

    ALTER TABLE staffing_requests
      DROP CONSTRAINT staffing_requests_request_status_check,
      ADD CONSTRAINT staffing_requests_request_status_check CHECK (request_status = 'draft');

    ALTER TABLE shift_need_events
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_type,
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_new_status,
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_new_version_positive,
      DROP CONSTRAINT IF EXISTS ck_shift_need_events_lifecycle_shape,
      ADD CONSTRAINT ck_shift_need_events_type CHECK (event_type = 'shift_need.created'),
      ADD CONSTRAINT ck_shift_need_events_new_status CHECK (new_status = 'draft'),
      ADD CONSTRAINT ck_shift_need_events_new_version_one CHECK (new_version = 1),
      ADD CONSTRAINT ck_shift_need_events_create_shape
        CHECK (previous_status IS NULL AND previous_version IS NULL);

    ALTER TABLE shift_needs
      DROP CONSTRAINT IF EXISTS ck_shift_needs_status_review_lifecycle,
      DROP CONSTRAINT IF EXISTS ck_shift_needs_version_positive,
      ADD CONSTRAINT ck_shift_needs_status_draft CHECK (shift_status = 'draft'),
      ADD CONSTRAINT ck_shift_needs_version_one CHECK (version = 1),
      ADD CONSTRAINT ck_shift_needs_creation_attribution
        CHECK (created_at = updated_at AND created_by = updated_by);
    """)
