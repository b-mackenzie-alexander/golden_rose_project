"""Database-side intake authority cannot be bypassed by a runtime writer."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def draft_values() -> dict[str, Any]:
    actor = uuid4()
    return {"id": uuid4(), "actor": actor, "now": datetime.now(UTC)}


def insert_draft(connection, values) -> None:
    connection.execute(
        text("""
        INSERT INTO intakes (intake_id,kind,schema_version,content,lifecycle_status,
          version,content_version,created_at,created_by,updated_at,updated_by)
        VALUES (:id,'worker',1,'{}','draft',1,1,:now,:actor,:now,:actor)
    """),
        values,
    )


def test_direct_draft_without_atomic_authority_fails(connection):
    with pytest.raises(IntegrityError):
        insert_draft(connection, draft_values())
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


@pytest.mark.parametrize("kind", ["intake", "employer", "employer_contact"])
def test_null_concrete_authority_is_rejected(connection, kind):
    with pytest.raises(IntegrityError):
        connection.execute(
            text("INSERT INTO entity_authorities(entity_type,entity_id) VALUES (:kind,:id)"),
            {"kind": kind, "id": uuid4()},
        )
    connection.rollback()


def test_link_shell_rejects_data(connection):
    with pytest.raises(IntegrityError):
        connection.execute(
            text("INSERT INTO intake_links(intake_id) VALUES (:id)"), {"id": uuid4()}
        )
    connection.rollback()


@pytest.mark.parametrize("content", ['{"residential_address":{}}', '{"display_name":"x"}', "[]"])
def test_worker_content_rejects_wrong_shape(connection, content):
    with pytest.raises(IntegrityError):
        values = draft_values() | {"content": content}
        connection.execute(
            text("""
            INSERT INTO intakes (intake_id,kind,schema_version,content,lifecycle_status,
                version,content_version,created_at,created_by,updated_at,updated_by)
            VALUES (:id,'worker',1,CAST(:content AS jsonb),'draft',1,1,:now,:actor,:now,:actor)
        """),
            values,
        )
    connection.rollback()


def insert_atomic_draft(
    connection, *, omit_result=False, result_actor=None, kind="worker"
) -> dict[str, Any]:
    """Build all authority rows explicitly, independent of application services."""
    from golden_rose.persistence.models import (
        audit_events,
        command_receipts,
        command_results,
        entity_authorities,
        intakes,
    )

    values = draft_values()
    identity, actor, now, command = values["id"], values["actor"], values["now"], uuid4()
    connection.execute(
        intakes.insert().values(
            intake_id=identity,
            kind=kind,
            schema_version=1,
            content={},
            lifecycle_status="draft",
            version=1,
            content_version=1,
            created_at=now,
            updated_at=now,
            created_by=actor,
            updated_by=actor,
        )
    )
    connection.execute(
        entity_authorities.insert().values(
            entity_type="intake", entity_id=identity, intake_id=identity
        )
    )
    connection.execute(
        command_receipts.insert().values(
            command_id=command,
            command_schema_version=1,
            command_type="create_intake",
            actor_id=actor,
            request_fingerprint=b"a" * 32,
            result_entity_type="intake",
            result_entity_id=identity,
            result_record_version=1,
            result_event_type="intake.created",
            created_at=now,
        )
    )
    connection.execute(
        audit_events.insert().values(
            audit_event_id=uuid4(),
            event_schema_name="intake.created",
            event_schema_version=1,
            event_type="intake.created",
            entity_type="intake",
            entity_id=identity,
            entity_sequence=1,
            prior_record_version=0,
            new_record_version=1,
            actor_type="staff",
            actor_id=actor,
            occurred_at=now,
            command_id=command,
            correlation_id=command,
            source_type="staff_api",
            related_event_ids=[],
            changed_fields=["full_name"],
            payload_classification="sensitive_operational",
        )
    )
    if not omit_result:
        connection.execute(
            command_results.insert().values(
                command_id=command,
                entity_type="intake",
                entity_id=identity,
                result_version=1,
                event_type="intake.created",
                actor_id=result_actor or actor,
                command_type="create_intake",
            )
        )
    return values | {"command": command}


def test_complete_atomic_draft_is_valid(connection):
    insert_atomic_draft(connection)
    connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


@pytest.mark.parametrize("invalid", ["missing", "wrong_actor", "extra"])
def test_invalid_result_rejected(connection, invalid):
    with pytest.raises(IntegrityError):
        values = insert_atomic_draft(
            connection,
            omit_result=invalid == "missing",
            result_actor=uuid4() if invalid == "wrong_actor" else None,
        )
        if invalid == "extra":
            connection.execute(
                text("""
                INSERT INTO command_results SELECT command_id,entity_type,:id,result_version,
                  event_type,actor_id,command_type FROM command_results WHERE command_id=:command
            """),
                {"id": uuid4(), "command": values["command"]},
            )
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


@pytest.mark.parametrize(
    "kind,section", [("worker", "party_address"), ("employer", "worker_residence")]
)
def test_address_wrong_kind_rejected(connection, kind, section):
    with pytest.raises(IntegrityError):
        values = insert_atomic_draft(connection, kind=kind)
        connection.execute(
            text(
                "INSERT INTO intake_addresses(intake_id,section,line1) "
                "VALUES (:id,:section,'Fictional Lane')"
            ),
            {"id": values["id"], "section": section},
        )
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


def test_revision_without_next_event_rejected(connection):
    values = insert_atomic_draft(connection)
    connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    with pytest.raises(IntegrityError):
        connection.execute(
            text(
                'UPDATE intakes SET content=\'{"full_name":"Fictional"}\', '
                "version=2,content_version=2 WHERE intake_id=:id"
            ),
            {"id": values["id"]},
        )
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


@pytest.mark.parametrize(
    "column,expression", [("kind", "'employer'"), ("created_by", ":actor"), ("intake_id", ":actor")]
)
def test_identity_and_attribution_immutable(connection, column, expression):
    values = insert_atomic_draft(connection)
    connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    with pytest.raises(IntegrityError):
        connection.execute(
            text(
                f"UPDATE intakes SET {column}={expression},version=2,"
                "content_version=2 WHERE intake_id=:id"
            ),
            {"id": values["id"], "actor": uuid4()},
        )
    connection.rollback()
