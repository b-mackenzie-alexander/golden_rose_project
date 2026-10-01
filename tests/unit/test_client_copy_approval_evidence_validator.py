import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_copy_approval_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    CopyApprovalEvidenceValidationError,
    validate_copy_approval_evidence,
)


def _valid_copy_approval_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-copy-approval-review-not-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "legal_approval_execution": "separate-approval-required",
            "business_copy_activation": "separate-approval-required",
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "copy_approval": {
            "copy_inventory_status": "ready",
            "legal_review_status": "ready",
            "business_review_status": "ready",
            "translation_review_status": "ready",
            "controlled_copy_owner_status": "ready",
        },
        "evidence": {
            "copy_inventory_receipt": "Copy inventory receipt recorded",
            "legal_review_receipt": "Legal review receipt recorded",
            "business_review_receipt": "Business review receipt recorded",
            "translation_review_receipt": "Translation review receipt recorded",
            "controlled_copy_owner": "Private copy owner record",
            "next_review_note": "Next copy review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "copy-approval.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_copy_approval_evidence_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_copy_approval_evidence(
        _write_evidence(tmp_path, _valid_copy_approval_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "copy_approval",
        "evidence",
    ]


def test_copy_approval_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="evidence_type"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_copy_approval_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="40-character SHA"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_blocked_legal_review(
    tmp_path: Path,
) -> None:
    document = _valid_copy_approval_evidence()
    document["copy_approval"]["legal_review_status"] = "blocked"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="legal_review_status"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_blocked_translation_review(
    tmp_path: Path,
) -> None:
    document = _valid_copy_approval_evidence()
    document["copy_approval"]["translation_review_status"] = "blocked"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="translation_review_status"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence"]["copy_inventory_receipt"] = "<value-safe-copy-inventory-record>"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="copy_inventory_receipt"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence"]["legal_review_receipt"] = "see https://private.invalid/legal"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="concrete URL"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence"]["controlled_copy_owner"] = "owner@example.invalid"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="email-like"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence"]["business_review_receipt"] = "secret reviewed"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="secret"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_legal_approval_completion_claim(
    tmp_path: Path,
) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence"]["legal_review_receipt"] = "legal approval completed"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="legal approval completed"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))


def test_copy_approval_evidence_rejects_public_publish_claim(
    tmp_path: Path,
) -> None:
    document = _valid_copy_approval_evidence()
    document["evidence"]["next_review_note"] = "public site published"

    with pytest.raises(CopyApprovalEvidenceValidationError, match="public site published"):
        validate_copy_approval_evidence(_write_evidence(tmp_path, document))
