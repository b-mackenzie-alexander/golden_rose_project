import subprocess
import sys

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError

from golden_rose.migration_runtime import main as migration_runtime_main
from scripts.verify_database_authority import (
    collect_authority_snapshot,
    evaluate_authority_snapshot,
)
from tests.integration.conftest import PROJECT_ROOT, VERSIONS_DIR

MIGRATION_LOGIN_ROLE = "golden_rose_migration_login"
RUNTIME_LOGIN_ROLE = "golden_rose_runtime_login"
MIGRATION_LOGIN_PASSWORD = "golden_rose_migration_login_pw"
RUNTIME_LOGIN_PASSWORD = "golden_rose_runtime_login_pw"


def test_database_authority_migration_file_exists_at_expected_path() -> None:
    migration_path = VERSIONS_DIR / "0005_database_authority.py"

    assert migration_path.exists()


def test_database_authority_migration_defines_generic_roles_and_never_commits_passwords() -> None:
    migration = (VERSIONS_DIR / "0005_database_authority.py").read_text(encoding="utf-8")

    required_fragments = [
        'SCHEMA_OWNER_ROLE = "golden_rose_schema_owner"',
        'MIGRATOR_ROLE = "golden_rose_migrator"',
        'RUNTIME_ROLE = "golden_rose_runtime"',
        "NOLOGIN",
        "ALTER SCHEMA public OWNER TO {SCHEMA_OWNER_ROLE}",
        "IF CURRENT_USER <> '{SCHEMA_OWNER_ROLE}'",
    ]
    for fragment in required_fragments:
        assert fragment in migration

    forbidden_fragments = [
        "PASSWORD",
        "password",
        "LOGIN PASSWORD",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in migration


def _alembic_config() -> Config:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")
    return alembic_config


def _quoted_ident(role_name: str) -> str:
    return '"' + role_name.replace('"', '""') + '"'


def _quoted_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _login_database_url(database_url: str, username: str, password: str) -> str:
    return (
        make_url(database_url)
        .set(username=username, password=password)
        .render_as_string(hide_password=False)
    )


def _make_login_engine(database_url: str, username: str, password: str) -> Engine:
    return create_engine(_login_database_url(database_url, username, password), future=True)


def _create_authenticated_login_roles(connection) -> None:
    connection.execute(text(f"DROP ROLE IF EXISTS {_quoted_ident(MIGRATION_LOGIN_ROLE)}"))
    connection.execute(text(f"DROP ROLE IF EXISTS {_quoted_ident(RUNTIME_LOGIN_ROLE)}"))
    migration_login_sql = (
        f"CREATE ROLE {_quoted_ident(MIGRATION_LOGIN_ROLE)} LOGIN PASSWORD "
        f"{_quoted_literal(MIGRATION_LOGIN_PASSWORD)}"
    )
    connection.execute(text(migration_login_sql))
    runtime_login_sql = (
        f"CREATE ROLE {_quoted_ident(RUNTIME_LOGIN_ROLE)} LOGIN PASSWORD "
        f"{_quoted_literal(RUNTIME_LOGIN_PASSWORD)}"
    )
    connection.execute(text(runtime_login_sql))
    connection.execute(text(f"GRANT golden_rose_migrator TO {_quoted_ident(MIGRATION_LOGIN_ROLE)}"))
    connection.execute(text(f"GRANT golden_rose_runtime TO {_quoted_ident(RUNTIME_LOGIN_ROLE)}"))
    connection.commit()


def _drop_authenticated_login_roles(connection) -> None:
    connection.execute(text(f"DROP ROLE IF EXISTS {_quoted_ident(MIGRATION_LOGIN_ROLE)}"))
    connection.execute(text(f"DROP ROLE IF EXISTS {_quoted_ident(RUNTIME_LOGIN_ROLE)}"))
    connection.commit()


def _drop_database_authority_roles(connection) -> None:
    connection.execute(
        text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'golden_rose_migrator')
                   AND EXISTS (
                        SELECT 1 FROM pg_roles WHERE rolname = 'golden_rose_schema_owner'
                   ) THEN
                    REVOKE golden_rose_schema_owner FROM golden_rose_migrator;
                END IF;
            END
            $$;
            """
        )
    )
    connection.execute(
        text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'golden_rose_schema_owner') THEN
                    DROP OWNED BY golden_rose_schema_owner;
                END IF;
            END
            $$;
            """
        )
    )
    connection.execute(text("DROP ROLE IF EXISTS golden_rose_runtime"))
    connection.execute(text("DROP ROLE IF EXISTS golden_rose_migrator"))
    connection.execute(text("DROP ROLE IF EXISTS golden_rose_schema_owner"))
    connection.commit()


def test_migration_runtime_bootstraps_clean_database_before_assuming_schema_owner(
    engine: Engine,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    with engine.connect() as connection:
        _drop_authenticated_login_roles(connection)
        _drop_database_authority_roles(connection)

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "test")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv("GOLDEN_ROSE_DATABASE_URL", database_url)
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")

    assert migration_runtime_main() == 0

    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0005_database_authority"
        )
        assert connection.execute(
            text("SELECT pg_has_role(CURRENT_USER, 'golden_rose_migrator', 'member')")
        ).scalar_one()


@pytest.fixture()
def authenticated_login_roles(database_url: str) -> dict[str, str]:
    return {
        "migration_login_role": MIGRATION_LOGIN_ROLE,
        "runtime_login_role": RUNTIME_LOGIN_ROLE,
        "migration_database_url": _login_database_url(
            database_url,
            MIGRATION_LOGIN_ROLE,
            MIGRATION_LOGIN_PASSWORD,
        ),
        "runtime_database_url": _login_database_url(
            database_url,
            RUNTIME_LOGIN_ROLE,
            RUNTIME_LOGIN_PASSWORD,
        ),
    }


def _assert_sql_denied(engine: Engine, statement: str) -> None:
    with engine.connect() as connection, pytest.raises(SQLAlchemyError):
        connection.execute(text(statement))


def test_database_authority_live_verifier_accepts_upgraded_schema(
    connection,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)

    try:
        snapshot = collect_authority_snapshot(
            connection,
            migration_login_role=authenticated_login_roles["migration_login_role"],
            runtime_login_role=authenticated_login_roles["runtime_login_role"],
        )
    finally:
        _drop_authenticated_login_roles(connection)

    assert evaluate_authority_snapshot(snapshot) == []


def test_database_authority_live_verifier_fails_closed_on_runtime_privilege_drift(
    connection,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)

    try:
        transaction = connection.begin()
        try:
            connection.execute(text("GRANT UPDATE ON TABLE audit_events TO golden_rose_runtime"))
            snapshot = collect_authority_snapshot(
                connection,
                migration_login_role=authenticated_login_roles["migration_login_role"],
                runtime_login_role=authenticated_login_roles["runtime_login_role"],
            )
        finally:
            transaction.rollback()
    finally:
        _drop_authenticated_login_roles(connection)

    violations = evaluate_authority_snapshot(snapshot)

    assert any("audit_events" in violation and "UPDATE" in violation for violation in violations)


def test_database_authority_live_verifier_fails_closed_on_direct_public_table_grant(
    connection,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)

    try:
        transaction = connection.begin()
        try:
            connection.execute(text("GRANT SELECT, INSERT ON TABLE audit_events TO PUBLIC"))
            snapshot = collect_authority_snapshot(
                connection,
                migration_login_role=authenticated_login_roles["migration_login_role"],
                runtime_login_role=authenticated_login_roles["runtime_login_role"],
            )
        finally:
            transaction.rollback()
    finally:
        _drop_authenticated_login_roles(connection)

    violations = evaluate_authority_snapshot(snapshot)

    assert any(
        "direct PUBLIC" in violation and "audit_events" in violation for violation in violations
    )


def test_database_authority_live_verifier_fails_closed_on_function_ownership_drift(
    connection,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)

    try:
        transaction = connection.begin()
        try:
            connection.execute(
                text(
                    "ALTER FUNCTION public.deny_mutation_on_append_only_tables() "
                    "OWNER TO golden_rose_migrator"
                )
            )
            snapshot = collect_authority_snapshot(
                connection,
                migration_login_role=authenticated_login_roles["migration_login_role"],
                runtime_login_role=authenticated_login_roles["runtime_login_role"],
            )
        finally:
            transaction.rollback()
    finally:
        _drop_authenticated_login_roles(connection)

    violations = evaluate_authority_snapshot(snapshot)

    assert any("function owner drifted" in violation for violation in violations)


def test_database_authority_runtime_login_cannot_assume_owner_or_mutate_append_only_tables(
    connection,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)
    runtime_engine = _make_login_engine(
        authenticated_login_roles["runtime_database_url"],
        RUNTIME_LOGIN_ROLE,
        RUNTIME_LOGIN_PASSWORD,
    )
    try:
        _assert_sql_denied(runtime_engine, "SET ROLE golden_rose_schema_owner")
        _assert_sql_denied(
            runtime_engine,
            "UPDATE audit_events SET event_type = event_type WHERE 1 = 0",
        )
        _assert_sql_denied(runtime_engine, "TRUNCATE TABLE command_receipts")
        _assert_sql_denied(runtime_engine, "CREATE TABLE public.runtime_leak(id integer)")
        _assert_sql_denied(runtime_engine, "ALTER TABLE audit_events DISABLE TRIGGER ALL")
        _assert_sql_denied(
            runtime_engine,
            "GRANT golden_rose_schema_owner TO golden_rose_runtime",
        )
    finally:
        runtime_engine.dispose()
        _drop_authenticated_login_roles(connection)


def test_database_authority_migration_login_can_assume_only_schema_owner(
    connection,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)
    migration_engine = _make_login_engine(
        authenticated_login_roles["migration_database_url"],
        MIGRATION_LOGIN_ROLE,
        MIGRATION_LOGIN_PASSWORD,
    )
    try:
        with migration_engine.connect() as migration_connection:
            assert (
                migration_connection.execute(text("SELECT SESSION_USER")).scalar_one()
                == MIGRATION_LOGIN_ROLE
            )
            assert (
                migration_connection.execute(text("SELECT CURRENT_USER")).scalar_one()
                == MIGRATION_LOGIN_ROLE
            )
            migration_connection.execute(text("SET ROLE golden_rose_schema_owner"))
            assert (
                migration_connection.execute(text("SELECT CURRENT_USER")).scalar_one()
                == "golden_rose_schema_owner"
            )
            with pytest.raises(SQLAlchemyError):
                migration_connection.execute(text("SET ROLE golden_rose_runtime"))
    finally:
        migration_engine.dispose()
        _drop_authenticated_login_roles(connection)


def test_database_authority_verifier_script_passes_on_reviewed_head(
    connection,
    database_url: str,
    authenticated_login_roles: dict[str, str],
) -> None:
    command.upgrade(_alembic_config(), "head")
    _create_authenticated_login_roles(connection)

    try:
        result = subprocess.run(
            [sys.executable, "scripts/verify_database_authority.py"],
            cwd=PROJECT_ROOT,
            check=False,
            text=True,
            capture_output=True,
            env={
                "GOLDEN_ROSE_DATABASE_URL": database_url,
                "GOLDEN_ROSE_RUNTIME_DATABASE_URL": authenticated_login_roles[
                    "runtime_database_url"
                ],
                "GOLDEN_ROSE_MIGRATION_DATABASE_URL": authenticated_login_roles[
                    "migration_database_url"
                ],
            },
        )
    finally:
        _drop_authenticated_login_roles(connection)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "database authority verification passed" in result.stdout
