import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_staff_feedback_closeout_receipt import (
    EXPECTED_VALIDATOR_COMMAND,
    StaffFeedbackCloseoutReceiptValidationError,
    validate_staff_feedback_closeout_receipt,
)


def _valid_closeout_receipt() -> dict[str, Any]:
    return {
        "evidence_type": "staff-feedback-closeout-receipt-not-cleanup",
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
            "source_commit": "c" * 40,
            "migration_revision": "0015_staff_account_corrections",
        },
        "preconditions": {
            "activation_receipt_status": "ready",
            "staff_feedback_triage_status": "ready",
            "staff_access_scope_status": "ready",
            "data_entry_scope_status": "ready",
            "closeout_owner_status": "ready",
            "rollback_status": "ready",
            "migration_disposition_status": "ready",
        },
        "closeout_receipt": {
            "receipt_scope": "current-environment-feedback-closeout-only",
            "source_artifact_effect": "records-operator-held-closeout-only",
            "feedback_window_status": "closed_for_bounded_current_environment_feedback",
            "staff_access_posture": "closed_or_expiring_under_operator_record",
            "data_entry_status": "stopped_or_bounded_by_closeout_scope",
            "feedback_disposition": "triaged_or_carried_forward",
            "retained_record_disposition": "not_migrated_by_this_record",
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
            "destructive_cleanup": "not-executed-without-separate-approval",
            "shared_runtime_rollout": "not-executed-without-separate-approval",
            "product_completion_claim": "not-claimed",
        },
        "evidence": {
            "activation_receipt": "Activation receipt recorded",
            "triage_receipt": "Triage receipt recorded",
            "staff_access_closeout_receipt": "Staff access closeout recorded",
            "data_entry_closeout_receipt": "Data entry closeout recorded",
            "retained_record_disposition_note": "Retained record disposition recorded",
            "rollback_or_forward_recovery_note": "Rollback posture recorded",
            "no_store_auth_sensitive_receipt": "No store auth posture recorded",
            "closeout_owner": "Private closeout owner record",
            "next_review_note": "Next review note recorded",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "staff-feedback-closeout-receipt.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_staff_feedback_closeout_receipt_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_staff_feedback_closeout_receipt(
        _write_evidence(tmp_path, _valid_closeout_receipt())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "preconditions",
        "closeout_receipt",
        "retained_boundaries",
        "evidence",
    ]


def test_staff_feedback_closeout_receipt_rejects_wrong_type(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence_type"] = "staff-feedback-closeout-cleanup-complete"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="evidence_type"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_short_commit(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="40-character SHA",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_blocked_precondition(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["preconditions"]["closeout_owner_status"] = "blocked"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="closeout_owner_status",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_closeout_scope_drift(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["closeout_receipt"]["receipt_scope"] = "production-closeout"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="receipt_scope",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["retained_boundaries"]["destructive_cleanup"] = "completed"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="destructive_cleanup",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["triage_receipt"] = "<value-safe-triage-record>"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="triage_receipt",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_concrete_url(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["activation_receipt"] = "see https://private.invalid/record"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="concrete URL"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["closeout_owner"] = "owner@example.invalid"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="email-like"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_secret_terms(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["staff_access_closeout_receipt"] = "secret token reviewed"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="secret"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_production_claim(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["next_review_note"] = "production deployed"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="production deployed",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_live_data_claim(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["data_entry_closeout_receipt"] = "live data admitted"

    with pytest.raises(
        StaffFeedbackCloseoutReceiptValidationError,
        match="live data admitted",
    ):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_cleanup_claim(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["rollback_or_forward_recovery_note"] = "records deleted"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="records deleted"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_migration_claim(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["retained_record_disposition_note"] = "data migrated"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="data migrated"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))


def test_staff_feedback_closeout_receipt_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_closeout_receipt()
    document["evidence"]["no_store_auth_sensitive_receipt"] = "product complete"

    with pytest.raises(StaffFeedbackCloseoutReceiptValidationError, match="product complete"):
        validate_staff_feedback_closeout_receipt(_write_evidence(tmp_path, document))
