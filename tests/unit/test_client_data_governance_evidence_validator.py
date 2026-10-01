import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_data_governance_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    DataGovernanceEvidenceValidationError,
    validate_data_governance_evidence,
)


def _valid_data_governance_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-data-governance-review-not-live-data-admission",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "data_export_execution": "separate-approval-required",
            "disclosure_execution": "separate-approval-required",
            "destructive_deletion": "separate-approval-required",
        },
        "source": {
            "source_commit": "d" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "data_governance": {
            "classification_status": "ready",
            "retention_policy_status": "ready",
            "deletion_policy_status": "ready",
            "export_policy_status": "ready",
            "disclosure_policy_status": "ready",
            "restricted_history_recipient_status": "ready",
        },
        "evidence": {
            "classification_matrix_receipt": "Classification matrix receipt recorded",
            "retention_schedule_receipt": "Retention schedule receipt recorded",
            "deletion_workflow_receipt": "Deletion workflow receipt recorded",
            "export_workflow_receipt": "Export workflow receipt recorded",
            "disclosure_rule_receipt": "Disclosure rule receipt recorded",
            "restricted_history_recipient_receipt": "Restricted history recipient receipt recorded",
            "governance_owner": "Private governance owner record",
            "next_review_note": "Next governance review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "data-governance.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_data_governance_evidence_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_data_governance_evidence(
        _write_evidence(tmp_path, _valid_data_governance_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "data_governance",
        "evidence",
    ]


def test_data_governance_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_data_governance_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="evidence_type"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_data_governance_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="40-character SHA"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_blocked_retention(
    tmp_path: Path,
) -> None:
    document = _valid_data_governance_evidence()
    document["data_governance"]["retention_policy_status"] = "blocked"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="retention_policy_status"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_blocked_restricted_recipients(
    tmp_path: Path,
) -> None:
    document = _valid_data_governance_evidence()
    document["data_governance"]["restricted_history_recipient_status"] = "blocked"

    with pytest.raises(
        DataGovernanceEvidenceValidationError,
        match="restricted_history_recipient_status",
    ):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_data_governance_evidence()
    document["evidence"]["classification_matrix_receipt"] = (
        "<value-safe-classification-matrix-record>"
    )

    with pytest.raises(
        DataGovernanceEvidenceValidationError,
        match="classification_matrix_receipt",
    ):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_data_governance_evidence()
    document["evidence"]["export_workflow_receipt"] = "see https://private.invalid/export"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="concrete URL"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_data_governance_evidence()
    document["evidence"]["governance_owner"] = "owner@example.invalid"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="email-like"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_data_governance_evidence()
    document["evidence"]["classification_matrix_receipt"] = "secret reviewed"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="secret"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_export_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_data_governance_evidence()
    document["evidence"]["export_workflow_receipt"] = "client data exported"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="client data exported"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))


def test_data_governance_evidence_rejects_destructive_deletion_claim(
    tmp_path: Path,
) -> None:
    document = _valid_data_governance_evidence()
    document["evidence"]["deletion_workflow_receipt"] = "production data deleted"

    with pytest.raises(DataGovernanceEvidenceValidationError, match="production data deleted"):
        validate_data_governance_evidence(_write_evidence(tmp_path, document))
