"""PostgreSQL shared recovery and authority-bound pagination."""

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from golden_rose.api.staff.intake_schemas import CreateIntakeRequest, QueryIntakesRequest
from golden_rose.application.intake_commands import execute_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.query_intakes import query_intakes
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(
    UUID("22222222-2222-4222-8222-222222222222"),
    "test",
    frozenset({"intake:read", "intake:draft:create"}),
)


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 9, 14, tzinfo=UTC)


@pytest.fixture
def drafts(clean_tables, engine):
    ids = []
    with Session(engine) as session:
        for number in range(3):
            result, _ = execute_intake(
                session=session,
                principal=PRINCIPAL,
                command_id=uuid4(),
                request=CreateIntakeRequest.model_validate(
                    {"kind": "worker", "content": {"phone": f"+1202555012{number}"}}
                ),
                clock=Clock(),
            )
            ids.append(result["current"]["summary"]["intake_id"])
    return ids


def query(session: Session, principal: StaffPrincipal = PRINCIPAL, **values: Any) -> dict[str, Any]:
    return query_intakes(
        session=session,
        principal=principal,
        request=QueryIntakesRequest.model_validate({"kind": "worker", **values}),
    )


def test_new_session_recovers_unnamed_shared_drafts_without_read_writes(drafts, engine):
    with Session(engine) as session:
        before = session.execute(text("SELECT count(*) FROM audit_events")).scalar_one()
        other = replace(PRINCIPAL, actor_id=uuid4())
        first = query(session, other, page_size=2)
        second = query(session, other, page_size=2, cursor=first["next_cursor"])
        items = first["items"] + second["items"]
        assert {item["intake_id"] for item in items} == set(drafts)
        assert len(items) == 3 and second["next_cursor"] is None
        assert all("display_name" not in item and "phone" not in item for item in items)
        assert query(session, other, reference=drafts[0])["items"][0]["intake_id"] == drafts[0]
        assert query(session, other, name_query="Fictional")["items"] == []
        assert session.execute(text("SELECT count(*) FROM audit_events")).scalar_one() == before


@pytest.mark.parametrize(
    "change",
    ["actor", "scope", "permissions", "page_size", "kind", "lifecycle", "filter", "tamper"],
)
def test_cursor_rejects_changed_authority_or_query(drafts, session, change):
    cursor = query(session, page_size=1)["next_cursor"]
    principal, values = PRINCIPAL, {"page_size": 1, "cursor": cursor}
    if change == "actor":
        principal = replace(principal, actor_id=uuid4())
    elif change == "scope":
        principal = replace(principal, intake_scope=frozenset(UUID(value) for value in drafts))
    elif change == "permissions":
        principal = replace(principal, permissions=frozenset({"intake:read"}))
    elif change == "page_size":
        values["page_size"] = 2
    elif change == "kind":
        values["kind"] = "employer"
    elif change == "lifecycle":
        values["lifecycle"] = "finalized"
    elif change == "filter":
        values["name_query"] = "Fictional"
    else:
        values["cursor"] = ("A" if cursor[0] != "A" else "B") + cursor[1:]
    with pytest.raises(IntakeError) as error:
        query_intakes(
            session=session,
            principal=principal,
            request=QueryIntakesRequest.model_validate({"kind": "worker", **values}),
        )
    assert error.value.code == "invalid_cursor" and error.value.status == 422


def test_finite_scope_limits_query_and_reference(drafts, session):
    principal = replace(PRINCIPAL, intake_scope=frozenset({UUID(drafts[0])}))
    assert [item["intake_id"] for item in query(session, principal)["items"]] == [drafts[0]]
    assert query(session, principal, reference=drafts[1])["items"] == []
    assert query(session, replace(principal, intake_scope=frozenset()))["items"] == []


def test_query_database_failure_rolls_back_and_raises_safe_error(clean_tables, engine):
    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError

    def fail_query(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("SELECT intakes.intake_id"):
            raise OperationalError(statement, {}, RuntimeError("fictional failure"))

    event.listen(engine, "before_cursor_execute", fail_query)
    try:
        with Session(engine) as session, pytest.raises(IntakeError) as error:
            query(session)
        assert error.value.code == "persistence_unavailable"
    finally:
        event.remove(engine, "before_cursor_execute", fail_query)
