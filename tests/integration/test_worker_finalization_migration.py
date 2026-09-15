"""Worker schema authority and rollback on an isolated disposable database."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.integration.test_intake_commands import create
from tests.integration.test_intake_finalization import (
    FINALIZER,
    finalize,
    review,
)
from tests.integration.test_intake_migrations import (
    migrate,
)
from tests.integration.test_intake_migrations import (
    migration_database as migration_database,
)


def test_empty_worker_successor_downgrades_to_pr_b(migration_database):
    migrate(migration_database, "head")
    migrate(migration_database, "0007_intake_review_follow_up", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.scalar(text("SELECT to_regclass('public.workers')")) is None
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0007_intake_review_follow_up"
        )
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM pg_constraint WHERE "
                    "conname='uq_command_results_single_result'"
                )
            )
            == 1
        )
    migrate(migration_database, "head")


def test_populated_successor_downgrade_stops_before_ddl(migration_database):
    from uuid import UUID

    migrate(migration_database, "head")
    with migration_database.connect() as connection:
        starting_revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    with Session(migration_database) as session:
        created, _ = create(
            session,
            principal=FINALIZER,
            content={
                "full_name": "Fictional Migration Worker",
                "phone": "+12025550123",
                "interests": {"other_description": "Fictional gardening"},
                "availability": {"mode": "flexible"},
                "residential_address": {
                    "line1": "10 Fictional Road",
                    "locality": "Fictional City",
                    "country": "US",
                    "region": "NY",
                    "postal_code": "10001",
                },
            },
        )
        intake = UUID(created["current"]["summary"]["intake_id"])
        finalize(session, intake, review(session, intake, 1))
    with pytest.raises(RuntimeError, match="before DDL"):
        migrate(migration_database, "0007_intake_review_follow_up", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM workers")) == 1
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            starting_revision
        )


def test_unaudited_worker_insert_cannot_commit(clean_tables, connection):
    connection.execute(
        text("""
      INSERT INTO workers(worker_id,full_name,version,created_at,updated_at,created_by,updated_by)
      VALUES(gen_random_uuid(),'Fictional Unauthorized',1,now(),now(),
             '22222222-2222-4222-8222-222222222222','22222222-2222-4222-8222-222222222222')
    """)
    )
    with pytest.raises(IntegrityError):
        connection.commit()
    connection.rollback()
    assert connection.scalar(text("SELECT count(*) FROM workers")) == 0


@pytest.mark.parametrize(
    "table",
    [
        "workers",
        "worker_contacts",
        "worker_residences",
        "worker_preferences",
        "worker_interest_selections",
        "intake_finalizations",
    ],
)
def test_worker_tables_have_minimal_runtime_grants(connection, table):
    assert connection.scalar(
        text("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid=to_regclass(:table)"),
        {"table": table},
    ) == ("golden_rose_schema_owner")
    for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
        permitted = connection.scalar(
            text("SELECT has_table_privilege('golden_rose_runtime',:table,:privilege)"),
            {"table": table, "privilege": privilege},
        )
        assert permitted == (privilege in {"SELECT", "INSERT"})
