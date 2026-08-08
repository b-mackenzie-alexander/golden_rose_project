"""enforce command authority relationships

Revision ID: 0002_enforce_authority_links
Revises: 0001_create_first_slice_tables
Create Date: 2026-08-07 00:00:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_enforce_authority_links"
down_revision = "0001_create_first_slice_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_foreign_key(
        "fk_audit_events_command_result",
        "audit_events",
        "command_receipts",
        ["command_id", "entity_id"],
        ["command_id", "result_entity_id"],
    )
    op.create_unique_constraint(
        "uq_audit_events_command_event_type",
        "audit_events",
        ["command_id", "event_type"],
    )
    op.create_unique_constraint(
        "uq_audit_events_command_entity",
        "audit_events",
        ["command_id", "entity_id"],
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


def downgrade() -> None:
    op.drop_constraint(
        "fk_command_receipts_creation_event",
        "command_receipts",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_audit_events_command_entity",
        "audit_events",
        type_="unique",
    )
    op.drop_constraint(
        "uq_audit_events_command_event_type",
        "audit_events",
        type_="unique",
    )
    op.drop_constraint(
        "fk_audit_events_command_result",
        "audit_events",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_command_receipts_command_result",
        "command_receipts",
        type_="unique",
    )
    op.drop_constraint(
        "fk_command_receipts_result_employer",
        "command_receipts",
        type_="foreignkey",
    )
