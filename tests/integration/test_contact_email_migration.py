from sqlalchemy import text

from tests.integration.test_intake_migrations import migrate
from tests.integration.test_intake_migrations import migration_database as migration_database


def test_contact_email_migration_adds_optional_columns_and_runtime_correction_grants(
    migration_database,
):
    migrate(migration_database, "0019_ext_calendar_imports")
    migrate(migration_database, "0020_contact_email_fields")

    with migration_database.connect() as connection:
        for table in ("worker_contacts", "employer_contact_details"):
            column = next(
                item
                for item in connection.execute(
                    text(
                        "SELECT column_name,is_nullable FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name=:table AND column_name='email'"
                    ),
                    {"table": table},
                ).mappings()
            )
            assert column == {"column_name": "email", "is_nullable": "YES"}
        for table, column in (
            ("worker_contacts", "email"),
            ("employer_contact_details", "email"),
        ):
            assert connection.scalar(
                text("SELECT has_column_privilege('golden_rose_runtime',:table,:column,'UPDATE')"),
                {"table": table, "column": column},
            )


def test_empty_contact_email_successor_downgrades_without_removing_prior_schema(
    migration_database,
):
    migrate(migration_database, "head")
    migrate(migration_database, "0019_ext_calendar_imports", downgrade=True)

    with migration_database.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0019_ext_calendar_imports"
        )
        for table in ("worker_contacts", "employer_contact_details"):
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name=:table AND column_name='email'"
                    ),
                    {"table": table},
                )
                == 0
            )
