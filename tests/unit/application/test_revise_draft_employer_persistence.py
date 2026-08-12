from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Update

import golden_rose.application.revise_draft_employer as revise_module
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.auth.principal import StaffPrincipal


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class PersistenceProbeSession:
    def __init__(self, *, employer_id: UUID, actor_id: UUID, now: datetime) -> None:
        self.rollback_count = 0
        self.commit_count = 0
        self._current = ("household", "Synthetic Persistence Seed")
        self._updated = (
            employer_id,
            "business",
            "Synthetic Persistence Update",
            "draft",
            "staff_entry",
            now,
            now,
            now,
            actor_id,
            2,
        )

    def execute(self, statement):
        if isinstance(statement, Update):
            return RequiredRowResult(self._updated)
        return OptionalRowResult(self._current)

    def rollback(self) -> None:
        self.rollback_count += 1

    def commit(self) -> None:
        self.commit_count += 1


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


def _principal() -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=UUID("41414141-4141-4414-8414-414141414141"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:revise"}),
    )


def _call_revision(*, session: PersistenceProbeSession) -> None:
    revise_draft_employer(
        session=cast(Session, session),
        principal=_principal(),
        command_id=UUID("42424242-4242-4424-8424-424242424242"),
        employer_id=UUID("43434343-4343-4434-8434-434343434343"),
        expected_version=1,
        employer_type="business",
        display_name="Synthetic Persistence Update",
        clock=FixedClock(datetime(2026, 8, 11, 20, 20, 0, tzinfo=UTC)),
    )


def test_revision_receipt_lookup_database_failure_is_safe_and_rolls_back(monkeypatch) -> None:
    session = PersistenceProbeSession(
        employer_id=UUID("43434343-4343-4434-8434-434343434343"),
        actor_id=_principal().actor_id,
        now=datetime(2026, 8, 11, 20, 20, 0, tzinfo=UTC),
    )

    def raise_database_failure(**_kwargs):
        raise SQLAlchemyError("Synthetic receipt lookup database marker")

    monkeypatch.setattr(revise_module, "get_command_receipt", raise_database_failure)

    with pytest.raises(SafePersistenceError, match="^persistence operation failed$"):
        _call_revision(session=session)

    assert session.rollback_count == 1
    assert session.commit_count == 0


def test_revision_audit_insert_database_failure_is_safe_and_rolls_back(monkeypatch) -> None:
    session = PersistenceProbeSession(
        employer_id=UUID("43434343-4343-4434-8434-434343434343"),
        actor_id=_principal().actor_id,
        now=datetime(2026, 8, 11, 20, 20, 0, tzinfo=UTC),
    )

    def receipt_not_found(**_kwargs):
        raise NoResultFound

    def reserve_receipt(**_kwargs) -> bool:
        return True

    def raise_database_failure(**_kwargs) -> None:
        raise SQLAlchemyError("Synthetic audit insert database marker")

    monkeypatch.setattr(revise_module, "get_command_receipt", receipt_not_found)
    monkeypatch.setattr(revise_module, "reserve_revision_command_receipt", reserve_receipt)
    monkeypatch.setattr(
        revise_module, "insert_employer_draft_revised_event", raise_database_failure
    )

    with pytest.raises(SafePersistenceError, match="^persistence operation failed$"):
        _call_revision(session=session)

    assert session.rollback_count == 1
    assert session.commit_count == 0
