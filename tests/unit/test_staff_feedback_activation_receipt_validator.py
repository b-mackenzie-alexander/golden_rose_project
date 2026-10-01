import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_staff_feedback_activation_receipt import (
    EXPECTED_VALIDATOR_COMMAND,
    StaffFeedbackActivationReceiptValidationError,
    validate_staff_feedback_activation_receipt,
)


def _valid_activation_receipt() -> dict[str, Any]:
    return {
        "evidence_type": "staff-feedback-activation-receipt-not-production",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "operator-held-separate-approval-required",
            "runtime_access_change": "operator-held-separate-approval-required",
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
            "source_commit": "d" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "preconditions": {
            "activation_approval_status": "ready",
            "staff_feedback_package_index_status": "ready",
            "staff_feedback_readiness_status": "ready",
            "staff_access_scope_status": "ready",
            "data_entry_scope_status": "ready",
            "expiration_or_closeout_status": "ready",
            "rollback_status": "ready",
        },
        "execution_receipt": {
            "receipt_scope": "current-environment-feedback-only",
            "source_artifact_effect": "records-operator-held-execution-only",
            "feedback_window_status": "opened_for_bounded_current_environment_feedback",
            "staff_access_scope": "bounded_current_environment_staff_access",
            "data_entry_scope": "bounded_by_approved_feedback_scope",
            "expiration_or_closeout": "required",
        },
        "retained_boundaries": {
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
            "product_completion_claim": "not-claimed",
        },
        "evidence": {
            "activation_approval_receipt": "Activation approval receipt recorded",
            "package_index_receipt": "Package index receipt recorded",
            "staff_access_scope_receipt": "Staff access scope receipt recorded",
            "data_entry_scope_receipt": "Data entry scope receipt recorded",
            "expiration_or_closeout_receipt": "Closeout receipt recorded",
            "rollback_receipt": "Rollback receipt recorded",
            "no_store_auth_sensitive_receipt": "No store auth posture recorded",
            "support_escalation_note": "Support escalation note recorded",
            "operator_owner": "Private operator owner record",
            "next_review_note": "Next review note recorded",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "staff-feedback-activation-receipt.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_staff_feedback_activation_receipt_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_staff_feedback_activation_receipt(
        _write_evidence(tmp_path, _valid_activation_receipt())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "preconditions",
        "execution_receipt",
        "retained_boundaries",
        "evidence",
    ]


def test_staff_feedback_activation_receipt_rejects_wrong_type(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence_type"] = "staff-feedback-production-activation"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="evidence_type"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_short_commit(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="40-character SHA",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_blocked_precondition(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["preconditions"]["staff_access_scope_status"] = "blocked"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="staff_access_scope_status",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_execution_scope_drift(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["execution_receipt"]["receipt_scope"] = "production"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="receipt_scope",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["retained_boundaries"]["live_data_admission"] = "admitted"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="live_data_admission",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["package_index_receipt"] = "<value-safe-package-index-record>"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="package_index_receipt",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_concrete_url(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["activation_approval_receipt"] = "see https://private.invalid/record"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="concrete URL"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["operator_owner"] = "owner@example.invalid"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="email-like"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_secret_terms(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["staff_access_scope_receipt"] = "secret token reviewed"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="secret"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_production_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["next_review_note"] = "production deployed"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="production deployed",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_live_data_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["data_entry_scope_receipt"] = "live data admitted"

    with pytest.raises(
        StaffFeedbackActivationReceiptValidationError,
        match="live data admitted",
    ):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_migration_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["rollback_receipt"] = "data migrated"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="data migrated"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_account_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["support_escalation_note"] = "GitHub account created"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="github account"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_activation_receipt_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_activation_receipt()
    document["evidence"]["no_store_auth_sensitive_receipt"] = "product complete"

    with pytest.raises(StaffFeedbackActivationReceiptValidationError, match="product complete"):
        validate_staff_feedback_activation_receipt(_write_evidence(tmp_path, document))
