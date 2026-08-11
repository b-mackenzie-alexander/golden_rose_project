"""add revision compatibility fields

Revision ID: 0003_revision_compat
Revises: 0002_enforce_authority_links
Create Date: 2026-08-09 00:30:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_revision_compat"
down_revision = "0002_enforce_authority_links"
branch_labels = None
depends_on = None

EMPLOYER_COMPAT_FUNCTION = """
CREATE FUNCTION populate_employer_revision_compatibility_fields() RETURNS trigger AS $$
BEGIN
    IF NEW.updated_at IS NULL THEN
        NEW.updated_at := NEW.created_at;
    END IF;
    IF NEW.updated_by IS NULL THEN
        NEW.updated_by := NEW.created_by;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

DROP_EMPLOYER_COMPAT_FUNCTION = "DROP FUNCTION populate_employer_revision_compatibility_fields();"

EMPLOYER_COMPAT_TRIGGER = """
CREATE TRIGGER employers_revision_compatibility_defaults
BEFORE INSERT ON employers
FOR EACH ROW EXECUTE FUNCTION populate_employer_revision_compatibility_fields();
"""

DROP_EMPLOYER_COMPAT_TRIGGER = (
    "DROP TRIGGER employers_revision_compatibility_defaults ON employers;"
)

RECEIPT_COMPAT_FUNCTION = """
CREATE FUNCTION populate_command_receipt_revision_compatibility_fields() RETURNS trigger AS $$
BEGIN
    IF NEW.command_type = 'create_draft_employer' THEN
        IF NEW.result_record_version IS NULL THEN
            NEW.result_record_version := 1;
        END IF;
        IF NEW.result_event_type IS NULL THEN
            NEW.result_event_type := 'employer.created';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

DROP_RECEIPT_COMPAT_FUNCTION = (
    "DROP FUNCTION populate_command_receipt_revision_compatibility_fields();"
)

RECEIPT_COMPAT_TRIGGER = """
CREATE TRIGGER command_receipts_revision_compatibility_defaults
BEFORE INSERT ON command_receipts
FOR EACH ROW EXECUTE FUNCTION populate_command_receipt_revision_compatibility_fields();
"""

DROP_RECEIPT_COMPAT_TRIGGER = (
    "DROP TRIGGER command_receipts_revision_compatibility_defaults ON command_receipts;"
)

REVISION_COMMAND_TYPES_CONSTRAINT = (
    "command_type IN ('create_draft_employer', 'revise_draft_employer')"
)

REVISION_AUDIT_SCHEMA_NAME_CONSTRAINT = (
    "event_schema_name IN ('employer.created', 'employer.draft_revised')"
)

REVISION_AUDIT_EVENT_TYPE_CONSTRAINT = (
    "event_type IN ('employer.created', 'employer.draft_revised')"
)

RECEIPT_RESULT_AUTHORITY_SHAPE_CONSTRAINT = (
    "((command_type = 'create_draft_employer' "
    "AND result_event_type = 'employer.created' "
    "AND result_record_version = 1) OR "
    "(command_type = 'revise_draft_employer' "
    "AND result_event_type = 'employer.draft_revised' "
    "AND result_record_version >= 2))"
)

INCOMPLETE_CREATE_RESULT_AUTHORITY_PREFLIGHT = """
SELECT EXISTS (
    SELECT 1
    FROM command_receipts AS cr
    JOIN audit_events AS ae
      ON ae.command_id = cr.command_id
     AND ae.entity_id = cr.result_entity_id
    WHERE cr.command_type = 'create_draft_employer'
      AND (
          ae.new_record_version <> 1
          OR ae.event_type <> 'employer.created'
          OR ae.actor_id <> cr.actor_id
      )
)
"""

POPULATED_REVISION_STATE_DOWNGRADE_PREFLIGHT = """
SELECT EXISTS (
    SELECT 1
    FROM employers
    WHERE version > 1
       OR updated_at <> created_at
       OR updated_by <> created_by
)
"""


def upgrade() -> None:
    bind = op.get_bind()
    has_incomplete_create_result_authority = bind.execute(
        sa.text(INCOMPLETE_CREATE_RESULT_AUTHORITY_PREFLIGHT)
    ).scalar_one()
    if has_incomplete_create_result_authority:
        raise RuntimeError("incomplete receipt/event authority blocks revision migration")

    op.add_column(
        "employers",
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "employers",
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE employers
        SET updated_at = created_at,
            updated_by = created_by
        WHERE updated_at IS NULL OR updated_by IS NULL
        """
    )
    op.alter_column("employers", "updated_at", nullable=False)
    op.alter_column("employers", "updated_by", nullable=False)
    op.execute(EMPLOYER_COMPAT_FUNCTION)
    op.execute(EMPLOYER_COMPAT_TRIGGER)

    op.add_column(
        "command_receipts",
        sa.Column(
            "result_record_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column(
        "command_receipts",
        sa.Column(
            "result_event_type",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'employer.created'"),
        ),
    )
    op.alter_column("command_receipts", "result_record_version", server_default=None)
    op.alter_column("command_receipts", "result_event_type", server_default=None)
    op.drop_constraint("ck_command_receipts_command_type", "command_receipts", type_="check")
    op.create_check_constraint(
        "ck_command_receipts_command_type",
        "command_receipts",
        REVISION_COMMAND_TYPES_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_command_receipts_result_record_version_positive",
        "command_receipts",
        "result_record_version >= 1",
    )
    op.create_check_constraint(
        "ck_command_receipts_result_authority_shape",
        "command_receipts",
        RECEIPT_RESULT_AUTHORITY_SHAPE_CONSTRAINT,
    )
    op.execute(RECEIPT_COMPAT_FUNCTION)
    op.execute(RECEIPT_COMPAT_TRIGGER)

    op.create_unique_constraint(
        "uq_command_receipts_result_authority",
        "command_receipts",
        [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
    )
    op.create_unique_constraint(
        "uq_audit_events_result_authority",
        "audit_events",
        ["command_id", "entity_id", "new_record_version", "event_type", "actor_id"],
    )
    op.drop_constraint("audit_events_command_id_fkey", "audit_events", type_="foreignkey")
    op.drop_constraint("fk_audit_events_command_result", "audit_events", type_="foreignkey")
    op.create_foreign_key(
        "fk_audit_events_command_result",
        "audit_events",
        "command_receipts",
        ["command_id", "entity_id", "new_record_version", "event_type", "actor_id"],
        [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_command_receipts_result_audit_event",
        "command_receipts",
        "audit_events",
        [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        ["command_id", "entity_id", "new_record_version", "event_type", "actor_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.drop_constraint("ck_audit_events_schema_name", "audit_events", type_="check")
    op.create_check_constraint(
        "ck_audit_events_schema_name",
        "audit_events",
        REVISION_AUDIT_SCHEMA_NAME_CONSTRAINT,
    )
    op.drop_constraint("ck_audit_events_event_type", "audit_events", type_="check")
    op.create_check_constraint(
        "ck_audit_events_event_type",
        "audit_events",
        REVISION_AUDIT_EVENT_TYPE_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_audit_events_schema_matches_type",
        "audit_events",
        "event_schema_name = event_type",
    )
    op.create_check_constraint(
        "ck_audit_events_correlation_matches_command",
        "audit_events",
        "correlation_id = command_id",
    )
    op.create_check_constraint(
        "ck_audit_events_entity_sequence_matches_new_record_version",
        "audit_events",
        "entity_sequence = new_record_version",
    )
    op.create_check_constraint(
        "ck_audit_events_one_step_version_advance",
        "audit_events",
        "new_record_version = prior_record_version + 1",
    )


def downgrade() -> None:
    bind = op.get_bind()
    has_populated_revision_state = bind.execute(
        sa.text(POPULATED_REVISION_STATE_DOWNGRADE_PREFLIGHT)
    ).scalar_one()
    if has_populated_revision_state:
        raise RuntimeError("populated revision-state data blocks downgrade")

    op.drop_constraint(
        "fk_command_receipts_result_audit_event",
        "command_receipts",
        type_="foreignkey",
    )
    op.drop_constraint("fk_audit_events_command_result", "audit_events", type_="foreignkey")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_command_id_fkey")
    op.create_foreign_key(
        "audit_events_command_id_fkey",
        "audit_events",
        "command_receipts",
        ["command_id"],
        ["command_id"],
    )
    op.create_foreign_key(
        "fk_audit_events_command_result",
        "audit_events",
        "command_receipts",
        ["command_id", "entity_id"],
        ["command_id", "result_entity_id"],
    )
    op.drop_constraint("uq_audit_events_result_authority", "audit_events", type_="unique")
    op.drop_constraint(
        "uq_command_receipts_result_authority",
        "command_receipts",
        type_="unique",
    )
    op.execute(
        "ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS "
        "ck_audit_events_one_step_version_advance"
    )
    op.execute(
        "ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS "
        "ck_audit_events_entity_sequence_matches_new_record_version"
    )
    op.execute(
        "ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS "
        "ck_audit_events_correlation_matches_command"
    )
    op.execute(
        "ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS ck_audit_events_schema_matches_type"
    )
    op.drop_constraint("ck_audit_events_event_type", "audit_events", type_="check")
    op.create_check_constraint(
        "ck_audit_events_event_type",
        "audit_events",
        "event_type = 'employer.created'",
    )
    op.drop_constraint("ck_audit_events_schema_name", "audit_events", type_="check")
    op.create_check_constraint(
        "ck_audit_events_schema_name",
        "audit_events",
        "event_schema_name = 'employer.created'",
    )

    op.execute(DROP_RECEIPT_COMPAT_TRIGGER)
    op.execute(DROP_RECEIPT_COMPAT_FUNCTION)
    op.drop_constraint("ck_command_receipts_command_type", "command_receipts", type_="check")
    op.execute(
        "ALTER TABLE command_receipts DROP CONSTRAINT IF EXISTS "
        "ck_command_receipts_result_authority_shape"
    )
    op.execute(
        "ALTER TABLE command_receipts DROP CONSTRAINT IF EXISTS "
        "ck_command_receipts_result_record_version_positive"
    )
    op.create_check_constraint(
        "ck_command_receipts_command_type",
        "command_receipts",
        "command_type = 'create_draft_employer'",
    )
    op.drop_column("command_receipts", "result_event_type")
    op.drop_column("command_receipts", "result_record_version")

    op.execute(DROP_EMPLOYER_COMPAT_TRIGGER)
    op.execute(DROP_EMPLOYER_COMPAT_FUNCTION)
    op.drop_column("employers", "updated_by")
    op.drop_column("employers", "updated_at")
