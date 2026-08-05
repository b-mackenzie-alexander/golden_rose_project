from conftest import VERSIONS_DIR
from sqlalchemy import inspect, text

from golden_rose.persistence.models import metadata


def test_initial_migration_file_exists_at_expected_path() -> None:
    migration_path = VERSIONS_DIR / "0001_create_first_slice_tables.py"

    assert migration_path.exists()


def test_initial_metadata_contains_required_tables() -> None:
    assert {"audit_events", "command_receipts", "employers"}.issubset(metadata.tables)


def test_live_schema_contains_expected_tables(connection) -> None:
    inspector = inspect(connection)

    assert {"audit_events", "command_receipts", "employers"}.issubset(
        set(inspector.get_table_names())
    )


def test_live_schema_exposes_expected_columns(connection) -> None:
    inspector = inspect(connection)

    employer_columns = {column["name"] for column in inspector.get_columns("employers")}
    command_receipt_columns = {
        column["name"] for column in inspector.get_columns("command_receipts")
    }
    audit_event_columns = {column["name"] for column in inspector.get_columns("audit_events")}

    assert employer_columns == {
        "employer_id",
        "employer_type",
        "display_name",
        "lifecycle_status",
        "source_channel",
        "received_at",
        "created_at",
        "created_by",
        "version",
    }
    assert command_receipt_columns == {
        "command_id",
        "command_schema_version",
        "command_type",
        "actor_id",
        "request_fingerprint",
        "result_entity_type",
        "result_entity_id",
        "created_at",
    }
    assert audit_event_columns == {
        "audit_event_id",
        "event_schema_name",
        "event_schema_version",
        "event_type",
        "entity_type",
        "entity_id",
        "entity_sequence",
        "prior_record_version",
        "new_record_version",
        "actor_type",
        "actor_id",
        "initiating_staff_actor_id",
        "occurred_at",
        "effective_at",
        "command_id",
        "correlation_id",
        "reason_code",
        "reason_text",
        "source_type",
        "source_reference",
        "related_event_ids",
        "changed_fields",
        "payload_classification",
    }


def test_live_schema_exposes_expected_constraints(connection) -> None:
    inspector = inspect(connection)

    employer_checks = {check["name"] for check in inspector.get_check_constraints("employers")}
    command_receipt_checks = {
        check["name"] for check in inspector.get_check_constraints("command_receipts")
    }
    audit_event_checks = {
        check["name"] for check in inspector.get_check_constraints("audit_events")
    }
    audit_event_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("audit_events")
    }

    assert employer_checks == {
        "ck_employers_display_name_nonblank",
        "ck_employers_lifecycle_status_draft",
        "ck_employers_source_channel_staff_entry",
        "ck_employers_type",
        "ck_employers_version_positive",
    }
    assert command_receipt_checks == {
        "ck_command_receipts_command_type",
        "ck_command_receipts_entity_type",
        "ck_command_receipts_request_fingerprint_len",
        "ck_command_receipts_schema_version",
    }
    assert audit_event_checks == {
        "ck_audit_events_actor_type",
        "ck_audit_events_entity_type",
        "ck_audit_events_event_type",
        "ck_audit_events_payload_classification",
        "ck_audit_events_schema_name",
        "ck_audit_events_schema_version",
        "ck_audit_events_source_type",
    }
    assert audit_event_unique_constraints == {"uq_audit_events_entity_sequence"}


def test_append_only_tables_reject_update_and_delete(connection, clean_tables) -> None:
    connection.execute(
        text(
            """
            INSERT INTO employers (
                employer_id, employer_type, display_name, lifecycle_status, source_channel,
                received_at, created_at, created_by, version
            ) VALUES (
                '11111111-1111-4111-8111-111111111111', 'household', 'Synthetic Household 001',
                'draft', 'staff_entry', NOW(), NOW(), '22222222-2222-4222-8222-222222222222', 1
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO command_receipts (
                command_id, command_schema_version, command_type, actor_id,
                request_fingerprint, result_entity_type, result_entity_id, created_at
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW()
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO audit_events (
                audit_event_id, event_schema_name, event_schema_version, event_type, entity_type,
                entity_id, entity_sequence, prior_record_version, new_record_version, actor_type,
                actor_id, initiating_staff_actor_id, occurred_at, effective_at, command_id,
                correlation_id, reason_code, reason_text, source_type, source_reference,
                related_event_ids, changed_fields, payload_classification
            ) VALUES (
                '44444444-4444-4444-8444-444444444444', 'employer.created', 1, 'employer.created',
                'employer', '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                '22222222-2222-4222-8222-222222222222', NULL, NOW(), NULL,
                '33333333-3333-4333-8333-333333333333', '33333333-3333-4333-8333-333333333333',
                NULL, NULL, 'staff_api', NULL, '[]'::jsonb,
                '{"field_names": ["employer_type"]}'::jsonb, 'sensitive_operational'
            )
            """
        )
    )
    connection.commit()

    for statement in (
        "UPDATE command_receipts SET command_type = 'tampered'",
        "DELETE FROM command_receipts",
        "UPDATE audit_events SET event_type = 'tampered'",
        "DELETE FROM audit_events",
    ):
        try:
            connection.execute(text(statement))
            connection.commit()
        except Exception:
            connection.rollback()
        else:
            raise AssertionError(f"statement unexpectedly succeeded: {statement}")


def test_create_all_is_not_used_in_repository() -> None:
    repository_python = sorted((VERSIONS_DIR.parents[1] / "src").rglob("*.py"))

    offending_paths = []
    for path in repository_python:
        if path.name == "models.py":
            continue
        if "create_all(" in path.read_text():
            offending_paths.append(path)

    assert offending_paths == []
