import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_staff_feedback_activation_approval import (
    EXPECTED_VALIDATOR_COMMAND,
    StaffFeedbackActivationApprovalValidationError,
    validate_staff_feedback_activation_approval,
)


def _valid_activation_approval() -> dict[str, Any]:
    return {
        "evidence_type": "staff-feedback-activation-approval-not-execution",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "runtime_access_change": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "credential_rotation": "separate-approval-required",
            "support_channel_activation": "separate-approval-required",
            "current_environment_data_migration": "separate-approval-required",
            "client_owned_environment_transition": "separate-approval-required",
            "github_account_creation": "separate-approval-required",
            "business_repository_transfer": "separate-approval-required",
            "data_export_execution": "separate-approval-required",
            "data_import_execution": "separate-approval-required",
            "destructive_cleanup": "separate-approval-required",
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0015_staff_account_corrections",
        },
        "prerequisites": {
            "staff_feedback_readiness_status": "ready",
            "staff_feedback_package_index_status": "ready",
            "staff_feedback_triage_process_status": "ready",
            "training_known_limitations_status": "ready",
            "staff_access_scope_status": "ready",
            "data_entry_scope_status": "ready",
            "support_escalation_status": "ready",
            "rollback_closeout_status": "ready",
            "migration_disposition_status": "ready",
        },
        "approval_decision": {
            "decision_status": "approved_for_bounded_staff_feedback",
            "scope_limit": "current-environment-feedback-only",
            "activation_execution": "not-executed-by-this-record",
            "live_data_boundary": "not-admitted-without-separate-approval",
            "support_boundary": "not-activated-without-separate-approval",
        },
        "activation_boundary": {
            "staff_feedback_window": "not-activated-by-this-record",
            "runtime_access_change": "not-executed-without-separate-approval",
            "production_deployment": "not-executed-without-separate-approval",
            "live_data_admission": "not-admitted-without-separate-approval",
            "support_channel_activation": "not-activated-without-separate-approval",
            "current_environment_data_migration": "not-executed-without-separate-approval",
            "client_owned_environment_transition": "not-executed-without-separate-approval",
            "data_export_execution": "not-executed-without-separate-approval",
            "data_import_execution": "not-executed-without-separate-approval",
            "github_account_creation": "not-executed-without-separate-approval",
            "business_repository_transfer": "not-executed-without-separate-approval",
            "shared_runtime_rollout": "not-executed-without-separate-approval",
        },
        "evidence": {
            "readiness_review_receipt": "Readiness review receipt recorded",
            "package_index_receipt": "Package index receipt recorded",
            "triage_process_receipt": "Triage process receipt recorded",
            "training_known_limitations_receipt": "Training limitations receipt recorded",
            "staff_access_scope_note": "Staff access scope note recorded",
            "data_entry_scope_note": "Data entry scope note recorded",
            "support_escalation_note": "Support escalation note recorded",
            "rollback_closeout_note": "Rollback closeout note recorded",
            "migration_disposition_note": "Migration disposition note recorded",
            "approval_owner": "Private approval owner record",
            "next_review_note": "Next approval review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "staff-feedback-activation-approval.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_staff_feedback_activation_approval_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_staff_feedback_activation_approval(
        _write_evidence(tmp_path, _valid_activation_approval())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "prerequisites",
        "approval_decision",
        "activation_boundary",
        "evidence",
    ]


def test_staff_feedback_activation_approval_rejects_wrong_type(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence_type"] = "staff-feedback-activation-executed"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="evidence_type"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_short_commit(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="40-character SHA",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_blocked_prerequisite(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["prerequisites"]["staff_access_scope_status"] = "blocked"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="staff_access_scope_status",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_decision_drift(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["approval_decision"]["activation_execution"] = "executed"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="activation_execution",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_activation_boundary_drift(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["activation_boundary"]["runtime_access_change"] = "executed"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="runtime_access_change",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["package_index_receipt"] = "<value-safe-package-index-record>"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="package_index_receipt",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_concrete_url(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["readiness_review_receipt"] = "see https://private.invalid/review"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="concrete URL"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["approval_owner"] = "owner@example.invalid"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="email-like"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_secret_terms(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["staff_access_scope_note"] = "secret token reviewed"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="secret"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_activation_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["readiness_review_receipt"] = "staff feedback activated"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="staff feedback activated",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_live_data_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["data_entry_scope_note"] = "live data admitted"

    with pytest.raises(
        StaffFeedbackActivationApprovalValidationError,
        match="live data admitted",
    ):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_migration_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["migration_disposition_note"] = "data migrated"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="data migrated"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_account_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["next_review_note"] = "GitHub account created"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="github account"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_approval_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_approval()
    document["evidence"]["training_known_limitations_receipt"] = "product complete"

    with pytest.raises(StaffFeedbackActivationApprovalValidationError, match="product complete"):
        validate_staff_feedback_activation_approval(_write_evidence(tmp_path, document))
