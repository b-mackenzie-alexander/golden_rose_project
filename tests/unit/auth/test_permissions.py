from uuid import uuid4

from golden_rose.auth.permissions import (
    EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION,
    EMPLOYER_CONTACT_READ_PERMISSION,
    EMPLOYER_DRAFT_REVISE_PERMISSION,
    EMPLOYER_READ_PERMISSION,
    STAFF_ACCOUNT_ACTIVATE_PERMISSION,
    STAFF_ACCOUNT_CREATE_PERMISSION,
    STAFF_ACCOUNT_DEPROVISION_PERMISSION,
    STAFF_ACCOUNT_READ_PERMISSION,
    STAFF_ACCOUNT_RECOVERY_RECORD_PERMISSION,
    STAFF_ACCOUNT_SESSION_REVOKE_PERMISSION,
    STAFF_ACCOUNT_SUSPEND_PERMISSION,
    can_activate_staff_account,
    can_create_draft_employer,
    can_create_draft_employer_contact,
    can_create_staff_account,
    can_deprovision_staff_account,
    can_read_employer,
    can_read_employer_contact,
    can_read_staff_account,
    can_record_staff_account_recovery,
    can_revise_draft_employer,
    can_revoke_staff_account_sessions,
    can_suspend_staff_account,
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


def test_employer_draft_revise_permission_constant_has_exact_value() -> None:
    assert EMPLOYER_DRAFT_REVISE_PERMISSION == "employer:draft:revise"


def test_principal_with_revision_permission_is_allowed() -> None:
    principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset({EMPLOYER_DRAFT_REVISE_PERMISSION}),
    )

    assert can_revise_draft_employer(principal) is True


def test_read_or_create_permission_does_not_imply_revision_permission() -> None:
    read_only_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset({EMPLOYER_READ_PERMISSION}),
    )
    create_only_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset({"employer:draft:create"}),
    )
    read_and_create_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="operations_staff",
        permissions=frozenset({EMPLOYER_READ_PERMISSION, "employer:draft:create"}),
    )

    assert can_revise_draft_employer(read_only_principal) is False
    assert can_revise_draft_employer(create_only_principal) is False
    assert can_revise_draft_employer(read_and_create_principal) is False


def test_owner_or_platform_role_label_does_not_grant_revision_permission() -> None:
    owner_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="owner",
        permissions=frozenset({"system:health:read"}),
    )
    platform_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="platform_administrator",
        permissions=frozenset({"system:health:read"}),
    )

    assert can_revise_draft_employer(owner_principal) is False
    assert can_revise_draft_employer(platform_principal) is False


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


def test_employer_contact_permission_constants_have_exact_values_and_do_not_follow_role_labels(  # noqa: E501
) -> None:
    owner_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="owner",
        permissions=frozenset({"system:health:read"}),
    )
    platform_principal = StaffPrincipal(
        actor_id=uuid4(),
        role_name="platform_administrator",
        permissions=frozenset({"system:health:read"}),
    )

    assert EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION == "employer_contact:draft:create"
    assert EMPLOYER_CONTACT_READ_PERMISSION == "employer_contact:read"
    assert can_create_draft_employer_contact(owner_principal) is False
    assert can_read_employer_contact(owner_principal) is False
    assert can_create_draft_employer_contact(platform_principal) is False
    assert can_read_employer_contact(platform_principal) is False


def test_staff_account_permission_constants_have_exact_values_and_require_named_grants() -> None:
    owner_with_labels_only = StaffPrincipal(
        actor_id=uuid4(),
        role_name="owner",
        permissions=frozenset({"system:health:read"}),
    )
    account_admin = StaffPrincipal(
        actor_id=uuid4(),
        role_name="owner",
        permissions=frozenset(
            {
                STAFF_ACCOUNT_CREATE_PERMISSION,
                STAFF_ACCOUNT_ACTIVATE_PERMISSION,
                STAFF_ACCOUNT_SUSPEND_PERMISSION,
                STAFF_ACCOUNT_DEPROVISION_PERMISSION,
                STAFF_ACCOUNT_READ_PERMISSION,
                STAFF_ACCOUNT_RECOVERY_RECORD_PERMISSION,
                STAFF_ACCOUNT_SESSION_REVOKE_PERMISSION,
            }
        ),
    )

    assert STAFF_ACCOUNT_CREATE_PERMISSION == "staff_account:create"
    assert STAFF_ACCOUNT_ACTIVATE_PERMISSION == "staff_account:activate"
    assert STAFF_ACCOUNT_SUSPEND_PERMISSION == "staff_account:suspend"
    assert STAFF_ACCOUNT_DEPROVISION_PERMISSION == "staff_account:deprovision"
    assert STAFF_ACCOUNT_READ_PERMISSION == "staff_account:read"
    assert STAFF_ACCOUNT_RECOVERY_RECORD_PERMISSION == "staff_account:recovery:record"
    assert STAFF_ACCOUNT_SESSION_REVOKE_PERMISSION == "staff_account:session:revoke"
    assert can_create_staff_account(owner_with_labels_only) is False
    assert can_activate_staff_account(owner_with_labels_only) is False
    assert can_suspend_staff_account(owner_with_labels_only) is False
    assert can_deprovision_staff_account(owner_with_labels_only) is False
    assert can_read_staff_account(owner_with_labels_only) is False
    assert can_record_staff_account_recovery(owner_with_labels_only) is False
    assert can_revoke_staff_account_sessions(owner_with_labels_only) is False
    assert can_create_staff_account(account_admin) is True
    assert can_activate_staff_account(account_admin) is True
    assert can_suspend_staff_account(account_admin) is True
    assert can_deprovision_staff_account(account_admin) is True
    assert can_read_staff_account(account_admin) is True
    assert can_record_staff_account_recovery(account_admin) is True
    assert can_revoke_staff_account_sessions(account_admin) is True
