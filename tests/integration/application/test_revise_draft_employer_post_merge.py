import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

import golden_rose.application.revise_draft_employer as revise_module
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.command_receipts import reserve_revision_command_receipt


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def _insert_employer_authority(session, employer_id: UUID) -> None:
    session.execute(
        text(
            """
            INSERT INTO entity_authorities (
                entity_type, entity_id, employer_id, employer_contact_id
            ) VALUES ('employer', :employer_id, :employer_id, NULL)
            """
        ),
        {"employer_id": employer_id},
    )


def test_future_version_catch_up_rechecks_locked_values_and_rejects_noop(
    engine,
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("71717171-7171-4717-8717-717171717171"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )
    employer_id = UUID("72727272-7272-4727-8727-727272727272")
    first_command_id = UUID("73737373-7373-4737-8737-737373737373")
    catch_up_command_id = UUID("74747474-7474-4747-8747-747474747474")
    created_at = datetime(2026, 8, 11, 20, 30, 0, tzinfo=UTC)
    first_revision_at = datetime(2026, 8, 11, 20, 31, 0, tzinfo=UTC)
    catch_up_revision_at = datetime(2026, 8, 11, 20, 32, 0, tzinfo=UTC)

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
                'Synthetic Catch Up Seed',
                'draft',
                'staff_entry',
                :created_at,
                :created_at,
                :actor_id,
                :created_at,
                :actor_id,
                1
            )
            """
        ),
        {
            "employer_id": employer_id,
            "created_at": created_at,
            "actor_id": principal.actor_id,
        },
    )
    _insert_employer_authority(session, employer_id)
    session.commit()

    catch_up_reached_reservation = threading.Event()
    first_revision_committed = threading.Event()
    original_reserve = reserve_revision_command_receipt

    def coordinated_reserve(**kwargs) -> bool:
        if kwargs["command_id"] == catch_up_command_id:
            catch_up_reached_reservation.set()
            if not first_revision_committed.wait(timeout=5):
                raise RuntimeError("first revision did not commit")
        return original_reserve(**kwargs)

    monkeypatch.setattr(revise_module, "reserve_revision_command_receipt", coordinated_reserve)

    def run_catch_up_revision():
        with Session(engine) as catch_up_session:
            try:
                return revise_draft_employer(
                    session=catch_up_session,
                    principal=principal,
                    command_id=catch_up_command_id,
                    employer_id=employer_id,
                    expected_version=2,
                    employer_type="business",
                    display_name="Synthetic Catch Up Current",
                    clock=FixedClock(catch_up_revision_at),
                )
            except Exception as exc:
                return exc

    with ThreadPoolExecutor(max_workers=1) as executor:
        catch_up_future = executor.submit(run_catch_up_revision)
        assert catch_up_reached_reservation.wait(timeout=5)

        with Session(engine) as first_session:
            first_result = revise_draft_employer(
                session=first_session,
                principal=principal,
                command_id=first_command_id,
                employer_id=employer_id,
                expected_version=1,
                employer_type="business",
                display_name="Synthetic Catch Up Current",
                clock=FixedClock(first_revision_at),
            )
        first_revision_committed.set()
        catch_up_result = catch_up_future.result(timeout=5)

    employer = (
        session.execute(
            text(
                """
            SELECT employer_type, display_name, version
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
    event = (
        session.execute(
            text(
                """
            SELECT command_id, new_record_version, changed_fields
            FROM audit_events
            WHERE entity_id = :employer_id
            """
            ),
            {"employer_id": employer_id},
        )
        .mappings()
        .one()
    )

    assert first_result.result_record_version == 2
    assert isinstance(catch_up_result, RuntimeError)
    assert str(catch_up_result) == "employer revision requires a change"
    assert dict(employer) == {
        "employer_type": "business",
        "display_name": "Synthetic Catch Up Current",
        "version": 2,
    }
    assert receipt_count == 1
    assert dict(event) == {
        "command_id": first_command_id,
        "new_record_version": 2,
        "changed_fields": {
            "field_names": ["employer_type", "display_name"],
            "approved_values": {"employer_type": "business"},
        },
    }
