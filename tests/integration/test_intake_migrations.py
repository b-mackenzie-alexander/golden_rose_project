"""Schema successor grants and result migration checks against real PostgreSQL."""

from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from tests.integration.conftest import PROJECT_ROOT
from tests.integration.test_intake_authority import insert_atomic_draft


def test_intake_tables_have_schema_owner(connection):
    rows = connection.execute(
        text("""
        SELECT c.relname, pg_get_userbyid(c.relowner)
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relname IN
          ('intakes','intake_addresses','intake_links','command_results')
    """)
    ).all()
    assert len(rows) == 4
    assert all(owner == "golden_rose_schema_owner" for _, owner in rows)


def test_result_backfill_is_complete(connection):
    assert (
        connection.execute(
            text("""
        SELECT count(*) FROM command_receipts c LEFT JOIN command_results r
          ON r.command_id=c.command_id AND r.entity_type=c.result_entity_type
          AND r.entity_id=c.result_entity_id AND r.result_version=c.result_record_version
          AND r.actor_id=c.actor_id AND r.event_type=c.result_event_type
          AND r.command_type=c.command_type WHERE r.command_id IS NULL
    """)
        ).scalar_one()
        == 0
    )


def test_runtime_has_narrow_update_and_no_result_mutation(connection):
    for table in ("intakes", "intake_addresses"):
        assert not connection.execute(
            text("SELECT has_table_privilege('golden_rose_runtime',:table,'UPDATE')"),
            {"table": table},
        ).scalar_one()
    for privilege in ("UPDATE", "DELETE", "TRUNCATE"):
        assert not connection.execute(
            text("SELECT has_table_privilege('golden_rose_runtime','command_results',:privilege)"),
            {"privilege": privilege},
        ).scalar_one()


@pytest.fixture
def migration_database(database_url):
    """A separate database in the expressly approved disposable test cluster."""
    name = "intake_migration_" + uuid4().hex
    admin = create_engine(
        make_url(database_url).set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin.connect() as connection:
        connection.execute(text(f"CREATE DATABASE {name}"))
    target = create_engine(make_url(database_url).set(database=name))
    try:
        yield target
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f"DROP DATABASE {name}"))
        admin.dispose()


def migrate(target, revision, *, downgrade=False) -> None:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    with target.connect() as connection:
        config.attributes["connection"] = connection
        (command.downgrade if downgrade else command.upgrade)(config, revision)


def legacy_employer(connection) -> dict[str, Any]:
    from datetime import UTC, datetime

    identity, actor, command_id, event = uuid4(), uuid4(), uuid4(), uuid4()
    values = {
        "id": identity,
        "actor": actor,
        "command": command_id,
        "event": event,
        "now": datetime.now(UTC),
    }
    connection.execute(
        text("""
      INSERT INTO employers(employer_id,employer_type,display_name,lifecycle_status,
        source_channel,received_at,created_at,created_by,updated_at,updated_by,version)
      VALUES(:id,'household','Fictional Migration','draft','staff_entry',:now,:now,:actor,:now,
      :actor,1)
    """),
        values,
    )
    connection.execute(
        text(
            "INSERT INTO entity_authorities(entity_type,entity_id,employer_id) "
            "VALUES('employer',:id,:id)"
        ),
        values,
    )
    connection.execute(
        text("""
      INSERT INTO command_receipts(command_id,command_schema_version,command_type,actor_id,
        request_fingerprint,result_entity_type,result_entity_id,result_record_version,
        result_event_type,created_at)
      VALUES(:command,1,'create_draft_employer',:actor,decode(repeat('ab',32),'hex'),
        'employer',:id,1,'employer.created',:now)
    """),
        values,
    )
    connection.execute(
        text("""
      INSERT INTO audit_events(audit_event_id,event_schema_name,event_schema_version,event_type,
        entity_type,entity_id,entity_sequence,prior_record_version,new_record_version,
        actor_type,actor_id,occurred_at,command_id,correlation_id,source_type,related_event_ids,
        changed_fields,payload_classification)
      VALUES(:event,'employer.created',1,'employer.created','employer',:id,1,0,1,
        'staff',:actor,:now,:command,:command,'staff_api','[]','[]','sensitive_operational')
    """),
        values,
    )
    return values


def test_populated_0005_upgrade_backfills_and_preserves_legacy(migration_database):
    migrate(migration_database, "0005_database_authority")
    with migration_database.begin() as connection:
        original = legacy_employer(connection)
    migrate(migration_database, "head")
    with migration_database.begin() as connection:
        assert (
            connection.execute(
                text("SELECT entity_id FROM command_results WHERE command_id=:command"), original
            ).scalar_one()
            == original["id"]
        )
        # Existing writers need not know command_results exists.
        later = legacy_employer(connection)
        assert (
            connection.execute(
                text("SELECT entity_id FROM command_results WHERE command_id=:command"), later
            ).scalar_one()
            == later["id"]
        )
    migrate(migration_database, "0005_database_authority", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM command_receipts")).scalar_one() == 2
        assert (
            connection.execute(text("SELECT to_regclass('public.command_results')")).scalar_one()
            is None
        )


def test_populated_intake_downgrade_refuses_before_ddl(migration_database):
    migrate(migration_database, "head")
    with migration_database.begin() as connection:
        insert_atomic_draft(connection)
    with pytest.raises(RuntimeError, match="before DDL"):
        migrate(migration_database, "0005_database_authority", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM intakes")).scalar_one() == 1
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0006_intake_drafts"
        )
        assert (
            connection.execute(text("SELECT to_regclass('public.command_results')")).scalar_one()
            == "command_results"
        )


def test_intake_catalog_readback_matches_exact_contract(migration_database):
    from scripts.verify_database_authority import (
        EXPECTED_INTAKE_CONSTRAINTS,
        EXPECTED_RUNTIME_UPDATE_COLUMNS,
        collect_authority_snapshot,
        evaluate_authority_snapshot,
    )

    migrate(migration_database, "head")
    with migration_database.connect() as connection:
        snapshot = collect_authority_snapshot(connection)
        assert snapshot["intake_constraints"] == EXPECTED_INTAKE_CONSTRAINTS
        update_columns = snapshot["runtime_update_columns"]
        assert isinstance(update_columns, dict)
        assert {key: set(value) for key, value in update_columns.items()} == {
            key: value for key, value in EXPECTED_RUNTIME_UPDATE_COLUMNS.items() if value
        }
        violations = evaluate_authority_snapshot(snapshot)
        # Authenticated-login evidence belongs to the existing authority integration suite.
        assert not [v for v in violations if "membership" not in v]
        connection.execute(text("ALTER TABLE intakes DROP CONSTRAINT ck_intakes_content_kind"))
        connection.execute(
            text("ALTER TABLE intakes ADD CONSTRAINT ck_intakes_content_kind CHECK(true)")
        )
        assert any(
            "ck_intakes_content_kind" in violation
            for violation in evaluate_authority_snapshot(collect_authority_snapshot(connection))
        )


def test_empty_successor_reaches_inherited_downgrade_guard(migration_database):
    migrate(migration_database, "head")
    with migration_database.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM intakes")).scalar_one() == 0
    with pytest.raises(RuntimeError, match="operator-reviewed role handoff"):
        migrate(migration_database, "base", downgrade=True)
    # Alembic's transactional DDL keeps the original head when 0005 refuses.
    with migration_database.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0006_intake_drafts"
        )


def test_temp_tables_cannot_spoof_intake_write_authority(migration_database):
    from datetime import UTC, datetime

    from sqlalchemy.exc import IntegrityError

    migrate(migration_database, "head")
    with migration_database.begin() as connection:
        values = insert_atomic_draft(connection)
    with migration_database.connect() as connection:
        connection.execute(text("CREATE TEMP TABLE command_results (LIKE public.command_results)"))
        connection.execute(text("CREATE TEMP TABLE audit_events (LIKE public.audit_events)"))
        now = datetime.now(UTC)
        command_id = uuid4()
        connection.execute(
            text("""
            INSERT INTO pg_temp.command_results
            VALUES (:command,'intake',:id,2,'intake.revised',:actor,'revise_intake')
        """),
            {"command": command_id, "id": values["id"], "actor": values["actor"]},
        )
        # A caller-created temporary audit/result pair must not satisfy public guards.
        connection.execute(
            text("""
            INSERT INTO pg_temp.audit_events SELECT audit_event_id,'intake.revised',1,
              'intake.revised',entity_type,entity_id,2,1,2,actor_type,actor_id,
              initiating_staff_actor_id,:now,effective_at,:command,:command,
              reason_code,reason_text,source_type,source_reference,related_event_ids,
              changed_fields,payload_classification FROM public.audit_events
            WHERE entity_id=:id
        """),
            {"command": command_id, "now": now, "id": values["id"]},
        )
        with pytest.raises(IntegrityError, match="missing atomic intake authority"):
            connection.execute(
                text("""
              UPDATE public.intakes SET content='{"full_name":"Fictional spoof"}',
                version=2,content_version=2,updated_at=:now WHERE intake_id=:id
            """),
                {"id": values["id"], "now": now},
            )
            connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        connection.rollback()
