import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_training_acceptance_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    TrainingAcceptanceEvidenceValidationError,
    validate_training_acceptance_evidence,
)


def _valid_training_acceptance_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-training-acceptance-review-not-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "provider_side_identity_activation": "separate-approval-required",
            "support_channel_activation": "separate-approval-required",
            "current_environment_data_migration": "separate-approval-required",
            "business_repository_transfer": "separate-approval-required",
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0015_staff_account_corrections",
        },
        "training_acceptance": {
            "staff_training_status": "ready",
            "support_escalation_status": "ready",
            "staff_workflow_acceptance_status": "ready",
            "management_model_review_status": "ready",
            "working_environment_feedback_status": "ready",
            "data_migration_planning_status": "ready",
            "repository_stewardship_status": "ready",
            "known_limitations_status": "ready",
        },
        "evidence": {
            "staff_training_receipt": "Staff training receipt recorded",
            "support_escalation_receipt": "Support escalation receipt recorded",
            "staff_workflow_acceptance_receipt": "Staff workflow acceptance recorded",
            "management_model_review_note": "Management model review note recorded",
            "working_environment_feedback_note": "Working environment feedback note recorded",
            "data_migration_planning_note": "Data migration planning note recorded",
            "repository_stewardship_note": "Repository stewardship note recorded",
            "known_limitations_acknowledgement": "Known limitations acknowledgement recorded",
            "acceptance_owner": "Private acceptance owner record",
            "next_review_note": "Next acceptance review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "training-acceptance.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_training_acceptance_evidence_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_training_acceptance_evidence(
        _write_evidence(tmp_path, _valid_training_acceptance_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "training_acceptance",
        "evidence",
    ]


def test_training_acceptance_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="evidence_type"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_training_acceptance_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="40-character SHA"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_blocked_workflow_acceptance(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["training_acceptance"]["staff_workflow_acceptance_status"] = "blocked"

    with pytest.raises(
        TrainingAcceptanceEvidenceValidationError,
        match="staff_workflow_acceptance_status",
    ):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_blocked_migration_planning(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["training_acceptance"]["data_migration_planning_status"] = "blocked"

    with pytest.raises(
        TrainingAcceptanceEvidenceValidationError,
        match="data_migration_planning_status",
    ):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["staff_training_receipt"] = "<value-safe-staff-training-record>"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="staff_training_receipt"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["support_escalation_receipt"] = "see https://private.invalid/support"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="concrete URL"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["acceptance_owner"] = "owner@example.invalid"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="email-like"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["management_model_review_note"] = "secret token reviewed"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="secret"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_support_activation_claim(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["support_escalation_receipt"] = "support channel activated"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="support channel"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_migration_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["data_migration_planning_note"] = "data migrated"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="data migrated"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))


def test_training_acceptance_evidence_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_training_acceptance_evidence()
    document["evidence"]["known_limitations_acknowledgement"] = "product complete"

    with pytest.raises(TrainingAcceptanceEvidenceValidationError, match="product complete"):
        validate_training_acceptance_evidence(_write_evidence(tmp_path, document))
