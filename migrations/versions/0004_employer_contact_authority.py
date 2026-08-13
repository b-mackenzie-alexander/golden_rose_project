"""add employer contact authority foundation

Revision ID: 0004_employer_contact_authority
Revises: 0003_revision_compat
Create Date: 2026-08-12 00:45:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_employer_contact_authority"
down_revision = "0003_revision_compat"
branch_labels = None
depends_on = None

ENTITY_AUTHORITY_TYPE_CONSTRAINT = "entity_type IN ('employer', 'employer_contact')"
ENTITY_AUTHORITY_ONE_CONCRETE_ID_CONSTRAINT = (
    "((entity_type = 'employer' AND employer_id = entity_id AND employer_contact_id IS NULL) OR "
    "(entity_type = 'employer_contact' "
    "AND employer_contact_id = entity_id AND employer_id IS NULL))"
)
COMMAND_RECEIPT_ENTITY_TYPE_CONSTRAINT = "result_entity_type IN ('employer', 'employer_contact')"
COMMAND_RECEIPT_COMMAND_TYPE_CONSTRAINT = (
    "command_type IN ('create_draft_employer', 'create_employer_contact', 'revise_draft_employer')"
)
COMMAND_RECEIPT_RESULT_AUTHORITY_SHAPE_CONSTRAINT = (
    "((command_type = 'create_draft_employer' "
    "AND result_entity_type = 'employer' "
    "AND result_event_type = 'employer.created' "
    "AND result_record_version = 1) OR "
    "(command_type = 'create_employer_contact' "
    "AND result_entity_type = 'employer_contact' "
    "AND result_event_type = 'employer_contact.created' "
    "AND result_record_version = 1) OR "
    "(command_type = 'revise_draft_employer' "
    "AND result_entity_type = 'employer' "
    "AND result_event_type = 'employer.draft_revised' "
    "AND result_record_version >= 2))"
)
AUDIT_EVENT_ENTITY_TYPE_CONSTRAINT = "entity_type IN ('employer', 'employer_contact')"
AUDIT_EVENT_SCHEMA_NAME_CONSTRAINT = (
    "event_schema_name IN ('employer.created', 'employer_contact.created', "
    "'employer.draft_revised')"
)
AUDIT_EVENT_EVENT_TYPE_CONSTRAINT = (
    "event_type IN ('employer.created', 'employer_contact.created', 'employer.draft_revised')"
)
UPGRADE_LOCK_TABLES = (
    "LOCK TABLE command_receipts, employers, audit_events IN SHARE ROW EXCLUSIVE MODE"
)
DOWNGRADE_LOCK_TABLES = (
    "LOCK TABLE command_receipts, employers, employer_contacts, entity_authorities, audit_events "
    "IN SHARE ROW EXCLUSIVE MODE"
)
SUCCESSOR_DOWNGRADE_REFUSAL_PREFLIGHT = """
SELECT EXISTS (
    SELECT 1
    FROM entity_authorities
    WHERE entity_type = 'employer_contact'
)
OR EXISTS (
    SELECT 1
    FROM employer_contacts
)
OR EXISTS (
    SELECT 1
    FROM command_receipts
    WHERE result_entity_type = 'employer_contact'
       OR command_type = 'create_employer_contact'
       OR result_event_type = 'employer_contact.created'
)
OR EXISTS (
    SELECT 1
    FROM audit_events
    WHERE entity_type = 'employer_contact'
       OR event_type = 'employer_contact.created'
       OR event_schema_name = 'employer_contact.created'
)
"""


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text(UPGRADE_LOCK_TABLES))

    op.create_table(
        "employer_contacts",
        sa.Column("employer_contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["employers.employer_id"],
            name="fk_employer_contacts_employer",
        ),
        sa.PrimaryKeyConstraint("employer_contact_id"),
        sa.UniqueConstraint(
            "employer_id",
            "employer_contact_id",
            name="uq_employer_contacts_parent_scoped_identity",
        ),
        sa.CheckConstraint(
            "btrim(full_name) <> ''", name="ck_employer_contacts_full_name_nonblank"
        ),
        sa.CheckConstraint("version = 1", name="ck_employer_contacts_version_is_one"),
    )

    op.create_table(
        "entity_authorities",
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employer_contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["employers.employer_id"],
            name="fk_entity_authorities_employer",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["employer_contact_id"],
            ["employer_contacts.employer_contact_id"],
            name="fk_entity_authorities_employer_contact",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("entity_type", "entity_id"),
        sa.UniqueConstraint("employer_id", name="uq_entity_authorities_employer_id"),
        sa.UniqueConstraint(
            "employer_contact_id",
            name="uq_entity_authorities_employer_contact_id",
        ),
        sa.CheckConstraint(
            ENTITY_AUTHORITY_TYPE_CONSTRAINT,
            name="ck_entity_authorities_entity_type",
        ),
        sa.CheckConstraint(
            ENTITY_AUTHORITY_ONE_CONCRETE_ID_CONSTRAINT,
            name="ck_entity_authorities_exactly_one_concrete_id",
        ),
    )

    op.execute(
        """
        INSERT INTO entity_authorities (entity_type, entity_id, employer_id, employer_contact_id)
        SELECT 'employer', employer_id, employer_id, NULL
        FROM employers
        """
    )

    op.drop_constraint("fk_command_receipts_creation_event", "command_receipts", type_="foreignkey")
    op.drop_constraint(
        "fk_command_receipts_result_employer", "command_receipts", type_="foreignkey"
    )
    op.drop_constraint("fk_audit_events_command_result", "audit_events", type_="foreignkey")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_entity_id_fkey")
    op.drop_constraint("uq_command_receipts_command_result", "command_receipts", type_="unique")
    op.drop_constraint("uq_command_receipts_result_authority", "command_receipts", type_="unique")
    op.drop_constraint("uq_audit_events_command_entity", "audit_events", type_="unique")
    op.drop_constraint("ck_command_receipts_entity_type", "command_receipts", type_="check")
    op.drop_constraint("ck_command_receipts_command_type", "command_receipts", type_="check")
    op.drop_constraint(
        "ck_command_receipts_result_authority_shape", "command_receipts", type_="check"
    )
    op.drop_constraint("ck_audit_events_schema_name", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_event_type", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_entity_type", "audit_events", type_="check")

    op.create_check_constraint(
        "ck_command_receipts_command_type",
        "command_receipts",
        COMMAND_RECEIPT_COMMAND_TYPE_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_command_receipts_entity_type",
        "command_receipts",
        COMMAND_RECEIPT_ENTITY_TYPE_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_command_receipts_result_authority_shape",
        "command_receipts",
        COMMAND_RECEIPT_RESULT_AUTHORITY_SHAPE_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_audit_events_schema_name",
        "audit_events",
        AUDIT_EVENT_SCHEMA_NAME_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_audit_events_event_type",
        "audit_events",
        AUDIT_EVENT_EVENT_TYPE_CONSTRAINT,
    )
    op.create_check_constraint(
        "ck_audit_events_entity_type",
        "audit_events",
        AUDIT_EVENT_ENTITY_TYPE_CONSTRAINT,
    )

    op.create_foreign_key(
        "fk_command_receipts_result_entity_authority",
        "command_receipts",
        "entity_authorities",
        ["result_entity_type", "result_entity_id"],
        ["entity_type", "entity_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_unique_constraint(
        "uq_command_receipts_command_result",
        "command_receipts",
        ["command_id", "result_entity_id"],
    )
    op.create_unique_constraint(
        "uq_command_receipts_command_result_entity",
        "command_receipts",
        ["command_id", "result_entity_type", "result_entity_id"],
    )
    op.create_unique_constraint(
        "uq_command_receipts_result_authority",
        "command_receipts",
        [
            "command_id",
            "result_entity_type",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
    )
    op.create_unique_constraint(
        "uq_audit_events_command_entity",
        "audit_events",
        ["command_id", "entity_type", "entity_id"],
    )
    op.create_foreign_key(
        "fk_command_receipts_creation_event",
        "command_receipts",
        "audit_events",
        ["command_id", "result_entity_type", "result_entity_id"],
        ["command_id", "entity_type", "entity_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_audit_events_entity_authority",
        "audit_events",
        "entity_authorities",
        ["entity_type", "entity_id"],
        ["entity_type", "entity_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_foreign_key(
        "fk_audit_events_command_result",
        "audit_events",
        "command_receipts",
        ["command_id", "entity_type", "entity_id", "new_record_version", "event_type", "actor_id"],
        [
            "command_id",
            "result_entity_type",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text(DOWNGRADE_LOCK_TABLES))

    has_successor_data = bind.execute(sa.text(SUCCESSOR_DOWNGRADE_REFUSAL_PREFLIGHT)).scalar_one()
    if has_successor_data:
        raise RuntimeError("successor employer-contact authority data blocks downgrade")

    op.drop_constraint("fk_audit_events_command_result", "audit_events", type_="foreignkey")
    op.drop_constraint("fk_audit_events_entity_authority", "audit_events", type_="foreignkey")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_entity_id_fkey")
    op.drop_constraint(
        "fk_command_receipts_creation_event",
        "command_receipts",
        type_="foreignkey",
    )
    op.drop_constraint("uq_audit_events_command_entity", "audit_events", type_="unique")
    op.drop_constraint(
        "uq_command_receipts_command_result_entity",
        "command_receipts",
        type_="unique",
    )
    op.drop_constraint(
        "uq_command_receipts_result_authority",
        "command_receipts",
        type_="unique",
    )
    op.drop_constraint("uq_command_receipts_command_result", "command_receipts", type_="unique")
    op.drop_constraint(
        "fk_command_receipts_result_entity_authority",
        "command_receipts",
        type_="foreignkey",
    )
    op.drop_constraint("ck_command_receipts_entity_type", "command_receipts", type_="check")
    op.drop_constraint("ck_audit_events_entity_type", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_event_type", "audit_events", type_="check")
    op.drop_constraint("ck_audit_events_schema_name", "audit_events", type_="check")
    op.drop_constraint(
        "ck_command_receipts_result_authority_shape", "command_receipts", type_="check"
    )
    op.drop_constraint("ck_command_receipts_command_type", "command_receipts", type_="check")

    op.create_check_constraint(
        "ck_audit_events_entity_type",
        "audit_events",
        "entity_type IN ('employer')",
    )
    op.create_check_constraint(
        "ck_audit_events_event_type",
        "audit_events",
        "event_type IN ('employer.created', 'employer.draft_revised')",
    )
    op.create_check_constraint(
        "ck_audit_events_schema_name",
        "audit_events",
        "event_schema_name IN ('employer.created', 'employer.draft_revised')",
    )
    op.create_check_constraint(
        "ck_command_receipts_command_type",
        "command_receipts",
        "command_type IN ('create_draft_employer', 'revise_draft_employer')",
    )
    op.create_check_constraint(
        "ck_command_receipts_entity_type",
        "command_receipts",
        "result_entity_type IN ('employer')",
    )
    op.create_check_constraint(
        "ck_command_receipts_result_authority_shape",
        "command_receipts",
        "((command_type = 'create_draft_employer' AND result_event_type = 'employer.created' "
        "AND result_record_version = 1) OR "
        "(command_type = 'revise_draft_employer' AND result_event_type = 'employer.draft_revised' "
        "AND result_record_version >= 2))",
    )
    op.create_foreign_key(
        "fk_command_receipts_result_employer",
        "command_receipts",
        "employers",
        ["result_entity_id"],
        ["employer_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_unique_constraint(
        "uq_command_receipts_command_result",
        "command_receipts",
        ["command_id", "result_entity_id"],
    )
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
        "uq_audit_events_command_entity",
        "audit_events",
        ["command_id", "entity_id"],
    )
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
        "fk_command_receipts_creation_event",
        "command_receipts",
        "audit_events",
        ["command_id", "result_entity_id"],
        ["command_id", "entity_id"],
        deferrable=True,
        initially="DEFERRED",
    )

    op.drop_table("entity_authorities")
    op.drop_table("employer_contacts")
