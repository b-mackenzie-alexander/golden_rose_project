from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.read_worker import read_worker
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(
    uuid4(),
    "synthetic_staff",
    frozenset({"worker:read", "worker_contact:read", "worker_residence:read"}),
)


@pytest.mark.parametrize(
    "section,permission",
    [
        ("identity", "worker:read"),
        ("contact", "worker:read"),
        ("contact", "worker_contact:read"),
        ("residence", "worker:read"),
        ("residence", "worker_residence:read"),
        ("preferences", "worker:read"),
    ],
)
def test_worker_read_permission_denial_precedes_lookup(section, permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_worker(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            worker_id=uuid4(),
            section=section,
        )
    assert (error.value.code, error.value.status) == ("forbidden", 403)
    session.execute.assert_not_called()


@pytest.mark.parametrize("section", ["identity", "contact", "residence", "preferences"])
def test_worker_scope_denial_precedes_lookup(section):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_worker(
            session=session,
            principal=replace(PRINCIPAL, worker_scope=frozenset()),
            worker_id=uuid4(),
            section=section,
        )
    assert (error.value.code, error.value.status) == ("not_found", 404)
    session.execute.assert_not_called()


@pytest.mark.parametrize("section", ["identity", "contact", "residence", "preferences"])
def test_worker_missing_returns_safe_not_found(section):
    session = Mock()
    session.execute.return_value.mappings.return_value.one_or_none.return_value = None
    with pytest.raises(IntakeError) as error:
        read_worker(session=session, principal=PRINCIPAL, worker_id=uuid4(), section=section)
    assert (error.value.code, error.value.status) == ("not_found", 404)


def test_worker_read_storage_error_rolls_back_without_details():
    session = Mock()
    session.execute.side_effect = OperationalError("private-sql", {}, Exception("private-driver"))
    with pytest.raises(IntakeError) as error:
        read_worker(session=session, principal=PRINCIPAL, worker_id=uuid4(), section="identity")
    assert (error.value.code, error.value.status) == ("persistence_unavailable", 503)
    session.rollback.assert_called_once()
    assert "private" not in str(error.value)


def test_worker_identity_projection_excludes_sensitive_columns_and_writes():
    session = Mock()
    target = uuid4()
    row = {"worker_id": target}
    session.execute.return_value.mappings.return_value.one_or_none.return_value = row
    result = read_worker(
        session=session,
        principal=replace(PRINCIPAL, worker_scope=frozenset({target})),
        worker_id=target,
        section="identity",
    )
    assert result == row
    statement = session.execute.call_args.args[0]
    assert set(statement.selected_columns.keys()) == {
        "worker_id",
        "full_name",
        "version",
        "contact_id",
        "residence_id",
        "preferences_id",
        "created_at",
        "updated_at",
    }
    session.commit.assert_not_called()
    session.flush.assert_not_called()
