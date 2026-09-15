"""Direct SQL probes of PR B atomic workflow authority, independent of services."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from golden_rose.persistence.models import audit_events, command_receipts, command_results
from tests.integration.test_intake_authority import insert_atomic_draft
from tests.integration.test_intake_migrations import migration_database as migration_database


def workflow(
    connection,
    values,
    *,
    outcome="intake_reviewed",
    payload=True,
    review=True,
    change_content=False,
) -> UUID:
    identity, actor, command, event, now = (
        values["id"],
        values["actor"],
        uuid4(),
        uuid4(),
        datetime.now(UTC),
    )
    connection.execute(
        text(
            "UPDATE intakes SET version=2, updated_by=:actor,updated_at=:now "
            + (',content=\'{"full_name":"Forged"}\' ' if change_content else "")
            + "WHERE intake_id=:id"
        ),
        values | {"now": now},
    )
    connection.execute(
        command_receipts.insert().values(
            command_id=command,
            command_schema_version=1,
            command_type="review_intake",
            actor_id=actor,
            request_fingerprint=b"b" * 32,
            result_entity_type="intake",
            result_entity_id=identity,
            result_record_version=2,
            result_event_type="intake.reviewed",
            created_at=now,
        )
    )
    connection.execute(
        command_results.insert().values(
            command_id=command,
            entity_type="intake",
            entity_id=identity,
            result_version=2,
            event_type="intake.reviewed",
            actor_id=actor,
            command_type="review_intake",
        )
    )
    connection.execute(
        audit_events.insert().values(
            audit_event_id=event,
            event_schema_name="intake.reviewed",
            event_schema_version=1,
            event_type="intake.reviewed",
            entity_type="intake",
            entity_id=identity,
            entity_sequence=2,
            prior_record_version=1,
            new_record_version=2,
            actor_type="staff",
            actor_id=actor,
            occurred_at=now,
            command_id=command,
            correlation_id=command,
            source_type="staff_api",
            related_event_ids=[],
            changed_fields=["review"],
            payload_classification="sensitive_operational",
        )
    )
    rid = uuid4()
    if review:
        connection.execute(
            text(
                "INSERT INTO intake_reviews VALUES (:rid,:id,:command,:event,1,1,2"
                ",:outcome,:actor,'Synthetic Reviewer',:now)"
            ),
            values
            | {"rid": rid, "command": command, "event": event, "now": now, "outcome": outcome},
        )
    if payload:
        connection.execute(
            text(
                'INSERT INTO intake_review_payloads VALUES (:rid,\'{"kind":"worker"'
                ',"content":{},"addresses":{}}\',NULL,\'{}\')'
            ),
            {"rid": rid},
        )
    return rid


def test_review_advances_record_only_and_preserves_snapshot(connection, clean_tables):
    values = insert_atomic_draft(connection)
    connection.commit()
    workflow(connection, values)
    connection.commit()
    assert connection.execute(
        text("SELECT version,content_version FROM intakes WHERE intake_id=:id"), values
    ).one() == (2, 1)
    connection.rollback()


@pytest.mark.parametrize(
    "options",
    [
        {"payload": False},
        {"review": False, "payload": False},
        {"outcome": "needs_follow_up"},
        {"change_content": True},
    ],
)
def test_review_missing_payload_disposition_or_changed_facts_rolls_back(
    connection, clean_tables, options
):
    values = insert_atomic_draft(connection)
    connection.commit()
    with pytest.raises(IntegrityError):
        workflow(connection, values, **options)
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()
    assert connection.execute(
        text("SELECT version,content_version FROM intakes WHERE intake_id=:id"), values
    ).one() == (1, 1)
    connection.rollback()


@pytest.mark.parametrize(
    "table",
    [
        "intake_reviews",
        "intake_review_payloads",
        "intake_follow_up_events",
        "intake_history_payloads",
        "work_interest_versions",
    ],
)
@pytest.mark.parametrize("operation", ["DELETE", "TRUNCATE"])
def test_history_statement_mutation_forbidden(connection, table, operation):
    with pytest.raises(DBAPIError):
        connection.execute(
            text(f"{operation} {'FROM' if operation == 'DELETE' else 'TABLE'} {table}")
        )
    connection.rollback()


def test_populated_0006_upgrade_preserves_drafts_and_review_downgrade_stops(migration_database):
    from tests.integration.test_intake_migrations import migrate

    migrate(migration_database, "0006_intake_drafts")
    with migration_database.begin() as connection:
        values = insert_atomic_draft(connection)
    migrate(migration_database, "head")
    with migration_database.begin() as connection:
        original_revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        workflow(connection, values)
    with pytest.raises(RuntimeError, match="before DDL"):
        migrate(migration_database, "0006_intake_drafts", downgrade=True)
    with migration_database.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM intake_reviews")).scalar_one() == 1
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == original_revision
        )


def catalog(connection, *, omit_version=False, actor_substitution=False, code=None) -> UUID:
    from golden_rose.persistence.models import (
        entity_authorities,
        work_interest_versions,
        work_interests,
    )

    identity, actor, command, event, now = uuid4(), uuid4(), uuid4(), uuid4(), datetime.now(UTC)
    connection.execute(
        work_interests.insert().values(
            interest_id=identity,
            code=code or "fictional_" + identity.hex,
            version=1,
            label_en="Fictional interest",
            label_es="Interés ficticio",
            active=True,
            created_at=now,
            created_by=actor,
            updated_at=now,
            updated_by=actor,
        )
    )
    connection.execute(
        entity_authorities.insert().values(
            entity_type="work_interest", entity_id=identity, work_interest_id=identity
        )
    )
    connection.execute(
        command_receipts.insert().values(
            command_id=command,
            command_schema_version=1,
            command_type="create_work_interest",
            actor_id=actor,
            request_fingerprint=b"c" * 32,
            result_entity_type="work_interest",
            result_entity_id=identity,
            result_record_version=1,
            result_event_type="work_interest.created",
            created_at=now,
        )
    )
    connection.execute(
        command_results.insert().values(
            command_id=command,
            entity_type="work_interest",
            entity_id=identity,
            result_version=1,
            event_type="work_interest.created",
            actor_id=actor,
            command_type="create_work_interest",
        )
    )
    connection.execute(
        audit_events.insert().values(
            audit_event_id=event,
            event_schema_name="work_interest.created",
            event_schema_version=1,
            event_type="work_interest.created",
            entity_type="work_interest",
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
            changed_fields=["label_en", "label_es", "active"],
            payload_classification="sensitive_operational",
        )
    )
    if not omit_version:
        connection.execute(
            work_interest_versions.insert().values(
                interest_id=identity,
                version=1,
                label_en="Fictional interest",
                label_es="Interés ficticio",
                active=True,
                actor_id=uuid4() if actor_substitution else actor,
                occurred_at=now,
                command_id=command,
            )
        )
    return identity


def test_catalog_requires_exact_immutable_version(connection, clean_tables):
    identity = catalog(connection)
    connection.commit()
    assert (
        connection.execute(
            text("SELECT version FROM work_interests WHERE interest_id=:id"), {"id": identity}
        ).scalar_one()
        == 1
    )
    connection.rollback()


@pytest.mark.parametrize("options", [{"omit_version": True}, {"actor_substitution": True}])
def test_catalog_missing_or_forged_history_rolls_back(connection, clean_tables, options):
    with pytest.raises(IntegrityError):
        catalog(connection, **options)
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


def test_snapshot_substitution_rolls_back(connection, clean_tables):
    from golden_rose.persistence.models import intake_review_payloads

    values = insert_atomic_draft(connection)
    connection.commit()
    with pytest.raises(IntegrityError):
        rid = workflow(connection, values, payload=False)
        connection.execute(
            intake_review_payloads.insert().values(
                review_id=rid,
                reviewed_content={
                    "kind": "worker",
                    "content": {"full_name": "Substituted"},
                    "addresses": {},
                },
                dependency_refs={},
            )
        )
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


def test_extra_catalog_audit_cannot_fabricate_a_revision(connection, clean_tables):
    identity = catalog(connection)
    original = dict(
        connection.execute(audit_events.select().where(audit_events.c.entity_id == identity))
        .mappings()
        .one()
    )
    actor = original["actor_id"]
    command = uuid4()
    connection.execute(
        command_receipts.insert().values(
            command_id=command,
            command_schema_version=1,
            command_type="revise_work_interest",
            actor_id=actor,
            request_fingerprint=b"d" * 32,
            result_entity_type="work_interest",
            result_entity_id=identity,
            result_record_version=2,
            result_event_type="work_interest.revised",
            created_at=original["occurred_at"],
        )
    )
    connection.execute(
        command_results.insert().values(
            command_id=command,
            entity_type="work_interest",
            entity_id=identity,
            result_version=2,
            event_type="work_interest.revised",
            actor_id=actor,
            command_type="revise_work_interest",
        )
    )
    original.update(
        audit_event_id=uuid4(),
        command_id=command,
        correlation_id=command,
        event_schema_name="work_interest.revised",
        event_type="work_interest.revised",
        entity_sequence=2,
        prior_record_version=1,
        new_record_version=2,
    )
    connection.execute(audit_events.insert().values(**original))
    with pytest.raises(IntegrityError):
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    connection.rollback()


@pytest.mark.parametrize("code", ["_fictional", "1_fictional"])
def test_catalog_code_accepts_contract_first_character(connection, clean_tables, code):
    catalog(connection, code=code)
    connection.commit()


@pytest.mark.parametrize("attach_review", [False, True])
def test_standalone_follow_up_cannot_carry_review(connection, clean_tables, attach_review):
    from golden_rose.persistence.models import (
        intake_follow_up_events,
        intake_history_payloads,
        intake_review_payloads,
        intake_reviews,
    )

    values = insert_atomic_draft(connection)
    connection.commit()
    review_id = workflow(connection, values, outcome="needs_follow_up")
    review = dict(connection.execute(intake_reviews.select()).mappings().one())
    follow = {
        "event_id": review["event_id"],
        "intake_id": values["id"],
        "command_id": review["command_id"],
        "version": 2,
        "content_version": 1,
        "action": "needs_follow_up",
        "actor_id": values["actor"],
        "actor_display_name": "Synthetic Reviewer",
        "occurred_at": review["occurred_at"],
        "owner_staff_id": values["actor"],
        "next_follow_up_at": review["occurred_at"],
        "time_zone": "UTC",
        "reason_code": "missing_information",
        "review_id": review_id,
    }
    connection.execute(intake_follow_up_events.insert().values(**follow))
    connection.execute(
        intake_history_payloads.insert().values(
            event_id=review["event_id"],
            reason_text="Fictional missing information",
        )
    )
    connection.commit()

    event, command, now = uuid4(), uuid4(), datetime.now(UTC)
    connection.execute(
        text("UPDATE intakes SET version=3,updated_at=:now WHERE intake_id=:id"),
        values | {"now": now},
    )
    receipt = dict(
        connection.execute(
            command_receipts.select().where(command_receipts.c.command_id == review["command_id"])
        )
        .mappings()
        .one()
    )
    receipt.update(
        command_id=command,
        command_type="follow_up_intake",
        result_record_version=3,
        result_event_type="intake.follow_up_recorded",
        created_at=now,
    )
    connection.execute(command_receipts.insert().values(**receipt))
    connection.execute(
        command_results.insert().values(
            command_id=command,
            entity_type="intake",
            entity_id=values["id"],
            result_version=3,
            event_type="intake.follow_up_recorded",
            actor_id=values["actor"],
            command_type="follow_up_intake",
        )
    )
    audit = dict(
        connection.execute(
            audit_events.select().where(audit_events.c.audit_event_id == review["event_id"])
        )
        .mappings()
        .one()
    )
    audit.update(
        audit_event_id=event,
        command_id=command,
        correlation_id=command,
        event_type="intake.follow_up_recorded",
        event_schema_name="intake.follow_up_recorded",
        entity_sequence=3,
        prior_record_version=2,
        new_record_version=3,
        occurred_at=now,
    )
    connection.execute(audit_events.insert().values(**audit))
    follow.update(
        event_id=event,
        command_id=command,
        version=3,
        action="reschedule",
        occurred_at=now,
        review_id=None,
        reason_code=None,
    )
    connection.execute(intake_follow_up_events.insert().values(**follow))
    connection.execute(
        intake_history_payloads.insert().values(
            event_id=event,
            reason_text="Fictional reschedule",
        )
    )
    if attach_review:
        review.update(
            review_id=uuid4(),
            event_id=event,
            command_id=command,
            reviewed_record_version=2,
            result_version=3,
            outcome="intake_reviewed",
            occurred_at=now,
        )
        connection.execute(intake_reviews.insert().values(**review))
        connection.execute(
            intake_review_payloads.insert().values(
                review_id=review["review_id"],
                reviewed_content={"arbitrary": "forged snapshot"},
                dependency_refs={},
            )
        )
        with pytest.raises(IntegrityError):
            connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        connection.rollback()
        assert connection.execute(text("SELECT version FROM intakes")).scalar_one() == 2
        assert connection.execute(text("SELECT count(*) FROM intake_reviews")).scalar_one() == 1
    else:
        connection.commit()
        assert connection.execute(text("SELECT version FROM intakes")).scalar_one() == 3
    connection.rollback()


@pytest.mark.parametrize("fabricate_snapshot", [False, True])
def test_cleared_address_snapshot_omits_empty_row_and_rejects_invented_values(
    connection, clean_tables, fabricate_snapshot
):
    from golden_rose.persistence.models import (
        intake_addresses,
        intake_follow_up_events,
        intake_history_payloads,
        intake_review_payloads,
        intake_reviews,
    )

    values = insert_atomic_draft(connection)
    # Clearing a saved address preserves this row with all components NULL.
    connection.execute(
        intake_addresses.insert().values(intake_id=values["id"], section="worker_residence")
    )
    connection.commit()
    review_id = workflow(connection, values, outcome="needs_follow_up", payload=False)
    review = dict(connection.execute(intake_reviews.select()).mappings().one())
    snapshot = {"kind": "worker", "content": {}, "addresses": {}}
    if fabricate_snapshot:
        snapshot["addresses"] = {"worker_residence": {"line1": "Invented address"}}
    connection.execute(
        intake_review_payloads.insert().values(
            review_id=review_id, reviewed_content=snapshot, dependency_refs={}
        )
    )
    connection.execute(
        intake_follow_up_events.insert().values(
            event_id=review["event_id"],
            intake_id=values["id"],
            command_id=review["command_id"],
            version=2,
            content_version=1,
            action="needs_follow_up",
            actor_id=values["actor"],
            actor_display_name="Synthetic Reviewer",
            occurred_at=review["occurred_at"],
            owner_staff_id=values["actor"],
            next_follow_up_at=review["occurred_at"],
            time_zone="UTC",
            reason_code="missing_information",
            review_id=review_id,
        )
    )
    connection.execute(
        intake_history_payloads.insert().values(
            event_id=review["event_id"], reason_text="Fictional missing address"
        )
    )
    if fabricate_snapshot:
        with pytest.raises(IntegrityError):
            connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        connection.rollback()
        assert connection.execute(text("SELECT version FROM intakes")).scalar_one() == 1
    else:
        connection.commit()
        assert connection.execute(text("SELECT version FROM intakes")).scalar_one() == 2
    connection.rollback()
