import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_staff_feedback_triage import (
    EXPECTED_VALIDATOR_COMMAND,
    StaffFeedbackTriageValidationError,
    validate_staff_feedback_triage,
)


def _valid_staff_feedback_triage() -> dict[str, Any]:
    return {
        "evidence_type": "staff-feedback-triage-review-not-acceptance",
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
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "triage_summary": {
            "feedback_window_scope_status": "recorded",
            "issue_inventory_status": "recorded",
            "blocker_disposition_status": "recorded",
            "accessibility_impact_status": "recorded",
            "privacy_impact_status": "recorded",
            "security_impact_status": "recorded",
            "defect_disposition_status": "recorded",
            "retest_status": "recorded",
            "migration_disposition_status": "recorded",
            "known_limitations_status": "recorded",
        },
        "issue_counts": {
            "blocker_count": 1,
            "high_count": 2,
            "medium_count": 3,
            "low_count": 4,
            "open_count": 2,
            "fixed_count": 3,
            "deferred_count": 2,
            "accepted_risk_count": 1,
            "not_a_defect_count": 2,
        },
        "evidence": {
            "feedback_window_scope_note": "Feedback window scope recorded",
            "issue_inventory_note": "Issue inventory note recorded",
            "blocker_disposition_note": "Blocker disposition note recorded",
            "accessibility_impact_note": "Accessibility impact note recorded",
            "privacy_impact_note": "Privacy impact note recorded",
            "security_impact_note": "Security impact note recorded",
            "defect_disposition_note": "Defect disposition note recorded",
            "retest_note": "Retest note recorded",
            "migration_disposition_note": "Migration disposition note recorded",
            "known_limitations_acknowledgement": "Known limitations acknowledgement recorded",
            "triage_owner": "Private triage owner record",
            "next_review_note": "Next triage review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "staff-feedback-triage.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_staff_feedback_triage_accepts_value_safe_record(tmp_path: Path) -> None:
    checked = validate_staff_feedback_triage(
        _write_evidence(tmp_path, _valid_staff_feedback_triage())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "triage_summary",
        "issue_counts",
        "evidence",
    ]


def test_staff_feedback_triage_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence_type"] = "client-acceptance-complete"

    with pytest.raises(StaffFeedbackTriageValidationError, match="evidence_type"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(StaffFeedbackTriageValidationError, match="40-character SHA"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_blocked_issue_inventory(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_triage()
    document["triage_summary"]["issue_inventory_status"] = "blocked"

    with pytest.raises(StaffFeedbackTriageValidationError, match="issue_inventory"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_negative_count(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["issue_counts"]["open_count"] = -1

    with pytest.raises(StaffFeedbackTriageValidationError, match="open_count"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_boolean_count(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["issue_counts"]["fixed_count"] = True

    with pytest.raises(StaffFeedbackTriageValidationError, match="fixed_count"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_mismatched_totals(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["issue_counts"]["fixed_count"] = 0

    with pytest.raises(StaffFeedbackTriageValidationError, match="totals"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_placeholder_evidence(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["issue_inventory_note"] = "<value-safe-issue-inventory-record>"

    with pytest.raises(StaffFeedbackTriageValidationError, match="issue_inventory"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["retest_note"] = "see https://private.invalid/feedback"

    with pytest.raises(StaffFeedbackTriageValidationError, match="concrete URL"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_email_like_owner(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["triage_owner"] = "owner@example.invalid"

    with pytest.raises(StaffFeedbackTriageValidationError, match="email-like"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["security_impact_note"] = "secret token reviewed"

    with pytest.raises(StaffFeedbackTriageValidationError, match="secret"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_staff_feedback_acceptance_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["defect_disposition_note"] = "staff feedback accepted"

    with pytest.raises(StaffFeedbackTriageValidationError, match="staff feedback accepted"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_client_acceptance_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["known_limitations_acknowledgement"] = "client accepted"

    with pytest.raises(StaffFeedbackTriageValidationError, match="client accepted"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_migration_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["migration_disposition_note"] = "data migrated"

    with pytest.raises(StaffFeedbackTriageValidationError, match="data migrated"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_github_account_claim(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["next_review_note"] = "GitHub account created"

    with pytest.raises(StaffFeedbackTriageValidationError, match="github account"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))


def test_staff_feedback_triage_rejects_complete_product_claim(tmp_path: Path) -> None:
    document = _valid_staff_feedback_triage()
    document["evidence"]["known_limitations_acknowledgement"] = "product complete"

    with pytest.raises(StaffFeedbackTriageValidationError, match="product complete"):
        validate_staff_feedback_triage(_write_evidence(tmp_path, document))
