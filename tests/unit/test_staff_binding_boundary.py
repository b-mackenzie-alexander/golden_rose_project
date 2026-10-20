from unittest.mock import Mock
from uuid import UUID

import pytest
from pydantic import ValidationError

from golden_rose.api.staff.schemas import CorrectStaffAccountRequest, CreateStaffAccountRequest
from golden_rose.application.staff_account_lifecycle import (
    StaffAccountLifecycleError,
    create_staff_account,
)
from golden_rose.auth.principal import StaffPrincipal


def test_normal_creation_rejects_manual_identity_instead_of_treating_it_as_proof():
    with pytest.raises(ValidationError):
        CreateStaffAccountRequest.model_validate(
            {
                "provider_subject": "Business owner",
                "provider_email": "owner@example.test",
                "display_name": "Owner",
                "role_name": "owner",
                "permission_names": ["staff_account:read"],
                "reason_text": "Onboarding",
            }
        )


@pytest.mark.parametrize("identity", ["provider_subject", "provider_email", "mfa_enrolled"])
def test_access_request_cannot_change_any_identity_or_mfa_field(identity):
    with pytest.raises(ValidationError):
        CorrectStaffAccountRequest.model_validate(
            {
                "display_name": "Owner",
                "role_name": "owner",
                "permission_names": ["staff_account:read"],
                "reason_text": "Change access",
                "expected_version": 1,
                identity: True if identity == "mfa_enrolled" else "untrusted@example.test",
            }
        )


def test_creation_service_also_rejects_manual_identity_before_any_persistence():
    principal = StaffPrincipal(
        actor_id=UUID(int=1), role_name="owner", permissions=frozenset({"staff_account:create"})
    )
    with pytest.raises(StaffAccountLifecycleError, match="manual"):
        create_staff_account(
            session=Mock(),
            principal=principal,
            command_id=UUID(int=2),
            staff_id=UUID(int=3),
            provider_subject="Business owner",
            provider_email="owner@example.test",
            display_name="Owner",
            role_name="owner",
            permission_names=frozenset({"staff_account:read"}),
            mfa_enrolled=True,
            clock=Mock(),
            identifiers=Mock(),
            reason_text="Onboarding",
        )


def test_recovery_permission_cannot_be_provisioned_to_another_account_by_a_lesser_editor():
    principal = StaffPrincipal(
        actor_id=UUID(int=1), role_name="owner", permissions=frozenset({"staff_account:create"})
    )
    with pytest.raises(PermissionError):
        create_staff_account(
            session=Mock(),
            principal=principal,
            command_id=UUID(int=2),
            staff_id=UUID(int=3),
            provider_subject="",
            provider_email="owner@example.test",
            display_name="Owner",
            role_name="owner",
            permission_names=frozenset({"staff_account:signin:reset"}),
            mfa_enrolled=False,
            clock=Mock(),
            identifiers=Mock(),
            reason_text="Onboarding",
        )
