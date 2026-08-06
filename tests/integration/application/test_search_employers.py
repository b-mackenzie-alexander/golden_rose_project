from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import golden_rose.application.search_employers as search_employers_module
from golden_rose.api.staff.schemas import SearchEmployersRequest
from golden_rose.application.create_draft_employer import create_draft_employer
from golden_rose.application.errors import SafePersistenceError
from golden_rose.application.search_employers import search_employers
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


def test_permitted_search_returns_page_and_next_cursor(session, clean_tables) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("51515151-5151-4151-8151-515151515151"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create", "employer:read"}),
    )
    first_employer_id = UUID("52525252-5252-4252-8252-525252525252")
    second_employer_id = UUID("53535353-5353-4353-8353-535353535353")
    first_audit_event_id = UUID("54545454-5454-4454-8454-545454545454")
    second_audit_event_id = UUID("55555555-5555-4555-8555-555555555555")

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("56565656-5656-4656-8656-565656565656"),
        employer_type="business",
        display_name="Rose Market Care",
        clock=FixedClock(datetime(2026, 8, 5, 1, 0, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(first_employer_id, first_audit_event_id),
    )
    create_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("57575757-5757-4757-8757-575757575757"),
        employer_type="business",
        display_name="Golden Rose Staffing",
        clock=FixedClock(datetime(2026, 8, 5, 2, 0, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(second_employer_id, second_audit_event_id),
    )

    page = search_employers(
        session=session,
        principal=principal,
        request=SearchEmployersRequest(display_name_query="rose", page_size=1),
    )

    assert len(page.items) == 1
    assert page.items[0].employer_id == second_employer_id
    assert page.items[0].display_name == "Golden Rose Staffing"
    assert not hasattr(page.items[0], "created_by")
    assert not hasattr(page.items[0], "created_at")
    assert not hasattr(page.items[0], "source_channel")
    assert page.next_cursor is not None


def test_persistence_failure_rolls_back_once_and_raises_safe_error(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("58585858-5858-4858-8858-585858585858"),
        role_name="operations_staff",
        permissions=frozenset({"employer:read"}),
    )
    rollback_calls = 0
    original_rollback = session.rollback

    def counting_rollback() -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        original_rollback()

    def fail_execute(*args: object, **kwargs: object) -> None:
        raise SQLAlchemyError("driver details should not escape")

    monkeypatch.setattr(session, "rollback", counting_rollback)
    monkeypatch.setattr(session, "execute", fail_execute)

    with pytest.raises(SafePersistenceError, match="persistence operation failed"):
        search_employers(
            session=session,
            principal=principal,
            request=SearchEmployersRequest(display_name_query="rose"),
        )

    assert rollback_calls == 1


def test_denied_search_never_decodes_fingerprints_or_queries(monkeypatch) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("59595959-5959-4959-8959-595959595959"),
        role_name="operations_staff",
        permissions=frozenset(),
    )
    decode_calls = 0
    query_calls = 0

    def fail_decode(*args: object, **kwargs: object) -> None:
        nonlocal decode_calls
        decode_calls += 1
        raise AssertionError("cursor decode should not be called")

    def fail_execute(*args: object, **kwargs: object) -> None:
        nonlocal query_calls
        query_calls += 1
        raise AssertionError("query should not be called")

    monkeypatch.setattr(search_employers_module, "decode_search_cursor", fail_decode)

    class DeniedSessionProbe:
        def execute(self, *args: object, **kwargs: object) -> None:
            fail_execute(*args, **kwargs)

    denied_session = cast(Session, DeniedSessionProbe())

    with pytest.raises(PermissionError, match="principal lacks employer:read"):
        search_employers(
            session=denied_session,
            principal=principal,
            request=SearchEmployersRequest(display_name_query="rose", cursor="bad-cursor"),
        )

    assert decode_calls == 0
    assert query_calls == 0


def test_search_normalizes_decomposed_query_after_authorization(
    session,
    clean_tables,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("60606060-6060-4060-8060-606060606060"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create", "employer:read"}),
    )
    employer_id = UUID("61616161-6161-4161-8161-616161616161")
    audit_event_id = UUID("62626262-6262-4262-8262-626262626262")

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("63636363-6363-4363-8363-636363636363"),
        employer_type="business",
        display_name="Café Rose Staffing",
        clock=FixedClock(datetime(2026, 8, 5, 3, 0, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    page = search_employers(
        session=session,
        principal=principal,
        request=SearchEmployersRequest(display_name_query="Cafe\u0301"),
    )

    assert [item.employer_id for item in page.items] == [employer_id]
    assert page.items[0].display_name == "Café Rose Staffing"


def test_role_label_without_permission_remains_denied() -> None:
    principal = StaffPrincipal(
        actor_id=UUID("64646464-6464-4464-8464-646464646464"),
        role_name="platform_administrator",
        permissions=frozenset(),
    )

    class DeniedSessionProbe:
        def execute(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("query should not be called")

    with pytest.raises(PermissionError, match="principal lacks employer:read"):
        search_employers(
            session=cast(Session, DeniedSessionProbe()),
            principal=principal,
            request=SearchEmployersRequest(display_name_query="rose"),
        )


def test_successful_queries_perform_no_writes_or_transaction_control(
    session,
    clean_tables,
    monkeypatch,
) -> None:
    principal = StaffPrincipal(
        actor_id=UUID("65656565-6565-4565-8565-656565656565"),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create", "employer:read"}),
    )
    employer_id = UUID("66666666-6666-4666-8666-666666666666")
    audit_event_id = UUID("67676767-6767-4767-8767-676767676767")

    create_draft_employer(
        session=session,
        principal=principal,
        command_id=UUID("68686868-6868-4868-8868-686868686868"),
        employer_type="business",
        display_name="Golden Rose Read Only",
        clock=FixedClock(datetime(2026, 8, 5, 4, 0, 0, tzinfo=UTC)),
        identifiers=FixedIdentifierFactory(employer_id, audit_event_id),
    )

    baseline_counts = {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
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

    page = search_employers(
        session=session,
        principal=principal,
        request=SearchEmployersRequest(display_name_query="rose"),
    )

    assert [item.employer_id for item in page.items] == [employer_id]
    assert {
        "employers": session.execute(text("SELECT COUNT(*) FROM employers")).scalar_one(),
        "command_receipts": session.execute(
            text("SELECT COUNT(*) FROM command_receipts")
        ).scalar_one(),
        "audit_events": session.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one(),
    } == baseline_counts
