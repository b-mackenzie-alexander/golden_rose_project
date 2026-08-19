"""establish database authority lifecycle

Revision ID: 0005_database_authority
Revises: 0004_employer_contact_authority
Create Date: 2026-08-16 20:30:00
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_database_authority"
down_revision = "0004_employer_contact_authority"
branch_labels = None
depends_on = None

SCHEMA_OWNER_ROLE = "golden_rose_schema_owner"
MIGRATOR_ROLE = "golden_rose_migrator"
RUNTIME_ROLE = "golden_rose_runtime"

CREATE_DATABASE_AUTHORITY_ROLES = f"""
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{SCHEMA_OWNER_ROLE}') THEN
        CREATE ROLE {SCHEMA_OWNER_ROLE} NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{MIGRATOR_ROLE}') THEN
        CREATE ROLE {MIGRATOR_ROLE} NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{RUNTIME_ROLE}') THEN
        CREATE ROLE {RUNTIME_ROLE} NOLOGIN;
    END IF;
END
$$;
"""

REVOKE_OPEN_SCHEMA_ACCESS = f"""
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO {RUNTIME_ROLE};
ALTER SCHEMA public OWNER TO {SCHEMA_OWNER_ROLE};
DO $$
BEGIN
    IF CURRENT_USER <> '{SCHEMA_OWNER_ROLE}' THEN
        GRANT {SCHEMA_OWNER_ROLE} TO {MIGRATOR_ROLE};
    END IF;
END
$$;
"""

ALTER_DEFAULT_PRIVILEGES = f"""
ALTER DEFAULT PRIVILEGES FOR ROLE {SCHEMA_OWNER_ROLE} IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE {SCHEMA_OWNER_ROLE} IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE {SCHEMA_OWNER_ROLE} IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE {SCHEMA_OWNER_ROLE} REVOKE ALL ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE {SCHEMA_OWNER_ROLE} IN SCHEMA public GRANT SELECT, INSERT ON TABLES TO {RUNTIME_ROLE};
ALTER DEFAULT PRIVILEGES FOR ROLE {SCHEMA_OWNER_ROLE} IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {RUNTIME_ROLE};
"""

OWNERSHIP_SQL = [
    f"ALTER TABLE public.alembic_version OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER TABLE public.employers OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER TABLE public.employer_contacts OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER TABLE public.entity_authorities OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER TABLE public.command_receipts OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER TABLE public.audit_events OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER FUNCTION public.deny_mutation_on_append_only_tables() OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER FUNCTION public.populate_employer_revision_compatibility_fields() OWNER TO {SCHEMA_OWNER_ROLE};",
    f"ALTER FUNCTION public.populate_command_receipt_revision_compatibility_fields() OWNER TO {SCHEMA_OWNER_ROLE};",
]

GRANT_SQL = [
    f"REVOKE ALL ON TABLE public.alembic_version FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"GRANT SELECT ON TABLE public.alembic_version TO {RUNTIME_ROLE};",
    f"REVOKE ALL ON TABLE public.employers FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"GRANT SELECT, INSERT, UPDATE ON TABLE public.employers TO {RUNTIME_ROLE};",
    f"REVOKE ALL ON TABLE public.employer_contacts FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"GRANT SELECT, INSERT ON TABLE public.employer_contacts TO {RUNTIME_ROLE};",
    f"REVOKE ALL ON TABLE public.entity_authorities FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"GRANT SELECT, INSERT ON TABLE public.entity_authorities TO {RUNTIME_ROLE};",
    f"REVOKE ALL ON TABLE public.command_receipts FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"GRANT SELECT, INSERT ON TABLE public.command_receipts TO {RUNTIME_ROLE};",
    f"REVOKE ALL ON TABLE public.audit_events FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"GRANT SELECT, INSERT ON TABLE public.audit_events TO {RUNTIME_ROLE};",
    f"REVOKE ALL ON FUNCTION public.deny_mutation_on_append_only_tables() FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"REVOKE ALL ON FUNCTION public.populate_employer_revision_compatibility_fields() FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
    f"REVOKE ALL ON FUNCTION public.populate_command_receipt_revision_compatibility_fields() FROM PUBLIC, {RUNTIME_ROLE}, {MIGRATOR_ROLE};",
]


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text(CREATE_DATABASE_AUTHORITY_ROLES))
    bind.execute(sa.text(REVOKE_OPEN_SCHEMA_ACCESS))
    bind.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))
    for statement in OWNERSHIP_SQL:
        bind.execute(sa.text(statement))
    for statement in GRANT_SQL:
        bind.execute(sa.text(statement))
    bind.execute(sa.text(ALTER_DEFAULT_PRIVILEGES))


def downgrade() -> None:
    msg = (
        "database authority lifecycle downgrade is intentionally unsupported without "
        "an operator-reviewed role handoff"
    )
    raise RuntimeError(msg)
