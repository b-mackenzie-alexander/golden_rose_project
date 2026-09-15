from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import OperationalError

from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.read_employer_output import read_employer_output
from golden_rose.auth.principal import StaffPrincipal

PRINCIPAL = StaffPrincipal(
    uuid4(),
    "synthetic_staff",
    frozenset(
        {
            "employer:read",
            "party_address:read",
            "worksite:read",
            "worksite_address:read",
            "staffing_request:read",
        }
    ),
)
SECTIONS = ["business_address", "worksite", "worksite_address", "request"]


@pytest.mark.parametrize(
    "section,permission",
    [
        *[(section, "employer:read") for section in SECTIONS],
        ("business_address", "party_address:read"),
        ("worksite", "worksite:read"),
        ("worksite_address", "worksite:read"),
        ("worksite_address", "worksite_address:read"),
        ("request", "staffing_request:read"),
    ],
)
def test_denial_precedes_lookup(section, permission):
    session = Mock()
    with pytest.raises(IntakeError) as error:
        read_employer_output(
            session=session,
            principal=replace(PRINCIPAL, permissions=PRINCIPAL.permissions - {permission}),
            employer_id=uuid4(),
            output_id=uuid4(),
            section=section,
        )
    assert error.value.status == 403
    session.execute.assert_not_called()


@pytest.mark.parametrize("section", SECTIONS)
def test_missing_is_safe(section):
    session = Mock()
    session.execute.return_value.mappings.return_value.one_or_none.return_value = None
    with pytest.raises(IntakeError) as error:
        read_employer_output(
            session=session,
            principal=PRINCIPAL,
            employer_id=uuid4(),
            output_id=uuid4(),
            section=section,
        )
    assert error.value.status == 404


@pytest.mark.parametrize("section", SECTIONS)
def test_parent_scoped_select_and_no_writes(section):
    session = Mock()
    employer_id, output_id = uuid4(), uuid4()
    row = (
        {
            "line1": "Fictional",
            "line2": None,
            "locality": "City",
            "region": "NY",
            "postal_code": "10001",
            "country": "US",
        }
        if "address" in section
        else {}
    )
    session.execute.return_value.mappings.return_value.one_or_none.return_value = row
    result = read_employer_output(
        session=session,
        principal=PRINCIPAL,
        employer_id=employer_id,
        output_id=output_id,
        section=section,
    )
    statement = session.execute.call_args.args[0]
    assert {employer_id, output_id, "draft"} <= set(statement.compile().params.values())
    if "address" not in section:
        assert not {"phone", "line1", "line2", "postal_code"} & set(
            statement.selected_columns.keys()
        )
    else:
        assert result["address"]["line1"] == "Fictional"
        assert "line2" not in result["address"]
    session.commit.assert_not_called()
    session.flush.assert_not_called()


def test_storage_error_is_safe():
    session = Mock()
    session.execute.side_effect = OperationalError("private", {}, Exception("private"))
    with pytest.raises(IntakeError) as error:
        read_employer_output(
            session=session,
            principal=PRINCIPAL,
            employer_id=uuid4(),
            output_id=uuid4(),
            section="request",
        )
    assert error.value.status == 503
    session.rollback.assert_called_once()
