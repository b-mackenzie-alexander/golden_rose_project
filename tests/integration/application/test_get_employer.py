from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

import golden_rose.application.get_employer as get_employer_module
from golden_rose.application.create_draft_employer import create_draft_employer
from golden_rose.application.errors import EmployerNotFoundError
from golden_rose.application.get_employer import get_employer
from golden_rose.auth.principal import StaffPrincipal


@dataclass(frozen=True)
class FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class FixedIdentifierFactory:
    def __init__(self, *identifiers: UUID) -> None:
        self._identifiers = list(identifiers)

    def new_uuid4(self) -> UUID:
        return self._identifiers.pop(0)


def test_permitted_get_returns_current_minimized_employer(session, clean_tables) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("42424242-4242-4242-8242-424242424242"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create", "employer:read"}),
    )
    command_id = UUID("43434343-4343-4343-8343-434343434343")
    employer_id = UUID("44444444-4444-4444-8444-444444444444")
    audit_event_id = UUID("45454545-4545-4545-8545-454545454545")
    fixed_now = datetime(2026, 8, 5, 1, 0, 0, tzinfo=UTC)

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=command_id,
        employer_type="household",
        display_name="Synthetic Read Household",
        clock=FixedClock(fixed_now),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    employer = get_employer(
        session=session,
        principal=principal,
        employer_id=employer_id,
    )

    assert employer.employer_id == employer_id
    assert employer.employer_type == "household"
    assert employer.display_name == "Synthetic Read Household"
    assert employer.lifecycle_status == "draft"
    assert employer.source_channel == "staff_entry"
    assert employer.received_at == fixed_now
    assert employer.created_at == fixed_now
    assert employer.version == 1
    assert not hasattr(employer, "created_by")


def test_missing_get_raises_nonreflective_not_found(session, clean_tables) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("46464646-4646-4646-8646-464646464646"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read"}),
    )

    with pytest.raises(EmployerNotFoundError, match="employer not found"):
        get_employer(
            session=session,
            principal=principal,
            employer_id=UUID("47474747-4747-4747-8747-474747474747"),
        )


def test_denied_get_never_calls_persistence(monkeypatch) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("48484848-4848-4848-8848-484848484848"),
        role_name="operations_staff",
        permissions=frozenset(),
    )
    persistence_calls = 0

    def fail_if_called(**_: object) -> None:
        nonlocal persistence_calls
        persistence_calls += 1
        raise AssertionError("persistence should not be called")

    monkeypatch.setattr(get_employer_module, "get_employer_by_id", fail_if_called)

    with pytest.raises(PermissionError, match="principal lacks employer:read"):
        get_employer(
            session=cast(Session, None),
            principal=principal,
            employer_id=UUID("49494949-4949-4949-8949-494949494949"),
        )

    assert persistence_calls == 0
