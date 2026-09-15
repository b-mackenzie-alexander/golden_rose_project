import importlib.util
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.fixture
def migration():
    path = (
        Path(__file__).resolve().parents[2] / "migrations/versions/0008a_employer_finalization.py"
    )
    spec = importlib.util.spec_from_file_location("employer_finalization_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_employer_migration_is_additive_and_emits_exact_authority(migration):
    assert migration.down_revision == "0008_intake_finalization"
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context), context.begin_transaction():
        migration.upgrade()
    sql = output.getvalue()
    assert sql.startswith("BEGIN;") and sql.rstrip().endswith("COMMIT;")
    for kind, table in migration.TABLES.items():
        assert f"CREATE TABLE {table} (" in sql
        assert f"{kind}_id IS NOT NULL AND {kind}_id=entity_id" in sql
        assert f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner" in sql
        assert f"GRANT SELECT,INSERT ON TABLE {table} TO golden_rose_runtime" in sql
        assert f"CREATE TRIGGER deny_mutation_{table}" in sql
    assert "THEN 5 WHEN f.employer_address_id IS NULL THEN 6 ELSE 7" in sql
    assert "AND NOT COALESCE((" in sql
    assert "s.employer_address_id IS NOT DISTINCT FROM f.employer_address_id" in sql
    assert "e.xmin::text=pg_current_xact_id()::text" in sql
    assert "SECURITY DEFINER" not in sql
    assert "CREATE TABLE workers" not in sql


def test_employer_downgrade_refuses_before_ddl(migration, monkeypatch):
    emitted: list[str] = []
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = True
    monkeypatch.setattr(migration, "execute", emitted.append)
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    with pytest.raises(RuntimeError, match="before DDL"):
        migration.downgrade()
    assert len(emitted) == 1 and emitted[0].startswith("LOCK TABLE ")
