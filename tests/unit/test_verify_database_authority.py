from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy.exc import SQLAlchemyError

from scripts.verify_database_authority import (
    _required_authenticated_probe_urls,
    evaluate_authority_snapshot,
    main,
    validate_database_identities,
)

ROOT = Path(__file__).resolve().parents[2]


def test_verify_database_authority_script_exists_at_expected_path() -> None:
    script_path = ROOT / "scripts" / "verify_database_authority.py"

    assert script_path.exists()


def _expected_snapshot() -> dict[str, object]:
    return {
        "roles": {
            "golden_rose_schema_owner": {
                "rolcanlogin": False,
                "rolsuper": False,
                "rolcreaterole": False,
                "rolcreatedb": False,
                "rolreplication": False,
                "rolbypassrls": False,
                "rolinherit": True,
            },
            "golden_rose_migrator": {
                "rolcanlogin": False,
                "rolsuper": False,
                "rolcreaterole": False,
                "rolcreatedb": False,
                "rolreplication": False,
                "rolbypassrls": False,
                "rolinherit": True,
            },
            "golden_rose_runtime": {
                "rolcanlogin": False,
                "rolsuper": False,
                "rolcreaterole": False,
                "rolcreatedb": False,
                "rolreplication": False,
                "rolbypassrls": False,
                "rolinherit": True,
            },
            "golden_rose_migration_login": {
                "rolcanlogin": True,
                "rolsuper": False,
                "rolcreaterole": False,
                "rolcreatedb": False,
                "rolreplication": False,
                "rolbypassrls": False,
                "rolinherit": True,
            },
            "golden_rose_runtime_login": {
                "rolcanlogin": True,
                "rolsuper": False,
                "rolcreaterole": False,
                "rolcreatedb": False,
                "rolreplication": False,
                "rolbypassrls": False,
                "rolinherit": True,
            },
        },
        "authority_memberships": [
            _membership("golden_rose_migrator", "golden_rose_schema_owner"),
            _membership("golden_rose_migration_login", "golden_rose_migrator"),
            _membership("golden_rose_runtime_login", "golden_rose_runtime"),
        ],
        "schema_owner": "golden_rose_schema_owner",
        "role_memberships": {
            "golden_rose_migrator": ["golden_rose_schema_owner"],
            "golden_rose_runtime": [],
        },
        "authenticated_role_memberships": {
            "golden_rose_migration_login": ["golden_rose_migrator"],
            "golden_rose_runtime_login": ["golden_rose_runtime"],
        },
        "migration_login_role": "golden_rose_migration_login",
        "runtime_login_role": "golden_rose_runtime_login",
        "table_owners": {
            "alembic_version": "golden_rose_schema_owner",
            "employers": "golden_rose_schema_owner",
            "employer_contacts": "golden_rose_schema_owner",
            "entity_authorities": "golden_rose_schema_owner",
            "command_receipts": "golden_rose_schema_owner",
            "audit_events": "golden_rose_schema_owner",
        },
        "function_owners": {
            "deny_mutation_on_append_only_tables": "golden_rose_schema_owner",
            "populate_employer_revision_compatibility_fields": "golden_rose_schema_owner",
            "populate_command_receipt_revision_compatibility_fields": "golden_rose_schema_owner",
        },
        "public_table_privileges": {},
        "runtime_table_privileges": {
            "alembic_version": ["SELECT"],
            "employers": ["INSERT", "SELECT", "UPDATE"],
            "employer_contacts": ["INSERT", "SELECT"],
            "entity_authorities": ["INSERT", "SELECT"],
            "command_receipts": ["INSERT", "SELECT"],
            "audit_events": ["INSERT", "SELECT"],
        },
        "runtime_schema_privileges": ["USAGE"],
        "runtime_function_privileges": {
            "deny_mutation_on_append_only_tables": [],
            "populate_employer_revision_compatibility_fields": [],
            "populate_command_receipt_revision_compatibility_fields": [],
        },
        "default_privileges": {
            "tables": ["INSERT", "SELECT"],
            "sequences": ["SELECT", "USAGE"],
            "functions": [],
        },
        "public_default_privileges": {
            "tables": [],
            "sequences": [],
            "functions": [],
        },
    }


def test_verify_database_authority_accepts_expected_snapshot() -> None:
    assert evaluate_authority_snapshot(_expected_snapshot()) == []


def test_verify_database_authority_fails_closed_on_runtime_append_only_update_drift() -> None:
    snapshot = _expected_snapshot()
    runtime_table_privileges = snapshot["runtime_table_privileges"]
    assert isinstance(runtime_table_privileges, dict)
    runtime_table_privileges["audit_events"] = ["INSERT", "SELECT", "UPDATE"]

    violations = evaluate_authority_snapshot(snapshot)

    assert any("audit_events" in violation and "UPDATE" in violation for violation in violations)


def test_verify_database_authority_fails_closed_on_direct_public_table_grant() -> None:
    snapshot = _expected_snapshot()
    snapshot["public_table_privileges"] = {"audit_events": ["SELECT", "INSERT"]}

    violations = evaluate_authority_snapshot(snapshot)

    assert any(
        "direct PUBLIC" in violation and "audit_events" in violation for violation in violations
    )


def test_verify_database_authority_fails_closed_on_function_ownership_drift() -> None:
    snapshot = _expected_snapshot()
    function_owners = snapshot["function_owners"]
    assert isinstance(function_owners, dict)
    function_owners["deny_mutation_on_append_only_tables"] = "unexpected_owner"

    violations = evaluate_authority_snapshot(snapshot)

    assert any("function owner drifted" in violation for violation in violations)


def test_verify_database_authority_fails_closed_on_authenticated_login_drift() -> None:
    snapshot = _expected_snapshot()
    authenticated_role_memberships = snapshot["authenticated_role_memberships"]
    assert isinstance(authenticated_role_memberships, dict)
    authenticated_role_memberships["golden_rose_runtime_login"] = [
        "golden_rose_runtime",
        "golden_rose_schema_owner",
    ]

    violations = evaluate_authority_snapshot(snapshot)

    assert any(
        "authenticated runtime login role golden_rose_runtime_login must inherit only "
        "golden_rose_runtime" in violation
        for violation in violations
    )


@pytest.mark.parametrize(
    "runtime_url, migration_url, expected_missing",
    [
        (None, "postgresql+psycopg://migration", "GOLDEN_ROSE_RUNTIME_DATABASE_URL"),
        ("postgresql+psycopg://runtime", None, "GOLDEN_ROSE_MIGRATION_DATABASE_URL"),
    ],
)
def test_verify_database_authority_requires_authenticated_probe_urls(
    monkeypatch: pytest.MonkeyPatch,
    runtime_url: str | None,
    migration_url: str | None,
    expected_missing: str,
) -> None:
    if runtime_url is None:
        monkeypatch.delenv("GOLDEN_ROSE_RUNTIME_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("GOLDEN_ROSE_RUNTIME_DATABASE_URL", runtime_url)
    if migration_url is None:
        monkeypatch.delenv("GOLDEN_ROSE_MIGRATION_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("GOLDEN_ROSE_MIGRATION_DATABASE_URL", migration_url)

    with pytest.raises(ValueError, match=expected_missing):
        _required_authenticated_probe_urls()


def test_verify_database_authority_rejects_mixed_database_identities() -> None:
    violations = validate_database_identities(
        {
            "authority": ("golden_rose", "10.0.0.2", 5432),
            "migration": ("golden_rose", "10.0.0.2", 5432),
            "runtime": ("other_database", "10.0.0.3", 5432),
        }
    )

    assert violations == [
        "database authority evidence must come from one database identity: "
        "authority=('golden_rose', '10.0.0.2', 5432), "
        "migration=('golden_rose', '10.0.0.2', 5432), "
        "runtime=('other_database', '10.0.0.3', 5432)"
    ]


def test_verify_database_authority_accepts_matching_database_identities() -> None:
    assert (
        validate_database_identities(
            {
                "authority": ("golden_rose", "10.0.0.2", 5432),
                "migration": ("golden_rose", "10.0.0.2", 5432),
                "runtime": ("golden_rose", "10.0.0.2", 5432),
            }
        )
        == []
    )


def test_verify_database_authority_main_fails_bounded_on_sqlalchemy_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(
        "GOLDEN_ROSE_RUNTIME_DATABASE_URL",
        "postgresql+psycopg://runtime:[REDACTED]@db.example/golden_rose",
    )
    monkeypatch.setenv(
        "GOLDEN_ROSE_MIGRATION_DATABASE_URL",
        "postgresql+psycopg://migration:[REDACTED]@db.example/golden_rose",
    )
    monkeypatch.setattr(
        "scripts.verify_database_authority.get_database_url",
        lambda: "postgresql+psycopg://authority:[REDACTED]@db.example/golden_rose",
    )

    def fail_identify_database(_database_url: str) -> tuple[str, str, int]:
        raise SQLAlchemyError(
            "could not connect to postgresql+psycopg://authority:[REDACTED]@db.example/golden_rose"
        )

    monkeypatch.setattr(
        "scripts.verify_database_authority.identify_database", fail_identify_database
    )

    assert main() == 1
    output = capsys.readouterr().out
    assert "database authority verification failed" in output
    assert "database connection boundary failed" in output
    assert "postgresql+psycopg" not in output
    assert "db.example" not in output


def _membership(member: str, granted: str, *, admin: bool = False) -> dict[str, object]:
    return {
        "member": member,
        "granted": granted,
        "grantor": "test_admin" if admin else "cloudsqlsuperuser",
        "grantor_superuser": admin,
        "admin_option": admin,
        "inherit_option": not admin,
        "set_option": not admin,
    }


def _managed_snapshot() -> dict[str, Any]:
    snapshot = cast(dict[str, Any], _expected_snapshot())
    snapshot["roles"]["cloudsqlsuperuser"] = {
        "rolcanlogin": True,
        "rolinherit": True,
        "rolcreatedb": True,
        "rolcreaterole": True,
        "rolsuper": False,
        "rolreplication": False,
        "rolbypassrls": False,
    }
    snapshot["authority_memberships"].extend(
        _membership("cloudsqlsuperuser", role, admin=True)
        for role in ("golden_rose_schema_owner", "golden_rose_migrator", "golden_rose_runtime")
    )
    return snapshot


def test_managed_catalog_graph_is_exact():
    assert evaluate_authority_snapshot(_managed_snapshot()) == []


@pytest.mark.parametrize(
    "drift",
    [
        "grantor",
        "missing_admin",
        "extra_admin",
        "admin_set",
        "admin_inherit",
        "admin_grantor",
        "unexpected_administrator",
        "retained_bootstrap",
        "extra_login_role",
        "login_createdb",
        "app_replication",
        "app_bypassrls",
        "duplicate",
        "restricted_admin",
        "managed_superuser",
        "missing_graph",
    ],
)
def test_managed_catalog_graph_rejects_drift(drift):
    snapshot = _managed_snapshot()
    rows = snapshot["authority_memberships"]
    if drift == "grantor":
        rows[0]["grantor"] = "retired_bootstrap"
    elif drift == "missing_admin":
        rows.pop()
    elif drift == "extra_admin":
        rows.append(_membership("cloudsqlsuperuser", "golden_rose_migration_login", admin=True))
    elif drift in ("admin_set", "admin_inherit"):
        rows[-1]["set_option" if drift == "admin_set" else "inherit_option"] = True
    elif drift == "admin_grantor":
        rows[-1]["grantor_superuser"] = False
    elif drift == "unexpected_administrator":
        rows[-1]["member"] = "unexpected_administrator"
    elif drift == "retained_bootstrap":
        rows.append(_membership("retained_bootstrap", "golden_rose_migrator"))
    elif drift == "extra_login_role":
        rows.append(_membership("golden_rose_runtime_login", "cloudsqlsuperuser"))
    elif drift == "login_createdb":
        snapshot["roles"]["golden_rose_migration_login"]["rolcreatedb"] = True
    elif drift in ("app_replication", "app_bypassrls"):
        attribute = "rolreplication" if drift == "app_replication" else "rolbypassrls"
        snapshot["roles"]["golden_rose_runtime"][attribute] = True
    elif drift == "duplicate":
        rows.append(dict(rows[0]))
    elif drift == "restricted_admin":
        rows[0]["admin_option"] = True
    elif drift == "managed_superuser":
        snapshot["roles"]["cloudsqlsuperuser"]["rolsuper"] = True
    elif drift == "missing_graph":
        snapshot.pop("authority_memberships")
    assert evaluate_authority_snapshot(snapshot)
