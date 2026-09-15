from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.worker_schemas import QueryWorkersRequest
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.query_workers import query_workers
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(uuid4(), "synthetic_staff", frozenset({"worker:read"}))


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name_query": "a"},
        {"name_query": "  "},
        {"name_query": "Fictional", "reference": str(uuid4())},
        {"reference": "invalid"},
        {"name_query": "Fictional", "page_size": True},
        {"name_query": "Fictional", "page_size": 51},
        {"name_query": "Fictional", "phone": "202-555-0151"},
        {"name_query": "Fictional", "cursor": "x" * 1025},
    ],
)
def test_worker_query_requires_one_bounded_identifying_filter(body):
    with pytest.raises(ValidationError):
        QueryWorkersRequest.model_validate(body)


def test_permission_denial_precedes_cursor_decode_and_lookup():
    session = Mock()
    with pytest.raises(IntakeError) as error:
        query_workers(
            session=session,
            principal=replace(PRINCIPAL, permissions=frozenset()),
            request=QueryWorkersRequest(name_query="Fictional", cursor="invalid"),
        )
    assert (error.value.code, error.value.status) == ("forbidden", 403)
    session.execute.assert_not_called()


def test_query_projects_minimal_fields_with_literal_match_and_scope():
    session = Mock()
    session.execute.return_value.mappings.return_value.all.return_value = []
    worker_id = uuid4()
    result = query_workers(
        session=session,
        principal=replace(PRINCIPAL, worker_scope=frozenset({worker_id})),
        request=QueryWorkersRequest(name_query=" A%_\\B ", page_size=7),
    )
    assert result == {"items": [], "next_cursor": None}
    statement = session.execute.call_args.args[0]
    assert set(statement.selected_columns.keys()) == {
        "worker_id",
        "full_name",
        "version",
        "created_at",
    }
    compiled = statement.compile()
    assert "%A\\%\\_\\\\B%" in compiled.params.values()
    assert [worker_id] in compiled.params.values()
    assert 8 in compiled.params.values()
    session.commit.assert_not_called()


def first_page() -> tuple[dict[str, Any], QueryWorkersRequest, list[dict[str, Any]]]:
    session = Mock()
    rows: list[dict[str, Any]] = [
        {
            "worker_id": uuid4(),
            "full_name": "Fictional Worker",
            "version": 1,
            "created_at": datetime(2026, 9, 14, tzinfo=UTC),
        }
        for _ in range(2)
    ]
    session.execute.return_value.mappings.return_value.all.return_value = rows
    request = QueryWorkersRequest(name_query="Fictional", page_size=1)
    result = query_workers(session=session, principal=PRINCIPAL, request=request)
    return result, request, rows


def test_pagination_cursor_carries_only_position_and_binding():
    result, request, rows = first_page()
    assert result["items"] == [{key: rows[0][key] for key in ("worker_id", "full_name", "version")}]
    assert result["next_cursor"]
    session = Mock()
    session.execute.return_value.mappings.return_value.all.return_value = []
    query_workers(
        session=session,
        principal=PRINCIPAL,
        request=request.model_copy(update={"cursor": result["next_cursor"]}),
    )
    compiled = session.execute.call_args.args[0].compile()
    assert rows[0]["worker_id"] in compiled.params.values()
    assert rows[0]["created_at"] in compiled.params.values()


@pytest.mark.parametrize("change", ["actor", "permissions", "scope", "filter", "size", "tamper"])
def test_cursor_cannot_cross_query_or_authority(change):
    result, request, _ = first_page()
    principal = PRINCIPAL
    cursor = result["next_cursor"]
    if change == "actor":
        principal = replace(principal, actor_id=uuid4())
    elif change == "permissions":
        principal = replace(principal, permissions=principal.permissions | {"worker_contact:read"})
    elif change == "scope":
        principal = replace(principal, worker_scope=frozenset())
    elif change == "filter":
        request = request.model_copy(update={"name_query": "Other"})
    elif change == "size":
        request = request.model_copy(update={"page_size": 2})
    else:
        cursor = ("A" if cursor[0] != "A" else "B") + cursor[1:]
    session = Mock()
    with pytest.raises(IntakeError) as error:
        query_workers(
            session=session,
            principal=principal,
            request=request.model_copy(update={"cursor": cursor}),
        )
    assert (error.value.code, error.value.status) == ("invalid_cursor", 422)
    session.execute.assert_not_called()
