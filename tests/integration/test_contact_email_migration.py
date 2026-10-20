import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.main import create_app
from tests.integration.api.test_intakes import PRINCIPAL, ROOT, safe
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


def test_fresh_contact_email_migration_accepts_email_in_draft_content(migration_database):
    migrate(migration_database, "head")
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: PRINCIPAL

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            ROOT,
            headers={"Idempotency-Key": "11111111-1111-4111-8111-111111111111"},
            json={
                "kind": "worker",
                "content": {"phone": "+12025550123", "email": "worker@example.test"},
            },
        )

    safe(response, 201)
    assert response.json()["current"]["candidate"]["email"] == "worker@example.test"


def test_contact_email_draft_blocks_downgrade_before_constraint_removal(migration_database):
    migrate(migration_database, "head")
    app = create_app(engine_factory=lambda: migration_database)
    app.dependency_overrides[get_staff_principal] = lambda: PRINCIPAL

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            ROOT,
            headers={"Idempotency-Key": "11111111-1111-4111-8111-111111111112"},
            json={
                "kind": "worker",
                "content": {"phone": "+12025550123", "email": "worker@example.test"},
            },
        )
    safe(response, 201)

    with pytest.raises(RuntimeError, match="contact email data blocks downgrade before DDL"):
        migrate(migration_database, "0019_ext_calendar_imports", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0021_staff_google_binding"
        )
