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
    path = Path(__file__).resolve().parents[2] / "migrations/versions/0008b_intake_link_storage.py"
    spec = importlib.util.spec_from_file_location("intake_link_storage", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_storage_is_additive_and_closed_until_command_integration(migration):
    assert migration.down_revision == "0008a_employer_finalization"
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context), context.begin_transaction():
        migration.upgrade()
    sql = output.getvalue()
    assert sql.startswith("BEGIN;") and sql.rstrip().endswith("COMMIT;")
    assert "ck_intakes_links_not_available" in sql
    assert "worker_id IS NULL AND employer_id IS NULL" in sql
    assert "DROP CONSTRAINT ck_intake_links_not_available" not in sql
    assert "GRANT " not in sql and "CREATE ROLE" not in sql
    assert "UPDATE intakes" not in sql
    for kind in ("worker", "employer"):
        assert f"ADD COLUMN {kind}_id UUID" in sql
        assert f"ADD COLUMN {kind}_version INTEGER" in sql
    for name in migration.CHILDREN:
        assert f"ADD COLUMN {name}_id UUID" in sql
        assert f"ADD COLUMN {name}_version INTEGER" in sql
    assert "REFERENCES worker_contacts (worker_id, worker_contact_id)" in sql
    assert (
        "REFERENCES employer_contact_details "
        "(employer_id, employer_contact_id, employer_contact_details_id)" in sql
    )
    assert "REFERENCES intakes (intake_id, worker_id)" in sql
    assert "REFERENCES intakes (intake_id, employer_id)" in sql
    assert "DEFERRABLE INITIALLY DEFERRED" in sql


def test_populated_downgrade_stops_before_ddl(migration, monkeypatch):
    emitted: list[str] = []
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = True
    monkeypatch.setattr(migration, "execute", emitted.append)
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    with pytest.raises(RuntimeError, match="before DDL"):
        migration.downgrade()
    assert len(emitted) == 1 and emitted[0].startswith("LOCK TABLE")


def test_empty_storage_downgrade_restores_prior_shape(migration, monkeypatch):
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = False
    monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context), context.begin_transaction():
        migration.downgrade()
    sql = output.getvalue()
    assert "DROP COLUMN worker_id" in sql
    assert "DROP COLUMN employer_id" in sql
    assert "DROP TABLE" not in sql
    assert "DROP CONSTRAINT ck_intake_links_not_available" not in sql
