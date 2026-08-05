import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_database_url() -> str:
    database_url = os.environ.get("GOLDEN_ROSE_DATABASE_URL")
    if not database_url:
        msg = "GOLDEN_ROSE_DATABASE_URL must be set"
        raise RuntimeError(msg)
    return database_url


def create_database_engine() -> Engine:
    return create_engine(get_database_url(), future=True)
