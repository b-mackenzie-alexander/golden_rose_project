import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Literal
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import golden_rose.application.revise_draft_employer as revise_draft_employer_module
from golden_rose.application.errors import (
    EmployerNotFoundError,
    EmployerVersionConflictError,
    SafePersistenceError,
)
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.auth.principal import StaffPrincipal


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def _run_revise_draft_employer_in_isolated_session(
    *,
    engine,
    barrier: threading.Barrier,
    principal: StaffPrincipal,
    command_id: UUID,
    employer_id: UUID,
    expected_version: int,
    employer_type: Literal["household", "business"],
    display_name: str,
    now: datetime,
):
    with Session(engine) as isolated_session:
        barrier.wait()
        return revise_draft_employer(
            session=isolated_session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=expected_version,
            employer_type=employer_type,
            display_name=display_name,
            clock=FixedClock(now),
        )


def test_revision_updates_only_name_type_updated_at_updated_by_and_version(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("51515151-5151-4515-8515-515151515151"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("52525252-5252-4525-8525-525252525252")
    command_id = UUID("53535353-5353-4535-8535-535353535353")
    created_by = UUID("54545454-5454-4545-8545-545454545454")
    created_at = datetime(2026, 8, 10, 20, 30, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 20, 35, 0, tzinfo=UTC)

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
                'Synthetic Draft Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    result = revise_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_id=employer_id,
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Revised Employer",
        clock=FixedClock(revised_at),
    )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_id, employer_type, display_name, lifecycle_status,
                       source_channel, received_at, created_at, created_by,
                       updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )

    assert result.replayed is False
    assert result.result_record_version == 2
    assert result.employer.employer_id == employer_id
    assert result.employer.employer_type == "business"
    assert result.employer.display_name == "Synthetic Revised Employer"
    assert result.employer.version == 2

    assert dict(employer) == {
        "employer_id": employer_id,
        "employer_type": "business",
        "display_name": "Synthetic Revised Employer",
        "lifecycle_status": "draft",
        "source_channel": "staff_entry",
        "received_at": created_at,
        "created_at": created_at,
        "created_by": created_by,
        "updated_at": revised_at,
        "updated_by": principal.actor_id,
        "version": 2,
    }


def test_revision_requires_named_permission_before_record_or_writes(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("56565656-5656-4565-8565-565656565656"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read"}),
    )
    employer_id = UUID("57575757-5757-4575-8575-575757575757")
    command_id = UUID("58585858-5858-4585-8585-585858585858")
    created_by = UUID("59595959-5959-4595-8595-595959595959")
    created_at = datetime(2026, 8, 10, 20, 40, 0, tzinfo=UTC)

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
                'Synthetic Protected Draft Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    with pytest.raises(PermissionError, match="principal lacks employer:draft:revise"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Unauthorized Revision Attempt",
            clock=FixedClock(datetime(2026, 8, 10, 20, 45, 0, tzinfo=UTC)),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Protected Draft Employer",
        "updated_by": created_by,
        "version": 1,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


def test_revision_rejects_missing_employer_without_writes(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("60606060-6060-4606-8606-606060606060"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    missing_employer_id = UUID("61616161-6161-4616-8616-616161616161")
    command_id = UUID("62626262-6262-4626-8626-626262626262")

    with pytest.raises(EmployerNotFoundError, match="employer not found"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=missing_employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Missing Employer Revision Attempt",
            clock=FixedClock(datetime(2026, 8, 10, 20, 50, 0, tzinfo=UTC)),
        )

    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert employer_count == 0
    assert receipt_count == 0
    assert audit_event_count == 0


def test_revision_rejects_stale_expected_version_without_writes(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("63636363-6363-4636-8636-636363636363"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("64646464-6464-4646-8646-646464646464")
    command_id = UUID("65656565-6565-4656-8656-656565656565")
    created_by = UUID("66666666-6666-4666-8666-666666666666")
    created_at = datetime(2026, 8, 10, 20, 55, 0, tzinfo=UTC)

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
                'Synthetic Stale Draft Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    with pytest.raises(RuntimeError, match="employer version conflict"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Stale Revision Attempt",
            clock=FixedClock(datetime(2026, 8, 10, 21, 0, 0, tzinfo=UTC)),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Stale Draft Employer",
        "updated_by": created_by,
        "version": 2,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


def test_revision_rejects_normalized_noop_without_consuming_command_key(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("67676767-6767-4676-8676-676767676767"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("68686868-6868-4686-8686-686868686868")
    command_id = UUID("69696969-6969-4696-8696-696969696969")
    created_by = UUID("70707070-7070-4707-8707-707070707070")
    created_at = datetime(2026, 8, 10, 21, 5, 0, tzinfo=UTC)

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
                'Synthetic Noop Draft Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    with pytest.raises(RuntimeError, match="employer revision requires a change"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="household",
            display_name="Synthetic Noop Draft Employer",
            clock=FixedClock(datetime(2026, 8, 10, 21, 10, 0, tzinfo=UTC)),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Noop Draft Employer",
        "updated_by": created_by,
        "version": 1,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


def test_revision_stale_precedes_noop_when_values_match_later_current_truth(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("71717171-7171-4717-8717-717171717171"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("72727272-7272-4727-8727-727272727272")
    command_id = UUID("73737373-7373-4737-8737-737373737373")
    created_by = UUID("74747474-7474-4747-8747-747474747474")
    created_at = datetime(2026, 8, 10, 21, 15, 0, tzinfo=UTC)

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
                'Synthetic Later Current Truth Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    with pytest.raises(RuntimeError, match="employer version conflict"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Later Current Truth Employer",
            clock=FixedClock(datetime(2026, 8, 10, 21, 20, 0, tzinfo=UTC)),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Later Current Truth Employer",
        "updated_by": created_by,
        "version": 2,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


def test_revision_normalizes_before_fingerprint_compare_and_update(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("75757575-7575-4757-8757-757575757575"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("76767676-7676-4767-8767-767676767676")
    command_id = UUID("77777777-7777-4777-8777-777777777777")
    created_by = UUID("78787878-7878-4787-8787-787878787878")
    created_at = datetime(2026, 8, 10, 21, 25, 0, tzinfo=UTC)

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
                'Café Central',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    with pytest.raises(RuntimeError, match="employer revision requires a change"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="  Café Central  ",
            clock=FixedClock(datetime(2026, 8, 10, 21, 30, 0, tzinfo=UTC)),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Café Central",
        "updated_by": created_by,
        "version": 1,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


def test_revision_reuses_matching_receipt_without_rewrite(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("79797979-7979-4797-8797-797979797979"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("80808080-8080-4808-8808-808080808080")
    command_id = UUID("81818181-8181-4818-8818-818181818181")
    audit_event_id = UUID("82828282-8282-4828-8828-828282828282")
    created_by = UUID("83838383-8383-4838-8838-838383838383")
    created_at = datetime(2026, 8, 10, 21, 35, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 21, 40, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Receipt Replay Employer",
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
                'business',
                'Synthetic Receipt Replay Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    result = revise_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_id=employer_id,
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Receipt Replay Employer",
        clock=FixedClock(datetime(2026, 8, 10, 21, 45, 0, tzinfo=UTC)),
    )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert result.replayed is True
    assert result.result_record_version == 2
    assert result.employer.employer_id == employer_id
    assert result.employer.employer_type == "business"
    assert result.employer.display_name == "Synthetic Receipt Replay Employer"
    assert result.employer.version == 2
    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Receipt Replay Employer",
        "updated_at": revised_at,
        "updated_by": principal.actor_id,
        "version": 2,
    }
    assert receipt_count == 1
    assert audit_event_count == 1


def test_identical_revision_replay_is_write_free_and_returns_current_truth(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("84848484-8484-4848-8848-848484848484"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("85858585-8585-4858-8858-858585858585")
    command_id = UUID("86868686-8686-4868-8868-868686868686")
    audit_event_id = UUID("87878787-8787-4878-8878-878787878787")
    created_by = UUID("88888888-8888-4888-8888-888888888888")
    created_at = datetime(2026, 8, 10, 21, 50, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 21, 55, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Identical Replay Employer",
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
                'business',
                'Synthetic Identical Replay Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    result = revise_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_id=employer_id,
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Identical Replay Employer",
        clock=FixedClock(datetime(2026, 8, 10, 22, 0, 0, tzinfo=UTC)),
    )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert result.replayed is True
    assert result.result_record_version == 2
    assert result.employer.employer_id == employer_id
    assert result.employer.employer_type == "business"
    assert result.employer.display_name == "Synthetic Identical Replay Employer"
    assert result.employer.version == 2
    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Identical Replay Employer",
        "updated_at": revised_at,
        "updated_by": principal.actor_id,
        "version": 2,
    }
    assert receipt_count == 1
    assert audit_event_count == 1


def test_identical_revision_replay_precedes_stale_and_noop_evaluation(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("89898989-8989-4898-8898-898989898989"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("90909090-9090-4909-8909-909090909090")
    command_id = UUID("91919191-9191-4919-8919-919191919191")
    audit_event_id = UUID("92929292-9292-4929-8929-929292929292")
    created_by = UUID("93939393-9393-4939-8939-939393939393")
    created_at = datetime(2026, 8, 10, 22, 5, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 22, 10, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Replay Precedence Employer",
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
                'business',
                'Synthetic Replay Precedence Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    result = revise_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_id=employer_id,
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Replay Precedence Employer",
        clock=FixedClock(datetime(2026, 8, 10, 22, 15, 0, tzinfo=UTC)),
    )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert result.replayed is True
    assert result.result_record_version == 2
    assert result.employer.employer_id == employer_id
    assert result.employer.employer_type == "business"
    assert result.employer.display_name == "Synthetic Replay Precedence Employer"
    assert result.employer.version == 2
    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Replay Precedence Employer",
        "updated_at": revised_at,
        "updated_by": principal.actor_id,
        "version": 2,
    }
    assert receipt_count == 1
    assert audit_event_count == 1


def test_conflicting_revision_replay_is_write_free(
    session,
    clean_tables,
) -> None:
    receipt_actor_id = UUID("94949494-9494-4949-8949-949494949494")
    principal = StaffPrincipal(
        actor_id=UUID("95959595-9595-4959-8959-959595959595"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("96969696-9696-4969-8969-969696969696")
    command_id = UUID("97979797-9797-4979-8979-979797979797")
    audit_event_id = UUID("98989898-9898-4989-8989-989898989898")
    created_by = UUID("99999999-9999-4999-8999-999999999999")
    created_at = datetime(2026, 8, 10, 22, 20, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 22, 25, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "Synthetic Conflict Replay Employer",
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
                'business',
                'Synthetic Conflict Replay Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :receipt_actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "receipt_actor_id": receipt_actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
                'employer',
                :entity_id,
                2,
                1,
                2,
                'staff',
                :receipt_actor_id,
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "receipt_actor_id": receipt_actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :receipt_actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "receipt_actor_id": receipt_actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    with pytest.raises(RuntimeError, match="idempotency conflict"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=2,
            employer_type="business",
            display_name="Synthetic Conflict Replay Employer",
            clock=FixedClock(datetime(2026, 8, 10, 22, 30, 0, tzinfo=UTC)),
        )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Conflict Replay Employer",
        "updated_at": revised_at,
        "updated_by": receipt_actor_id,
        "version": 2,
    }
    assert receipt_count == 1
    assert audit_event_count == 1


def test_changed_revision_replay_conflict_precedes_stale_evaluation(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("01010101-aaaa-4aaa-8aaa-010101010101"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("02020202-bbbb-4bbb-8bbb-020202020202")
    command_id = UUID("03030303-cccc-4ccc-8ccc-030303030303")
    audit_event_id = UUID("04040404-dddd-4ddd-8ddd-040404040404")
    created_by = UUID("05050505-eeee-4eee-8eee-050505050505")
    created_at = datetime(2026, 8, 10, 22, 35, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 22, 40, 0, tzinfo=UTC)
    conflicting_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 1,
                "employer_type": "household",
                "display_name": "Different prior payload",
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
                'business',
                'Synthetic Changed Replay Precedence Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": conflicting_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    with pytest.raises(RuntimeError, match="idempotency conflict"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Changed Replay Precedence Employer",
            clock=FixedClock(datetime(2026, 8, 10, 22, 45, 0, tzinfo=UTC)),
        )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Changed Replay Precedence Employer",
        "updated_at": revised_at,
        "updated_by": principal.actor_id,
        "version": 2,
    }
    assert receipt_count == 1
    assert audit_event_count == 1


def test_revision_replay_rejects_inconsistent_result_version_event_type_or_target(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("06060606-aaaa-4aaa-8aaa-060606060606"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("07070707-bbbb-4bbb-8bbb-070707070707")
    replay_target_employer_id = UUID("21212121-bbbb-4bbb-8bbb-212121212121")
    command_id = UUID("08080808-cccc-4ccc-8ccc-080808080808")
    audit_event_id = UUID("09090909-dddd-4ddd-8ddd-090909090909")
    created_by = UUID("11111111-eeee-4eee-8eee-111111111111")
    created_at = datetime(2026, 8, 10, 22, 50, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 22, 55, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Invalid Revision Replay Metadata Employer",
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).digest()

    for target_employer_id in (employer_id, replay_target_employer_id):
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
                    'Synthetic Invalid Revision Replay Metadata Employer',
                    'draft',
                    'staff_entry',
                    :created_at,
                    :created_at,
                    :created_by,
                    :revised_at,
                    :actor_id,
                    3
                )
                """
            ),
            {
                "employer_id": target_employer_id,
                "created_at": created_at,
                "created_by": created_by,
                "revised_at": revised_at,
                "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
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
            "audit_event_id": audit_event_id,
            "entity_id": replay_target_employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": replay_target_employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Invalid Revision Replay Metadata Employer",
            clock=FixedClock(datetime(2026, 8, 10, 23, 0, 0, tzinfo=UTC)),
        )


def test_revision_replay_after_later_revision_returns_current_truth_and_original_result_version_without_writes(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("22222222-aaaa-4aaa-8aaa-222222222222"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("23232323-bbbb-4bbb-8bbb-232323232323")
    command_id = UUID("24242424-cccc-4ccc-8ccc-242424242424")
    audit_event_id = UUID("25252525-dddd-4ddd-8ddd-252525252525")
    created_by = UUID("26262626-eeee-4eee-8eee-262626262626")
    created_at = datetime(2026, 8, 10, 23, 5, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 23, 10, 0, tzinfo=UTC)
    later_updated_at = datetime(2026, 8, 10, 23, 20, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 1,
                "employer_type": "business",
                "display_name": "Synthetic Replay Later Truth Employer",
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
                'Synthetic Replay Later Truth Employer v3',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :later_updated_at,
                :actor_id,
                3
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "later_updated_at": later_updated_at,
            "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                2,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    result = revise_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_id=employer_id,
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Replay Later Truth Employer",
        clock=FixedClock(datetime(2026, 8, 10, 23, 30, 0, tzinfo=UTC)),
    )

    employer = (
        session.execute(
            text(
                """
                SELECT employer_type, display_name, updated_at, updated_by, version
                FROM employers
                WHERE employer_id = :employer_id
                """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert result.replayed is True
    assert result.result_record_version == 2
    assert result.employer.employer_id == employer_id
    assert result.employer.employer_type == "household"
    assert result.employer.display_name == "Synthetic Replay Later Truth Employer v3"
    assert result.employer.version == 3
    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Replay Later Truth Employer v3",
        "updated_at": later_updated_at,
        "updated_by": principal.actor_id,
        "version": 3,
    }
    assert receipt_count == 1
    assert audit_event_count == 1


def test_revision_races_use_two_read_committed_sessions_and_synchronization_barrier(
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("27272727-aaaa-4aaa-8aaa-272727272727"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("28282828-bbbb-4bbb-8bbb-282828282828")
    created_by = UUID("29292929-cccc-4ccc-8ccc-292929292929")
    created_at = datetime(2026, 8, 10, 23, 35, 0, tzinfo=UTC)
    barrier = threading.Barrier(2)

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
                'Synthetic Race Harness Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    def run_and_capture(**kwargs):
        try:
            return _run_revise_draft_employer_in_isolated_session(**kwargs)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=UUID("30303030-dddd-4ddd-8ddd-303030303030"),
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Race Harness Employer A",
            now=datetime(2026, 8, 10, 23, 36, 0, tzinfo=UTC),
        )
        future_two = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=UUID("31313131-eeee-4eee-8eee-313131313131"),
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Race Harness Employer B",
            now=datetime(2026, 8, 10, 23, 36, 1, tzinfo=UTC),
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
    assert isinstance(failures[0], EmployerVersionConflictError)
    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_two_distinct_commands_with_same_expected_version_have_one_winner(
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("32323232-aaaa-4aaa-8aaa-323232323232"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("33333333-bbbb-4bbb-8bbb-333333333333")
    created_by = UUID("34343434-cccc-4ccc-8ccc-343434343434")
    created_at = datetime(2026, 8, 10, 23, 40, 0, tzinfo=UTC)
    barrier = threading.Barrier(2)

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
                'Synthetic One Winner Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    def run_and_capture(**kwargs):
        try:
            return _run_revise_draft_employer_in_isolated_session(**kwargs)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=UUID("35353535-dddd-4ddd-8ddd-353535353535"),
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic One Winner Employer A",
            now=datetime(2026, 8, 10, 23, 41, 0, tzinfo=UTC),
        )
        future_two = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=UUID("36363636-eeee-4eee-8eee-363636363636"),
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic One Winner Employer B",
            now=datetime(2026, 8, 10, 23, 41, 1, tzinfo=UTC),
        )

    result_one = future_one.result()
    result_two = future_two.result()
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
    employer_count = session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one()
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    successes = [result for result in (result_one, result_two) if not isinstance(result, Exception)]
    failures = [result for result in (result_one, result_two) if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], EmployerVersionConflictError)
    assert successes[0].replayed is False
    assert successes[0].result_record_version == 2
    assert successes[0].employer.employer_id == employer_id
    assert successes[0].employer.version == 2
    assert dict(employer) in (
        {
            "employer_type": "business",
            "display_name": "Synthetic One Winner Employer A",
            "updated_by": principal.actor_id,
            "version": 2,
        },
        {
            "employer_type": "business",
            "display_name": "Synthetic One Winner Employer B",
            "updated_by": principal.actor_id,
            "version": 2,
        },
    )
    assert employer_count == 1
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_concurrent_identical_revision_command_has_one_update_receipt_and_event(
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("37373737-aaaa-4aaa-8aaa-373737373737"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("38383838-bbbb-4bbb-8bbb-383838383838")
    created_by = UUID("39393939-cccc-4ccc-8ccc-393939393939")
    created_at = datetime(2026, 8, 10, 23, 45, 0, tzinfo=UTC)
    barrier = threading.Barrier(2)
    command_id = UUID("40404040-dddd-4ddd-8ddd-404040404040")

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
                'Synthetic Concurrent Identical Revision Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    def run_and_capture(**kwargs):
        try:
            return _run_revise_draft_employer_in_isolated_session(**kwargs)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Concurrent Identical Revision Employer Updated",
            now=datetime(2026, 8, 10, 23, 46, 0, tzinfo=UTC),
        )
        future_two = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Concurrent Identical Revision Employer Updated",
            now=datetime(2026, 8, 10, 23, 46, 1, tzinfo=UTC),
        )

    result_one = future_one.result()
    result_two = future_two.result()
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
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    successes = [result for result in (result_one, result_two) if not isinstance(result, Exception)]
    failures = [result for result in (result_one, result_two) if isinstance(result, Exception)]

    assert len(successes) == 2
    assert failures == []
    assert sorted([success.replayed for success in successes]) == [False, True]
    assert successes[0].employer == successes[1].employer
    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Concurrent Identical Revision Employer Updated",
        "updated_by": principal.actor_id,
        "version": 2,
    }
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_concurrent_same_key_changed_actor_or_payload_has_one_success_and_one_conflict(
    engine,
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("41414141-aaaa-4aaa-8aaa-414141414141"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("42424242-bbbb-4bbb-8bbb-424242424242")
    created_by = UUID("43434343-cccc-4ccc-8ccc-434343434343")
    created_at = datetime(2026, 8, 10, 23, 50, 0, tzinfo=UTC)
    barrier = threading.Barrier(2)
    command_id = UUID("44444444-dddd-4ddd-8ddd-444444444444")

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
                'Synthetic Concurrent Conflict Revision Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    def run_and_capture(**kwargs):
        try:
            return _run_revise_draft_employer_in_isolated_session(**kwargs)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_one = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Concurrent Conflict Revision Employer A",
            now=datetime(2026, 8, 10, 23, 51, 0, tzinfo=UTC),
        )
        future_two = executor.submit(
            run_and_capture,
            engine=engine,
            barrier=barrier,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Concurrent Conflict Revision Employer B",
            now=datetime(2026, 8, 10, 23, 51, 1, tzinfo=UTC),
        )

    result_one = future_one.result()
    result_two = future_two.result()
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
    command_receipt_count = session.execute(
        text("SELECT COUNT(*) FROM command_receipts")
    ).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    successes = [result for result in (result_one, result_two) if not isinstance(result, Exception)]
    failures = [result for result in (result_one, result_two) if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], RuntimeError)
    assert str(failures[0]) == "idempotency conflict"
    assert successes[0].replayed is False
    assert successes[0].result_record_version == 2
    assert dict(employer) in (
        {
            "employer_type": "business",
            "display_name": "Synthetic Concurrent Conflict Revision Employer A",
            "updated_by": principal.actor_id,
            "version": 2,
        },
        {
            "employer_type": "business",
            "display_name": "Synthetic Concurrent Conflict Revision Employer B",
            "updated_by": principal.actor_id,
            "version": 2,
        },
    )
    assert command_receipt_count == 1
    assert audit_event_count == 1


def test_late_audit_failure_rolls_back_receipt_and_employer_update(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("45454545-aaaa-4aaa-8aaa-454545454545"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("46464646-bbbb-4bbb-8bbb-464646464646")
    command_id = UUID("47474747-cccc-4ccc-8ccc-474747474747")
    created_by = UUID("48484848-dddd-4ddd-8ddd-484848484848")
    created_at = datetime(2026, 8, 10, 23, 55, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 10, 23, 56, 0, tzinfo=UTC)

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
                'Synthetic Late Audit Failure Employer',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    def raise_late_audit_failure(**_kwargs):
        raise RuntimeError("synthetic late audit failure")

    monkeypatch.setattr(
        revise_draft_employer_module,
        "insert_employer_draft_revised_event",
        raise_late_audit_failure,
    )

    with pytest.raises(RuntimeError, match="synthetic late audit failure"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Late Audit Failure Employer Updated",
            clock=FixedClock(revised_at),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Late Audit Failure Employer",
        "updated_by": created_by,
        "version": 1,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


@pytest.mark.parametrize(
    (
        "initial_employer_type",
        "initial_display_name",
        "revised_employer_type",
        "revised_display_name",
        "expected_changed_fields",
        "employer_id",
        "command_id",
        "created_at",
        "revised_at",
    ),
    [
        (
            "household",
            "Synthetic Audit Name Only Employer",
            "household",
            "Synthetic Audit Name Only Employer Updated",
            {"field_names": ["display_name"], "approved_values": {}},
            UUID("51515151-cccc-4ccc-8ccc-515151515151"),
            UUID("52525252-dddd-4ddd-8ddd-525252525252"),
            datetime(2026, 8, 11, 0, 0, 0, tzinfo=UTC),
            datetime(2026, 8, 11, 0, 1, 0, tzinfo=UTC),
        ),
        (
            "household",
            "Synthetic Audit Type Only Employer",
            "business",
            "Synthetic Audit Type Only Employer",
            {
                "field_names": ["employer_type"],
                "approved_values": {"employer_type": "business"},
            },
            UUID("53535353-cccc-4ccc-8ccc-535353535353"),
            UUID("54545454-dddd-4ddd-8ddd-545454545454"),
            datetime(2026, 8, 11, 0, 2, 0, tzinfo=UTC),
            datetime(2026, 8, 11, 0, 3, 0, tzinfo=UTC),
        ),
        (
            "household",
            "Synthetic Audit Both Employer",
            "business",
            "Synthetic Audit Both Employer Updated",
            {
                "field_names": ["employer_type", "display_name"],
                "approved_values": {"employer_type": "business"},
            },
            UUID("55555555-cccc-4ccc-8ccc-555555555555"),
            UUID("56565656-dddd-4ddd-8ddd-565656565656"),
            datetime(2026, 8, 11, 0, 4, 0, tzinfo=UTC),
            datetime(2026, 8, 11, 0, 5, 0, tzinfo=UTC),
        ),
    ],
)
def test_revision_audit_event_is_minimized_for_each_allowed_changed_field_set(
    session,
    clean_tables,
    initial_employer_type,
    initial_display_name,
    revised_employer_type,
    revised_display_name,
    expected_changed_fields,
    employer_id,
    command_id,
    created_at,
    revised_at,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("49494949-aaaa-4aaa-8aaa-494949494949"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    created_by = UUID("50505050-bbbb-4bbb-8bbb-505050505050")

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
                :employer_type,
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
            "employer_type": initial_employer_type,
            "display_name": initial_display_name,
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    result = revise_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_id=employer_id,
        expected_version=1,
        employer_type=revised_employer_type,
        display_name=revised_display_name,
        clock=FixedClock(revised_at),
    )

    audit_event = (
        session.execute(
            text(
                """
                SELECT changed_fields, event_type, prior_record_version, new_record_version
                FROM audit_events
                WHERE command_id = :command_id
                """
            ),
            {"command_id": command_id},
        )
        .mappings()
        .one()
    )

    assert result.replayed is False
    assert result.result_record_version == 2
    assert dict(audit_event) == {
        "changed_fields": expected_changed_fields,
        "event_type": "employer.draft_revised",
        "prior_record_version": 1,
        "new_record_version": 2,
    }


def test_revision_persistence_failures_are_value_safe(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("57575757-aaaa-4aaa-8aaa-575757575757"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("58585858-bbbb-4bbb-8bbb-585858585858")
    command_id = UUID("59595959-cccc-4ccc-8ccc-595959595959")
    created_by = UUID("60606060-dddd-4ddd-8ddd-606060606060")
    created_at = datetime(2026, 8, 11, 0, 10, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 11, 0, 11, 0, tzinfo=UTC)

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
                'Synthetic Sensitive Revision Seed',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    def raise_persistence_failure(**_kwargs):
        raise SQLAlchemyError(
            "psycopg UniqueViolation postgresql+psycopg:// Synthetic Sensitive Revision Update"
        )

    monkeypatch.setattr(
        revise_draft_employer_module,
        "reserve_revision_command_receipt",
        raise_persistence_failure,
    )

    with pytest.raises(SafePersistenceError) as exc_info:
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name="Synthetic Sensitive Revision Update",
            clock=FixedClock(revised_at),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    message = str(exc_info.value)
    assert message == "persistence operation failed"
    assert "psycopg" not in message
    assert "UniqueViolation" not in message
    assert "Synthetic Sensitive Revision Update" not in message
    assert "postgresql+psycopg://" not in message
    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Sensitive Revision Seed",
        "updated_by": created_by,
        "version": 1,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


@pytest.mark.parametrize(
    ("display_name", "message"),
    [
        ("   ", "display_name must not be blank"),
        ("x" * 201, "display_name must be 200 characters or fewer"),
        ("Bad\nName", "display_name must not contain control characters"),
    ],
)
def test_revision_rejects_invalid_display_name_without_writes(
    session,
    clean_tables,
    display_name: str,
    message: str,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("61616161-eeee-4eee-8eee-616161616161"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("62626262-ffff-4fff-8fff-626262626262")
    created_by = UUID("63636363-1111-4111-8111-636363636363")
    created_at = datetime(2026, 8, 11, 0, 20, 0, tzinfo=UTC)

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
                'Synthetic Invalid Revision Seed',
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
            "created_at": created_at,
            "created_by": created_by,
        },
    )
    session.commit()

    with pytest.raises(ValueError, match=message):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=UUID("64646464-2222-4222-8222-646464646464"),
            employer_id=employer_id,
            expected_version=1,
            employer_type="business",
            display_name=display_name,
            clock=FixedClock(datetime(2026, 8, 11, 0, 25, 0, tzinfo=UTC)),
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
    receipt_count = session.execute(text("SELECT COUNT(*) FROM command_receipts")).scalar_one()
    audit_event_count = session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()

    assert dict(employer) == {
        "employer_type": "household",
        "display_name": "Synthetic Invalid Revision Seed",
        "updated_by": created_by,
        "version": 1,
    }
    assert receipt_count == 0
    assert audit_event_count == 0


def test_identical_revision_replay_rejects_malformed_receipt_result_version(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("65656565-3333-4333-8333-656565656565"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("66666666-4444-4444-8444-666666666666")
    command_id = UUID("67676767-5555-4555-8555-676767676767")
    created_by = UUID("69696969-7777-4777-8777-696969696969")
    created_at = datetime(2026, 8, 11, 0, 30, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 11, 0, 35, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "Synthetic Malformed Receipt Employer",
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
                'business',
                'Synthetic Malformed Receipt Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "actor_id": principal.actor_id,
        },
    )
    session.commit()

    monkeypatch.setattr(
        revise_draft_employer_module,
        "get_command_receipt",
        lambda **_kwargs: SimpleNamespace(
            command_id=command_id,
            command_schema_version=1,
            command_type="revise_draft_employer",
            actor_id=principal.actor_id,
            request_fingerprint=request_fingerprint,
            result_entity_type="employer",
            result_entity_id=employer_id,
            result_record_version=4,
            result_event_type="employer.draft_revised",
            created_at=revised_at,
        ),
    )

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=2,
            employer_type="business",
            display_name="Synthetic Malformed Receipt Employer",
            clock=FixedClock(datetime(2026, 8, 11, 0, 40, 0, tzinfo=UTC)),
        )


def test_identical_revision_replay_rejects_current_version_behind_receipt_result_version(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("70707070-8888-4888-8888-707070707070"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("71717171-9999-4999-8999-717171717171")
    command_id = UUID("72727272-aaaa-4aaa-8aaa-727272727272")
    audit_event_id = UUID("73737373-bbbb-4bbb-8bbb-737373737373")
    created_by = UUID("74747474-cccc-4ccc-8ccc-747474747474")
    created_at = datetime(2026, 8, 11, 0, 45, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 11, 0, 50, 0, tzinfo=UTC)
    request_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "command_schema_version": 1,
                "command_type": "revise_draft_employer",
                "employer_id": str(employer_id),
                "expected_version": 2,
                "employer_type": "business",
                "display_name": "Synthetic Behind Current Employer",
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
                'business',
                'Synthetic Behind Current Employer',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :created_by,
                :revised_at,
                :actor_id,
                2
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "created_by": created_by,
            "revised_at": revised_at,
            "actor_id": principal.actor_id,
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
                'employer.draft_revised',
                1,
                'employer.draft_revised',
                'employer',
                :entity_id,
                3,
                2,
                3,
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
            "audit_event_id": audit_event_id,
            "entity_id": employer_id,
            "actor_id": principal.actor_id,
            "occurred_at": revised_at,
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
                'revise_draft_employer',
                :actor_id,
                :request_fingerprint,
                'employer',
                :result_entity_id,
                3,
                'employer.draft_revised',
                :created_at
            )
            """
        ),
        {
            "command_id": command_id,
            "actor_id": principal.actor_id,
            "request_fingerprint": request_fingerprint,
            "result_entity_id": employer_id,
            "created_at": revised_at,
        },
    )
    session.commit()

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        revise_draft_employer(
            session=session,
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=2,
            employer_type="business",
            display_name="Synthetic Behind Current Employer",
            clock=FixedClock(datetime(2026, 8, 11, 0, 55, 0, tzinfo=UTC)),
        )
