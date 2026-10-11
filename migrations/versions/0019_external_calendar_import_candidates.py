# ruff: noqa: E501
"""Add external calendar import candidate review tables."""

import sqlalchemy as sa
from alembic import op

revision = "0019_ext_calendar_imports"
down_revision = "0018_staff_acct_corr_auth"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    CREATE TABLE staff_calendar_connections (
      connection_id uuid PRIMARY KEY,
      staff_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
      provider_name varchar(40) NOT NULL CHECK(provider_name='google_calendar'),
      calendar_alias varchar(160) NOT NULL CHECK(btrim(calendar_alias)<>''),
      token_material_ref varchar(255),
      granted_scopes jsonb NOT NULL CHECK(jsonb_typeof(granted_scopes)='array'),
      connection_status varchar(32) NOT NULL CHECK(connection_status IN ('authorization_required','connected','disconnected','unavailable')),
      connected_at timestamptz,
      disconnected_at timestamptz,
      last_sync_status varchar(32) NOT NULL CHECK(last_sync_status IN ('never_synced','ready','failed','configuration_required')),
      last_sync_error varchar(80),
      created_at timestamptz NOT NULL,
      created_by uuid NOT NULL REFERENCES staff_accounts(staff_id),
      updated_at timestamptz NOT NULL,
      updated_by uuid NOT NULL REFERENCES staff_accounts(staff_id),
      version integer NOT NULL CHECK(version>=1),
      UNIQUE(staff_id,provider_name,calendar_alias)
    );

    CREATE TABLE external_calendar_imports (
      import_id uuid PRIMARY KEY,
      connection_id uuid NOT NULL REFERENCES staff_calendar_connections(connection_id),
      provider_event_uid varchar(200) NOT NULL CHECK(btrim(provider_event_uid)<>''),
      provider_event_updated_at timestamptz NOT NULL,
      event_title varchar(200) NOT NULL CHECK(btrim(event_title)<>''),
      starts_at timestamptz NOT NULL,
      ends_at timestamptz NOT NULL,
      time_zone varchar(64) NOT NULL CHECK(btrim(time_zone)<>''),
      location_review varchar(200),
      import_status varchar(32) NOT NULL CHECK(import_status IN ('candidate','ignored','marked_existing','linked','draft_started','superseded','unavailable')),
      linked_entity_type varchar(40),
      linked_entity_id uuid,
      created_at timestamptz NOT NULL,
      created_by uuid NOT NULL REFERENCES staff_accounts(staff_id),
      updated_at timestamptz NOT NULL,
      updated_by uuid NOT NULL REFERENCES staff_accounts(staff_id),
      version integer NOT NULL CHECK(version>=1),
      CHECK(starts_at < ends_at),
      CHECK((linked_entity_type IS NULL AND linked_entity_id IS NULL) OR (linked_entity_type IN ('staffing_request','shift_need','follow_up') AND linked_entity_id IS NOT NULL)),
      UNIQUE(connection_id,provider_event_uid)
    );

    CREATE TABLE external_calendar_import_events (
      event_id uuid PRIMARY KEY,
      command_id uuid NOT NULL UNIQUE,
      import_id uuid NOT NULL REFERENCES external_calendar_imports(import_id),
      connection_id uuid NOT NULL REFERENCES staff_calendar_connections(connection_id),
      actor_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
      event_type varchar(64) NOT NULL CHECK(event_type IN ('external_calendar.candidate_imported','external_calendar.candidate_deduplicated','external_calendar.candidate_ignored','external_calendar.candidate_marked_existing')),
      previous_status varchar(32) CHECK(previous_status IS NULL OR previous_status IN ('candidate','ignored','marked_existing','linked','draft_started','superseded','unavailable')),
      new_status varchar(32) NOT NULL CHECK(new_status IN ('candidate','ignored','marked_existing','linked','draft_started','superseded','unavailable')),
      previous_version integer CHECK(previous_version IS NULL OR previous_version>=1),
      new_version integer NOT NULL CHECK(new_version>=1),
      occurred_at timestamptz NOT NULL,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text)<>'')
    );

    CREATE TRIGGER deny_mutation_external_calendar_import_events
      BEFORE UPDATE OR DELETE OR TRUNCATE ON external_calendar_import_events
      FOR EACH STATEMENT EXECUTE FUNCTION deny_mutation_on_append_only_tables();

    ALTER TABLE staff_calendar_connections OWNER TO golden_rose_schema_owner;
    ALTER TABLE external_calendar_imports OWNER TO golden_rose_schema_owner;
    ALTER TABLE external_calendar_import_events OWNER TO golden_rose_schema_owner;
    REVOKE ALL ON TABLE staff_calendar_connections, external_calendar_imports, external_calendar_import_events
      FROM PUBLIC, golden_rose_runtime, golden_rose_migrator;
    GRANT SELECT, INSERT ON TABLE staff_calendar_connections, external_calendar_imports, external_calendar_import_events
      TO golden_rose_runtime;
    GRANT UPDATE(calendar_alias,token_material_ref,granted_scopes,connection_status,connected_at,disconnected_at,last_sync_status,last_sync_error,updated_at,updated_by,version)
      ON staff_calendar_connections TO golden_rose_runtime;
    GRANT UPDATE(import_status,linked_entity_type,linked_entity_id,updated_at,updated_by,version)
      ON external_calendar_imports TO golden_rose_runtime;
    """)


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT EXISTS(SELECT 1 FROM external_calendar_imports)")):
        raise RuntimeError("external calendar import evidence blocks downgrade before DDL")
    execute("""
    DROP TRIGGER IF EXISTS deny_mutation_external_calendar_import_events
      ON external_calendar_import_events;
    DROP TABLE IF EXISTS external_calendar_import_events;
    DROP TABLE IF EXISTS external_calendar_imports;
    DROP TABLE IF EXISTS staff_calendar_connections;
    """)
