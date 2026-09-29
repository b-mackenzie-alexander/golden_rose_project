import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"
VERSIONS_DIR = MIGRATIONS_DIR / "versions"


@pytest.fixture(scope="session")
def database_url() -> str:
    database_url_value = os.environ.get("GOLDEN_ROSE_DATABASE_URL")
    if not database_url_value:
        pytest.fail("GOLDEN_ROSE_DATABASE_URL must be set for integration tests")
    return database_url_value


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    db_engine = create_engine(database_url, future=True)
    try:
        yield db_engine
    finally:
        db_engine.dispose()


@pytest.fixture()
def connection(engine: Engine):
    with engine.connect() as db_connection:
        yield db_connection


@pytest.fixture()
def session(engine: Engine):
    with Session(engine) as db_session:
        yield db_session


def clean_test_tables(connection) -> None:
    # These statement guards intentionally reject TRUNCATE, including CASCADE.
    # Only the disposable test database owner disables its exact cleanup guards.
    staff_account_tables = tuple(
        connection.execute(
            text("""
        SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname IN
          ('staff_account_lifecycle_events','staff_permission_grants',
           'staff_delegations','staff_accounts')
    """)
        )
        .scalars()
        .all()
    )
    guarded_tables = (
        connection.execute(
            text("""
        SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname IN
          ('intakes','intake_addresses','intake_links','command_results',
           'work_interests','work_interest_versions','intake_reviews','intake_review_payloads',
           'intake_follow_up_events','intake_history_payloads',
           'workers','worker_contacts','worker_residences','worker_preferences',
           'worker_interest_selections','intake_finalizations','employer_contact_details',
           'employer_addresses','worksites','staffing_requests',
           'shift_need_events',
           'canonical_corrections','canonical_correction_payloads',
           'canonical_review_heads','canonical_output_reviews','canonical_output_review_payloads')
    """)
        )
        .scalars()
        .all()
    )
    for table in guarded_tables:
        connection.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER deny_mutation_{table}"))
    targets = ", ".join(
        [
            "audit_events",
            "command_receipts",
            "employers",
            *staff_account_tables,
            *guarded_tables,
        ]
    )
    connection.execute(text(f"TRUNCATE TABLE {targets} CASCADE"))
    for table in guarded_tables:
        connection.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER deny_mutation_{table}"))


@pytest.fixture()
def clean_tables(connection) -> None:
    clean_test_tables(connection)
    connection.commit()
