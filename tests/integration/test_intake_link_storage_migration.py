"""Closed link storage upgrades preserve populated predecessor outputs."""

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from golden_rose.api.dependencies import get_staff_directory, get_staff_principal
from golden_rose.main import create_app
from tests.integration.api.test_employer_finalizations import reviewed_employer
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_intake_finalization import DIRECTORY, FINALIZER
from tests.integration.test_intake_migrations import migrate
from tests.integration.test_intake_migrations import migration_database as migration_database


@pytest.mark.parametrize("kind", ["worker", "household", "business"])
def test_populated_predecessor_upgrade_and_storage_downgrade_preserve_outputs(
    migration_database, kind
):
    migrate(migration_database, "0008a_employer_finalization")
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: FINALIZER
    app.dependency_overrides[get_staff_directory] = lambda: DIRECTORY
    with TestClient(app, raise_server_exceptions=False) as client:
        target, body = (
            reviewed_worker(client) if kind == "worker" else reviewed_employer(client, kind)
        )
        original = command(client, f"{ROOT}/{target}/finalizations", body, 201).json()
        migrate(migration_database, "0008b_intake_link_storage")
        with migration_database.connect() as connection:
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "0008b_intake_link_storage"
            )
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM intakes WHERE worker_id IS NOT NULL "
                        "OR employer_id IS NOT NULL"
                    )
                )
                == 0
            )
        response = client.get(f"{ROOT}/{target}")
        assert response.status_code == 200, response.text
        assert response.json()["finalization"] == original["finalization"]
        migrate(migration_database, "0008a_employer_finalization", downgrade=True)
        migrate(migration_database, "0008b_intake_link_storage")
        assert client.get(f"{ROOT}/{target}").json()["finalization"] == original["finalization"]


def test_link_storage_keeps_inherited_write_rejection(migration_database):
    migrate(migration_database, "0008b_intake_link_storage")
    with pytest.raises(IntegrityError) as error, migration_database.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO intake_links(intake_id) VALUES('22222222-2222-4222-8222-222222222222')"
            )
        )
    assert isinstance(error.value.orig, psycopg.Error)
    assert error.value.orig.diag.constraint_name in {
        "ck_intake_links_not_available",
        "ck_intake_links_parent_shape",
    }
    with migration_database.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM intake_links")) == 0
        assert not connection.scalar(
            text(
                "SELECT has_column_privilege('golden_rose_runtime','intakes','worker_id','UPDATE')"
            )
        )
        assert not connection.scalar(
            text(
                "SELECT has_column_privilege('golden_rose_runtime','intake_links',"
                "'worker_contact_id','UPDATE')"
            )
        )


def test_concrete_parent_foreign_keys_are_validated(migration_database):
    migrate(migration_database, "0008b_intake_link_storage")
    with migration_database.connect() as connection:
        rows = (
            connection.execute(
                text("""
            SELECT conname, convalidated, condeferrable, condeferred
            FROM pg_constraint WHERE conrelid='intake_links'::regclass
              AND conname LIKE 'fk_intake_links_%' AND conname<>'fk_intake_links_intake'
        """)
            )
            .mappings()
            .all()
        )
        assert len(rows) == 9
        assert all(
            row["convalidated"] and row["condeferrable"] and row["condeferred"] for row in rows
        )
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM pg_constraint WHERE conrelid='intakes'::regclass "
                    "AND conname='ck_intakes_links_not_available' AND convalidated"
                )
            )
            == 1
        )
