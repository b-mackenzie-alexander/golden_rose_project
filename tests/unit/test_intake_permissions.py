from uuid import uuid4

import pytest

from golden_rose.application.intake_commands import authorize_intake
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal


def test_address_capture_requires_read_and_write_even_for_retry():
    actor = StaffPrincipal(
        uuid4(),
        "synthetic_staff",
        frozenset(
            {
                "intake:read",
                "intake:draft:revise",
                "worker_residence:write",
            }
        ),
    )
    with pytest.raises(IntakeError, match="forbidden"):
        authorize_intake(actor, "intake:draft:revise", "worker_residence")


def test_platform_administrator_has_no_implicit_intake_authority():
    actor = StaffPrincipal(uuid4(), "platform_administrator", frozenset())
    with pytest.raises(IntakeError, match="forbidden"):
        authorize_intake(actor, "intake:draft:create")
