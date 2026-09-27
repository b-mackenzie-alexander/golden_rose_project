from uuid import uuid4

import pytest

from golden_rose.auth.staff_accounts import StaffAccount, StaffDelegation


def test_active_mfa_ready_staff_account_becomes_principal() -> None:
    intake_id = uuid4()
    account = StaffAccount(
        staff_id=uuid4(),
        provider_subject="oidc:staff:123",
        display_name="Mariela Torres",
        role_name="operations_staff",
        status="active",
        permissions=frozenset({"intake:review"}),
        mfa_enrolled=True,
        intake_scope=frozenset({intake_id}),
    )

    principal = account.to_principal()

    assert principal.actor_id == account.staff_id
    assert principal.role_name == "operations_staff"
    assert principal.permissions == frozenset({"intake:review"})
    assert principal.intake_scope == frozenset({intake_id})


@pytest.mark.parametrize("status,mfa_enrolled", [("suspended", True), ("active", False)])
def test_staff_account_rejects_sessions_without_active_mfa_ready_state(
    status: str,
    mfa_enrolled: bool,
) -> None:
    account = StaffAccount(
        staff_id=uuid4(),
        provider_subject="oidc:staff:123",
        display_name="Mariela Torres",
        role_name="operations_staff",
        status=status,  # type: ignore[arg-type]
        permissions=frozenset({"intake:review"}),
        mfa_enrolled=mfa_enrolled,
    )

    with pytest.raises(ValueError, match="not eligible"):
        account.to_principal()


def test_staff_delegation_matches_exact_permission_and_scope() -> None:
    intake_id = uuid4()
    delegation = StaffDelegation(
        delegation_id=uuid4(),
        grantor_staff_id=uuid4(),
        grantee_staff_id=uuid4(),
        permission_name="intake:review",
        scope_kind="intake",
        scope_id=intake_id,
        active=True,
    )

    assert delegation.applies_to("intake:review", "intake", intake_id)
    assert not delegation.applies_to("intake:review", "global", None)
    assert not delegation.applies_to("intake:finalize", "intake", intake_id)
