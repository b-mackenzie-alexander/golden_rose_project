import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_staff_feedback_readiness import (
    EXPECTED_VALIDATOR_COMMAND,
    StaffFeedbackReadinessValidationError,
    validate_staff_feedback_readiness,
)


def _valid_staff_feedback_readiness() -> dict[str, Any]:
    return {
        "evidence_type": "staff-feedback-readiness-review-not-activation",
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
            "business_repository_transfer": "separate-approval-required",
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "feedback_readiness": {
            "current_environment_scope_status": "ready",
            "staff_identity_access_status": "ready",
            "no_store_auth_sensitive_status": "ready",
            "staff_training_status": "ready",
            "support_escalation_status": "ready",
            "data_entry_scope_status": "ready",
            "feedback_triage_status": "ready",
            "migration_disposition_status": "ready",
            "repository_stewardship_status": "ready",
            "rollback_or_closeout_status": "ready",
            "known_limitations_status": "ready",
        },
        "evidence": {
            "current_environment_scope_note": "Current environment scope recorded",
            "staff_identity_access_receipt": "Staff identity access receipt recorded",
            "no_store_auth_sensitive_receipt": "No store auth handling receipt recorded",
            "staff_training_receipt": "Staff training receipt recorded",
            "support_escalation_receipt": "Support escalation receipt recorded",
            "data_entry_scope_note": "Data entry scope note recorded",
            "feedback_triage_note": "Feedback triage note recorded",
            "migration_disposition_note": "Migration disposition note recorded",
            "repository_stewardship_note": "Repository stewardship note recorded",
            "rollback_or_closeout_note": "Rollback closeout note recorded",
            "known_limitations_acknowledgement": "Known limitations acknowledgement recorded",
            "readiness_owner": "Private readiness owner record",
            "next_review_note": "Next readiness review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "staff-feedback-readiness.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_staff_feedback_readiness_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_staff_feedback_readiness(
        _write_evidence(tmp_path, _valid_staff_feedback_readiness())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "feedback_readiness",
        "evidence",
    ]


def test_staff_feedback_readiness_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence_type"] = "production-activation"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="evidence_type"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_staff_feedback_readiness()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="40-character SHA"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_blocked_staff_access(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["feedback_readiness"]["staff_identity_access_status"] = "blocked"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="staff_identity_access"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_blocked_migration_disposition(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["feedback_readiness"]["migration_disposition_status"] = "blocked"

    with pytest.raises(
        StaffFeedbackReadinessValidationError,
        match="migration_disposition_status",
    ):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["current_environment_scope_note"] = (
        "<value-safe-current-environment-scope-record>"
    )

    with pytest.raises(StaffFeedbackReadinessValidationError, match="scope_note"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["feedback_triage_note"] = "see https://private.invalid/feedback"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="concrete URL"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["readiness_owner"] = "owner@example.invalid"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="email-like"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["staff_identity_access_receipt"] = "secret token reviewed"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="secret"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_staff_feedback_activation_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["current_environment_scope_note"] = "staff feedback activated"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="staff feedback"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_migration_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["migration_disposition_note"] = "data migrated"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="data migrated"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_github_account_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["repository_stewardship_note"] = "GitHub account created"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="github account"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))


def test_staff_feedback_readiness_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_readiness()
    document["evidence"]["known_limitations_acknowledgement"] = "product complete"

    with pytest.raises(StaffFeedbackReadinessValidationError, match="product complete"):
        validate_staff_feedback_readiness(_write_evidence(tmp_path, document))
