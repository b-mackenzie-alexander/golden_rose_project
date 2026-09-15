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
    path = (
        Path(__file__).resolve().parents[2] / "migrations/versions/0008c_intake_link_authority.py"
    )
    spec = importlib.util.spec_from_file_location("intake_link_authority", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def emitted(migration, direction) -> str:
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context), context.begin_transaction():
        getattr(migration, direction)()
    return output.getvalue()


def test_successor_installs_authority_before_opening_storage(migration):
    assert migration.down_revision == "0008b_intake_link_storage"
    sql = emitted(migration, "upgrade")
    assert sql.index("CREATE CONSTRAINT TRIGGER guard_intake_links") < sql.index(
        "DROP CONSTRAINT ck_intake_links_not_available"
    )
    assert "GRANT UPDATE(worker_id,worker_version,employer_id,employer_version)" in sql
    assert "GRANT UPDATE ON" not in sql
    assert "BEFORE DELETE OR TRUNCATE ON intake_links" in sql
    assert "link_intake" in sql and "intake.linked" in sql
    assert "payload.dependency_refs IS DISTINCT FROM intake_link_refs" in sql
    assert "WHERE worker_disposition='created'" in sql
    assert "staffing_request_disposition='created'" in sql
    assert "CREATE ROLE" not in sql and "UPDATE intakes SET" not in sql


def test_populated_downgrade_refuses_before_ddl(migration, monkeypatch):
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = True
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    statements: list[str] = []
    monkeypatch.setattr(migration, "execute", statements.append)
    with pytest.raises(RuntimeError, match="before DDL"):
        migration.downgrade()
    assert len(statements) == 1 and statements[0].startswith("LOCK TABLE")


def test_safe_downgrade_restores_closed_predecessor(migration, monkeypatch):
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = False
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    sql = emitted(migration, "downgrade")
    assert "ADD CONSTRAINT ck_intake_links_not_available CHECK (false)" in sql
    assert "BEFORE UPDATE OR DELETE OR TRUNCATE ON intake_links" in sql
    assert "REVOKE UPDATE(worker_id,worker_version,employer_id,employer_version)" in sql
    assert "DROP TABLE" not in sql
    assert "dependency_refs='{}'::jsonb" in sql


def test_reverse_link_authority_and_created_transaction_are_enforced(migration):
    sql = emitted(migration, "upgrade")
    assert "guard_intake_link_event AFTER INSERT ON audit_events" in sql
    assert "i.version=NEW.new_record_version" in sql
    assert "i.xmin::text=pg_current_xact_id()::text" in sql
    assert "record->'_written_here' IS DISTINCT FROM 'true'::jsonb" in sql
    assert "reused IS DISTINCT FROM refs OR n<>expected" in sql
    assert "incomplete household output address" in sql
    assert "to_jsonb(NEW) IS DISTINCT FROM to_jsonb(l)" in sql
    assert "guard_intake_link_once BEFORE UPDATE ON intake_links" in sql


def test_predecessor_definition_drift_fails_closed(migration):
    with pytest.raises(RuntimeError, match="predecessor definition changed"):
        migration.replace_once("changed definition", "old definition", "replacement")
    with pytest.raises(RuntimeError, match="predecessor definition changed"):
        migration.replace_once("same same", "same", "replacement")


def test_helpers_have_fixed_tables_and_no_definer_authority(migration):
    sql = emitted(migration, "upgrade")
    assert "SECURITY DEFINER" not in sql
    for function in migration.FUNCTIONS:
        assert f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC" in sql
    for function in migration.FUNCTIONS[3:]:
        assert f"GRANT EXECUTE ON FUNCTION {function}" not in sql
    assert "FOR UPDATE;" in migration.canonical_function()
    assert "FOR UPDATE OF w" in sql
