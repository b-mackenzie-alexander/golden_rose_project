from collections.abc import Callable
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from golden_rose.application.create_draft_employer import create_draft_employer
from golden_rose.application.create_employer_contact import create_employer_contact
from golden_rose.application.revise_draft_employer import revise_draft_employer
from golden_rose.application.synthetic_data import SyntheticDataAdmissionError
from golden_rose.auth.permissions import (
    CREATE_DRAFT_EMPLOYER_PERMISSION,
    EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
    EMPLOYER_DRAFT_REVISE_PERMISSION,
    EMPLOYER_READ_PERMISSION,
)
from golden_rose.auth.principal import StaffPrincipal


class NoDatabaseSession:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"database access occurred through {name}")


class NoClock:
    def now(self) -> Any:
        raise AssertionError("clock accessed before synthetic admission")


class NoIdentifiers:
    def new_uuid4(self) -> UUID:
        raise AssertionError("identifier allocated before synthetic admission")


def _principal() -> StaffPrincipal:
    return StaffPrincipal(
        actor_id=uuid4(),
        role_name="synthetic_staff",
        permissions=frozenset(
            {
                CREATE_DRAFT_EMPLOYER_PERMISSION,
                EMPLOYER_READ_PERMISSION,
                EMPLOYER_DRAFT_REVISE_PERMISSION,
                EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
            }
        ),
    )


def test_develop_rejects_plausible_live_employer_and_contact_values_before_any_write() -> None:
    session = cast(Session, NoDatabaseSession())
    principal = _principal()

    calls: list[Callable[[], object]] = [
        lambda: create_draft_employer(
            session=session,
            principal=principal,
            command_id=uuid4(),
            employer_type="business",
            display_name="Acme Staffing",
            clock=NoClock(),
            identifiers=NoIdentifiers(),
            environment="develop",
        ),
        lambda: revise_draft_employer(
            session=session,
            principal=principal,
            command_id=uuid4(),
            employer_id=uuid4(),
            expected_version=1,
            employer_type="business",
            display_name="Jane Smith Household",
            clock=NoClock(),
            environment="develop",
        ),
        lambda: create_employer_contact(
            session=session,
            principal=principal,
            employer_id=uuid4(),
            command_id=uuid4(),
            full_name="John Smith",
            clock=NoClock(),
            identifiers=NoIdentifiers(),
            environment="develop",
        ),
    ]

    for call in calls:
        with pytest.raises(
            SyntheticDataAdmissionError,
            match="develop accepts only generated fictional synthetic values",
        ) as exc:
            call()
        assert "Acme" not in str(exc.value)
        assert "Jane" not in str(exc.value)
        assert "John" not in str(exc.value)


def test_develop_accepts_only_bounded_generated_synthetic_value_shapes() -> None:
    from golden_rose.application.synthetic_data import require_develop_synthetic_value

    require_develop_synthetic_value(
        environment="develop",
        field="employer_display_name",
        value="Synthetic Qual Employer 1a2b3c4d",
    )
    require_develop_synthetic_value(
        environment="develop",
        field="employer_display_name",
        value="Synthetic Demo Employer 1a2b3c4d Revised",
    )
    require_develop_synthetic_value(
        environment="develop",
        field="contact_full_name",
        value="Synthetic Contact 1a2b3c4d",
    )
    require_develop_synthetic_value(
        environment="local",
        field="employer_display_name",
        value="Any local fictional fixture",
    )
