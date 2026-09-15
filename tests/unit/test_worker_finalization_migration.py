"""Offline migration generation and fail-before-DDL downgrade checks."""

import importlib.util
from io import StringIO
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.fixture
def migration() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "migrations/versions/0008_intake_finalization.py"
    spec = importlib.util.spec_from_file_location("worker_finalization_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_migration_generates_transactional_ddl_with_concrete_authority(migration):
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql",
        opts={
            "as_sql": True,
            "output_buffer": output,
        },
    )
    with Operations.context(context), context.begin_transaction():
        migration.upgrade()
    sql = output.getvalue()
    assert sql.startswith("BEGIN;") and sql.rstrip().endswith("COMMIT;")
    assert "CREATE TABLE worker_preferences (" in sql
    assert "worker_preferencess" not in sql
    assert "DROP CONSTRAINT uq_command_results_single_result" in sql
    for table in migration.TABLES:
        assert f"ALTER TABLE {table} OWNER TO golden_rose_schema_owner" in sql
        assert f"GRANT SELECT, INSERT ON TABLE {table} TO golden_rose_runtime" in sql
        assert f"CREATE TRIGGER deny_mutation_{table}" in sql
    for kind in migration.KINDS:
        assert f"FOREIGN KEY({kind}_id)" in sql
        assert f"{kind}_id IS NOT NULL AND {kind}_id=entity_id" in sql
    assert "CREATE CONSTRAINT TRIGGER guard_finalization_results" in sql


def test_populated_successor_downgrade_stops_before_ddl(migration, monkeypatch):
    emitted: list[str] = []
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = True
    monkeypatch.setattr(migration, "execute", emitted.append)
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    with pytest.raises(RuntimeError, match="before DDL"):
        migration.downgrade()
    assert len(emitted) == 1
    assert emitted[0].startswith("LOCK TABLE ")
