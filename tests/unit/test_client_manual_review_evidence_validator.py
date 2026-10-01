import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_manual_review_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    ManualReviewEvidenceValidationError,
    validate_manual_review_evidence,
)


def _valid_manual_review_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-manual-accessibility-language-review-not-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "public_accessibility_claim": "separate-approval-required",
            "translation_certification": "separate-approval-required",
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "manual_review": {
            "keyboard_navigation_status": "ready",
            "screen_reader_status": "ready",
            "reflow_status": "ready",
            "contrast_status": "ready",
            "fluent_spanish_status": "ready",
            "bilingual_parity_status": "ready",
        },
        "evidence": {
            "keyboard_review_receipt": "Keyboard review receipt recorded",
            "screen_reader_review_receipt": "Screen reader review receipt recorded",
            "reflow_review_receipt": "Reflow review receipt recorded",
            "contrast_review_receipt": "Contrast review receipt recorded",
            "fluent_spanish_review_receipt": "Fluent Spanish review receipt recorded",
            "bilingual_parity_receipt": "Bilingual parity review receipt recorded",
            "manual_review_owner": "Private manual review owner record",
            "next_review_note": "Next manual review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "manual-review.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_manual_review_evidence_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_manual_review_evidence(
        _write_evidence(tmp_path, _valid_manual_review_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "manual_review",
        "evidence",
    ]


def test_manual_review_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_manual_review_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(ManualReviewEvidenceValidationError, match="evidence_type"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_manual_review_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(ManualReviewEvidenceValidationError, match="40-character SHA"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_blocked_keyboard_review(
    tmp_path: Path,
) -> None:
    document = _valid_manual_review_evidence()
    document["manual_review"]["keyboard_navigation_status"] = "blocked"

    with pytest.raises(ManualReviewEvidenceValidationError, match="keyboard_navigation_status"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_blocked_fluent_spanish_review(
    tmp_path: Path,
) -> None:
    document = _valid_manual_review_evidence()
    document["manual_review"]["fluent_spanish_status"] = "blocked"

    with pytest.raises(ManualReviewEvidenceValidationError, match="fluent_spanish_status"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_manual_review_evidence()
    document["evidence"]["keyboard_review_receipt"] = "<value-safe-keyboard-review-record>"

    with pytest.raises(ManualReviewEvidenceValidationError, match="keyboard_review_receipt"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_manual_review_evidence()
    document["evidence"]["screen_reader_review_receipt"] = "see https://private.invalid/a11y"

    with pytest.raises(ManualReviewEvidenceValidationError, match="concrete URL"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_manual_review_evidence()
    document["evidence"]["manual_review_owner"] = "owner@example.invalid"

    with pytest.raises(ManualReviewEvidenceValidationError, match="email-like"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_manual_review_evidence()
    document["evidence"]["contrast_review_receipt"] = "secret reviewed"

    with pytest.raises(ManualReviewEvidenceValidationError, match="secret"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_certification_claim(
    tmp_path: Path,
) -> None:
    document = _valid_manual_review_evidence()
    document["evidence"]["reflow_review_receipt"] = "WCAG certified"

    with pytest.raises(ManualReviewEvidenceValidationError, match="wcag certified"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))


def test_manual_review_evidence_rejects_public_publish_claim(
    tmp_path: Path,
) -> None:
    document = _valid_manual_review_evidence()
    document["evidence"]["next_review_note"] = "public site published"

    with pytest.raises(ManualReviewEvidenceValidationError, match="public site published"):
        validate_manual_review_evidence(_write_evidence(tmp_path, document))
