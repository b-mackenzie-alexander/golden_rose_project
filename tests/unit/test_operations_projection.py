from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.exc import SQLAlchemyError

from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.operations_projection import query_operations_projection
from golden_rose.auth.principal import StaffPrincipal

ACTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYER_ID = UUID("22222222-2222-4222-8222-222222222222")
INTAKE_ID = UUID("33333333-3333-4333-8333-333333333333")
REQUEST_ID = UUID("44444444-4444-4444-8444-444444444444")
SHIFT_ID = UUID("55555555-5555-4555-8555-555555555555")
NOW = datetime(2026, 9, 30, 14, 0, tzinfo=UTC)


class FakeResult:
    def __init__(self, value: Any = None) -> None:
        self.value = value

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> Any:
        return self.value


class FakeSession:
    def __init__(self, results: list[FakeResult | Exception]) -> None:
        self.results = list(results)
        self.rollbacks = 0
        self.executed: list[Any] = []

    def execute(self, statement: Any) -> FakeResult:
        self.executed.append(statement)
        if not self.results:
            return FakeResult([])
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def rollback(self) -> None:
        self.rollbacks += 1


def principal(*permissions: str) -> StaffPrincipal:
    return StaffPrincipal(ACTOR_ID, "operations_staff", frozenset(permissions))


def all_permissions() -> StaffPrincipal:
    return principal("employer:read", "staffing_request:read", "shift_need:read")


def test_operations_projection_requires_request_and_shift_read_permissions():
    with pytest.raises(IntakeError) as error:
        query_operations_projection(
            session=FakeSession([]),  # type: ignore[arg-type]
            principal=principal("employer:read", "staffing_request:read"),
        )

    assert error.value.status == 403


def test_operations_projection_returns_request_and_shift_items():
    request_row = {
        "source_intake_id": INTAKE_ID,
        "employer_id": EMPLOYER_ID,
        "employer_name": "Restaurante La Esperanza",
        "staffing_request_id": REQUEST_ID,
        "request_status": "pending_review",
        "role_title": "Line cook",
        "worker_count": 2,
        "version": 3,
        "received_at": NOW,
        "updated_at": NOW,
    }
    shift_row = {
        "source_intake_id": INTAKE_ID,
        "employer_id": EMPLOYER_ID,
        "employer_name": "Restaurante La Esperanza",
        "staffing_request_id": REQUEST_ID,
        "shift_need_id": SHIFT_ID,
        "request_status": "pending_review",
        "shift_status": "pending_review",
        "role_title": "Line cook",
        "worker_count": 1,
        "starts_at": NOW,
        "ends_at": datetime(2026, 9, 30, 18, 0, tzinfo=UTC),
        "time_zone": "America/New_York",
        "version": 2,
        "updated_at": NOW,
    }
    session = FakeSession([FakeResult([request_row]), FakeResult([shift_row])])

    result = query_operations_projection(
        session=session,  # type: ignore[arg-type]
        principal=all_permissions(),
        page_size=500,
    )

    assert result == {
        "request_items": [{"item_type": "staffing_request", **request_row}],
        "shift_items": [{"item_type": "shift_need", **shift_row}],
    }
    assert len(session.executed) == 2
    assert session.rollbacks == 0


def test_operations_projection_rolls_back_persistence_errors():
    session = FakeSession([SQLAlchemyError("database unavailable")])

    with pytest.raises(IntakeError) as error:
        query_operations_projection(
            session=session,  # type: ignore[arg-type]
            principal=all_permissions(),
        )

    assert error.value.status == 503
    assert session.rollbacks == 1
