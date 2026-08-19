import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import golden_rose.application.query_employer_contacts as query_employer_contacts_module
from golden_rose.application.contact_cursor import ContactCursor, encode_contact_cursor
from golden_rose.application.create_draft_employer import IdempotencyConflictError
from golden_rose.application.create_employer_contact import create_employer_contact
from golden_rose.application.errors import EmployerNotFoundError, SafePersistenceError
from golden_rose.application.get_employer_contact import get_employer_contact
from golden_rose.application.query_employer_contacts import query_employer_contacts
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.employer_contacts import (
    build_create_employer_contact_request_fingerprint,
)
from tests.integration.application.test_create_draft_employer import (
    FixedClock,
    FixedIdentifierFactory,
)
from tests.integration.conftest import PROJECT_ROOT


def _run_create_employer_contact_in_isolated_session(
    *,
    engine,
    barrier: threading.Barrier,
    principal: StaffPrincipal,
    employer_id: UUID,
    command_id: UUID,
    full_name: str,
    now: datetime,
    identifiers: FixedIdentifierFactory,
):
    with Session(engine) as isolated_session:
        isolation_level = isolated_session.execute(text("SHOW transaction_isolation")).scalar_one()
        assert isolation_level == "read committed"
        barrier.wait()
        return create_employer_contact(
            session=isolated_session,
            principal=principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name=full_name,
            clock=FixedClock(now),
            identifiers=identifiers,
        )


def _run_create_employer_contact_and_capture(**kwargs):
    try:
        return _run_create_employer_contact_in_isolated_session(**kwargs)
    except Exception as exc:
        return exc


def test_create_employer_contact_creates_authority_contact_receipt_and_event_atomically(
    session,
    clean_tables,
) -> None:
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("path_separator", "os")
    command.upgrade(alembic_config, "head")

    inspector = inspect(session.connection())
    assert "entity_authorities" in inspector.get_table_names()
    assert "employer_contacts" in inspector.get_table_names()

    principal = StaffPrincipal(
        actor_id=UUID("61616161-6161-4616-8616-616161616161"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("62626262-6262-4626-8626-626262626262")
    command_id = UUID("63636363-6363-4636-8636-636363636363")
    employer_contact_id = UUID("64646464-6464-4646-8646-646464646464")
    audit_event_id = UUID("65656565-6565-4656-8656-656565656565")
    fixed_now = datetime(2026, 8, 12, 22, 0, 0, tzinfo=UTC)

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
                'business',
                'Synthetic Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    result = create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=command_id,
        full_name="  Cafe\u0301 Contact  ",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_contact_id, audit_event_id),
    )

    contact = (
        session.execute(
            text(
                """
                SELECT employer_contact_id, employer_id, full_name, created_by, updated_by, version
                FROM employer_contacts
                WHERE employer_contact_id = :employer_contact_id
                """
            ),
            {"employer_contact_id": employer_contact_id},
        )
        .mappings()
        .one()
    )
    authority = (
        session.execute(
            text(
                """
                SELECT entity_type, entity_id, employer_id, employer_contact_id
                FROM entity_authorities
                WHERE entity_type = 'employer_contact'
                  AND entity_id = :employer_contact_id
                """
            ),
            {"employer_contact_id": employer_contact_id},
        )
        .mappings()
        .one()
    )
    receipt = (
        session.execute(
            text(
                """
                SELECT
                    command_id,
                    actor_id,
                    result_entity_type,
                    result_entity_id,
                    result_record_version,
                    result_event_type
                FROM command_receipts
                WHERE command_id = :command_id
                """
            ),
            {"command_id": command_id},
        )
        .mappings()
        .one()
    )
    audit_event = (
        session.execute(
            text(
                """
                SELECT audit_event_id, event_schema_name, event_type, entity_type, entity_id,
                       new_record_version, actor_id, command_id, correlation_id, source_type,
                       payload_classification
                FROM audit_events
                WHERE audit_event_id = :audit_event_id
                """
            ),
            {"audit_event_id": audit_event_id},
        )
        .mappings()
        .one()
    )

    assert result.employer_contact_id == employer_contact_id
    assert result.replayed is False
    assert result.full_name == "Café Contact"
    assert dict(contact) == {
        "employer_contact_id": employer_contact_id,
        "employer_id": employer_id,
        "full_name": "Café Contact",
        "created_by": principal.actor_id,
        "updated_by": principal.actor_id,
        "version": 1,
    }
    assert dict(authority) == {
        "entity_type": "employer_contact",
        "entity_id": employer_contact_id,
        "employer_id": None,
        "employer_contact_id": employer_contact_id,
    }
    assert dict(receipt) == {
        "command_id": command_id,
        "actor_id": principal.actor_id,
        "result_entity_type": "employer_contact",
        "result_entity_id": employer_contact_id,
        "result_record_version": 1,
        "result_event_type": "employer_contact.created",
    }
    assert dict(audit_event) == {
        "audit_event_id": audit_event_id,
        "event_schema_name": "employer_contact.created",
        "event_type": "employer_contact.created",
        "entity_type": "employer_contact",
        "entity_id": employer_contact_id,
        "new_record_version": 1,
        "actor_id": principal.actor_id,
        "command_id": command_id,
        "correlation_id": command_id,
        "source_type": "staff_api",
        "payload_classification": "sensitive_operational",
    }

    changed_fields = session.execute(
        text("SELECT changed_fields FROM audit_events WHERE audit_event_id = :audit_event_id"),
        {"audit_event_id": audit_event_id},
    ).scalar_one()
    assert changed_fields == {
        "field_names": ["full_name"],
        "approved_values": {},
    }
    assert "full_name" not in changed_fields["approved_values"]
    assert "Café Contact" not in repr(changed_fields)
    assert "request_body" not in changed_fields
    assert "row_snapshot" not in changed_fields


def test_create_employer_contact_denial_precedes_parent_receipt_and_writes(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("66666666-6666-4666-8666-666666666666"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read"}),
    )
    employer_id = UUID("67676767-6767-4676-8676-676767676767")
    command_id = UUID("68686868-6868-4686-8686-686868686868")
    fixed_now = datetime(2026, 8, 12, 22, 5, 0, tzinfo=UTC)

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
                'business',
                'Denied Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    with pytest.raises(PermissionError, match="principal lacks employer_contact:draft:create"):
        create_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name="Denied Contact",
            clock=FixedClock(fixed_now),
            identifiers=FixedIdentifierFactory(
                UUID("69696969-6969-4696-8696-696969696969"),
                UUID("70707070-7070-4707-8707-707070707070"),
            ),
        )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Denied Parent Employer",
        "updated_by": principal.actor_id,
        "version": 1,
    }
    assert employer_contact_count == 0
    assert employer_contact_authority_count == 0
    assert receipt_count == 0
    assert audit_event_count == 0


def test_create_employer_contact_requires_existing_draft_parent_without_receipt(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("71717171-7171-4717-8717-717171717171"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    missing_employer_id = UUID("72727272-7272-4727-8727-727272727272")
    command_id = UUID("73737373-7373-4737-8737-737373737373")
    fixed_now = datetime(2026, 8, 12, 22, 10, 0, tzinfo=UTC)

    with pytest.raises(EmployerNotFoundError, match="employer not found"):
        create_employer_contact(
            session=session,
            principal=principal,
            employer_id=missing_employer_id,
            command_id=command_id,
            full_name="Missing Parent Contact",
            clock=FixedClock(fixed_now),
            identifiers=FixedIdentifierFactory(
                UUID("74747474-7474-4747-8747-747474747474"),
                UUID("75757575-7575-4757-8757-757575757575"),
            ),
        )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert employer_count == 0
    assert employer_contact_count == 0
    assert employer_contact_authority_count == 0
    assert receipt_count == 0
    assert audit_event_count == 0


def test_create_employer_contact_normalizes_before_fingerprint_and_storage(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("76767676-7676-4767-8767-767676767676"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("77777777-7777-4777-8777-777777777777")
    command_id = UUID("78787878-7878-4787-8787-787878787878")
    employer_contact_id = UUID("79797979-7979-4797-8797-797979797979")
    audit_event_id = UUID("80808080-8080-4808-8808-808080808080")
    fixed_now = datetime(2026, 8, 12, 22, 15, 0, tzinfo=UTC)
    raw_full_name = "  Cafe\u0301 Contact  "
    normalized_full_name = "Café Contact"

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
                'business',
                'Normalized Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    first_result = create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=command_id,
        full_name=raw_full_name,
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_contact_id, audit_event_id),
    )

    second_result = create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=command_id,
        full_name=normalized_full_name,
        clock=FixedClock(datetime(2026, 8, 12, 22, 16, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("81818181-8181-4818-8818-818181818181"),
            UUID("82828282-8282-4828-8828-828282828282"),
        ),
    )

    contact = (
        session.execute(
            text(
                """
                SELECT employer_contact_id, full_name
                FROM employer_contacts
                WHERE employer_contact_id = :employer_contact_id
                """
            ),
            {"employer_contact_id": employer_contact_id},
        )
        .mappings()
        .one()
    )
    receipt = (
        session.execute(
            text(
                """
                SELECT request_fingerprint, result_entity_id
                FROM command_receipts
                WHERE command_id = :command_id
                """
            ),
            {"command_id": command_id},
        )
        .mappings()
        .one()
    )
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert first_result.replayed is False
    assert second_result.replayed is True
    assert second_result.employer_contact_id == employer_contact_id
    assert second_result.full_name == normalized_full_name
    assert dict(contact) == {
        "employer_contact_id": employer_contact_id,
        "full_name": normalized_full_name,
    }
    assert receipt["request_fingerprint"] == build_create_employer_contact_request_fingerprint(
        employer_id=employer_id,
        full_name=normalized_full_name,
    )
    assert receipt["request_fingerprint"] != build_create_employer_contact_request_fingerprint(
        employer_id=employer_id,
        full_name=raw_full_name,
    )
    assert receipt["result_entity_id"] == employer_contact_id
    assert employer_contact_count == 1
    assert employer_contact_authority_count == 1
    assert receipt_count == 1
    assert audit_event_count == 1


def test_create_employer_contact_identical_replay_returns_current_contact_without_writes(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("83838383-8383-4838-8838-838383838383"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("84848484-8484-4848-8848-848484848484")
    command_id = UUID("85858585-8585-4858-8858-858585858585")
    employer_contact_id = UUID("86868686-8686-4868-8868-868686868686")
    audit_event_id = UUID("87878787-8787-4878-8878-878787878787")
    fixed_now = datetime(2026, 8, 12, 22, 20, 0, tzinfo=UTC)

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
                'business',
                'Replay Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    first_result = create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=command_id,
        full_name="Replay Contact",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_contact_id, audit_event_id),
    )

    counts_before_replay = session.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM employer_contacts) AS employer_contact_count,
                (
                    SELECT COUNT(*)
                    FROM entity_authorities
                    WHERE entity_type = 'employer_contact'
                ) AS employer_contact_authority_count,
                (SELECT COUNT(*) FROM command_receipts) AS receipt_count,
                (SELECT COUNT(*) FROM audit_events) AS audit_event_count
            """
        )
    ).one()

    second_result = create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=command_id,
        full_name="Replay Contact",
        clock=FixedClock(datetime(2026, 8, 12, 22, 21, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(
            UUID("88888888-8888-4888-8888-888888888888"),
            UUID("89898989-8989-4898-8898-898989898989"),
        ),
    )

    counts_after_replay = session.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM employer_contacts) AS employer_contact_count,
                (
                    SELECT COUNT(*)
                    FROM entity_authorities
                    WHERE entity_type = 'employer_contact'
                ) AS employer_contact_authority_count,
                (SELECT COUNT(*) FROM command_receipts) AS receipt_count,
                (SELECT COUNT(*) FROM audit_events) AS audit_event_count
            """
        )
    ).one()
    contact = (
        session.execute(
            text(
                """
                SELECT employer_contact_id, full_name, version
                FROM employer_contacts
                WHERE employer_contact_id = :employer_contact_id
                """
            ),
            {"employer_contact_id": employer_contact_id},
        )
        .mappings()
        .one()
    )

    assert first_result.replayed is False
    assert first_result.employer_contact_id == employer_contact_id
    assert first_result.result_record_version == 1
    assert second_result.replayed is True
    assert second_result.employer_contact_id == employer_contact_id
    assert second_result.full_name == "Replay Contact"
    assert second_result.result_record_version == 1
    assert dict(contact) == {
        "employer_contact_id": employer_contact_id,
        "full_name": "Replay Contact",
        "version": 1,
    }
    assert counts_before_replay == counts_after_replay


def test_create_employer_contact_rejects_changed_actor_parent_type_schema_or_payload_without_disclosure(  # noqa: E501
    session,
    clean_tables,
) -> None:
    original_principal = StaffPrincipal(
        actor_id=UUID("90909090-9090-4909-8909-909090909090"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    conflicting_principal = StaffPrincipal(
        actor_id=UUID("91919191-9191-4919-8919-919191919191"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    original_employer_id = UUID("92929292-9292-4929-8929-929292929292")
    conflicting_employer_id = UUID("93939393-9393-4939-8939-939393939393")
    command_id = UUID("94949494-9494-4949-8949-949494949494")
    employer_contact_id = UUID("95959595-9595-4959-8959-959595959595")
    audit_event_id = UUID("96969696-9696-4969-8969-969696969696")
    fixed_now = datetime(2026, 8, 12, 22, 25, 0, tzinfo=UTC)

    for employer_id, display_name in (
        (original_employer_id, "Original Replay Parent"),
        (conflicting_employer_id, "Conflicting Replay Parent"),
    ):
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
                    'business',
                    :display_name,
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
                "display_name": display_name,
                "created_at": fixed_now,
                "created_by": original_principal.actor_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO entity_authorities (
                    entity_type,
                    entity_id,
                    employer_id,
                    employer_contact_id
                ) VALUES (
                    'employer',
                    :employer_id,
                    :employer_id,
                    NULL
                )
                """
            ),
            {"employer_id": employer_id},
        )
    session.commit()

    original_result = create_employer_contact(
        session=session,
        principal=original_principal,
        employer_id=original_employer_id,
        command_id=command_id,
        full_name="Synthetic Original Contact",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_contact_id, audit_event_id),
    )

    with pytest.raises(IdempotencyConflictError) as changed_payload_conflict:
        create_employer_contact(
            session=session,
            principal=original_principal,
            employer_id=original_employer_id,
            command_id=command_id,
            full_name="Synthetic Changed Contact",
            clock=FixedClock(datetime(2026, 8, 12, 22, 26, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("97979797-9797-4979-8979-979797979797"),
                UUID("98989898-9898-4989-8989-989898989898"),
            ),
        )

    with pytest.raises(IdempotencyConflictError) as changed_actor_conflict:
        create_employer_contact(
            session=session,
            principal=conflicting_principal,
            employer_id=original_employer_id,
            command_id=command_id,
            full_name="Synthetic Original Contact",
            clock=FixedClock(datetime(2026, 8, 12, 22, 27, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("99999999-9999-4999-8999-999999999999"),
                UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            ),
        )

    with pytest.raises(IdempotencyConflictError) as changed_parent_conflict:
        create_employer_contact(
            session=session,
            principal=original_principal,
            employer_id=conflicting_employer_id,
            command_id=command_id,
            full_name="Synthetic Original Contact",
            clock=FixedClock(datetime(2026, 8, 12, 22, 28, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("abababab-abab-4bab-8bab-abababababab"),
                UUID("acacacac-acac-4cac-8cac-acacacacacac"),
            ),
        )

    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert str(changed_payload_conflict.value) == "idempotency conflict"
    assert str(changed_actor_conflict.value) == "idempotency conflict"
    assert str(changed_parent_conflict.value) == "idempotency conflict"
    assert str(original_result.employer_contact_id) not in str(changed_payload_conflict.value)
    assert "Synthetic Original Contact" not in str(changed_payload_conflict.value)
    assert employer_contact_count == 1
    assert employer_contact_authority_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_create_employer_contact_concurrent_identical_same_key_has_one_fresh_and_one_replay_at_read_committed(  # noqa: E501
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("adadadad-adad-4dad-8dad-adadadadadad"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("aeaeaeae-aeae-4eae-8eae-aeaeaeaeaeae")
    command_id = UUID("afafafaf-afaf-4faf-8faf-afafafafafaf")
    barrier = threading.Barrier(2)
    fixed_now = datetime(2026, 8, 12, 22, 30, 0, tzinfo=UTC)

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
                'business',
                'Concurrent Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            _run_create_employer_contact_in_isolated_session,
            engine=engine,
            barrier=barrier,
            principal=principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name="Synthetic Concurrent Contact",
            now=fixed_now,
            identifiers=FixedIdentifierFactory(
                UUID("b0b0b0b0-b0b0-40b0-80b0-b0b0b0b0b0b0"),
                UUID("b1b1b1b1-b1b1-41b1-81b1-b1b1b1b1b1b1"),
            ),
        )
        future_two = executor.submit(
            _run_create_employer_contact_in_isolated_session,
            engine=engine,
            barrier=barrier,
            principal=principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name="Synthetic Concurrent Contact",
            now=datetime(2026, 8, 12, 22, 30, 1, tzinfo=UTC),
            identifiers=FixedIdentifierFactory(
                UUID("b2b2b2b2-b2b2-42b2-82b2-b2b2b2b2b2b2"),
                UUID("b3b3b3b3-b3b3-43b3-83b3-b3b3b3b3b3b3"),
            ),
        )

    result_one = future_one.result()
    result_two = future_two.result()
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert sorted([result_one.replayed, result_two.replayed]) == [False, True]
    assert result_one.employer_contact_id == result_two.employer_contact_id
    assert result_one.full_name == result_two.full_name == "Synthetic Concurrent Contact"
    assert employer_contact_count == 1
    assert employer_contact_authority_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_create_employer_contact_concurrent_changed_authority_same_key_has_one_fresh_and_one_conflict_at_read_committed(  # noqa: E501
    engine,
    session,
    clean_tables,
) -> None:
    original_principal = StaffPrincipal(
        actor_id=UUID("b4b4b4b4-b4b4-44b4-84b4-b4b4b4b4b4b4"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    conflicting_principal = StaffPrincipal(
        actor_id=UUID("b5b5b5b5-b5b5-45b5-85b5-b5b5b5b5b5b5"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("b6b6b6b6-b6b6-46b6-86b6-b6b6b6b6b6b6")
    command_id = UUID("b7b7b7b7-b7b7-47b7-87b7-b7b7b7b7b7b7")
    barrier = threading.Barrier(2)
    fixed_now = datetime(2026, 8, 12, 22, 35, 0, tzinfo=UTC)

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
                'business',
                'Concurrent Conflict Parent',
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
            "created_by": original_principal.actor_id,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            _run_create_employer_contact_and_capture,
            engine=engine,
            barrier=barrier,
            principal=original_principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name="Synthetic Conflict Contact",
            now=fixed_now,
            identifiers=FixedIdentifierFactory(
                UUID("b8b8b8b8-b8b8-48b8-88b8-b8b8b8b8b8b8"),
                UUID("b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9"),
            ),
        )
        future_two = executor.submit(
            _run_create_employer_contact_and_capture,
            engine=engine,
            barrier=barrier,
            principal=conflicting_principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name="Synthetic Conflict Contact",
            now=datetime(2026, 8, 12, 22, 35, 1, tzinfo=UTC),
            identifiers=FixedIdentifierFactory(
                UUID("babababa-baba-4aba-8aba-babababababa"),
                UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            ),
        )

    result_one = future_one.result()
    result_two = future_two.result()
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    successes = [result for result in (result_one, result_two) if not isinstance(result, Exception)]
    failures = [result for result in (result_one, result_two) if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], IdempotencyConflictError)
    assert str(failures[0]) == "idempotency conflict"
    assert employer_contact_count == 1
    assert employer_contact_authority_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_create_employer_contact_late_failure_rolls_back_every_authority_row(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("bcbcbcbc-bcbc-4cbc-8cbc-bcbcbcbcbcbc"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("bdbdbdbd-bdbd-4dbd-8dbd-bdbdbdbdbdbd")
    command_id = UUID("bebebebe-bebe-4ebe-8ebe-bebebebebebe")
    fixed_now = datetime(2026, 8, 12, 22, 40, 0, tzinfo=UTC)

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
                'business',
                'Late Failure Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    def fail_late_audit_insert(**_kwargs):
        raise RuntimeError("synthetic late authority failure")

    monkeypatch.setattr(
        "golden_rose.application.create_employer_contact.insert_employer_contact_created_event",
        fail_late_audit_insert,
    )

    with pytest.raises(RuntimeError, match="synthetic late authority failure"):
        create_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name="Late Failure Contact",
            clock=FixedClock(fixed_now),
            identifiers=FixedIdentifierFactory(
                UUID("bfbfbfbf-bfbf-4fbf-8fbf-bfbfbfbfbfbf"),
                UUID("c0c0c0c0-c0c0-40c0-80c0-c0c0c0c0c0c0"),
            ),
        )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Late Failure Parent Employer",
        "updated_by": principal.actor_id,
        "version": 1,
    }
    assert employer_contact_count == 0
    assert employer_contact_authority_count == 0
    assert receipt_count == 0
    assert audit_event_count == 0


def test_create_employer_contact_safe_persistence_error_redacts_driver_and_submitted_values(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:draft:create"}),
    )
    employer_id = UUID("c2c2c2c2-c2c2-42c2-82c2-c2c2c2c2c2c2")
    fixed_now = datetime(2026, 8, 12, 22, 45, 0, tzinfo=UTC)

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
                'business',
                'Safe Error Parent Employer',
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
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    def raise_persistence_failure(**_kwargs):
        raise SQLAlchemyError(
            "psycopg UniqueViolation postgresql+psycopg:// Synthetic Driver Collision Contact"
        )

    monkeypatch.setattr(
        "golden_rose.application.create_employer_contact.reserve_create_employer_contact_receipt",
        raise_persistence_failure,
    )

    with pytest.raises(SafePersistenceError) as exc_info:
        create_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            command_id=UUID("c6c6c6c6-c6c6-46c6-86c6-c6c6c6c6c6c6"),
            full_name="Synthetic Driver Collision Contact",
            clock=FixedClock(datetime(2026, 8, 12, 22, 46, 0, tzinfo=UTC)),
            identifiers=FixedIdentifierFactory(
                UUID("c7c7c7c7-c7c7-47c7-87c7-c7c7c7c7c7c7"),
                UUID("c8c8c8c8-c8c8-48c8-88c8-c8c8c8c8c8c8"),
            ),
        )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    employer_contact_count = session.execute(
        text("SELECT COUNT(*) FROM employer_contacts")
    ).scalar_one()
    employer_contact_authority_count = session.execute(
        text("SELECT COUNT(*) FROM entity_authorities WHERE entity_type = 'employer_contact'")
    ).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    message = str(exc_info.value)
    assert message == "persistence operation failed"
    assert "psycopg" not in message
    assert "UniqueViolation" not in message
    assert "Synthetic Driver Collision Contact" not in message
    assert "postgresql+psycopg://" not in message
    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Safe Error Parent Employer",
        "updated_by": principal.actor_id,
        "version": 1,
    }
    assert employer_contact_count == 0
    assert employer_contact_authority_count == 0
    assert receipt_count == 0
    assert audit_event_count == 0


def test_query_employer_contacts_returns_bounded_parent_page_in_deterministic_order_without_count_or_writes(  # noqa: E501
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("f1f1f1f1-f1f1-41f1-81f1-f1f1f1f1f1f1"),
        role_name="operations_staff",
        permissions=frozenset(
            {"employer:read", "employer_contact:read", "employer_contact:draft:create"}
        ),
    )
    employer_id = UUID("f2f2f2f2-f2f2-42f2-82f2-f2f2f2f2f2f2")
    first_contact_id = UUID("f3f3f3f3-f3f3-43f3-83f3-f3f3f3f3f3f3")
    second_contact_id = UUID("f4f4f4f4-f4f4-44f4-84f4-f4f4f4f4f4f4")
    third_contact_id = UUID("f5f5f5f5-f5f5-45f5-85f5-f5f5f5f5f5f5")
    first_audit_event_id = UUID("f6f6f6f6-f6f6-46f6-86f6-f6f6f6f6f6f6")
    second_audit_event_id = UUID("f7f7f7f7-f7f7-47f7-87f7-f7f7f7f7f7f7")
    third_audit_event_id = UUID("f8f8f8f8-f8f8-48f8-88f8-f8f8f8f8f8f8")

    created_at_older = datetime(2026, 8, 12, 23, 10, 0, tzinfo=UTC)
    created_at_same = datetime(2026, 8, 12, 23, 11, 0, tzinfo=UTC)

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
                'business',
                'Query Parent Employer',
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
            "created_at": created_at_older,
            "created_by": principal.actor_id,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO entity_authorities (
                entity_type,
                entity_id,
                employer_id,
                employer_contact_id
            ) VALUES (
                'employer',
                :employer_id,
                :employer_id,
                NULL
            )
            """
        ),
        {"employer_id": employer_id},
    )
    session.commit()

    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=UUID("f9f9f9f9-f9f9-49f9-89f9-f9f9f9f9f9f9"),
        full_name="Older Contact",
        clock=FixedClock(created_at_older),
        identifiers=FixedIdentifierFactory(first_contact_id, first_audit_event_id),
    )
    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=UUID("fafafafa-fafa-4afa-8afa-fafafafafafa"),
        full_name="Same Time Contact A",
        clock=FixedClock(created_at_same),
        identifiers=FixedIdentifierFactory(second_contact_id, second_audit_event_id),
    )
    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=UUID("fbfbfbfb-fbfb-4bfb-8bfb-fbfbfbfbfbfb"),
        full_name="Same Time Contact B",
        clock=FixedClock(created_at_same),
        identifiers=FixedIdentifierFactory(third_contact_id, third_audit_event_id),
    )

    baseline_counts = {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    }

    def fail_commit() -> None:
        raise AssertionError("commit should not be called")

    def fail_flush(*args: object, **kwargs: object) -> None:
        raise AssertionError("flush should not be called")

    def fail_rollback() -> None:
        raise AssertionError("rollback should not be called")

    monkeypatch.setattr(session, "commit", fail_commit)
    monkeypatch.setattr(session, "flush", fail_flush)
    monkeypatch.setattr(session, "rollback", fail_rollback)

    cursor = encode_contact_cursor(
        ContactCursor(
            version=1,
            employer_id=employer_id,
            page_size=2,
            after_created_at=created_at_same,
            after_employer_contact_id=third_contact_id,
        )
    )

    page = query_employer_contacts(
        session=session,
        principal=principal,
        employer_id=employer_id,
        page_size=2,
        cursor=cursor,
    )

    assert [item.employer_contact_id for item in page.items] == [
        second_contact_id,
        first_contact_id,
    ]
    assert [item.full_name for item in page.items] == ["Same Time Contact A", "Older Contact"]
    assert all(item.employer_id == employer_id for item in page.items)
    assert all(item.version == 1 for item in page.items)
    assert page.next_cursor is None
    assert {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


def test_query_employer_contacts_denial_precedes_cursor_parent_and_contact_access(
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("fcfcfcfc-fcfc-4cfc-8cfc-fcfcfcfcfcfc"),
        role_name="operations_staff",
        permissions=frozenset(),
    )
    decode_calls = 0
    query_calls = 0

    def fail_decode(*args: object, **kwargs: object) -> None:
        nonlocal decode_calls
        decode_calls += 1
        raise AssertionError("cursor decode should not be called")

    monkeypatch.setattr(query_employer_contacts_module, "decode_contact_cursor", fail_decode)

    class DeniedSessionProbe:
        def execute(self, *args: object, **kwargs: object) -> None:
            nonlocal query_calls
            query_calls += 1
            raise AssertionError("query should not be called")

    with pytest.raises(PermissionError, match="principal lacks employer:read"):
        query_employer_contacts(
            session=cast(Session, DeniedSessionProbe()),
            principal=principal,
            employer_id=UUID("fdfdfdfd-fdfd-4dfd-8dfd-fdfdfdfdfdfd"),
            page_size=2,
            cursor="bad-cursor",
        )

    assert decode_calls == 0
    assert query_calls == 0


def test_query_employer_contacts_cursor_continues_without_duplicate_or_gap_and_is_parent_page_size_bound(  # noqa: E501
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("0a0a0a0a-0a0a-4a0a-8a0a-0a0a0a0a0a0a"),
        role_name="operations_staff",
        permissions=frozenset(
            {"employer:read", "employer_contact:read", "employer_contact:draft:create"}
        ),
    )
    employer_id = UUID("0b0b0b0b-0b0b-4b0b-8b0b-0b0b0b0b0b0b")
    other_employer_id = UUID("0c0c0c0c-0c0c-4c0c-8c0c-0c0c0c0c0c0c")
    contact_ids = [
        UUID("11111111-1111-4111-8111-111111111111"),
        UUID("22222222-2222-4222-8222-222222222222"),
        UUID("33333333-3333-4333-8333-333333333333"),
        UUID("44444444-4444-4444-8444-444444444444"),
    ]
    other_contact_id = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
    audit_event_ids = [
        UUID("12121212-1212-4212-8212-121212121212"),
        UUID("23232323-2323-4232-8232-232323232323"),
        UUID("34343434-3434-4343-8343-343434343434"),
        UUID("45454545-4545-4454-8454-454545454545"),
    ]
    other_audit_event_id = UUID("56565656-5656-4565-8565-565656565656")
    shared_created_at = datetime(2026, 8, 12, 23, 30, 0, tzinfo=UTC)

    for seeded_employer_id, display_name in (
        (employer_id, "Continuation Parent Employer"),
        (other_employer_id, "Other Parent Employer"),
    ):
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
                    'business',
                    :display_name,
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
                "employer_id": seeded_employer_id,
                "display_name": display_name,
                "created_at": shared_created_at,
                "created_by": principal.actor_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO entity_authorities (
                    entity_type,
                    entity_id,
                    employer_id,
                    employer_contact_id
                ) VALUES (
                    'employer',
                    :employer_id,
                    :employer_id,
                    NULL
                )
                """
            ),
            {"employer_id": seeded_employer_id},
        )
    session.commit()

    command_ids = [
        UUID("67676767-6767-4676-8676-676767676767"),
        UUID("78787878-7878-4787-8787-787878787878"),
        UUID("89898989-8989-4898-8898-898989898989"),
        UUID("9a9a9a9a-9a9a-49a9-89a9-9a9a9a9a9a9a"),
    ]
    names = ["Contact One", "Contact Two", "Contact Three", "Contact Four"]
    for command_id, contact_id, audit_event_id, full_name in zip(
        command_ids, contact_ids, audit_event_ids, names, strict=True
    ):
        create_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            command_id=command_id,
            full_name=full_name,
            clock=FixedClock(shared_created_at),
            identifiers=FixedIdentifierFactory(contact_id, audit_event_id),
        )

    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=other_employer_id,
        command_id=UUID("abababab-abab-4bab-8bab-abababababab"),
        full_name="Other Parent Contact",
        clock=FixedClock(shared_created_at),
        identifiers=FixedIdentifierFactory(other_contact_id, other_audit_event_id),
    )

    baseline_counts = {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    }

    def fail_commit() -> None:
        raise AssertionError("commit should not be called")

    def fail_flush(*args: object, **kwargs: object) -> None:
        raise AssertionError("flush should not be called")

    def fail_rollback() -> None:
        raise AssertionError("rollback should not be called")

    monkeypatch.setattr(session, "commit", fail_commit)
    monkeypatch.setattr(session, "flush", fail_flush)
    monkeypatch.setattr(session, "rollback", fail_rollback)

    first_page = query_employer_contacts(
        session=session,
        principal=principal,
        employer_id=employer_id,
        page_size=2,
        cursor=None,
    )
    assert [item.employer_contact_id for item in first_page.items] == [
        contact_ids[3],
        contact_ids[2],
    ]
    assert [item.full_name for item in first_page.items] == ["Contact Four", "Contact Three"]
    assert first_page.next_cursor is not None

    second_page = query_employer_contacts(
        session=session,
        principal=principal,
        employer_id=employer_id,
        page_size=2,
        cursor=first_page.next_cursor,
    )
    assert [item.employer_contact_id for item in second_page.items] == [
        contact_ids[1],
        contact_ids[0],
    ]
    assert [item.full_name for item in second_page.items] == ["Contact Two", "Contact One"]
    assert second_page.next_cursor is None

    combined_ids = [item.employer_contact_id for item in [*first_page.items, *second_page.items]]
    assert combined_ids == [contact_ids[3], contact_ids[2], contact_ids[1], contact_ids[0]]
    assert len(combined_ids) == len(set(combined_ids)) == 4
    assert other_contact_id not in combined_ids
    assert {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


def test_query_employer_contacts_rejects_invalid_cursor_before_contact_query_without_writes() -> (
    None
):
    principal = StaffPrincipal(
        actor_id=UUID("5a5a5a5a-5a5a-45a5-85a5-5a5a5a5a5a5a"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:read"}),
    )
    execute_calls = 0
    commit_calls = 0
    flush_calls = 0
    rollback_calls = 0

    class InvalidCursorSessionProbe:
        def execute(self, *args: object, **kwargs: object) -> None:
            nonlocal execute_calls
            execute_calls += 1
            raise AssertionError("query should not be called")

        def commit(self) -> None:
            nonlocal commit_calls
            commit_calls += 1
            raise AssertionError("commit should not be called")

        def flush(self, *args: object, **kwargs: object) -> None:
            nonlocal flush_calls
            flush_calls += 1
            raise AssertionError("flush should not be called")

        def rollback(self) -> None:
            nonlocal rollback_calls
            rollback_calls += 1
            raise AssertionError("rollback should not be called")

    with pytest.raises(ValueError, match="invalid contact cursor"):
        query_employer_contacts(
            session=cast(Session, InvalidCursorSessionProbe()),
            principal=principal,
            employer_id=UUID("6a6a6a6a-6a6a-46a6-86a6-6a6a6a6a6a6a"),
            page_size=2,
            cursor="%%%not-a-cursor%%%",
        )

    assert execute_calls == 0
    assert commit_calls == 0
    assert flush_calls == 0
    assert rollback_calls == 0


def test_query_employer_contacts_missing_parent_is_bounded_and_write_free() -> None:
    principal = StaffPrincipal(
        actor_id=UUID("7a7a7a7a-7a7a-47a7-87a7-7a7a7a7a7a7a"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:read"}),
    )
    execute_calls = 0
    commit_calls = 0
    flush_calls = 0
    rollback_calls = 0

    class MissingParentResult:
        def one_or_none(self) -> None:
            return None

    class MissingParentSessionProbe:
        def execute(self, *args: object, **kwargs: object) -> MissingParentResult:
            nonlocal execute_calls
            execute_calls += 1
            if execute_calls > 1:
                raise AssertionError("contact query should not be called")
            return MissingParentResult()

        def commit(self) -> None:
            nonlocal commit_calls
            commit_calls += 1
            raise AssertionError("commit should not be called")

        def flush(self, *args: object, **kwargs: object) -> None:
            nonlocal flush_calls
            flush_calls += 1
            raise AssertionError("flush should not be called")

        def rollback(self) -> None:
            nonlocal rollback_calls
            rollback_calls += 1
            raise AssertionError("rollback should not be called")

    with pytest.raises(EmployerNotFoundError, match="employer not found"):
        query_employer_contacts(
            session=cast(Session, MissingParentSessionProbe()),
            principal=principal,
            employer_id=UUID("8a8a8a8a-8a8a-48a8-88a8-8a8a8a8a8a8a"),
            page_size=2,
            cursor=None,
        )

    assert execute_calls == 1
    assert commit_calls == 0
    assert flush_calls == 0
    assert rollback_calls == 0


def test_query_employer_contacts_safe_persistence_failure_is_value_safe(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("9a9a9a9a-9a9a-49a9-89a9-9a9a9a9a9a9a"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:read"}),
    )
    rollback_calls = 0
    original_rollback = session.rollback

    def counting_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback()

    def fail_execute(*args: object, **kwargs: object) -> None:
        raise SQLAlchemyError(
            "psycopg UniqueViolation postgresql+psycopg:// Synthetic Sensitive Contact Query"
        )

    monkeypatch.setattr(session, "rollback", counting_rollback)
    monkeypatch.setattr(session, "execute", fail_execute)

    with pytest.raises(SafePersistenceError) as exc_info:
        query_employer_contacts(
            session=session,
            principal=principal,
            employer_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            page_size=2,
            cursor=None,
        )

    message = str(exc_info.value)
    assert message == "persistence operation failed"
    assert "psycopg" not in message
    assert "UniqueViolation" not in message
    assert "Synthetic Sensitive Contact Query" not in message
    assert "postgresql+psycopg://" not in message
    assert rollback_calls == 1


def test_get_employer_contact_returns_exact_parent_scoped_record_without_writes(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("b1b1b1b1-b1b1-41b1-81b1-b1b1b1b1b1b1"),
        role_name="operations_staff",
        permissions=frozenset(
            {"employer:read", "employer_contact:read", "employer_contact:draft:create"}
        ),
    )
    employer_id = UUID("b2b2b2b2-b2b2-42b2-82b2-b2b2b2b2b2b2")
    other_employer_id = UUID("b3b3b3b3-b3b3-43b3-83b3-b3b3b3b3b3b3")
    target_contact_id = UUID("b4b4b4b4-b4b4-44b4-84b4-b4b4b4b4b4b4")
    other_contact_id = UUID("b5b5b5b5-b5b5-45b5-85b5-b5b5b5b5b5b5")
    target_audit_event_id = UUID("b6b6b6b6-b6b6-46b6-86b6-b6b6b6b6b6b6")
    other_audit_event_id = UUID("b7b7b7b7-b7b7-47b7-87b7-b7b7b7b7b7b7")
    fixed_now = datetime(2026, 8, 13, 0, 0, 0, tzinfo=UTC)

    for seeded_employer_id, display_name in (
        (employer_id, "Read Target Employer"),
        (other_employer_id, "Read Other Employer"),
    ):
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
                    'business',
                    :display_name,
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
                "employer_id": seeded_employer_id,
                "display_name": display_name,
                "created_at": fixed_now,
                "created_by": principal.actor_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO entity_authorities (
                    entity_type,
                    entity_id,
                    employer_id,
                    employer_contact_id
                ) VALUES (
                    'employer',
                    :employer_id,
                    :employer_id,
                    NULL
                )
                """
            ),
            {"employer_id": seeded_employer_id},
        )
    session.commit()

    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        command_id=UUID("b8b8b8b8-b8b8-48b8-88b8-b8b8b8b8b8b8"),
        full_name="Exact Parent Contact",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(target_contact_id, target_audit_event_id),
    )
    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=other_employer_id,
        command_id=UUID("b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9"),
        full_name="Other Parent Contact",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(other_contact_id, other_audit_event_id),
    )

    baseline_counts = {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    }

    def fail_commit() -> None:
        raise AssertionError("commit should not be called")

    def fail_flush(*args: object, **kwargs: object) -> None:
        raise AssertionError("flush should not be called")

    def fail_rollback() -> None:
        raise AssertionError("rollback should not be called")

    monkeypatch.setattr(session, "commit", fail_commit)
    monkeypatch.setattr(session, "flush", fail_flush)
    monkeypatch.setattr(session, "rollback", fail_rollback)

    contact = get_employer_contact(
        session=session,
        principal=principal,
        employer_id=employer_id,
        employer_contact_id=target_contact_id,
    )

    assert contact.employer_contact_id == target_contact_id
    assert contact.employer_id == employer_id
    assert contact.full_name == "Exact Parent Contact"
    assert contact.created_by == principal.actor_id
    assert contact.updated_by == principal.actor_id
    assert contact.version == 1
    assert contact.employer_contact_id != other_contact_id
    assert {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


def test_get_employer_contact_denial_precedes_parent_and_contact_lookup(monkeypatch) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1"),
        role_name="operations_staff",
        permissions=frozenset(),
    )
    query_calls = 0

    class DeniedSessionProbe:
        def execute(self, *args: object, **kwargs: object) -> None:
            nonlocal query_calls
            query_calls += 1
            raise AssertionError("execute should not be called")

    with pytest.raises(PermissionError, match="principal lacks employer:read"):
        get_employer_contact(
            session=cast(Session, DeniedSessionProbe()),
            principal=principal,
            employer_id=UUID("c2c2c2c2-c2c2-42c2-82c2-c2c2c2c2c2c2"),
            employer_contact_id=UUID("c3c3c3c3-c3c3-43c3-83c3-c3c3c3c3c3c3"),
        )

    assert query_calls == 0


def test_get_employer_contact_cross_parent_and_missing_contact_are_indistinguishable(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("d1d1d1d1-d1d1-41d1-81d1-d1d1d1d1d1d1"),
        role_name="operations_staff",
        permissions=frozenset(
            {"employer:read", "employer_contact:read", "employer_contact:draft:create"}
        ),
    )
    employer_id = UUID("d2d2d2d2-d2d2-42d2-82d2-d2d2d2d2d2d2")
    other_employer_id = UUID("d3d3d3d3-d3d3-43d3-83d3-d3d3d3d3d3d3")
    target_contact_id = UUID("d4d4d4d4-d4d4-44d4-84d4-d4d4d4d4d4d4")
    missing_contact_id = UUID("d5d5d5d5-d5d5-45d5-85d5-d5d5d5d5d5d5")
    audit_event_id = UUID("d6d6d6d6-d6d6-46d6-86d6-d6d6d6d6d6d6")
    fixed_now = datetime(2026, 8, 13, 1, 0, 0, tzinfo=UTC)

    for seeded_employer_id, display_name in (
        (employer_id, "Primary Parent Employer"),
        (other_employer_id, "Other Parent Employer"),
    ):
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
                    'business',
                    :display_name,
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
                "employer_id": seeded_employer_id,
                "display_name": display_name,
                "created_at": fixed_now,
                "created_by": principal.actor_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO entity_authorities (
                    entity_type,
                    entity_id,
                    employer_id,
                    employer_contact_id
                ) VALUES (
                    'employer',
                    :employer_id,
                    :employer_id,
                    NULL
                )
                """
            ),
            {"employer_id": seeded_employer_id},
        )
    session.commit()

    create_employer_contact(
        session=session,
        principal=principal,
        employer_id=other_employer_id,
        command_id=UUID("d7d7d7d7-d7d7-47d7-87d7-d7d7d7d7d7d7"),
        full_name="Other Parent Contact",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(target_contact_id, audit_event_id),
    )

    baseline_counts = {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    }

    with pytest.raises(EmployerNotFoundError) as cross_parent_exc_info:
        get_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            employer_contact_id=target_contact_id,
        )

    with pytest.raises(EmployerNotFoundError) as missing_contact_exc_info:
        get_employer_contact(
            session=session,
            principal=principal,
            employer_id=employer_id,
            employer_contact_id=missing_contact_id,
        )

    assert str(cross_parent_exc_info.value) == "employer not found"
    assert str(missing_contact_exc_info.value) == "employer not found"
    assert str(cross_parent_exc_info.value) == str(missing_contact_exc_info.value)
    assert {
        "employer_contacts": session.execute(
            text("SELECT COUNT(*) FROM employer_contacts")
        ).scalar_one(),
        "entity_authorities": session.execute(
            text("SELECT COUNT(*) FROM entity_authorities")
        ).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts


def test_get_employer_contact_safe_persistence_failure_is_value_safe(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("e1e1e1e1-e1e1-41e1-81e1-e1e1e1e1e1e1"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read", "employer_contact:read"}),
    )
    rollback_calls = 0
    original_rollback = session.rollback

    def counting_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback()

    def fail_execute(*args: object, **kwargs: object) -> None:
        raise SQLAlchemyError(
            "psycopg UniqueViolation postgresql+psycopg:// Synthetic Sensitive Contact Read"
        )

    monkeypatch.setattr(session, "rollback", counting_rollback)
    monkeypatch.setattr(session, "execute", fail_execute)

    with pytest.raises(SafePersistenceError) as exc_info:
        get_employer_contact(
            session=session,
            principal=principal,
            employer_id=UUID("e2e2e2e2-e2e2-42e2-82e2-e2e2e2e2e2e2"),
            employer_contact_id=UUID("e3e3e3e3-e3e3-43e3-83e3-e3e3e3e3e3e3"),
        )

    message = str(exc_info.value)
    assert message == "persistence operation failed"
    assert "psycopg" not in message
    assert "UniqueViolation" not in message
    assert "Synthetic Sensitive Contact Read" not in message
    assert "postgresql+psycopg://" not in message
    assert rollback_calls == 1
