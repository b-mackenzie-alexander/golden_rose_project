"""create first slice tables

Revision ID: 0001_create_first_slice_tables
Revises:
Create Date: 2026-08-04 00:00:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_create_first_slice_tables"
down_revision = None
branch_labels = None
depends_on = None

IMMUTABLE_GUARD_FUNCTION = """
CREATE FUNCTION deny_mutation_on_append_only_tables() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;
"""

DROP_IMMUTABLE_GUARD_FUNCTION = "DROP FUNCTION deny_mutation_on_append_only_tables();"

CREATE_IMMUTABLE_GUARDS = [
    """
    CREATE TRIGGER command_receipts_no_update
    BEFORE UPDATE ON command_receipts
    FOR EACH ROW EXECUTE FUNCTION deny_mutation_on_append_only_tables();
    """,
    """
    CREATE TRIGGER command_receipts_no_delete
    BEFORE DELETE ON command_receipts
    FOR EACH ROW EXECUTE FUNCTION deny_mutation_on_append_only_tables();
    """,
    """
    CREATE TRIGGER audit_events_no_update
    BEFORE UPDATE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION deny_mutation_on_append_only_tables();
    """,
    """
    CREATE TRIGGER audit_events_no_delete
    BEFORE DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION deny_mutation_on_append_only_tables();
    """,
]

DROP_IMMUTABLE_GUARDS = [
    "DROP TRIGGER audit_events_no_delete ON audit_events;",
    "DROP TRIGGER audit_events_no_update ON audit_events;",
    "DROP TRIGGER command_receipts_no_delete ON command_receipts;",
    "DROP TRIGGER command_receipts_no_update ON command_receipts;",
]


def upgrade() -> None:
    op.create_table(
        "employers",
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_type", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("source_channel", sa.String(length=32), nullable=False),
        sa.Column("received_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("employer_type IN ('household', 'business')", name="ck_employers_type"),
        sa.CheckConstraint("btrim(display_name) <> ''", name="ck_employers_display_name_nonblank"),
        sa.CheckConstraint(
            "lifecycle_status = 'draft'", name="ck_employers_lifecycle_status_draft"
        ),
        sa.CheckConstraint(
            "source_channel = 'staff_entry'", name="ck_employers_source_channel_staff_entry"
        ),
        sa.CheckConstraint("version >= 1", name="ck_employers_version_positive"),
        sa.PrimaryKeyConstraint("employer_id"),
    )

    op.create_table(
        "command_receipts",
        sa.Column("command_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("command_schema_version", sa.Integer(), nullable=False),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", postgresql.BYTEA(), nullable=False),
        sa.Column("result_entity_type", sa.String(length=32), nullable=False),
        sa.Column("result_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("command_schema_version = 1", name="ck_command_receipts_schema_version"),
        sa.CheckConstraint(
            "command_type = 'create_draft_employer'", name="ck_command_receipts_command_type"
        ),
        sa.CheckConstraint(
            "octet_length(request_fingerprint) = 32",
            name="ck_command_receipts_request_fingerprint_len",
        ),
        sa.CheckConstraint(
            "result_entity_type = 'employer'", name="ck_command_receipts_entity_type"
        ),
        sa.PrimaryKeyConstraint("command_id"),
    )

    op.create_table(
        "audit_events",
        sa.Column("audit_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_schema_name", sa.String(length=64), nullable=False),
        sa.Column("event_schema_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_sequence", sa.Integer(), nullable=False),
        sa.Column("prior_record_version", sa.Integer(), nullable=False),
        sa.Column("new_record_version", sa.Integer(), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initiating_staff_actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("effective_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("command_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("reason_text", sa.String(length=512), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("related_event_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_classification", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "event_schema_name = 'employer.created'", name="ck_audit_events_schema_name"
        ),
        sa.CheckConstraint("event_schema_version = 1", name="ck_audit_events_schema_version"),
        sa.CheckConstraint("event_type = 'employer.created'", name="ck_audit_events_event_type"),
        sa.CheckConstraint("entity_type = 'employer'", name="ck_audit_events_entity_type"),
        sa.CheckConstraint("actor_type = 'staff'", name="ck_audit_events_actor_type"),
        sa.CheckConstraint("source_type = 'staff_api'", name="ck_audit_events_source_type"),
        sa.CheckConstraint(
            "payload_classification = 'sensitive_operational'",
            name="ck_audit_events_payload_classification",
        ),
        sa.ForeignKeyConstraint(["command_id"], ["command_receipts.command_id"]),
        sa.ForeignKeyConstraint(["entity_id"], ["employers.employer_id"]),
        sa.PrimaryKeyConstraint("audit_event_id"),
        sa.UniqueConstraint(
            "entity_type", "entity_id", "entity_sequence", name="uq_audit_events_entity_sequence"
        ),
    )

    op.execute(IMMUTABLE_GUARD_FUNCTION)
    for statement in CREATE_IMMUTABLE_GUARDS:
        op.execute(statement)


def downgrade() -> None:
    for statement in DROP_IMMUTABLE_GUARDS:
        op.execute(statement)
    op.execute(DROP_IMMUTABLE_GUARD_FUNCTION)
    op.drop_table("audit_events")
    op.drop_table("command_receipts")
    op.drop_table("employers")
