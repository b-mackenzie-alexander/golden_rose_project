import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import ForeignKeyConstraint, inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from golden_rose.persistence.models import metadata
from tests.integration.conftest import PROJECT_ROOT, VERSIONS_DIR


def test_initial_migration_file_exists_at_expected_path() -> None:
    migration_path = VERSIONS_DIR / "0001_create_first_slice_tables.py"

    assert migration_path.exists()


def test_initial_metadata_contains_required_tables() -> None:
    assert {"audit_events", "command_receipts", "employers"}.issubset(metadata.tables)


def test_revision_metadata_contains_updated_at_and_updated_by() -> None:
    employer_columns = metadata.tables["employers"].columns

    assert "updated_at" in employer_columns
    assert employer_columns["updated_at"].nullable is False
    assert "updated_by" in employer_columns
    assert employer_columns["updated_by"].nullable is False


def test_revision_metadata_binds_audit_event_to_command_result_version() -> None:
    command_receipt_columns = metadata.tables["command_receipts"].columns
    audit_event_constraints = {
        constraint.name: constraint for constraint in metadata.tables["audit_events"].constraints
    }

    assert "result_record_version" in command_receipt_columns
    assert command_receipt_columns["result_record_version"].nullable is False
    assert "result_event_type" in command_receipt_columns
    assert command_receipt_columns["result_event_type"].nullable is False
    assert "fk_audit_events_command_result" in audit_event_constraints

    audit_event_fk = audit_event_constraints["fk_audit_events_command_result"]

    assert isinstance(audit_event_fk, ForeignKeyConstraint)
    assert tuple(audit_event_fk.column_keys) == (
        "command_id",
        "entity_id",
        "new_record_version",
        "event_type",
        "actor_id",
    )
    assert tuple(element.column.name for element in audit_event_fk.elements) == (
        "command_id",
        "result_entity_id",
        "result_record_version",
        "result_event_type",
        "actor_id",
    )


def test_revision_metadata_requires_exactly_one_receipt_event_pair_bidirectionally() -> None:
    command_receipt_constraints = {
        constraint.name: constraint
        for constraint in metadata.tables["command_receipts"].constraints
    }
    audit_event_constraints = {
        constraint.name: constraint for constraint in metadata.tables["audit_events"].constraints
    }

    assert "uq_command_receipts_result_authority" in command_receipt_constraints
    assert "uq_audit_events_result_authority" in audit_event_constraints
    assert "fk_command_receipts_result_audit_event" in command_receipt_constraints

    receipt_event_fk = command_receipt_constraints["fk_command_receipts_result_audit_event"]

    assert isinstance(receipt_event_fk, ForeignKeyConstraint)
    assert tuple(receipt_event_fk.column_keys) == (
        "command_id",
        "result_entity_id",
        "result_record_version",
        "result_event_type",
        "actor_id",
    )
    assert tuple(element.column.name for element in receipt_event_fk.elements) == (
        "command_id",
        "entity_id",
        "new_record_version",
        "event_type",
        "actor_id",
    )
    assert receipt_event_fk.deferrable is True
    assert receipt_event_fk.initially == "DEFERRED"


def test_initial_metadata_exposes_authority_relationships() -> None:
    command_receipt_constraints = {
        constraint.name: constraint
        for constraint in metadata.tables["command_receipts"].constraints
    }
    audit_event_constraints = {
        constraint.name: constraint for constraint in metadata.tables["audit_events"].constraints
    }

    receipt_fk = command_receipt_constraints["fk_command_receipts_result_employer"]
    receipt_event_fk = command_receipt_constraints["fk_command_receipts_creation_event"]
    audit_event_fk = audit_event_constraints["fk_audit_events_command_result"]

    assert isinstance(receipt_fk, ForeignKeyConstraint)
    assert isinstance(receipt_event_fk, ForeignKeyConstraint)
    assert isinstance(audit_event_fk, ForeignKeyConstraint)

    assert "uq_command_receipts_command_result" in command_receipt_constraints
    assert "uq_audit_events_command_entity" in audit_event_constraints
    assert "uq_audit_events_command_event_type" in audit_event_constraints
    assert "uq_audit_events_result_authority" in audit_event_constraints
    assert tuple(receipt_fk.column_keys) == ("result_entity_id",)
    assert tuple(element.column.name for element in receipt_fk.elements) == ("employer_id",)
    assert receipt_fk.deferrable is True
    assert receipt_fk.initially == "DEFERRED"
    assert tuple(receipt_event_fk.column_keys) == ("command_id", "result_entity_id")
    assert tuple(element.column.name for element in receipt_event_fk.elements) == (
        "command_id",
        "entity_id",
    )
    assert receipt_event_fk.deferrable is True
    assert receipt_event_fk.initially == "DEFERRED"
    assert tuple(audit_event_fk.column_keys) == (
        "command_id",
        "entity_id",
        "new_record_version",
        "event_type",
        "actor_id",
    )
    assert tuple(element.column.name for element in audit_event_fk.elements) == (
        "command_id",
        "result_entity_id",
        "result_record_version",
        "result_event_type",
        "actor_id",
    )
    assert audit_event_fk.deferrable is True
    assert audit_event_fk.initially == "DEFERRED"


def test_populated_predecessor_schema_upgrades_with_authority_preserved(engine) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )

    command.downgrade(alembic_config, "0001_create_first_slice_tables")
    try:
        with engine.begin() as predecessor_connection:
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO employers (
                        employer_id, employer_type, display_name, lifecycle_status,
                        source_channel, received_at, created_at, created_by, version
                    ) VALUES (
                        '11111111-1111-4111-8111-111111111111', 'business',
                        'Synthetic Predecessor Employer', 'draft', 'staff_entry',
                        NOW(), NOW(), '22222222-2222-4222-8222-222222222222', 1
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO command_receipts (
                        command_id, command_schema_version, command_type, actor_id,
                        request_fingerprint, result_entity_type, result_entity_id, created_at
                    ) VALUES (
                        '33333333-3333-4333-8333-333333333333', 1,
                        'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                        decode(repeat('aa', 32), 'hex'), 'employer',
                        '11111111-1111-4111-8111-111111111111', NOW()
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        audit_event_id, event_schema_name, event_schema_version, event_type,
                        entity_type, entity_id, entity_sequence, prior_record_version,
                        new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                        occurred_at, effective_at, command_id, correlation_id, reason_code,
                        reason_text, source_type, source_reference, related_event_ids,
                        changed_fields, payload_classification
                    ) VALUES (
                        '44444444-4444-4444-8444-444444444444', 'employer.created', 1,
                        'employer.created', 'employer',
                        '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                        '22222222-2222-4222-8222-222222222222', NULL, NOW(), NULL,
                        '33333333-3333-4333-8333-333333333333',
                        '33333333-3333-4333-8333-333333333333', NULL, NULL,
                        'staff_api', NULL, '[]'::jsonb,
                        '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                        'sensitive_operational'
                    )
                    """
                )
            )

        command.upgrade(alembic_config, "head")

        with engine.connect() as upgraded_connection:
            assert (
                upgraded_connection.execute(text("SELECT count(*) FROM employers")).scalar_one()
                == 1
            )
            assert (
                upgraded_connection.execute(
                    text("SELECT count(*) FROM command_receipts")
                ).scalar_one()
                == 1
            )
            assert (
                upgraded_connection.execute(text("SELECT count(*) FROM audit_events")).scalar_one()
                == 1
            )
            constraint_names = {
                row[0]
                for row in upgraded_connection.execute(
                    text(
                        """
                        SELECT conname
                        FROM pg_constraint
                        WHERE conname IN (
                            'fk_command_receipts_creation_event',
                            'fk_command_receipts_result_employer',
                            'fk_audit_events_command_result',
                            'uq_audit_events_command_entity'
                        )
                        """
                    )
                )
            }
            assert constraint_names == {
                "fk_command_receipts_creation_event",
                "fk_command_receipts_result_employer",
                "fk_audit_events_command_result",
                "uq_audit_events_command_entity",
            }
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


def test_revision_migration_upgrades_existing_create_rows_and_receipts(engine) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )

    command.downgrade(alembic_config, "0002_enforce_authority_links")
    try:
        with engine.begin() as predecessor_connection:
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO employers (
                        employer_id, employer_type, display_name, lifecycle_status,
                        source_channel, received_at, created_at, created_by, version
                    ) VALUES (
                        '11111111-1111-4111-8111-111111111111', 'business',
                        'Synthetic Predecessor Employer', 'draft', 'staff_entry',
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                        '22222222-2222-4222-8222-222222222222', 1
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO command_receipts (
                        command_id, command_schema_version, command_type, actor_id,
                        request_fingerprint, result_entity_type, result_entity_id, created_at
                    ) VALUES (
                        '33333333-3333-4333-8333-333333333333', 1,
                        'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                        decode(repeat('aa', 32), 'hex'), 'employer',
                        '11111111-1111-4111-8111-111111111111', TIMESTAMPTZ '2026-08-04T12:00:00Z'
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        audit_event_id, event_schema_name, event_schema_version, event_type,
                        entity_type, entity_id, entity_sequence, prior_record_version,
                        new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                        occurred_at, effective_at, command_id, correlation_id, reason_code,
                        reason_text, source_type, source_reference, related_event_ids,
                        changed_fields, payload_classification
                    ) VALUES (
                        '44444444-4444-4444-8444-444444444444', 'employer.created', 1,
                        'employer.created', 'employer',
                        '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                        '22222222-2222-4222-8222-222222222222', NULL,
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', NULL,
                        '33333333-3333-4333-8333-333333333333',
                        '33333333-3333-4333-8333-333333333333', NULL, NULL,
                        'staff_api', NULL, '[]'::jsonb,
                        '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                        'sensitive_operational'
                    )
                    """
                )
            )

        command.upgrade(alembic_config, "head")

        with engine.connect() as upgraded_connection:
            inspector = inspect(upgraded_connection)
            employer_columns = {column["name"] for column in inspector.get_columns("employers")}
            command_receipt_columns = {
                column["name"] for column in inspector.get_columns("command_receipts")
            }

            assert {"updated_at", "updated_by"}.issubset(employer_columns)
            assert {"result_record_version", "result_event_type"}.issubset(command_receipt_columns)
            upgraded_row = upgraded_connection.execute(
                text(
                    """
                    SELECT
                        e.updated_at,
                        e.updated_by,
                        cr.result_record_version,
                        cr.result_event_type
                    FROM employers AS e
                    JOIN command_receipts AS cr ON cr.result_entity_id = e.employer_id
                    WHERE e.employer_id = '11111111-1111-4111-8111-111111111111'
                    """
                )
            ).one()

            assert upgraded_row.updated_at.isoformat() == "2026-08-04T12:00:00+00:00"
            assert str(upgraded_row.updated_by) == "22222222-2222-4222-8222-222222222222"
            assert upgraded_row.result_record_version == 1
            assert upgraded_row.result_event_type == "employer.created"
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


def test_revision_migration_refuses_incomplete_existing_receipt_event_cardinality(engine) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )

    command.downgrade(alembic_config, "0002_enforce_authority_links")
    try:
        with engine.begin() as predecessor_connection:
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO employers (
                        employer_id, employer_type, display_name, lifecycle_status,
                        source_channel, received_at, created_at, created_by, version
                    ) VALUES (
                        '11111111-1111-4111-8111-111111111111', 'business',
                        'Synthetic Incomplete Authority Employer', 'draft', 'staff_entry',
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                        '22222222-2222-4222-8222-222222222222', 1
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO command_receipts (
                        command_id, command_schema_version, command_type, actor_id,
                        request_fingerprint, result_entity_type, result_entity_id, created_at
                    ) VALUES (
                        '33333333-3333-4333-8333-333333333333', 1,
                        'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                        decode(repeat('aa', 32), 'hex'), 'employer',
                        '11111111-1111-4111-8111-111111111111', TIMESTAMPTZ '2026-08-04T12:00:00Z'
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        audit_event_id, event_schema_name, event_schema_version, event_type,
                        entity_type, entity_id, entity_sequence, prior_record_version,
                        new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                        occurred_at, effective_at, command_id, correlation_id, reason_code,
                        reason_text, source_type, source_reference, related_event_ids,
                        changed_fields, payload_classification
                    ) VALUES (
                        '44444444-4444-4444-8444-444444444444', 'employer.created', 1,
                        'employer.created', 'employer',
                        '11111111-1111-4111-8111-111111111111', 2, 1, 2, 'staff',
                        '22222222-2222-4222-8222-222222222222', NULL,
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', NULL,
                        '33333333-3333-4333-8333-333333333333',
                        '33333333-3333-4333-8333-333333333333', NULL, NULL,
                        'staff_api', NULL, '[]'::jsonb,
                        '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                        'sensitive_operational'
                    )
                    """
                )
            )

        with pytest.raises(
            RuntimeError,
            match="incomplete receipt/event authority blocks revision migration",
        ):
            command.upgrade(alembic_config, "head")

        with engine.connect() as failed_upgrade_connection:
            inspector = inspect(failed_upgrade_connection)
            employer_columns = {column["name"] for column in inspector.get_columns("employers")}
            command_receipt_columns = {
                column["name"] for column in inspector.get_columns("command_receipts")
            }

            assert "updated_at" not in employer_columns
            assert "updated_by" not in employer_columns
            assert "result_record_version" not in command_receipt_columns
            assert "result_event_type" not in command_receipt_columns
            assert (
                failed_upgrade_connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                == "0002_enforce_authority_links"
            )
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


def test_revision_migration_backfills_receipts_under_transactional_trigger_guard(engine) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )

    command.downgrade(alembic_config, "0002_enforce_authority_links")
    try:
        with engine.begin() as predecessor_connection:
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO employers (
                        employer_id, employer_type, display_name, lifecycle_status,
                        source_channel, received_at, created_at, created_by, version
                    ) VALUES (
                        '11111111-1111-4111-8111-111111111111', 'business',
                        'Synthetic Trigger Guard Employer', 'draft', 'staff_entry',
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                        '22222222-2222-4222-8222-222222222222', 1
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO command_receipts (
                        command_id, command_schema_version, command_type, actor_id,
                        request_fingerprint, result_entity_type, result_entity_id, created_at
                    ) VALUES (
                        '33333333-3333-4333-8333-333333333333', 1,
                        'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                        decode(repeat('aa', 32), 'hex'), 'employer',
                        '11111111-1111-4111-8111-111111111111', TIMESTAMPTZ '2026-08-04T12:00:00Z'
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        audit_event_id, event_schema_name, event_schema_version, event_type,
                        entity_type, entity_id, entity_sequence, prior_record_version,
                        new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                        occurred_at, effective_at, command_id, correlation_id, reason_code,
                        reason_text, source_type, source_reference, related_event_ids,
                        changed_fields, payload_classification
                    ) VALUES (
                        '44444444-4444-4444-8444-444444444444', 'employer.created', 1,
                        'employer.created', 'employer',
                        '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                        '22222222-2222-4222-8222-222222222222', NULL,
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', NULL,
                        '33333333-3333-4333-8333-333333333333',
                        '33333333-3333-4333-8333-333333333333', NULL, NULL,
                        'staff_api', NULL, '[]'::jsonb,
                        '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                        'sensitive_operational'
                    )
                    """
                )
            )

        command.upgrade(alembic_config, "head")

        with engine.connect() as upgraded_connection:
            upgraded_row = upgraded_connection.execute(
                text(
                    """
                    SELECT result_record_version, result_event_type
                    FROM command_receipts
                    WHERE command_id = '33333333-3333-4333-8333-333333333333'
                    """
                )
            ).one()
            trigger_names = {
                row[0]
                for row in upgraded_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'command_receipts'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }

            assert upgraded_row.result_record_version == 1
            assert upgraded_row.result_event_type == "employer.created"
            assert "command_receipts_revision_compatibility_defaults" in trigger_names
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


def test_revision_migration_restores_receipt_mutation_denial_after_upgrade(engine) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )

    command.downgrade(alembic_config, "0002_enforce_authority_links")
    try:
        with engine.begin() as predecessor_connection:
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO employers (
                        employer_id, employer_type, display_name, lifecycle_status,
                        source_channel, received_at, created_at, created_by, version
                    ) VALUES (
                        '11111111-1111-4111-8111-111111111111', 'business',
                        'Synthetic Mutation Guard Employer', 'draft', 'staff_entry',
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                        '22222222-2222-4222-8222-222222222222', 1
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO command_receipts (
                        command_id, command_schema_version, command_type, actor_id,
                        request_fingerprint, result_entity_type, result_entity_id, created_at
                    ) VALUES (
                        '33333333-3333-4333-8333-333333333333', 1,
                        'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                        decode(repeat('aa', 32), 'hex'), 'employer',
                        '11111111-1111-4111-8111-111111111111', TIMESTAMPTZ '2026-08-04T12:00:00Z'
                    )
                    """
                )
            )
            predecessor_connection.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        audit_event_id, event_schema_name, event_schema_version, event_type,
                        entity_type, entity_id, entity_sequence, prior_record_version,
                        new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                        occurred_at, effective_at, command_id, correlation_id, reason_code,
                        reason_text, source_type, source_reference, related_event_ids,
                        changed_fields, payload_classification
                    ) VALUES (
                        '44444444-4444-4444-8444-444444444444', 'employer.created', 1,
                        'employer.created', 'employer',
                        '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                        '22222222-2222-4222-8222-222222222222', NULL,
                        TIMESTAMPTZ '2026-08-04T12:00:00Z', NULL,
                        '33333333-3333-4333-8333-333333333333',
                        '33333333-3333-4333-8333-333333333333', NULL, NULL,
                        'staff_api', NULL, '[]'::jsonb,
                        '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                        'sensitive_operational'
                    )
                    """
                )
            )

        command.upgrade(alembic_config, "head")

        with engine.connect() as upgraded_connection:
            trigger_names = {
                row[0]
                for row in upgraded_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'command_receipts'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }

            assert "command_receipts_no_update" in trigger_names

            with pytest.raises(SQLAlchemyError):
                upgraded_connection.execute(
                    text(
                        """
                        UPDATE command_receipts
                        SET result_event_type = 'tampered'
                        WHERE command_id = '33333333-3333-4333-8333-333333333333'
                        """
                    )
                )
                upgraded_connection.commit()
            upgraded_connection.rollback()
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


def test_revision_live_schema_enforces_one_step_event_version_authority(connection) -> None:
    inspector = inspect(connection)

    command_receipt_columns = {
        column["name"] for column in inspector.get_columns("command_receipts")
    }
    employer_columns = {column["name"] for column in inspector.get_columns("employers")}
    command_receipt_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("command_receipts")
    }
    audit_event_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("audit_events")
    }
    command_receipt_foreign_keys = {
        foreign_key["name"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("command_receipts")
    }
    audit_event_foreign_keys = {
        foreign_key["name"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("audit_events")
    }

    receipt_fk_flags = {
        row["conname"]: {
            "condeferrable": row["condeferrable"],
            "condeferred": row["condeferred"],
        }
        for row in connection.execute(
            text(
                """
                SELECT conname, condeferrable, condeferred
                FROM pg_constraint
                WHERE conname = 'fk_command_receipts_result_audit_event'
                """
            )
        ).mappings()
    }

    assert {"updated_at", "updated_by"}.issubset(employer_columns)
    assert {"result_record_version", "result_event_type"}.issubset(command_receipt_columns)
    assert "uq_command_receipts_result_authority" in command_receipt_unique_constraints
    assert "uq_audit_events_result_authority" in audit_event_unique_constraints
    assert command_receipt_foreign_keys["fk_command_receipts_result_audit_event"] == {
        "name": "fk_command_receipts_result_audit_event",
        "constrained_columns": [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        "referred_schema": None,
        "referred_table": "audit_events",
        "referred_columns": [
            "command_id",
            "entity_id",
            "new_record_version",
            "event_type",
            "actor_id",
        ],
        "options": {"initially": "DEFERRED", "deferrable": True},
        "comment": None,
    }
    assert audit_event_foreign_keys["fk_audit_events_command_result"] == {
        "name": "fk_audit_events_command_result",
        "constrained_columns": [
            "command_id",
            "entity_id",
            "new_record_version",
            "event_type",
            "actor_id",
        ],
        "referred_schema": None,
        "referred_table": "command_receipts",
        "referred_columns": [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        "options": {"initially": "DEFERRED", "deferrable": True},
        "comment": None,
    }
    assert receipt_fk_flags == {
        "fk_command_receipts_result_audit_event": {
            "condeferrable": True,
            "condeferred": True,
        }
    }


def test_revision_live_schema_rejects_mismatched_receipt_event_version(
    connection, clean_tables
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO employers (
                employer_id, employer_type, display_name, lifecycle_status, source_channel,
                received_at, created_at, created_by, version, updated_at, updated_by
            ) VALUES (
                '11111111-1111-4111-8111-111111111111', 'business',
                'Synthetic Version Mismatch Employer', 'draft', 'staff_entry', NOW(), NOW(),
                '22222222-2222-4222-8222-222222222222', 1, NOW(),
                '22222222-2222-4222-8222-222222222222'
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO command_receipts (
                command_id, command_schema_version, command_type, actor_id,
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
            )
            """
        )
    )
    with pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    audit_event_id, event_schema_name, event_schema_version,
                    event_type, entity_type, entity_id, entity_sequence,
                    prior_record_version, new_record_version, actor_type,
                    actor_id, initiating_staff_actor_id, occurred_at,
                    effective_at, command_id,
                    correlation_id, reason_code, reason_text, source_type, source_reference,
                    related_event_ids, changed_fields, payload_classification
                ) VALUES (
                    '44444444-4444-4444-8444-444444444444', 'employer.created',
                    1, 'employer.created', 'employer',
                    '11111111-1111-4111-8111-111111111111', 1, 0, 2,
                    'staff',
                    '22222222-2222-4222-8222-222222222222', NULL, NOW(), NULL,
                    '33333333-3333-4333-8333-333333333333', '33333333-3333-4333-8333-333333333333',
                    NULL, NULL, 'staff_api', NULL, '[]'::jsonb,
                    '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                    'sensitive_operational'
                )
                """
            )
        )

    connection.rollback()


def test_revision_live_schema_rejects_orphan_receipt_and_orphan_event_at_commit(
    connection, clean_tables
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO employers (
                employer_id, employer_type, display_name, lifecycle_status, source_channel,
                received_at, created_at, created_by, version, updated_at, updated_by
            ) VALUES (
                '11111111-1111-4111-8111-111111111111', 'business',
                'Synthetic Orphan Receipt Employer', 'draft', 'staff_entry', NOW(), NOW(),
                '22222222-2222-4222-8222-222222222222', 1, NOW(),
                '22222222-2222-4222-8222-222222222222'
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO command_receipts (
                command_id, command_schema_version, command_type, actor_id,
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
            )
            """
        )
    )

    with pytest.raises(IntegrityError):
        connection.commit()

    connection.rollback()

    connection.execute(
        text(
            """
            INSERT INTO employers (
                employer_id, employer_type, display_name, lifecycle_status, source_channel,
                received_at, created_at, created_by, version, updated_at, updated_by
            ) VALUES (
                '55555555-5555-4555-8555-555555555555', 'business',
                'Synthetic Orphan Event Employer', 'draft', 'staff_entry', NOW(), NOW(),
                '22222222-2222-4222-8222-222222222222', 1, NOW(),
                '22222222-2222-4222-8222-222222222222'
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO audit_events (
                audit_event_id, event_schema_name, event_schema_version,
                event_type, entity_type, entity_id, entity_sequence,
                prior_record_version, new_record_version, actor_type,
                actor_id, initiating_staff_actor_id, occurred_at,
                effective_at, command_id,
                correlation_id, reason_code, reason_text, source_type, source_reference,
                related_event_ids, changed_fields, payload_classification
            ) VALUES (
                '66666666-6666-4666-8666-666666666666', 'employer.created',
                1, 'employer.created', 'employer',
                '55555555-5555-4555-8555-555555555555', 1, 0, 1,
                'staff',
                '22222222-2222-4222-8222-222222222222', NULL, NOW(), NULL,
                '77777777-7777-4777-8777-777777777777', '77777777-7777-4777-8777-777777777777',
                NULL, NULL, 'staff_api', NULL, '[]'::jsonb,
                '{"field_names": ["employer_type", "display_name"]}'::jsonb, 'sensitive_operational'
            )
            """
        )
    )

    with pytest.raises(IntegrityError):
        connection.commit()

    connection.rollback()


def test_revision_empty_downgrade_restores_closeout_schema_and_guards(engine) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )

    try:
        command.downgrade(alembic_config, "0002_enforce_authority_links")

        with engine.connect() as downgraded_connection:
            inspector = inspect(downgraded_connection)

            employer_columns = {column["name"] for column in inspector.get_columns("employers")}
            command_receipt_columns = {
                column["name"] for column in inspector.get_columns("command_receipts")
            }
            audit_event_foreign_keys = {
                foreign_key["name"]: foreign_key
                for foreign_key in inspector.get_foreign_keys("audit_events")
            }
            command_receipt_foreign_keys = {
                foreign_key["name"]: foreign_key
                for foreign_key in inspector.get_foreign_keys("command_receipts")
            }
            command_receipt_triggers = {
                row[0]
                for row in downgraded_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'command_receipts'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }
            audit_event_triggers = {
                row[0]
                for row in downgraded_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'audit_events'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }

            assert "updated_at" not in employer_columns
            assert "updated_by" not in employer_columns
            assert "result_record_version" not in command_receipt_columns
            assert "result_event_type" not in command_receipt_columns
            assert "fk_command_receipts_result_audit_event" not in command_receipt_foreign_keys
            assert audit_event_foreign_keys["fk_audit_events_command_result"] == {
                "name": "fk_audit_events_command_result",
                "constrained_columns": ["command_id", "entity_id"],
                "referred_schema": None,
                "referred_table": "command_receipts",
                "referred_columns": ["command_id", "result_entity_id"],
                "options": {},
                "comment": None,
            }
            assert {
                "command_receipts_no_update",
                "command_receipts_no_delete",
            }.issubset(command_receipt_triggers)
            assert {"audit_events_no_update", "audit_events_no_delete"}.issubset(
                audit_event_triggers
            )
    finally:
        command.upgrade(alembic_config, "head")


def test_revision_populated_create_only_downgrade_preserves_rows_correspondence_constraints_and_guards(  # noqa: E501
    engine,
) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )
        migration_connection.execute(
            text(
                """
                INSERT INTO employers (
                    employer_id, employer_type, display_name, lifecycle_status, source_channel,
                    received_at, created_at, created_by, updated_at, updated_by, version
                ) VALUES (
                    '11111111-1111-4111-8111-111111111111', 'business',
                    'Synthetic Downgrade Preservation Employer', 'draft', 'staff_entry',
                    TIMESTAMPTZ '2026-08-04T12:00:00Z', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                    '22222222-2222-4222-8222-222222222222', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                    '22222222-2222-4222-8222-222222222222', 1
                )
                """
            )
        )
        migration_connection.execute(
            text(
                """
                INSERT INTO command_receipts (
                    command_id, command_schema_version, command_type, actor_id,
                    request_fingerprint, result_entity_type, result_entity_id,
                    result_record_version, result_event_type, created_at
                ) VALUES (
                    '33333333-3333-4333-8333-333333333333', 1,
                    'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                    decode(repeat('aa', 32), 'hex'), 'employer',
                    '11111111-1111-4111-8111-111111111111', 1, 'employer.created',
                    TIMESTAMPTZ '2026-08-04T12:00:00Z'
                )
                """
            )
        )
        migration_connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    audit_event_id, event_schema_name, event_schema_version, event_type,
                    entity_type, entity_id, entity_sequence, prior_record_version,
                    new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                    occurred_at, effective_at, command_id, correlation_id, reason_code,
                    reason_text, source_type, source_reference, related_event_ids,
                    changed_fields, payload_classification
                ) VALUES (
                    '44444444-4444-4444-8444-444444444444', 'employer.created', 1,
                    'employer.created', 'employer',
                    '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                    '22222222-2222-4222-8222-222222222222', NULL,
                    TIMESTAMPTZ '2026-08-04T12:00:00Z', NULL,
                    '33333333-3333-4333-8333-333333333333',
                    '33333333-3333-4333-8333-333333333333', NULL, NULL,
                    'staff_api', NULL, '[]'::jsonb,
                    '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                    'sensitive_operational'
                )
                """
            )
        )

    try:
        command.downgrade(alembic_config, "0002_enforce_authority_links")

        with engine.connect() as downgraded_connection:
            inspector = inspect(downgraded_connection)

            employer_columns = {column["name"] for column in inspector.get_columns("employers")}
            command_receipt_columns = {
                column["name"] for column in inspector.get_columns("command_receipts")
            }
            command_receipt_foreign_keys = {
                foreign_key["name"]: foreign_key
                for foreign_key in inspector.get_foreign_keys("command_receipts")
            }
            audit_event_foreign_keys = {
                foreign_key["name"]: foreign_key
                for foreign_key in inspector.get_foreign_keys("audit_events")
            }
            command_receipt_triggers = {
                row[0]
                for row in downgraded_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'command_receipts'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }
            audit_event_triggers = {
                row[0]
                for row in downgraded_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'audit_events'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }
            downgraded_row = downgraded_connection.execute(
                text(
                    """
                    SELECT
                        e.display_name,
                        e.version,
                        cr.command_type,
                        cr.result_entity_id,
                        ae.entity_id,
                        ae.new_record_version
                    FROM employers AS e
                    JOIN command_receipts AS cr
                      ON cr.result_entity_id = e.employer_id
                    JOIN audit_events AS ae
                      ON ae.command_id = cr.command_id
                     AND ae.entity_id = e.employer_id
                    WHERE e.employer_id = '11111111-1111-4111-8111-111111111111'
                    """
                )
            ).one()

            assert "updated_at" not in employer_columns
            assert "updated_by" not in employer_columns
            assert "result_record_version" not in command_receipt_columns
            assert "result_event_type" not in command_receipt_columns
            assert "fk_command_receipts_result_audit_event" not in command_receipt_foreign_keys
            assert audit_event_foreign_keys["fk_audit_events_command_result"] == {
                "name": "fk_audit_events_command_result",
                "constrained_columns": ["command_id", "entity_id"],
                "referred_schema": None,
                "referred_table": "command_receipts",
                "referred_columns": ["command_id", "result_entity_id"],
                "options": {},
                "comment": None,
            }
            assert downgraded_row.display_name == "Synthetic Downgrade Preservation Employer"
            assert downgraded_row.version == 1
            assert downgraded_row.command_type == "create_draft_employer"
            assert str(downgraded_row.result_entity_id) == "11111111-1111-4111-8111-111111111111"
            assert str(downgraded_row.entity_id) == "11111111-1111-4111-8111-111111111111"
            assert downgraded_row.new_record_version == 1
            assert {
                "command_receipts_no_update",
                "command_receipts_no_delete",
            }.issubset(command_receipt_triggers)
            assert {"audit_events_no_update", "audit_events_no_delete"}.issubset(
                audit_event_triggers
            )
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


def test_revision_populated_downgrade_fails_closed_and_preserves_schema_data_guards(
    engine,
) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")

    command.upgrade(alembic_config, "head")

    with engine.begin() as migration_connection:
        migration_connection.execute(
            text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
        )
        migration_connection.execute(
            text(
                """
                INSERT INTO employers (
                    employer_id, employer_type, display_name, lifecycle_status, source_channel,
                    received_at, created_at, created_by, updated_at, updated_by, version
                ) VALUES (
                    '11111111-1111-4111-8111-111111111111', 'business',
                    'Synthetic Refusal Employer', 'draft', 'staff_entry',
                    TIMESTAMPTZ '2026-08-04T12:00:00Z', TIMESTAMPTZ '2026-08-04T12:00:00Z',
                    '22222222-2222-4222-8222-222222222222', TIMESTAMPTZ '2026-08-05T12:00:00Z',
                    '33333333-3333-4333-8333-333333333333', 2
                )
                """
            )
        )
        migration_connection.execute(
            text(
                """
                INSERT INTO command_receipts (
                    command_id, command_schema_version, command_type, actor_id,
                    request_fingerprint, result_entity_type, result_entity_id,
                    result_record_version, result_event_type, created_at
                ) VALUES (
                    '44444444-4444-4444-8444-444444444444', 1,
                    'create_draft_employer', '22222222-2222-4222-8222-222222222222',
                    decode(repeat('aa', 32), 'hex'), 'employer',
                    '11111111-1111-4111-8111-111111111111', 1, 'employer.created',
                    TIMESTAMPTZ '2026-08-04T12:00:00Z'
                )
                """
            )
        )
        migration_connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    audit_event_id, event_schema_name, event_schema_version, event_type,
                    entity_type, entity_id, entity_sequence, prior_record_version,
                    new_record_version, actor_type, actor_id, initiating_staff_actor_id,
                    occurred_at, effective_at, command_id, correlation_id, reason_code,
                    reason_text, source_type, source_reference, related_event_ids,
                    changed_fields, payload_classification
                ) VALUES (
                    '55555555-5555-4555-8555-555555555555', 'employer.created', 1,
                    'employer.created', 'employer',
                    '11111111-1111-4111-8111-111111111111', 1, 0, 1, 'staff',
                    '22222222-2222-4222-8222-222222222222', NULL,
                    TIMESTAMPTZ '2026-08-04T12:00:00Z', NULL,
                    '44444444-4444-4444-8444-444444444444',
                    '44444444-4444-4444-8444-444444444444', NULL, NULL,
                    'staff_api', NULL, '[]'::jsonb,
                    '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                    'sensitive_operational'
                )
                """
            )
        )

    try:
        with pytest.raises(RuntimeError):
            command.downgrade(alembic_config, "0002_enforce_authority_links")

        with engine.connect() as head_connection:
            inspector = inspect(head_connection)

            employer_columns = {column["name"] for column in inspector.get_columns("employers")}
            command_receipt_columns = {
                column["name"] for column in inspector.get_columns("command_receipts")
            }
            command_receipt_triggers = {
                row[0]
                for row in head_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'command_receipts'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }
            audit_event_triggers = {
                row[0]
                for row in head_connection.execute(
                    text(
                        """
                        SELECT tgname
                        FROM pg_trigger
                        WHERE tgrelid = 'audit_events'::regclass
                          AND NOT tgisinternal
                        """
                    )
                )
            }
            preserved_row = head_connection.execute(
                text(
                    """
                    SELECT display_name, version, updated_by <> created_by AS updated_actor_changed,
                           updated_at > created_at AS updated_time_changed
                    FROM employers
                    WHERE employer_id = '11111111-1111-4111-8111-111111111111'
                    """
                )
            ).one()

            assert {"updated_at", "updated_by"}.issubset(employer_columns)
            assert {"result_record_version", "result_event_type"}.issubset(command_receipt_columns)
            assert preserved_row.display_name == "Synthetic Refusal Employer"
            assert preserved_row.version == 2
            assert preserved_row.updated_actor_changed is True
            assert preserved_row.updated_time_changed is True
            assert {
                "command_receipts_no_update",
                "command_receipts_no_delete",
            }.issubset(command_receipt_triggers)
            assert {"audit_events_no_update", "audit_events_no_delete"}.issubset(
                audit_event_triggers
            )
    finally:
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text("TRUNCATE TABLE audit_events, command_receipts, employers CASCADE")
            )
        command.upgrade(alembic_config, "head")


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
        "updated_at",
        "updated_by",
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
        "result_record_version",
        "result_event_type",
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
        "ck_command_receipts_result_authority_shape",
        "ck_command_receipts_result_record_version_positive",
        "ck_command_receipts_schema_version",
    }
    assert audit_event_checks == {
        "ck_audit_events_actor_type",
        "ck_audit_events_correlation_matches_command",
        "ck_audit_events_entity_type",
        "ck_audit_events_entity_sequence_matches_new_record_version",
        "ck_audit_events_event_type",
        "ck_audit_events_one_step_version_advance",
        "ck_audit_events_payload_classification",
        "ck_audit_events_schema_matches_type",
        "ck_audit_events_schema_name",
        "ck_audit_events_schema_version",
        "ck_audit_events_source_type",
    }
    assert audit_event_unique_constraints == {
        "uq_audit_events_command_entity",
        "uq_audit_events_command_event_type",
        "uq_audit_events_entity_sequence",
        "uq_audit_events_result_authority",
    }


def test_live_schema_exposes_authority_relationships(connection) -> None:
    inspector = inspect(connection)

    command_receipt_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("command_receipts")
    }
    audit_event_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("audit_events")
    }
    command_receipt_foreign_keys = {
        foreign_key["name"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("command_receipts")
    }
    audit_event_foreign_keys = {
        foreign_key["name"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("audit_events")
    }

    receipt_fk_flags = {
        row["conname"]: {
            "condeferrable": row["condeferrable"],
            "condeferred": row["condeferred"],
        }
        for row in connection.execute(
            text(
                """
            SELECT conname, condeferrable, condeferred
            FROM pg_constraint
            WHERE conname IN (
                'fk_command_receipts_result_employer',
                'fk_command_receipts_creation_event',
                'fk_audit_events_command_result'
            )
            """
            )
        ).mappings()
    }

    assert "uq_command_receipts_command_result" in command_receipt_unique_constraints
    assert "uq_audit_events_command_entity" in audit_event_unique_constraints
    assert "uq_audit_events_command_event_type" in audit_event_unique_constraints
    assert "uq_audit_events_result_authority" in audit_event_unique_constraints
    assert command_receipt_foreign_keys["fk_command_receipts_result_employer"] == {
        "name": "fk_command_receipts_result_employer",
        "constrained_columns": ["result_entity_id"],
        "referred_schema": None,
        "referred_table": "employers",
        "referred_columns": ["employer_id"],
        "options": {"initially": "DEFERRED", "deferrable": True},
        "comment": None,
    }
    assert command_receipt_foreign_keys["fk_command_receipts_creation_event"] == {
        "name": "fk_command_receipts_creation_event",
        "constrained_columns": ["command_id", "result_entity_id"],
        "referred_schema": None,
        "referred_table": "audit_events",
        "referred_columns": ["command_id", "entity_id"],
        "options": {"initially": "DEFERRED", "deferrable": True},
        "comment": None,
    }
    assert audit_event_foreign_keys["fk_audit_events_command_result"] == {
        "name": "fk_audit_events_command_result",
        "constrained_columns": [
            "command_id",
            "entity_id",
            "new_record_version",
            "event_type",
            "actor_id",
        ],
        "referred_schema": None,
        "referred_table": "command_receipts",
        "referred_columns": [
            "command_id",
            "result_entity_id",
            "result_record_version",
            "result_event_type",
            "actor_id",
        ],
        "options": {"initially": "DEFERRED", "deferrable": True},
        "comment": None,
    }
    assert receipt_fk_flags == {
        "fk_command_receipts_creation_event": {
            "condeferrable": True,
            "condeferred": True,
        },
        "fk_command_receipts_result_employer": {
            "condeferrable": True,
            "condeferred": True,
        },
        "fk_audit_events_command_result": {
            "condeferrable": True,
            "condeferred": True,
        },
    }


def test_receipt_requires_its_result_employer(connection, clean_tables) -> None:
    connection.execute(
        text(
            """
            INSERT INTO command_receipts (
                command_id, command_schema_version, command_type, actor_id,
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
            )
            """
        )
    )

    with pytest.raises(IntegrityError):
        connection.commit()

    connection.rollback()


def test_receipt_requires_exactly_one_matching_creation_event(connection, clean_tables) -> None:
    connection.execute(
        text(
            """
            INSERT INTO employers (
                employer_id, employer_type, display_name, lifecycle_status, source_channel,
                received_at, created_at, created_by, version
            ) VALUES (
                '11111111-1111-4111-8111-111111111111', 'business',
                'Synthetic Orphan Receipt Employer', 'draft', 'staff_entry', NOW(), NOW(),
                '22222222-2222-4222-8222-222222222222', 1
            )
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO command_receipts (
                command_id, command_schema_version, command_type, actor_id,
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
            )
            """
        )
    )

    with pytest.raises(IntegrityError):
        connection.commit()

    connection.rollback()


def test_audit_event_command_must_name_receipt_result(connection, clean_tables) -> None:
    connection.execute(
        text(
            """
            INSERT INTO employers (
                employer_id, employer_type, display_name, lifecycle_status, source_channel,
                received_at, created_at, created_by, version
            ) VALUES
                (
                    '11111111-1111-4111-8111-111111111111', 'household', 'Synthetic Household 001',
                    'draft', 'staff_entry', NOW(), NOW(), '22222222-2222-4222-8222-222222222222', 1
                ),
                (
                    '55555555-5555-4555-8555-555555555555', 'business', 'Synthetic Business 001',
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
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
            )
            """
        )
    )
    with pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    audit_event_id, event_schema_name, event_schema_version,
                    event_type, entity_type, entity_id, entity_sequence,
                    prior_record_version, new_record_version, actor_type,
                    actor_id, initiating_staff_actor_id, occurred_at,
                    effective_at, command_id,
                    correlation_id, reason_code, reason_text, source_type, source_reference,
                    related_event_ids, changed_fields, payload_classification
                ) VALUES (
                    '44444444-4444-4444-8444-444444444444', 'employer.created',
                    1, 'employer.created', 'employer',
                    '55555555-5555-4555-8555-555555555555', 1, 0, 1,
                    'staff',
                    '22222222-2222-4222-8222-222222222222', NULL, NOW(), NULL,
                    '33333333-3333-4333-8333-333333333333', '33333333-3333-4333-8333-333333333333',
                    NULL, NULL, 'staff_api', NULL, '[]'::jsonb,
                    '{"field_names": ["employer_type"]}'::jsonb, 'sensitive_operational'
                )
                """
            )
        )
        connection.commit()

    connection.rollback()


def test_create_command_rejects_duplicate_creation_event(connection, clean_tables) -> None:
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
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
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

    with pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    audit_event_id, event_schema_name, event_schema_version,
                    event_type, entity_type, entity_id, entity_sequence,
                    prior_record_version, new_record_version, actor_type,
                    actor_id, initiating_staff_actor_id, occurred_at,
                    effective_at, command_id,
                    correlation_id, reason_code, reason_text, source_type, source_reference,
                    related_event_ids, changed_fields, payload_classification
                ) VALUES (
                    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'employer.created',
                    1, 'employer.created', 'employer',
                    '11111111-1111-4111-8111-111111111111', 2, 1, 2,
                    'staff',
                    '22222222-2222-4222-8222-222222222222', NULL, NOW(), NULL,
                    '33333333-3333-4333-8333-333333333333', '33333333-3333-4333-8333-333333333333',
                    NULL, NULL, 'staff_api', NULL, '[]'::jsonb,
                    '{"field_names": ["employer_type"]}'::jsonb, 'sensitive_operational'
                )
                """
            )
        )

    connection.rollback()


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
                request_fingerprint, result_entity_type, result_entity_id, created_at,
                result_record_version, result_event_type
            ) VALUES (
                '33333333-3333-4333-8333-333333333333', 1, 'create_draft_employer',
                '22222222-2222-4222-8222-222222222222', decode(repeat('aa', 32), 'hex'),
                'employer', '11111111-1111-4111-8111-111111111111', NOW(), 1,
                'employer.created'
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
        except SQLAlchemyError:
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
