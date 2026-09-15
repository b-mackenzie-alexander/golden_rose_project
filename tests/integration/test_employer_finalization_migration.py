"""Isolated additive migration and fail-before-DDL refusal evidence."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from golden_rose.api.dependencies import get_staff_directory, get_staff_principal
from golden_rose.main import create_app
from tests.integration.api.test_employer_finalizations import reviewed_employer
from tests.integration.api.test_intake_finalizations import reviewed_worker
from tests.integration.api.test_intake_review_workflows import ROOT, command
from tests.integration.test_intake_finalization import DIRECTORY, FINALIZER
from tests.integration.test_intake_migrations import migrate
from tests.integration.test_intake_migrations import migration_database as migration_database


@pytest.fixture
def isolated_client(migration_database):
    migrate(migration_database, "head")
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: FINALIZER
    app.dependency_overrides[get_staff_directory] = lambda: DIRECTORY
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_worker_outputs_survive_employer_downgrade_and_reupgrade(
    isolated_client, migration_database
):
    target, body = reviewed_worker(isolated_client)
    result = command(isolated_client, f"{ROOT}/{target}/finalizations", body, 201).json()
    migrate(migration_database, "0008_intake_finalization", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM workers")) == 1
        assert connection.scalar(text("SELECT to_regclass('public.staffing_requests')")) is None
    migrate(migration_database, "head")
    current = isolated_client.get(f"{ROOT}/{target}")
    assert current.status_code == 200, current.text
    assert current.json()["finalization"] == result["finalization"]


def test_populated_employer_downgrade_preserves_head_before_ddl(
    isolated_client, migration_database
):
    target, body = reviewed_employer(isolated_client, "business")
    command(isolated_client, f"{ROOT}/{target}/finalizations", body, 201)
    with migration_database.connect() as connection:
        starting_revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    with pytest.raises(RuntimeError, match="before DDL"):
        migrate(migration_database, "0008_intake_finalization", downgrade=True)
    with migration_database.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == starting_revision
        )
        assert connection.scalar(text("SELECT count(*) FROM staffing_requests")) == 1


@pytest.mark.parametrize(
    "table", ["employer_contact_details", "employer_addresses", "worksites", "staffing_requests"]
)
def test_employer_tables_retain_minimum_runtime_grants(isolated_client, migration_database, table):
    with migration_database.connect() as connection:
        owner = connection.scalar(
            text("SELECT tableowner FROM pg_tables WHERE schemaname='public' AND tablename=:table"),
            {"table": table},
        )
        assert owner == "golden_rose_schema_owner"
        for privilege in ("SELECT", "INSERT"):
            assert connection.scalar(
                text("SELECT has_table_privilege('golden_rose_runtime',:table,:privilege)"),
                {"table": table, "privilege": privilege},
            )
        for privilege in ("UPDATE", "DELETE", "TRUNCATE"):
            assert not connection.scalar(
                text("SELECT has_table_privilege('golden_rose_runtime',:table,:privilege)"),
                {"table": table, "privilege": privilege},
            )
