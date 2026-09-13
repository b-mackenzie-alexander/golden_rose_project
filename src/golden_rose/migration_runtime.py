from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from golden_rose.config import DEVELOP_DEPLOYMENT_TARGET, Settings
from golden_rose.database import assume_database_role, create_database_engine

EX_CONFIG = 78
EX_TEMPFAIL = 75
MIGRATION_ADVISORY_LOCK_KEY = 4_021_005
MIGRATION_ASSUMED_ROLE = "golden_rose_schema_owner"

DATABASE_AUTHORITY_ROLE_COUNT_QUERY = """
SELECT count(*) AS golden_rose_database_authority_role_count
FROM pg_roles
WHERE rolname IN (
    'golden_rose_schema_owner',
    'golden_rose_migrator',
    'golden_rose_runtime'
)
"""

DATABASE_AUTHORITY_INITIALIZED_QUERY = """
WITH application_roles AS (
    SELECT oid, rolname, rolcanlogin, rolinherit, rolsuper, rolcreatedb,
           rolcreaterole, rolreplication, rolbypassrls
    FROM pg_roles
    WHERE rolname IN (
        'golden_rose_schema_owner',
        'golden_rose_migrator',
        'golden_rose_runtime'
    )
),
schema_owner_membership AS (
    SELECT member_role.rolname AS member_name, membership.admin_option,
           membership.inherit_option, membership.set_option
    FROM pg_auth_members AS membership
    JOIN pg_roles AS granted_role ON granted_role.oid = membership.roleid
    JOIN pg_roles AS member_role ON member_role.oid = membership.member
    WHERE granted_role.rolname = 'golden_rose_schema_owner'
),
migrator_membership AS (
    SELECT member_role.rolname AS member_name, member_role.rolcanlogin,
           member_role.rolsuper, member_role.rolcreatedb, member_role.rolcreaterole,
           member_role.rolreplication, member_role.rolbypassrls,
           membership.admin_option, membership.inherit_option, membership.set_option
    FROM pg_auth_members AS membership
    JOIN pg_roles AS granted_role ON granted_role.oid = membership.roleid
    JOIN pg_roles AS member_role ON member_role.oid = membership.member
    WHERE granted_role.rolname = 'golden_rose_migrator'
),
governed_outgoing_memberships AS (
    SELECT granted_role.rolname AS granted_name,
           member_role.rolname AS member_name,
           membership.admin_option, membership.inherit_option, membership.set_option
    FROM pg_auth_members AS membership
    JOIN pg_roles AS granted_role ON granted_role.oid = membership.roleid
    JOIN pg_roles AS member_role ON member_role.oid = membership.member
    WHERE member_role.rolname IN (
        'golden_rose_schema_owner',
        'golden_rose_migrator',
        'golden_rose_runtime',
        current_user
    )
)
SELECT (
    (SELECT count(*) = 3
       AND bool_and(NOT rolcanlogin AND rolinherit AND NOT rolsuper
                    AND NOT rolcreatedb AND NOT rolcreaterole
                    AND NOT rolreplication AND NOT rolbypassrls)
     FROM application_roles)
    AND
    (SELECT count(*) = 1
       AND bool_and(member_name = 'golden_rose_migrator' AND NOT admin_option
                    AND inherit_option AND set_option)
     FROM schema_owner_membership)
    AND
    (SELECT count(*) = 1
       AND bool_and(member_name = current_user AND rolcanlogin
                    AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
                    AND NOT rolreplication AND NOT rolbypassrls
                    AND NOT admin_option AND inherit_option AND set_option)
     FROM migrator_membership)
    AND
    (SELECT count(*) = 2
       AND bool_and(
           (
               granted_name = 'golden_rose_schema_owner'
               AND member_name = 'golden_rose_migrator'
               AND NOT admin_option AND inherit_option AND set_option
           )
           OR
           (
               granted_name = 'golden_rose_migrator'
               AND member_name = current_user
               AND NOT admin_option AND inherit_option AND set_option
           )
       )
     FROM governed_outgoing_memberships)
) AS golden_rose_database_authority_initialized
"""

INITIAL_DATABASE_AUTHORITY_BOOTSTRAP = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'golden_rose_schema_owner') THEN
        CREATE ROLE golden_rose_schema_owner NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'golden_rose_migrator') THEN
        CREATE ROLE golden_rose_migrator NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'golden_rose_runtime') THEN
        CREATE ROLE golden_rose_runtime NOLOGIN;
    END IF;
END
$$;
ALTER SCHEMA public OWNER TO golden_rose_schema_owner;
GRANT golden_rose_schema_owner TO golden_rose_migrator;
GRANT golden_rose_migrator TO CURRENT_USER;
"""


# PostgreSQL 16 records role grants against the current grantor. Using the
# temporary login would prevent its retirement even after all objects moved.
MANAGED_INITIAL_DATABASE_AUTHORITY_BOOTSTRAP = """
SET LOCAL ROLE cloudsqlsuperuser;
CREATE ROLE golden_rose_schema_owner NOLOGIN;
CREATE ROLE golden_rose_migrator NOLOGIN;
CREATE ROLE golden_rose_runtime NOLOGIN;
GRANT golden_rose_schema_owner TO golden_rose_migrator
    WITH ADMIN FALSE, INHERIT TRUE, SET TRUE;
GRANT golden_rose_migrator TO SESSION_USER
    WITH ADMIN FALSE, INHERIT TRUE, SET TRUE;
RESET ROLE;
ALTER SCHEMA public OWNER TO golden_rose_schema_owner;
"""

# Only the three automatic PG16 creator memberships are excluded from incoming
# application memberships. Their complete options, grantor, and managed role
# attributes are checked below; outgoing restricted-role checks stay unchanged.
MANAGED_DATABASE_AUTHORITY_INITIALIZED_QUERY = (
    DATABASE_AUTHORITY_INITIALIZED_QUERY.replace(
        "WHERE granted_role.rolname = 'golden_rose_schema_owner'",
        "WHERE granted_role.rolname = 'golden_rose_schema_owner' "
        "AND member_role.rolname <> 'cloudsqlsuperuser'",
    )
    .replace(
        "WHERE granted_role.rolname = 'golden_rose_migrator'",
        "WHERE granted_role.rolname = 'golden_rose_migrator' "
        "AND member_role.rolname <> 'cloudsqlsuperuser'",
    )
    .replace(
        ") AS golden_rose_database_authority_initialized",
        """
    AND (SELECT count(*) = 1 AND bool_and(
        member.rolcanlogin AND member.rolinherit AND NOT member.rolsuper
        AND NOT member.rolcreatedb AND NOT member.rolcreaterole
        AND NOT member.rolreplication AND NOT member.rolbypassrls
        AND NOT membership.admin_option AND membership.inherit_option
        AND membership.set_option)
        FROM pg_auth_members membership
        JOIN pg_roles granted ON granted.oid = membership.roleid
        JOIN pg_roles member ON member.oid = membership.member
        WHERE granted.rolname = 'golden_rose_runtime'
          AND member.rolname <> 'cloudsqlsuperuser')
    AND NOT EXISTS (
        SELECT 1 FROM pg_auth_members membership
        JOIN pg_roles granted ON granted.oid = membership.roleid
        JOIN pg_roles member ON member.oid = membership.member
        JOIN pg_roles grantor ON grantor.oid = membership.grantor
        WHERE granted.rolname = 'golden_rose_schema_owner'
          AND member.rolname = 'golden_rose_migrator'
          AND grantor.rolname <> 'cloudsqlsuperuser')
    AND (SELECT count(*) = 1 AND bool_and(
        rolcanlogin AND rolinherit AND rolcreatedb AND rolcreaterole
        AND NOT rolsuper AND NOT rolreplication AND NOT rolbypassrls)
        FROM pg_roles WHERE rolname = 'cloudsqlsuperuser')
    AND (SELECT count(*) = 3 AND count(DISTINCT granted.rolname) = 3 AND bool_and(
        membership.admin_option AND NOT membership.inherit_option
        AND NOT membership.set_option AND grantor.rolsuper)
        FROM pg_auth_members membership
        JOIN pg_roles granted ON granted.oid = membership.roleid
        JOIN pg_roles member ON member.oid = membership.member
        JOIN pg_roles grantor ON grantor.oid = membership.grantor
        WHERE member.rolname = 'cloudsqlsuperuser'
          AND granted.rolname IN ('golden_rose_schema_owner',
              'golden_rose_migrator', 'golden_rose_runtime'))
) AS golden_rose_database_authority_initialized
""",
    )
)


def main() -> int:
    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValueError:
        return EX_CONFIG

    managed_target = (
        settings.environment == "develop"
        and settings.deployment_target == DEVELOP_DEPLOYMENT_TARGET
    )
    engine = create_database_engine()
    try:
        with engine.begin() as connection:
            lock_acquired = connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": MIGRATION_ADVISORY_LOCK_KEY},
            ).scalar_one()
            if not lock_acquired:
                return EX_TEMPFAIL

            role_count = int(
                connection.execute(text(DATABASE_AUTHORITY_ROLE_COUNT_QUERY)).scalar_one()
            )
            if role_count == 0:
                connection.execute(
                    text(
                        MANAGED_INITIAL_DATABASE_AUTHORITY_BOOTSTRAP
                        if managed_target
                        else INITIAL_DATABASE_AUTHORITY_BOOTSTRAP
                    )
                )
            elif (
                role_count != 3
                or not connection.execute(
                    text(
                        MANAGED_DATABASE_AUTHORITY_INITIALIZED_QUERY
                        if managed_target
                        else DATABASE_AUTHORITY_INITIALIZED_QUERY
                    )
                ).scalar_one()
            ):
                return EX_CONFIG
            assume_database_role(connection, MIGRATION_ASSUMED_ROLE)
            # Docker installs the package in site-packages; Alembic stays in WORKDIR /app.
            config = Config(str(Path.cwd() / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            connection.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": MIGRATION_ADVISORY_LOCK_KEY},
            )
    finally:
        engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
