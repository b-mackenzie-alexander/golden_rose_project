from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Update

import golden_rose.application.revise_draft_employer as revise_module
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.auth.principal import StaffPrincipal
from golden_rose.persistence.command_receipts import CommandReceiptRecord


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class OptionalRowResult:
    def __init__(self, row: tuple[str, str] | None) -> None:
        self._row = row

    def one_or_none(self) -> tuple[str, str] | None:
        return self._row


class RequiredRowResult:
    def __init__(self, row: tuple[object, ...]) -> None:
        self._row = row

    def one(self) -> tuple[object, ...]:
        return self._row


class CatchUpRaceSession:
    def __init__(self, *, employer_id: UUID, actor_id: UUID, now: datetime) -> None:
        self.caught_up = False
        self.commit_count = 0
        self.rollback_count = 0
        self._updated_row = (
            employer_id,
            "business",
            "Synthetic Catch Up Employer",
            "draft",
            "staff_entry",
            now,
            now,
            now,
            actor_id,
            3,
        )

    def execute(self, statement):
        if isinstance(statement, Update):
            return RequiredRowResult(self._updated_row)
        current = ("business", "Synthetic Catch Up Employer") if self.caught_up else None
        return OptionalRowResult(current)

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def test_revision_rechecks_locked_current_values_after_receipt_reservation_before_writing(
    monkeypatch,
) -> None:
    employer_id = UUID("31313131-3131-4313-8313-313131313131")
    command_id = UUID("32323232-3232-4323-8323-323232323232")
    actor_id = UUID("33333333-3333-4333-8333-333333333333")
    now = datetime(2026, 8, 11, 20, 15, 0, tzinfo=UTC)
    session = CatchUpRaceSession(employer_id=employer_id, actor_id=actor_id, now=now)
    inserted_events: list[dict[str, object]] = []

    def receipt_not_found(**_kwargs):
        raise NoResultFound

    def reserve_receipt(**_kwargs) -> bool:
        session.caught_up = True
        return True

    def capture_event(**kwargs) -> None:
        inserted_events.append(kwargs)

    monkeypatch.setattr(revise_module, "get_command_receipt", receipt_not_found)
    monkeypatch.setattr(revise_module, "reserve_revision_command_receipt", reserve_receipt)
    monkeypatch.setattr(revise_module, "insert_employer_draft_revised_event", capture_event)

    principal = StaffPrincipal(
        actor_id=actor_id,
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )

    with pytest.raises(RuntimeError, match="employer revision requires a change"):
        revise_draft_employer(
            session=cast(Session, session),
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=2,
            employer_type="business",
            display_name="Synthetic Catch Up Employer",
            clock=FixedClock(now),
        )

    assert inserted_events == []
    assert session.commit_count == 0


def test_revision_retries_receipt_lookup_after_transient_conflict_race_not_found(
    monkeypatch,
) -> None:
    employer_id = UUID("51515151-5151-4515-8515-515151515151")
    command_id = UUID("52525252-5252-4525-8525-525252525252")
    actor_id = UUID("53535353-5353-4535-8535-535353535353")
    now = datetime(2026, 8, 11, 20, 16, 0, tzinfo=UTC)
    session = CatchUpRaceSession(employer_id=employer_id, actor_id=actor_id, now=now)

    receipt = CommandReceiptRecord(
        command_id=command_id,
        command_schema_version=1,
        command_type="revise_draft_employer",
        actor_id=actor_id,
        request_fingerprint=b"x" * 32,
        result_entity_type="employer",
        result_entity_id=employer_id,
        result_record_version=3,
        result_event_type="employer.draft_revised",
        created_at=now,
    )
    get_receipt_calls = 0

    def get_receipt(**_kwargs):
        nonlocal get_receipt_calls
        get_receipt_calls += 1
        if get_receipt_calls in {1, 2}:
            raise NoResultFound
        return receipt

    def reserve_receipt(**_kwargs) -> bool:
        return False

    monkeypatch.setattr(revise_module, "get_command_receipt", get_receipt)
    monkeypatch.setattr(revise_module, "reserve_revision_command_receipt", reserve_receipt)

    principal = StaffPrincipal(
        actor_id=actor_id,
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )

    with pytest.raises(RuntimeError, match="idempotency conflict"):
        revise_draft_employer(
            session=cast(Session, session),
            principal=principal,
            command_id=command_id,
            employer_id=employer_id,
            expected_version=2,
            employer_type="household",
            display_name="Synthetic Conflicting Replay Payload",
            clock=FixedClock(now),
        )

    assert get_receipt_calls == 3
    assert session.rollback_count == 2
    assert session.commit_count == 0
