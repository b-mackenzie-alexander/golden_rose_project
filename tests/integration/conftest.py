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


@pytest.fixture()
def clean_tables(connection) -> None:
    connection.execute(text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE"))
    connection.commit()
