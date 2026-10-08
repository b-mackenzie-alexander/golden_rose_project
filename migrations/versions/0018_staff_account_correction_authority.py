# ruff: noqa: E501
"""Grant runtime authority for staff account correction fields."""

import sqlalchemy as sa
from alembic import op

revision = "0018_staff_acct_corr_auth"
down_revision = "0017_staff_signin_email_mgmt"
branch_labels = None
depends_on = None


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    GRANT UPDATE(provider_subject,provider_email,display_name,role_name)
      ON staff_accounts TO golden_rose_runtime;
    """)


def downgrade() -> None:
    execute("""
    REVOKE UPDATE(provider_subject,provider_email,display_name,role_name)
      ON staff_accounts FROM golden_rose_runtime;
    """)
