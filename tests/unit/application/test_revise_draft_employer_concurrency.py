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
