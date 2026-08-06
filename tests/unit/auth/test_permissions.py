from uuid import uuid4

from golden_rose.auth.permissions import (
    EMPLOYER_READ_PERMISSION,
    can_create_draft_employer,
    can_read_employer,
)
from golden_rose.auth.principal import StaffPrincipal


def test_principal_with_draft_permission_is_allowed() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )

    assert can_create_draft_employer(principal) is True


def test_employer_read_permission_constant_has_exact_value() -> None:
    assert EMPLOYER_READ_PERMISSION == "employer:read"


def test_principal_with_read_permission_is_allowed() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset({EMPLOYER_READ_PERMISSION}),
    )

    assert can_read_employer(principal) is True


def test_principal_without_read_permission_is_denied() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset(),
    )

    assert can_read_employer(principal) is False


def test_role_labels_do_not_grant_read_permission() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="owner",
        permissions=frozenset({"system:health:read"}),
    )

    assert can_read_employer(principal) is False


def test_principal_without_draft_permission_is_denied() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset(),
    )

    assert can_create_draft_employer(principal) is False


def test_platform_role_label_without_named_permission_is_denied() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="platform_administrator",
        permissions=frozenset({"system:health:read"}),
    )

    assert can_create_draft_employer(principal) is False


def test_principal_actor_id_is_uuid_data_and_not_request_supplied() -> None:
    actor_id = uuid4()
    principal = StaffPrincipal(
        actor_id=actor_id,
        role_name="owner",
        permissions=frozenset({"employer:draft:create"}),
    )

    assert principal.actor_id == actor_id
    assert isinstance(principal.actor_id, type(actor_id))
    assert not hasattr(principal, "headers")
    assert not hasattr(principal, "request_body")
