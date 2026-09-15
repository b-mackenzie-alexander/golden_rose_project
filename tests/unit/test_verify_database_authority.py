from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy.exc import SQLAlchemyError

from scripts.verify_database_authority import (
    EXPECTED_INTAKE_CONSTRAINTS,
    EXPECTED_INTAKE_TRIGGERS,
    _required_authenticated_probe_urls,
    evaluate_authority_snapshot,
    main,
    validate_database_identities,
)

ROOT = Path(__file__).resolve().parents[2]


def test_verify_database_authority_script_exists_at_expected_path() -> None:
    script_path = ROOT / "scripts" / "verify_database_authority.py"

    assert script_path.exists()


def _predecessor_snapshot() -> dict[str, object]:
    return {
        "intake_constraints": dict(EXPECTED_INTAKE_CONSTRAINTS),
        "intake_triggers": {
            key: {"function": function, "enabled": "O", "deferred": deferred}
            for key, (function, deferred) in EXPECTED_INTAKE_TRIGGERS.items()
        },
        "security_definer_functions": [],
        "runtime_update_columns": {
            "work_interests": [
                "version",
                "label_en",
                "label_es",
                "active",
                "updated_at",
                "updated_by",
            ],
            "intakes": ["content", "version", "content_version", "updated_at", "updated_by"],
            "intake_addresses": ["line1", "line2", "locality", "region", "postal_code", "country"],
        },
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
            "work_interests": "golden_rose_schema_owner",
            "work_interest_versions": "golden_rose_schema_owner",
            "intake_reviews": "golden_rose_schema_owner",
            "intake_review_payloads": "golden_rose_schema_owner",
            "intake_follow_up_events": "golden_rose_schema_owner",
            "intake_history_payloads": "golden_rose_schema_owner",
            "alembic_version": "golden_rose_schema_owner",
            "employers": "golden_rose_schema_owner",
            "employer_contacts": "golden_rose_schema_owner",
            "entity_authorities": "golden_rose_schema_owner",
            "command_receipts": "golden_rose_schema_owner",
            "audit_events": "golden_rose_schema_owner",
            "intakes": "golden_rose_schema_owner",
            "intake_addresses": "golden_rose_schema_owner",
            "intake_links": "golden_rose_schema_owner",
            "command_results": "golden_rose_schema_owner",
        },
        "function_owners": {
            "guard_intake_workflow_authority": "golden_rose_schema_owner",
            "guard_work_interest_identity": "golden_rose_schema_owner",
            "guard_work_interest_authority": "golden_rose_schema_owner",
            "deny_mutation_on_append_only_tables": "golden_rose_schema_owner",
            "populate_employer_revision_compatibility_fields": "golden_rose_schema_owner",
            "populate_command_receipt_revision_compatibility_fields": "golden_rose_schema_owner",
            "populate_legacy_command_result": "golden_rose_schema_owner",
            "guard_intake_identity": "golden_rose_schema_owner",
            "guard_intake_write_authority": "golden_rose_schema_owner",
            "guard_intake_address_authority": "golden_rose_schema_owner",
        },
        "public_table_privileges": {},
        "runtime_table_privileges": {
            "work_interests": ["INSERT", "SELECT"],
            "work_interest_versions": ["INSERT", "SELECT"],
            "intake_reviews": ["INSERT", "SELECT"],
            "intake_review_payloads": ["INSERT", "SELECT"],
            "intake_follow_up_events": ["INSERT", "SELECT"],
            "intake_history_payloads": ["INSERT", "SELECT"],
            "alembic_version": ["SELECT"],
            "employers": ["INSERT", "SELECT", "UPDATE"],
            "employer_contacts": ["INSERT", "SELECT"],
            "entity_authorities": ["INSERT", "SELECT"],
            "command_receipts": ["INSERT", "SELECT"],
            "audit_events": ["INSERT", "SELECT"],
            "intakes": ["INSERT", "SELECT"],
            "intake_addresses": ["INSERT", "SELECT"],
            "intake_links": ["INSERT", "SELECT"],
            "command_results": ["INSERT", "SELECT"],
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


def _expected_snapshot() -> dict[str, object]:
    from scripts import verify_database_authority as verifier

    snapshot = _predecessor_snapshot()
    snapshot.update(
        {
            "table_owners": dict.fromkeys(
                verifier.EXPECTED_SCHEMA_OWNER_OBJECTS, verifier.SCHEMA_OWNER_ROLE
            ),
            "function_owners": dict.fromkeys(
                verifier.EXPECTED_SCHEMA_OWNER_FUNCTIONS, verifier.SCHEMA_OWNER_ROLE
            ),
            "runtime_table_privileges": {
                k: sorted(v) for k, v in verifier.EXPECTED_RUNTIME_TABLE_PRIVILEGES.items()
            },
            "runtime_function_privileges": {
                k: sorted(v) for k, v in verifier.EXPECTED_RUNTIME_FUNCTION_PRIVILEGES.items()
            },
            "runtime_update_columns": {
                k: sorted(v) for k, v in verifier.EXPECTED_RUNTIME_UPDATE_COLUMNS.items()
            },
            "public_function_privileges": [],
            "trigger_definitions": dict(verifier.EXPECTED_TRIGGER_DEFINITIONS),
            "function_hashes": dict(verifier.EXPECTED_FUNCTION_HASHES),
            "unique_indexes": dict(verifier.EXPECTED_UNIQUE_INDEXES),
        }
    )
    return snapshot


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


def _cloud_sql_snapshot() -> dict[str, Any]:
    snapshot = _managed_snapshot()
    snapshot["authority_memberships"] = snapshot["authority_memberships"][:3]
    for row in snapshot["authority_memberships"]:
        row["grantor"] = "platform_superuser"
        row["grantor_superuser"] = True
    return snapshot


def test_cloud_sql_native_catalog_graph_is_exact() -> None:
    assert evaluate_authority_snapshot(_cloud_sql_snapshot()) == []


@pytest.mark.parametrize(
    "drift",
    [
        "non_superuser",
        "mixed_grantors",
        "creator_row",
        "extra_login",
        "admin",
        "missing",
        "duplicate",
    ],
)
def test_cloud_sql_native_catalog_graph_rejects_drift(drift: str) -> None:
    snapshot = _cloud_sql_snapshot()
    rows = snapshot["authority_memberships"]
    if drift == "non_superuser":
        rows[0]["grantor_superuser"] = False
    elif drift == "mixed_grantors":
        rows[0]["grantor"] = "other_superuser"
    elif drift == "creator_row":
        rows.append(_membership("cloudsqlsuperuser", "golden_rose_runtime", admin=True))
    elif drift == "extra_login":
        rows.append(_membership("retained_bootstrap", "golden_rose_migrator"))
    elif drift == "admin":
        rows[1]["admin_option"] = True
    elif drift == "missing":
        rows.pop()
    elif drift == "duplicate":
        rows.append(dict(rows[0]))
    assert evaluate_authority_snapshot(snapshot)


@pytest.mark.parametrize(
    "key,value",
    [
        ("intake_constraints", {"intakes.ck_intakes_content_kind": "CHECK (true)"}),
        ("intake_triggers", {}),
        ("runtime_update_columns", {"intakes": ["content", "intake_id"]}),
        ("security_definer_functions", ["guard_intake_identity"]),
    ],
)
def test_intake_authority_drift_fails_closed(key, value):
    snapshot = _expected_snapshot()
    snapshot[key] = value
    assert evaluate_authority_snapshot(snapshot)


def test_ci_checks_downgrade_on_verified_empty_disposable_successor():
    workflow = (ROOT / ".github/workflows/application-quality.yml").read_text()
    create = workflow.index("CREATE DATABASE golden_rose_downgrade_test")
    empty_check = workflow.index("SELECT count(*) FROM {table}", create)
    downgrade = workflow.index("if uv run alembic downgrade base", empty_check)
    refusal = workflow.index("operator-reviewed role handoff", downgrade)
    assert create < empty_check < downgrade < refusal
    assert "DROP DATABASE" not in workflow
    assert 'assert os.environ.get("GITHUB_ACTIONS") == "true"' in workflow
    assert '"127.0.0.1", 55432, "golden_rose_test", "golden_rose_test"' in workflow
