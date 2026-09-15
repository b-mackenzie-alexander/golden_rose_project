"""Finalization preconditions, independent of canonical record creation."""

from dataclasses import replace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from golden_rose.api.staff.intake_finalization_schemas import FinalizeIntakeRequest
from golden_rose.application.finalize_intake import require_finalization_review
from golden_rose.application.intake_errors import IntakeError
from golden_rose.auth.principal import StaffPrincipal


@pytest.fixture
def context():
    intake_id, review_id = uuid4(), uuid4()
    principal = StaffPrincipal(
        uuid4(), "test", frozenset({"intake:read", "intake:finalize", "worker_residence:read"})
    )
    row = {
        "intake_id": intake_id,
        "kind": "worker",
        "lifecycle_status": "draft",
        "version": 4,
        "content_version": 2,
        "content": {},
    }
    latest = {
        "review_id": review_id,
        "outcome": "intake_reviewed",
        "reviewed_content_version": 2,
        "reviewed_record_version": 2,
        "result_version": 3,
        "dependency_refs": {},
    }
    session = Mock()
    session.execute.return_value.mappings.return_value.one_or_none.return_value = latest
    return {
        "session": session,
        "principal": principal,
        "row": row,
        "request": FinalizeIntakeRequest(expected_version=4, review_id=review_id),
        "dependency_refs": {},
    }, latest


def test_follow_up_aggregate_version_does_not_stale_review(context):
    arguments, _ = context
    require_finalization_review(**arguments)
    arguments["session"].commit.assert_not_called()
    arguments["session"].rollback.assert_not_called()


@pytest.mark.parametrize(
    "patch,code",
    [
        ({"review_id": uuid4()}, "review_required"),
        ({"outcome": "needs_follow_up"}, "review_required"),
        ({"reviewed_content_version": 1}, "review_required"),
        ({"dependency_refs": {"party": {"id": str(uuid4()), "version": 1}}}, "dependency_changed"),
        ({"dependency_refs": None}, "persistence_unavailable"),
    ],
)
def test_finalization_requires_exact_latest_current_review(context, patch, code):
    arguments, latest = context
    latest.update(patch)
    with pytest.raises(IntakeError) as caught:
        require_finalization_review(**arguments)
    assert caught.value.code == code
    assert caught.value.status == (503 if code == "persistence_unavailable" else 409)


def test_no_review_cannot_finalize(context):
    arguments, _ = context
    arguments["session"].execute.return_value.mappings.return_value.one_or_none.return_value = None
    with pytest.raises(IntakeError, match="review_required"):
        require_finalization_review(**arguments)


@pytest.mark.parametrize("permission", ["intake:read", "intake:finalize", "worker_residence:read"])
def test_revoked_permission_rejects_before_review_lookup(context, permission):
    arguments, _ = context
    principal = arguments["principal"]
    arguments["principal"] = replace(principal, permissions=principal.permissions - {permission})
    with pytest.raises(IntakeError) as caught:
        require_finalization_review(**arguments)
    assert caught.value.status == 403
    arguments["session"].execute.assert_not_called()


def test_revoked_record_scope_rejects_before_review_lookup(context):
    arguments, _ = context
    arguments["principal"] = replace(arguments["principal"], intake_scope=frozenset())
    with pytest.raises(IntakeError) as caught:
        require_finalization_review(**arguments)
    assert caught.value.status == 404
    arguments["session"].execute.assert_not_called()


@pytest.mark.parametrize("section", ["party_address", "worksite_address"])
def test_employer_finalization_requires_each_restricted_read(context, section):
    arguments, _ = context
    arguments["row"]["kind"] = "employer"
    principal = arguments["principal"]
    arguments["principal"] = replace(
        principal,
        permissions=(principal.permissions | {"party_address:read", "worksite_address:read"})
        - {f"{section}:read"},
    )
    with pytest.raises(IntakeError) as caught:
        require_finalization_review(**arguments)
    assert caught.value.status == 403
    arguments["session"].execute.assert_not_called()


def test_catalog_reference_requires_read_permission(context):
    arguments, _ = context
    arguments["row"]["content"] = {
        "interests": {"selections": [{"interest_id": str(uuid4()), "catalog_version": 1}]}
    }
    with pytest.raises(IntakeError) as caught:
        require_finalization_review(**arguments)
    assert caught.value.status == 403
    arguments["session"].execute.assert_not_called()


@pytest.mark.parametrize(
    "patch,code",
    [
        ({"version": 5}, "version_conflict"),
        ({"lifecycle_status": "finalized"}, "already_finalized"),
    ],
)
def test_stale_version_and_finalized_intake_reject_before_review_lookup(context, patch, code):
    arguments, _ = context
    arguments["row"].update(patch)
    with pytest.raises(IntakeError, match=code):
        require_finalization_review(**arguments)
    arguments["session"].execute.assert_not_called()


def test_dependency_comparison_includes_identity_version_and_child_set(context):
    arguments, latest = context
    reference = {"id": str(uuid4()), "version": 2}
    latest["dependency_refs"] = {"party": reference}
    arguments["dependency_refs"] = {"party": dict(reference)}
    require_finalization_review(**arguments)
    for dependencies in (
        {"party": {**reference, "version": 3}},
        {"party": {**reference, "id": str(uuid4())}},
        {"party": reference, "contact": {"id": str(uuid4()), "version": 1}},
    ):
        arguments["dependency_refs"] = dependencies
        with pytest.raises(IntakeError, match="dependency_changed"):
            require_finalization_review(**arguments)
