from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.read_contact_details import read_contact_details
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(
    uuid4(),
    "synthetic_staff",
    frozenset(
        {
            "employer:read",
            "employer_contact:read",
            "employer_contact:details:read",
            "party_address:read",
        }
    ),
)


@pytest.mark.parametrize("address", [False, True])
@pytest.mark.parametrize(
    "permission", ["employer:read", "employer_contact:read", "employer_contact:details:read"]
)
def test_permissions_precede_lookup(address, permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_contact_details(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            employer_id=uuid4(),
            contact_id=uuid4(),
            address=address,
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


def test_address_permission_precedes_lookup():
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_contact_details(
            session=session,
            principal=replace(
                PRINCIPAL, permissions=PRINCIPAL.permissions - {"party_address:read"}
            ),
            employer_id=uuid4(),
            contact_id=uuid4(),
            address=True,
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


@pytest.mark.parametrize("address", [False, True])
def test_missing_details_are_not_found(address):
    session = Mock()
    session.execute.return_value.mappings.return_value.one_or_none.return_value = None
    with pytest.raises(IntakeError) as error:
        read_contact_details(
            session=session,
            principal=PRINCIPAL,
            employer_id=uuid4(),
            contact_id=uuid4(),
            address=address,
        )
    assert error.value.status == 404


def test_phone_projection_is_parent_scoped_without_address_or_writes():
    session = Mock()
    session.execute.return_value.mappings.return_value.one_or_none.return_value = {}
    employer_id, contact_id = uuid4(), uuid4()
    read_contact_details(
        session=session, principal=PRINCIPAL, employer_id=employer_id, contact_id=contact_id
    )
    statement = session.execute.call_args.args[0]
    assert set(statement.selected_columns.keys()) == {
        "contact_details_id",
        "employer_id",
        "employer_contact_id",
        "version",
        "phone",
    }
    assert {employer_id, contact_id, "draft"} <= set(statement.compile().params.values())
    session.commit.assert_not_called()
    session.flush.assert_not_called()


def test_storage_failure_is_safe():
    session = Mock()
    session.execute.side_effect = OperationalError("private", {}, Exception("private"))
    with pytest.raises(IntakeError) as error:
        read_contact_details(
            session=session, principal=PRINCIPAL, employer_id=uuid4(), contact_id=uuid4()
        )
    assert error.value.status == 503
    session.rollback.assert_called_once()
