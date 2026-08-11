import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from golden_rose.application.create_draft_employer import (
    IdempotencyConflictError,
    create_draft_employer,
)
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.auth.principal import StaffPrincipal


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FixedIdentifierFactory:
    def __init__(self, *identifiers: UUID) -> None:
        self._identifiers = list(identifiers)

    def new_uuid4(self) -> UUID:
        return self._identifiers.pop(0)


def _run_create_draft_employer_in_isolated_session(
    *,
    engine,
    barrier: threading.Barrier,
    principal: StaffPrincipal,
    command_id: UUID,
    employer_type: Literal["household", "business"],
    display_name: str,
    now: datetime,
    identifiers: FixedIdentifierFactory,
):
    with Session(engine) as isolated_session:
        barrier.wait()
        return create_draft_employer(
            session=isolated_session,
            principal=principal,
            command_id=command_id,
            employer_type=employer_type,
            display_name=display_name,
            clock=FixedClock(now),
            identifiers=identifiers,
        )


def test_create_draft_employer_creates_receipt_employer_and_audit_event(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("22222222-2222-4222-8222-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("33333333-3333-4333-8333-333333333333")
    employer_id = UUID("11111111-1111-4111-8111-111111111111")
    audit_event_id = UUID("44444444-4444-4444-8444-444444444444")
    fixed_now = datetime(2026, 8, 4, 23, 30, 45, tzinfo=UTC)

    result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Household 001",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    assert result.replayed is False
    assert result.employer.employer_id == employer_id
    assert result.employer.version == 1
    assert result.employer.created_at == fixed_now
    assert result.employer.received_at == fixed_now

    command_receipt = (
        session.execute(
            text(
                """
            SELECT command_id, command_schema_version, command_type, actor_id,
                   result_entity_type, result_entity_id
            FROM command_receipts
            WHERE command_id = :command_id
            """
            ),
            {"command_id": command_id},
        )
        .mappings()
        .one()
    )
    employer = (
        session.execute(
            text(
                """
            SELECT employer_id, employer_type, display_name, lifecycle_status,
                   source_channel, created_by, version
            FROM employers
            WHERE employer_id = :employer_id
            """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    audit_event = (
        session.execute(
            text(
                """
            SELECT audit_event_id, event_schema_name, event_schema_version, event_type,
                   entity_type, entity_id, entity_sequence, prior_record_version,
                   new_record_version, actor_type, actor_id, command_id, correlation_id,
                   source_type, payload_classification
            FROM audit_events
            WHERE audit_event_id = :audit_event_id
            """
            ),
            {"audit_event_id": audit_event_id},
        )
        .mappings()
        .one()
    )

    assert dict(command_receipt) == {
        "command_id": command_id,
        "command_schema_version": 1,
        "command_type": "create_draft_employer",
        "actor_id": principal.actor_id,
        "result_entity_type": "employer",
        "result_entity_id": employer_id,
    }
    assert dict(employer) == {
        "employer_id": employer_id,
        "employer_type": "household",
        "display_name": "Synthetic Household 001",
        "lifecycle_status": "draft",
        "source_channel": "staff_entry",
        "created_by": principal.actor_id,
        "version": 1,
    }
    assert dict(audit_event) == {
        "audit_event_id": audit_event_id,
        "event_schema_name": "employer.created",
        "event_schema_version": 1,
        "event_type": "employer.created",
        "entity_type": "employer",
        "entity_id": employer_id,
        "entity_sequence": 1,
        "prior_record_version": 0,
        "new_record_version": 1,
        "actor_type": "staff",
        "actor_id": principal.actor_id,
        "command_id": command_id,
        "correlation_id": command_id,
        "source_type": "staff_api",
        "payload_classification": "sensitive_operational",
    }


def test_existing_create_command_populates_revision_compatible_attribution_and_receipt(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("26262626-2626-4262-8262-262626262626"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("27272727-2727-4272-8272-272727272727")
    employer_id = UUID("28282828-2828-4282-8282-282828282828")
    audit_event_id = UUID("29292929-2929-4292-8292-292929292929")
    fixed_now = datetime(2026, 8, 10, 19, 35, 0, tzinfo=UTC)

    result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="business",
        display_name="Synthetic Revision Compatible Employer",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    employer = (
        session.execute(
            text(
                """
            SELECT employer_id, created_at, created_by, updated_at, updated_by, version
            FROM employers
            WHERE employer_id = :employer_id
            """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    command_receipt = (
        session.execute(
            text(
                """
            SELECT command_id, actor_id, result_entity_id, result_record_version, result_event_type
            FROM command_receipts
            WHERE command_id = :command_id
            """
            ),
            {"command_id": command_id},
        )
        .mappings()
        .one()
    )

    assert result.replayed is False
    assert dict(employer) == {
        "employer_id": employer_id,
        "created_at": fixed_now,
        "created_by": principal.actor_id,
        "updated_at": fixed_now,
        "updated_by": principal.actor_id,
        "version": 1,
    }
    assert dict(command_receipt) == {
        "command_id": command_id,
        "actor_id": principal.actor_id,
        "result_entity_id": employer_id,
        "result_record_version": 1,
        "result_event_type": "employer.created",
    }


def test_receipt_replay_rejects_changed_command_type_actor_target_or_payload(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("30303030-3030-4030-8030-303030303030"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("31313131-3131-4131-8131-313131313131")
    fixed_now = datetime(2026, 8, 10, 20, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO employers (
                employer_id,
                employer_type,
                display_name,
                lifecycle_status,
                source_channel,
                received_at,
                created_at,
                created_by,
                updated_at,
                updated_by,
                version
            ) VALUES (
                :employer_id,
                'household',
                'Synthetic Seed Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :created_at,
                :created_by,
                1
            )
            """
        ),
        {
            "employer_id": UUID("33333333-3333-4333-8333-333333333333"),
            "created_at": fixed_now,
            "created_by": UUID("36363636-3636-4363-8363-363636363636"),
        },
    )

    session.execute(
        text(
            """
            INSERT INTO audit_events (
                audit_event_id,
                event_schema_name,
                event_schema_version,
                event_type,
                entity_type,
                entity_id,
                entity_sequence,
                prior_record_version,
                new_record_version,
                actor_type,
                actor_id,
                initiating_staff_actor_id,
                occurred_at,
                effective_at,
                command_id,
                correlation_id,
                reason_code,
                reason_text,
                source_type,
                source_reference,
                related_event_ids,
                changed_fields,
                payload_classification
            ) VALUES (
                :audit_event_id,
                'employer.created',
                1,
                'employer.created',
                'employer',
                :entity_id,
                1,
                0,
                1,
                'staff',
                :actor_id,
                NULL,
                :occurred_at,
                NULL,
                :command_id,
                :command_id,
                NULL,
                NULL,
                'staff_api',
                NULL,
                '[]'::jsonb,
                '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                'sensitive_operational'
            )
            """
        ),
        {
            "audit_event_id": UUID("37373737-3737-4373-8373-373737373737"),
            "entity_id": UUID("33333333-3333-4333-8333-333333333333"),
            "actor_id": UUID("32323232-3232-4232-8232-323232323232"),
            "occurred_at": fixed_now,
            "command_id": command_id,
        },
    )

    session.execute(
        text(
            """
            INSERT INTO command_receipts (
                command_id,
                command_schema_version,
                command_type,
                actor_id,
                request_fingerprint,
                result_entity_type,
                result_entity_id,
                result_record_version,
                result_event_type,
                created_at
            ) VALUES (
                :command_id,
                1,
                'create_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                1,
                'employer.created',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": UUID("32323232-3232-4232-8232-323232323232"),
            "request_fingerprint": hashlib.sha256(b"mismatched-payload").digest(),
            "result_entity_id": UUID("33333333-3333-4333-8333-333333333333"),
            "created_at": fixed_now,
        },
    )
    session.commit()

    with pytest.raises(IdempotencyConflictError) as conflict:
        create_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_type="household",
            display_name="Synthetic Authority Household",
            clock=FixedClock(fixed_now),
            identifiers=FixedIdentifierFactory(
                UUID("34343434-3434-4334-8334-343434343434"),
                UUID("35353535-3535-4353-8353-353535353535"),
            ),
        )

    assert str(conflict.value) == "idempotency conflict"


def test_replay_rejects_authority_state_where_current_version_precedes_receipt_result_version(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("38383838-3838-4838-8838-383838383838"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("39393939-3939-4939-8939-393939393939")
    employer_id = UUID("40404040-4040-4040-8040-404040404040")
    fixed_now = datetime(2026, 8, 10, 20, 10, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "create_draft_employer",
                "employer_type": "household",
                "display_name": "Synthetic Corrupted Replay Employer",
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).digest()

    session.execute(
        text(
            """
            INSERT INTO employers (
                employer_id,
                employer_type,
                display_name,
                lifecycle_status,
                source_channel,
                received_at,
                created_at,
                created_by,
                updated_at,
                updated_by,
                version
            ) VALUES (
                :employer_id,
                'household',
                'Synthetic Corrupted Replay Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :created_at,
                :created_by,
                1
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": fixed_now,
            "created_by": principal.actor_id,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO audit_events (
                audit_event_id,
                event_schema_name,
                event_schema_version,
                event_type,
                entity_type,
                entity_id,
                entity_sequence,
                prior_record_version,
                new_record_version,
                actor_type,
                actor_id,
                initiating_staff_actor_id,
                occurred_at,
                effective_at,
                command_id,
                correlation_id,
                reason_code,
                reason_text,
                source_type,
                source_reference,
                related_event_ids,
                changed_fields,
                payload_classification
            ) VALUES (
                :audit_event_id,
                'employer.created',
                1,
                'employer.created',
                'employer',
                :entity_id,
                2,
                1,
                2,
                'staff',
                :actor_id,
                NULL,
                :occurred_at,
                NULL,
                :command_id,
                :command_id,
                NULL,
                NULL,
                'staff_api',
                NULL,
                '[]'::jsonb,
                '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                'sensitive_operational'
            )
            """
        ),
        {
            "audit_event_id": UUID("41414141-4141-4141-8141-414141414141"),
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": fixed_now,
            "command_id": command_id,
        },
    )
    with pytest.raises(IntegrityError, match="ck_command_receipts_result_authority_shape"):
        session.execute(
            text(
                """
                INSERT INTO command_receipts (
                    command_id,
                    command_schema_version,
                    command_type,
                    actor_id,
                    request_fingerprint,
                    result_entity_type,
                    result_entity_id,
                    result_record_version,
                    result_event_type,
                    created_at
                ) VALUES (
                    :command_id,
                    1,
                    'create_draft_employer',
                    :actor_id,
                    :request_fingerprint,
                    'employer',
                    :result_entity_id,
                    2,
                    'employer.created',
                    :created_at
                )
                """
            ),
            {
                "command_id": command_id,
                "actor_id": principal.actor_id,
                "request_fingerprint": request_fingerprint,
                "result_entity_id": employer_id,
                "created_at": fixed_now,
            },
        )
    session.rollback()


def test_create_replay_rejects_inconsistent_result_version_event_type_or_target(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("44444444-4444-4444-8444-444444444444"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("45454545-4545-4545-8545-454545454545")
    employer_id = UUID("46464646-4646-4646-8646-464646464646")
    fixed_now = datetime(2026, 8, 10, 20, 20, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "create_draft_employer",
                "employer_type": "household",
                "display_name": "Synthetic Invalid Create Replay Metadata Employer",
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).digest()

    session.execute(
        text(
            """
            INSERT INTO employers (
                employer_id,
                employer_type,
                display_name,
                lifecycle_status,
                source_channel,
                received_at,
                created_at,
                created_by,
                updated_at,
                updated_by,
                version
            ) VALUES (
                :employer_id,
                'household',
                'Synthetic Invalid Create Replay Metadata Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :created_at,
                :created_by,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": fixed_now,
            "created_by": principal.actor_id,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO audit_events (
                audit_event_id,
                event_schema_name,
                event_schema_version,
                event_type,
                entity_type,
                entity_id,
                entity_sequence,
                prior_record_version,
                new_record_version,
                actor_type,
                actor_id,
                initiating_staff_actor_id,
                occurred_at,
                effective_at,
                command_id,
                correlation_id,
                reason_code,
                reason_text,
                source_type,
                source_reference,
                related_event_ids,
                changed_fields,
                payload_classification
            ) VALUES (
                :audit_event_id,
                'employer.created',
                1,
                'employer.created',
                'employer',
                :entity_id,
                2,
                1,
                2,
                'staff',
                :actor_id,
                NULL,
                :occurred_at,
                NULL,
                :command_id,
                :command_id,
                NULL,
                NULL,
                'staff_api',
                NULL,
                '[]'::jsonb,
                '{"field_names": ["employer_type", "display_name"]}'::jsonb,
                'sensitive_operational'
            )
            """
        ),
        {
            "audit_event_id": UUID("47474747-4747-4747-8747-474747474747"),
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": fixed_now,
            "command_id": command_id,
        },
    )
    with pytest.raises(IntegrityError, match="ck_command_receipts_result_authority_shape"):
        session.execute(
            text(
                """
                INSERT INTO command_receipts (
                    command_id,
                    command_schema_version,
                    command_type,
                    actor_id,
                    request_fingerprint,
                    result_entity_type,
                    result_entity_id,
                    result_record_version,
                    result_event_type,
                    created_at
                ) VALUES (
                    :command_id,
                    1,
                    'create_draft_employer',
                    :actor_id,
                    :request_fingerprint,
                    'employer',
                    :result_entity_id,
                    2,
                    'employer.created',
                    :created_at
                )
                """
            ),
            {
                "command_id": command_id,
                "actor_id": principal.actor_id,
                "request_fingerprint": request_fingerprint,
                "result_entity_id": employer_id,
                "created_at": fixed_now,
            },
        )
    session.rollback()


def test_create_draft_employer_audit_event_changed_fields_omits_display_name_value(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("22222222-2222-4222-8222-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("55555555-5555-4555-8555-555555555555")
    employer_id = UUID("66666666-6666-4666-8666-666666666666")
    audit_event_id = UUID("77777777-7777-4777-8777-777777777777")

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="business",
        display_name="Synthetic Business 001",
        clock=FixedClock(datetime(2026, 8, 4, 23, 35, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    changed_fields = session.execute(
        text("SELECT changed_fields FROM audit_events WHERE audit_event_id = :audit_event_id"),
        {"audit_event_id": audit_event_id},
    ).scalar_one()

    assert changed_fields == {
        "field_names": [
            "employer_type",
            "display_name",
            "lifecycle_status",
            "source_channel",
        ],
        "approved_values": {
            "employer_type": "business",
            "lifecycle_status": "draft",
            "source_channel": "staff_entry",
        },
    }
    assert "display_name" not in changed_fields["approved_values"]
    assert "Synthetic Business 001" not in repr(changed_fields)
    assert "request_body" not in changed_fields
    assert "row_snapshot" not in changed_fields


def test_create_draft_employer_rolls_back_when_late_write_fails(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("22222222-2222-4222-8222-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )

    def fail_audit_event_insert(**_: object) -> None:
        raise RuntimeError("synthetic late failure")

    monkeypatch.setattr(
        "golden_rose.application.create_draft_employer.insert_employer_created_event",
        fail_audit_event_insert,
    )

    with pytest.raises(RuntimeError, match="synthetic late failure"):
        create_draft_employer(
            session=session,
            principal=principal,
            command_id=UUID("88888888-8888-4888-8888-888888888888"),
            employer_type="household",
            display_name="Synthetic Household 002",
            clock=FixedClock(datetime(2026, 8, 4, 23, 40, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("99999999-9999-4999-8999-999999999999"),
                UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            ),
        )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert employer_count == 0
    assert command_receipt_count == 0
    assert audit_event_count == 0


def test_create_draft_employer_rolls_back_and_redacts_audit_id_collision_failure(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("22222222-2222-4222-8222-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    colliding_audit_event_id = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        employer_type="household",
        display_name="Synthetic Household Seed",
        clock=FixedClock(datetime(2026, 8, 4, 23, 45, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            colliding_audit_event_id,
        ),
    )

    with pytest.raises(SafePersistenceError) as exc_info:
        create_draft_employer(
            session=session,
            principal=principal,
            command_id=UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
            employer_type="business",
            display_name="Synthetic Business Collision",
            clock=FixedClock(datetime(2026, 8, 4, 23, 46, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),
                colliding_audit_event_id,
            ),
        )

    message = str(exc_info.value)
    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1
    assert message == "persistence operation failed"
    assert "Synthetic Business Collision" not in message
    assert "INSERT INTO" not in message
    assert "postgresql+psycopg://" not in message
    assert "psycopg" not in message


def test_create_draft_employer_identical_replay_returns_original_result_without_duplicates(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("22222222-2222-4222-8222-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("12121212-1212-4212-8212-121212121212")
    employer_id = UUID("13131313-1313-4313-8313-131313131313")
    audit_event_id = UUID("14141414-1414-4414-8414-141414141414")
    fixed_now = datetime(2026, 8, 4, 23, 47, 0, tzinfo=UTC)

    first_result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Replay Household",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )
    second_result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Replay Household",
        clock=FixedClock(datetime(2026, 8, 4, 23, 48, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("15151515-1515-4515-8515-151515151515"),
            UUID("16161616-1616-4616-8616-161616161616"),
        ),
    )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert first_result.replayed is False
    assert second_result.replayed is True
    assert second_result.employer == first_result.employer
    assert second_result.employer.employer_id == employer_id
    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_create_replay_after_later_revision_returns_current_truth_with_original_result_version(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("61616161-aaaa-4aaa-8aaa-616161616161"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create", "employer:draft:revise"}),
    )
    command_id = UUID("62626262-bbbb-4bbb-8bbb-626262626262")
    employer_id = UUID("63636363-cccc-4ccc-8ccc-636363636363")
    audit_event_id = UUID("64646464-dddd-4ddd-8ddd-646464646464")
    created_at = datetime(2026, 8, 11, 0, 15, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 11, 0, 16, 0, tzinfo=UTC)

    first_result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Later Revision Employer",
        clock=FixedClock(created_at),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )
    revise_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("65656565-eeee-4eee-8eee-656565656565"),
        employer_id=employer_id,
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Later Revision Employer Updated",
        clock=FixedClock(revised_at),
    )
    command_receipt_count_before_replay = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count_before_replay = session.execute(
        text("SELECT COUNT(*) FROM audit_events")
    ).scalar_one()
    second_result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Later Revision Employer",
        clock=FixedClock(datetime(2026, 8, 11, 0, 17, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("66666666-ffff-4fff-8fff-666666666666"),
            UUID("67676767-abab-4bab-8bab-676767676767"),
        ),
    )

    command_receipt = (
        session.execute(
            text(
                """
                SELECT result_record_version
                FROM command_receipts
                WHERE command_id = :command_id
                """
            ),
            {"command_id": command_id},
        )
        .mappings()
        .one()
    )
    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert first_result.replayed is False
    assert first_result.employer.version == 1
    assert second_result.replayed is True
    assert second_result.employer.employer_id == employer_id
    assert second_result.employer.employer_type == "business"
    assert second_result.employer.display_name == "Synthetic Later Revision Employer Updated"
    assert second_result.employer.version == 2
    assert dict(command_receipt) == {"result_record_version": 1}
    assert employer_count == 1
    assert command_receipt_count_before_replay == 2
    assert audit_event_count_before_replay == 2
    assert command_receipt_count == command_receipt_count_before_replay
    assert audit_event_count == audit_event_count_before_replay


def test_create_normalizes_display_name_before_fingerprint_and_insert(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("abababab-abab-4bab-8bab-abababababab"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("bcbcbcbc-bcbc-4cbc-8cbc-bcbcbcbcbcbc")
    employer_id = UUID("cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd")
    audit_event_id = UUID("dededede-dede-4ede-8ede-dededededede")

    result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="business",
        display_name="Cafe\u0301 Rose",
        clock=FixedClock(datetime(2026, 8, 6, 0, 5, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    stored_display_name = session.execute(
        text("SELECT display_name FROM employers WHERE employer_id = :employer_id"),
        {"employer_id": employer_id},
    ).scalar_one()

    assert result.employer.display_name == "Café Rose"
    assert stored_display_name == "Café Rose"


def test_replay_treats_composed_and_decomposed_names_as_same_payload(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("efefefef-efef-4fef-8fef-efefefefefef"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("f0f0f0f0-f0f0-40f0-80f0-f0f0f0f0f0f0")
    employer_id = UUID("f1f1f1f1-f1f1-41f1-81f1-f1f1f1f1f1f1")
    audit_event_id = UUID("f2f2f2f2-f2f2-42f2-82f2-f2f2f2f2f2f2")
    fixed_now = datetime(2026, 8, 6, 0, 10, 0, tzinfo=UTC)

    first_result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="business",
        display_name="Cafe\u0301 Rose",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )
    second_result = create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="business",
        display_name="Café Rose",
        clock=FixedClock(datetime(2026, 8, 6, 0, 11, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("f3f3f3f3-f3f3-43f3-83f3-f3f3f3f3f3f3"),
            UUID("f4f4f4f4-f4f4-44f4-84f4-f4f4f4f4f4f4"),
        ),
    )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()

    assert first_result.replayed is False
    assert second_result.replayed is True
    assert second_result.employer == first_result.employer
    assert second_result.employer.display_name == "Café Rose"
    assert employer_count == 1


def test_create_draft_employer_conflicting_replay_raises_without_disclosing_resource(
    session,
    clean_tables,
) -> None:
    original_principal = StaffPrincipal(
        actor_id=UUID("22222222-2222-4222-8222-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    conflicting_principal = StaffPrincipal(
        actor_id=UUID("23232323-2323-4232-8232-232323232323"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    command_id = UUID("17171717-1717-4717-8717-171717171717")
    employer_id = UUID("18181818-1818-4818-8818-181818181818")
    audit_event_id = UUID("19191919-1919-4919-8919-191919191919")

    original_result = create_draft_employer(
        session=session,
        principal=original_principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Original Employer",
        clock=FixedClock(datetime(2026, 8, 4, 23, 49, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    with pytest.raises(IdempotencyConflictError) as changed_field_conflict:
        create_draft_employer(
            session=session,
            principal=original_principal,
            command_id=command_id,
            employer_type="business",
            display_name="Synthetic Original Employer",
            clock=FixedClock(datetime(2026, 8, 4, 23, 50, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("20202020-2020-4020-8020-202020202020"),
                UUID("21212121-2121-4121-8121-212121212121"),
            ),
        )

    with pytest.raises(IdempotencyConflictError) as changed_actor_conflict:
        create_draft_employer(
            session=session,
            principal=conflicting_principal,
            command_id=command_id,
            employer_type="household",
            display_name="Synthetic Original Employer",
            clock=FixedClock(datetime(2026, 8, 4, 23, 51, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("24242424-2424-4242-8242-242424242424"),
                UUID("25252525-2525-4252-8252-252525252525"),
            ),
        )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert str(changed_field_conflict.value) == "idempotency conflict"
    assert str(changed_actor_conflict.value) == "idempotency conflict"
    assert str(original_result.employer.employer_id) not in str(changed_field_conflict.value)
    assert "Synthetic Original Employer" not in str(changed_field_conflict.value)
    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_create_draft_employer_concurrent_identical_commands_return_one_authoritative_result(
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("26262626-2626-4262-8262-262626262626"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    barrier = threading.Barrier(2)
    command_id = UUID("27272727-2727-4272-8272-272727272727")

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            _run_create_draft_employer_in_isolated_session,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_type="household",
            display_name="Synthetic Concurrent Household",
            now=datetime(2026, 8, 4, 23, 52, 0, tzinfo=UTC),
            identifiers=FixedIdentifierFactory(
                UUID("28282828-2828-4282-8282-282828282828"),
                UUID("29292929-2929-4292-8292-292929292929"),
            ),
        )
        future_two = executor.submit(
            _run_create_draft_employer_in_isolated_session,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_type="household",
            display_name="Synthetic Concurrent Household",
            now=datetime(2026, 8, 4, 23, 52, 1, tzinfo=UTC),
            identifiers=FixedIdentifierFactory(
                UUID("30303030-3030-4030-8030-303030303030"),
                UUID("31313131-3131-4131-8131-313131313131"),
            ),
        )

    result_one = future_one.result()
    result_two = future_two.result()
    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert sorted([result_one.replayed, result_two.replayed]) == [False, True]
    assert result_one.employer == result_two.employer
    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_create_draft_employer_concurrent_conflicting_commands_yield_one_conflict(
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("32323232-3232-4232-8232-323232323232"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    barrier = threading.Barrier(2)
    command_id = UUID("33333333-3333-4333-8333-333333333334")

    def run_and_capture(**kwargs):
        try:
            return _run_create_draft_employer_in_isolated_session(**kwargs)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_type="household",
            display_name="Synthetic Conflict Household",
            now=datetime(2026, 8, 4, 23, 53, 0, tzinfo=UTC),
            identifiers=FixedIdentifierFactory(
                UUID("34343434-3434-4334-8334-343434343434"),
                UUID("35353535-3535-4353-8353-353535353535"),
            ),
        )
        future_two = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_type="business",
            display_name="Synthetic Conflict Household",
            now=datetime(2026, 8, 4, 23, 53, 1, tzinfo=UTC),
            identifiers=FixedIdentifierFactory(
                UUID("36363636-3636-4363-8363-363636363636"),
                UUID("37373737-3737-4373-8373-373737373737"),
            ),
        )

    result_one = future_one.result()
    result_two = future_two.result()
    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    successes = [result for result in (result_one, result_two) if not isinstance(result, Exception)]
    failures = [result for result in (result_one, result_two) if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], IdempotencyConflictError)
    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_safe_persistence_error_redacts_driver_details_for_db_failures(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("38383838-3838-4383-8383-383838383838"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("39393939-3939-4393-8393-393939393939"),
        employer_type="household",
        display_name="Synthetic Driver Seed",
        clock=FixedClock(datetime(2026, 8, 4, 23, 54, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("40404040-4040-4040-8040-404040404040"),
            UUID("41414141-4141-4141-8141-414141414141"),
        ),
    )

    with pytest.raises(SafePersistenceError) as exc_info:
        create_draft_employer(
            session=session,
            principal=principal,
            command_id=UUID("42424242-4242-4242-8242-424242424242"),
            employer_type="business",
            display_name="Synthetic Driver Collision",
            clock=FixedClock(datetime(2026, 8, 4, 23, 55, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("43434343-4343-4343-8343-434343434343"),
                UUID("41414141-4141-4141-8141-414141414141"),
            ),
        )

    message = str(exc_info.value)
    assert message == "persistence operation failed"
    assert "psycopg" not in message
    assert "UniqueViolation" not in message
    assert "Synthetic Driver Collision" not in message
    assert "postgresql+psycopg://" not in message
