from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from golden_rose.config import Settings
from golden_rose.database import assume_database_role, create_database_engine

EX_CONFIG = 78
EX_TEMPFAIL = 75
MIGRATION_ADVISORY_LOCK_KEY = 4_021_005
MIGRATION_ASSUMED_ROLE = "golden_rose_schema_owner"
ROOT = Path(__file__).resolve().parents[2]

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
GRANT golden_rose_schema_owner TO golden_rose_migrator WITH ADMIN OPTION;
GRANT golden_rose_migrator TO CURRENT_USER;
"""


def main() -> int:
    try:
        Settings()  # type: ignore[call-arg]
    except ValueError:
        return EX_CONFIG

    engine = create_database_engine()
    try:
        with engine.begin() as connection:
            lock_acquired = connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": MIGRATION_ADVISORY_LOCK_KEY},
            ).scalar_one()
            if not lock_acquired:
                return EX_TEMPFAIL

            connection.execute(text(INITIAL_DATABASE_AUTHORITY_BOOTSTRAP))
            assume_database_role(connection, MIGRATION_ASSUMED_ROLE)
            config = Config(str(ROOT / "alembic.ini"))
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
