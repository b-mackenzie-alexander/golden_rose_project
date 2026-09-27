# ruff: noqa: E501
"""Add durable staff account and delegation records."""

import sqlalchemy as sa
from alembic import op

revision = "0010_staff_accounts"
down_revision = "0009a_canonical_reviews"
branch_labels = None
depends_on = None

TABLES = ("staff_delegations", "staff_permission_grants", "staff_accounts")


def execute(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    execute("""
    CREATE TABLE staff_accounts (
      staff_id uuid PRIMARY KEY,
      provider_subject varchar(256) NOT NULL UNIQUE CHECK(btrim(provider_subject)<>''),
      display_name varchar(160) NOT NULL CHECK(btrim(display_name)<>''),
      role_name varchar(80) NOT NULL CHECK(role_name IN ('owner','delegated_manager','operations_staff','platform_administrator')),
      lifecycle_status varchar(32) NOT NULL CHECK(lifecycle_status IN ('active','suspended','deprovisioned')),
      mfa_enrolled boolean NOT NULL DEFAULT false,
      created_at timestamptz NOT NULL,
      created_by uuid NOT NULL,
      updated_at timestamptz NOT NULL,
      updated_by uuid NOT NULL,
      version integer NOT NULL CHECK(version>=1),
      CHECK((lifecycle_status='active' AND mfa_enrolled) OR lifecycle_status<>'active')
    );
    CREATE TABLE staff_permission_grants (
      grant_id uuid PRIMARY KEY,
      staff_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
      permission_name varchar(120) NOT NULL CHECK(btrim(permission_name)<>''),
      scope_kind varchar(40) NOT NULL CHECK(scope_kind IN ('global','intake','worker')),
      scope_id uuid,
      granted_at timestamptz NOT NULL,
      granted_by uuid NOT NULL REFERENCES staff_accounts(staff_id),
      revoked_at timestamptz,
      revoked_by uuid REFERENCES staff_accounts(staff_id),
      revocation_reason varchar(512) CHECK(revocation_reason IS NULL OR btrim(revocation_reason)<>''),
      CHECK((scope_kind='global' AND scope_id IS NULL) OR (scope_kind<>'global' AND scope_id IS NOT NULL)),
      CHECK((revoked_at IS NULL AND revoked_by IS NULL AND revocation_reason IS NULL) OR (revoked_at IS NOT NULL AND revoked_by IS NOT NULL AND revocation_reason IS NOT NULL)),
      CHECK(revoked_at IS NULL OR revoked_at>=granted_at)
    );
    CREATE UNIQUE INDEX uq_staff_permission_grants_active_scope
      ON staff_permission_grants(staff_id,permission_name,scope_kind,COALESCE(scope_id,'00000000-0000-0000-0000-000000000000'::uuid))
      WHERE revoked_at IS NULL;
    CREATE TABLE staff_delegations (
      delegation_id uuid PRIMARY KEY,
      grantor_staff_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
      grantee_staff_id uuid NOT NULL REFERENCES staff_accounts(staff_id),
      permission_name varchar(120) NOT NULL CHECK(btrim(permission_name)<>''),
      scope_kind varchar(40) NOT NULL CHECK(scope_kind IN ('global','intake','worker')),
      scope_id uuid,
      reason_text varchar(512) NOT NULL CHECK(btrim(reason_text)<>''),
      starts_at timestamptz NOT NULL,
      expires_at timestamptz NOT NULL,
      revoked_at timestamptz,
      revoked_by uuid REFERENCES staff_accounts(staff_id),
      revocation_reason varchar(512) CHECK(revocation_reason IS NULL OR btrim(revocation_reason)<>''),
      CHECK(grantor_staff_id<>grantee_staff_id),
      CHECK((scope_kind='global' AND scope_id IS NULL) OR (scope_kind<>'global' AND scope_id IS NOT NULL)),
      CHECK(expires_at>starts_at),
      CHECK((revoked_at IS NULL AND revoked_by IS NULL AND revocation_reason IS NULL) OR (revoked_at IS NOT NULL AND revoked_by IS NOT NULL AND revocation_reason IS NOT NULL)),
      CHECK(revoked_at IS NULL OR revoked_at>=starts_at)
    );
    CREATE INDEX ix_staff_permission_grants_staff_active
      ON staff_permission_grants(staff_id,permission_name) WHERE revoked_at IS NULL;
    CREATE INDEX ix_staff_delegations_grantee_active
      ON staff_delegations(grantee_staff_id,permission_name) WHERE revoked_at IS NULL;
    """)
    for table in TABLES:
        execute(f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner")
        execute(f"REVOKE ALL ON {table} FROM PUBLIC,golden_rose_runtime,golden_rose_migrator")
        execute(f"GRANT SELECT ON {table} TO golden_rose_runtime")


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM staff_accounts) "
            "OR EXISTS(SELECT 1 FROM staff_permission_grants) "
            "OR EXISTS(SELECT 1 FROM staff_delegations)"
        )
    ):
        raise RuntimeError("staff account data blocks downgrade before DDL")
    for table in TABLES:
        op.drop_table(table)
