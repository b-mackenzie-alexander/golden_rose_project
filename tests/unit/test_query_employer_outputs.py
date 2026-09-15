from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Literal, cast
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.exc import OperationalError

from golden_rose.api.staff.employer_output_schemas import QueryEmployerOutputsRequest
from golden_rose.application.intake_cursors import binding, encode_cursor
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.query_employer_outputs import query_employer_outputs
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(
    uuid4(),
    "synthetic_staff",
    frozenset({"employer:read", "party_address:read", "worksite:read", "staffing_request:read"}),
)


@pytest.mark.parametrize(
    "body",
    [
        {"page_size": 0},
        {"page_size": 51},
        {"page_size": True},
        {"cursor": "x" * 1025},
        {"name_query": "private"},
        {"address": "private"},
    ],
)
def test_query_contract_is_bounded(body):
    with pytest.raises(ValidationError):
        QueryEmployerOutputsRequest.model_validate(body)


@pytest.mark.parametrize(
    "kind,permission",
    [
        ("addresses", "party_address:read"),
        ("worksites", "worksite:read"),
        ("requests", "staffing_request:read"),
        ("requests", "employer:read"),
    ],
)
def test_permission_check_precedes_cursor_and_sql(kind, permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        query_employer_outputs(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            employer_id=uuid4(),
            kind=kind,
            request=QueryEmployerOutputsRequest(cursor="invalid"),
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


def page(kind="worksites") -> tuple[Any, ...]:
    session = Mock()
    parent = uuid4()
    id_name = {
        "addresses": "employer_address_id",
        "worksites": "worksite_id",
        "requests": "staffing_request_id",
    }[kind]
    rows = [
        {
            id_name: uuid4(),
            "employer_id": parent,
            "version": 1,
            "created_at": datetime(2026, 9, 14, tzinfo=UTC),
            **({"purpose": "business"} if kind == "addresses" else {}),
            **(
                {
                    "request_status": "draft",
                    "role_title": "Fictional",
                    "worker_count": 1,
                    "offer": {"minimum": "20", "per_worker": True},
                }
                if kind == "requests"
                else {}
            ),
        }
        for _ in range(2)
    ]
    session.execute.return_value.one_or_none.return_value = (parent,)
    session.execute.return_value.mappings.return_value.all.return_value = rows
    request = QueryEmployerOutputsRequest(page_size=1)
    result = query_employer_outputs(
        session=session, principal=PRINCIPAL, employer_id=parent, kind=kind, request=request
    )
    return session, parent, request, rows, result


@pytest.mark.parametrize("kind", ["addresses", "worksites", "requests"])
def test_projection_parent_limit_and_no_writes(kind):
    session, parent, _, rows, result = page(kind)
    assert result["next_cursor"]
    assert result["items"] == [{k: v for k, v in rows[0].items() if k != "created_at"}]
    statement = session.execute.call_args.args[0]
    assert parent in statement.compile().params.values()
    assert 2 in statement.compile().params.values()
    assert not {"line1", "phone", "duties_summary", "schedule"} & set(
        statement.selected_columns.keys()
    )
    session.commit.assert_not_called()


@pytest.mark.parametrize("change", ["parent", "kind", "size", "actor", "permissions", "tamper"])
def test_cursor_rejects_changed_binding_before_sql(change):
    _, parent, request, _, result = page()
    principal, cursor = PRINCIPAL, result["next_cursor"]
    kind: Literal["addresses", "worksites", "requests"] = "worksites"
    if change == "parent":
        parent = uuid4()
    elif change == "kind":
        kind = "addresses"
    elif change == "size":
        request = request.model_copy(update={"page_size": 2})
    elif change == "actor":
        principal = replace(principal, actor_id=uuid4())
    elif change == "permissions":
        principal = replace(principal, permissions=principal.permissions | {"extra:read"})
    else:
        cursor = "!" + cursor[1:]
    session = Mock()
    with pytest.raises(IntakeError) as error:
        query_employer_outputs(
            session=session,
            principal=principal,
            employer_id=parent,
            kind=kind,
            request=request.model_copy(update={"cursor": cursor}),
        )
    assert error.value.code == "invalid_cursor"
    session.execute.assert_not_called()


def test_cursor_applies_timestamp_and_uuid_boundary():
    session, parent, request, rows, result = page()
    query_employer_outputs(
        session=session,
        principal=PRINCIPAL,
        employer_id=parent,
        kind="worksites",
        request=request.model_copy(update={"cursor": result["next_cursor"]}),
    )
    params = session.execute.call_args.args[0].compile().params
    assert rows[0]["created_at"] in params.values()
    assert rows[0]["worksite_id"] in params.values()


def test_missing_parent_is_not_empty_list():
    session = Mock()
    session.execute.return_value.one_or_none.return_value = None
    with pytest.raises(IntakeError) as error:
        query_employer_outputs(
            session=session,
            principal=PRINCIPAL,
            employer_id=uuid4(),
            kind="worksites",
            request=QueryEmployerOutputsRequest(),
        )
    assert error.value.status == 404
    assert session.execute.call_count == 1


@pytest.mark.parametrize("stage", ["parent", "children"])
def test_storage_failure_rolls_back_safely(stage):
    session = Mock()
    failure = OperationalError("private", {}, Exception("private"))
    if stage == "parent":
        session.execute.side_effect = failure
    else:
        parent = Mock()
        parent.one_or_none.return_value = (uuid4(),)
        session.execute.side_effect = [parent, failure]
    with pytest.raises(IntakeError) as error:
        query_employer_outputs(
            session=session,
            principal=PRINCIPAL,
            employer_id=uuid4(),
            kind="requests",
            request=QueryEmployerOutputsRequest(),
        )
    assert error.value.status == 503
    session.rollback.assert_called_once()
    assert "private" not in str(error.value)


def test_request_offer_terms_removed_by_sql():
    session, _, _, _, _ = page("requests")
    compiled = session.execute.call_args.args[0].compile(
        dialect=cast(Callable[[], Dialect], postgresql.dialect)()
    )
    assert "offer - " in str(compiled)
    assert "terms" in compiled.params.values()


@pytest.mark.parametrize(
    "position",
    [
        {},
        {"at": "invalid", "id": str(uuid4())},
        {"at": "2026-09-14T00:00:00", "id": str(uuid4())},
        {"at": "2026-09-14T00:00:00+00:00", "id": "invalid"},
    ],
)
def test_signed_invalid_boundary_rejected_before_lookup(position):
    parent = uuid4()
    bound = binding(
        PRINCIPAL,
        {
            "kind": "canonical_employer_worksites",
            "parent": str(parent),
            "order": "created_at_desc_id_desc",
            "scope": "shared_synthetic_employers",
            "query": {"page_size": 25},
        },
    )
    session = Mock()
    with pytest.raises(IntakeError) as error:
        query_employer_outputs(
            session=session,
            principal=PRINCIPAL,
            employer_id=parent,
            kind="worksites",
            request=QueryEmployerOutputsRequest(cursor=encode_cursor(bound, position)),
        )
    assert error.value.code == "invalid_cursor"
    session.execute.assert_not_called()
