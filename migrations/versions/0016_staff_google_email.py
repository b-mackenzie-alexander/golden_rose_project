# ruff: noqa: E501
"""Add pending Google email binding for staff accounts."""

import sqlalchemy as sa
from alembic import op

revision = "0016_staff_google_email"
down_revision = "0015_staff_account_corrections"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    ALTER TABLE staff_accounts
      ADD COLUMN provider_email varchar(320);
    ALTER TABLE staff_accounts
      ADD CONSTRAINT uq_staff_accounts_provider_email UNIQUE(provider_email),
      ADD CONSTRAINT ck_staff_accounts_provider_email_shape
        CHECK(
          provider_email IS NULL
          OR (
            provider_email=lower(provider_email)
            AND btrim(provider_email)<>''
            AND position('@' in provider_email)>1
          )
        );
    """)


def downgrade() -> None:
    execute("""
    ALTER TABLE staff_accounts
      DROP CONSTRAINT IF EXISTS ck_staff_accounts_provider_email_shape,
      DROP CONSTRAINT IF EXISTS uq_staff_accounts_provider_email,
      DROP COLUMN IF EXISTS provider_email;
    """)
