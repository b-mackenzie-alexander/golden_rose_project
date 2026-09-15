from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Session

from golden_rose.application.intake_errors import IntakeError
from golden_rose.persistence.intake_links import (
    CHILDREN,
    PARTIES,
    get_link_dependencies,
    write_link_dependencies,
)


@pytest.mark.parametrize("linked", [True, False])
def test_reference_writes_never_change_candidate_or_canonical_facts(linked):
    session = Mock(spec=Session)
    worker_id = uuid4()
    dependencies = {"worker": {"id": str(worker_id), "version": 1}} if linked else {}
    write_link_dependencies(
        session,
        intake_id=uuid4(),
        dependencies=dependencies,
        version=3,
        content_version=2,
        updated_at=datetime(2026, 9, 14, tzinfo=UTC),
        updated_by=uuid4(),
    )
    statements = [call.args[0] for call in session.execute.call_args_list]
    assert [statement.table.name for statement in statements] == ["intakes", "intake_links"]
    compiled = [
        statement.compile(dialect=cast(Callable[[], Dialect], postgresql.dialect)())
        for statement in statements
    ]
    assert "content" not in compiled[0].params
    assert compiled[0].params["worker_id"] == (worker_id if linked else None)
    assert compiled[0].params["employer_id"] is None
    assert compiled[0].params["content_version"] == 2
    for name in CHILDREN:
        assert compiled[1].params[f"{name}_id"] is None
        assert compiled[1].params[f"{name}_version"] is None
    assert ("ON CONFLICT" in str(compiled[1])) == linked
    if linked:
        assert "IS DISTINCT FROM" in str(compiled[1]).split("ON CONFLICT", 1)[1]
    assert "DELETE" not in str(compiled[1])
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_read_normalizes_stored_references_without_writes():
    session = Mock(spec=Session)
    row: dict[str, Any] = {
        f"{name}_{suffix}": None for name in PARTIES + CHILDREN for suffix in ("id", "version")
    }
    worker_id = uuid4()
    row.update(worker_id=worker_id, worker_version=3)
    session.execute.return_value.mappings.return_value.one_or_none.return_value = row
    assert get_link_dependencies(session, uuid4()) == {
        "worker": {"id": str(worker_id), "version": 3}
    }
    assert session.execute.call_args.args[0].is_select
    session.commit.assert_not_called()


def test_partial_reference_fails_closed():
    session = Mock(spec=Session)
    row: dict[str, Any] = {
        f"{name}_{suffix}": None for name in PARTIES + CHILDREN for suffix in ("id", "version")
    }
    row["worker_id"] = uuid4()
    session.execute.return_value.mappings.return_value.one_or_none.return_value = row
    with pytest.raises(IntakeError) as error:
        get_link_dependencies(session, uuid4())
    assert error.value.status == 503
