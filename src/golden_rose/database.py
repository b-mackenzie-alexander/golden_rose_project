import os
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

ROLE_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,62}$")


def get_database_url() -> str:
    database_url = os.environ.get("GOLDEN_ROSE_DATABASE_URL")
    if not database_url:
        msg = "GOLDEN_ROSE_DATABASE_URL must be set"
        raise RuntimeError(msg)
    return database_url


def validate_database_role_identifier(role_name: str) -> str:
    if not ROLE_IDENTIFIER_PATTERN.fullmatch(role_name):
        msg = "database role identifier must be a lowercase PostgreSQL-safe identifier"
        raise RuntimeError(msg)
    return role_name


def assume_database_role(connection: Connection, role_name: str) -> None:
    validated_role = validate_database_role_identifier(role_name)
    connection.execute(text(f"SET ROLE {validated_role}"))


def create_database_engine() -> Engine:
    return create_engine(get_database_url(), future=True)
