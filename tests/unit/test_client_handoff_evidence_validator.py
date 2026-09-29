import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_handoff_evidence import (
    EXPECTED_PLAN_COMMAND,
    HandoffEvidenceValidationError,
    validate_handoff_evidence,
)


def _valid_evidence() -> dict[str, Any]:
    return {
        "authority_boundary": {
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "cloud_execution": "separate-approval-required",
        },
        "source": {
            "source_commit": "a" * 40,
            "migration_revision": "0012_staff_account_evidence",
        },
        "artifact_admission": {
            "image_digest": "sha256:" + ("b" * 64),
            "signature_evidence": "cosign admission record 2026-09-29",
            "sbom_evidence": "sbom validation record 2026-09-29",
            "provenance_evidence": "slsa provenance record 2026-09-29",
            "repository_subject_restriction": "repo subject golden rose protected develop",
        },
        "plan_review": {
            "validator_command": EXPECTED_PLAN_COMMAND,
            "status": "passed",
        },
        "database_authority": {
            "receipt": "database authority receipt 2026-09-29",
            "status": "passed",
        },
        "smoke": {
            "health": "passed",
            "readiness": "passed",
            "staff_entry_boundary": "passed",
        },
        "recovery": {
            "rollback_or_forward_recovery_note": "forward recovery note 2026-09-29",
            "status": "recorded",
        },
        "operations": {
            "backup_restore_owner": "private owner record backup restore",
            "monitoring_owner": "private owner record monitoring",
            "incident_owner": "private owner record incident",
            "support_owner": "private owner record support",
        },
        "owner_acceptance": {
            "acceptance_checklist": "private acceptance checklist 2026-09-29",
            "status": "accepted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_client_handoff_evidence_accepts_value_safe_record(tmp_path: Path) -> None:
    checked = validate_handoff_evidence(_write_evidence(tmp_path, _valid_evidence()))

    assert checked == [
        "authority_boundary",
        "source",
        "artifact_admission",
        "plan_review",
        "database_authority",
        "smoke",
        "recovery",
        "operations",
        "owner_acceptance",
    ]


def test_client_handoff_evidence_rejects_missing_section(tmp_path: Path) -> None:
    document = _valid_evidence()
    del document["database_authority"]

    with pytest.raises(HandoffEvidenceValidationError, match="database_authority"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_non_sha_commit(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["source"]["source_commit"] = "main"

    with pytest.raises(HandoffEvidenceValidationError, match="40-character SHA"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_mutable_image_reference(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["artifact_admission"]["image_digest"] = "golden-rose:latest"

    with pytest.raises(HandoffEvidenceValidationError, match="image_digest"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_failed_smoke(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["smoke"]["readiness"] = "not_run"

    with pytest.raises(HandoffEvidenceValidationError, match="smoke.readiness"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_placeholder_evidence(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["database_authority"]["receipt"] = "<value-safe-database-authority-record>"

    with pytest.raises(HandoffEvidenceValidationError, match="must be filled"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["artifact_admission"]["signature_evidence"] = "see https://private.invalid/record"

    with pytest.raises(HandoffEvidenceValidationError, match="concrete URL"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_email_like_owner(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["operations"]["support_owner"] = "support-owner@example.invalid"

    with pytest.raises(HandoffEvidenceValidationError, match="email-like"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_live_data_claim(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["owner_acceptance"]["acceptance_checklist"] = "accepted live client data"

    with pytest.raises(HandoffEvidenceValidationError, match="live client data"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_secret_payload_terms(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["database_authority"]["receipt"] = "database secret payload noted"

    with pytest.raises(HandoffEvidenceValidationError, match="payload"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))


def test_client_handoff_evidence_rejects_provider_side_reset_claim(tmp_path: Path) -> None:
    document = _valid_evidence()
    document["recovery"]["rollback_or_forward_recovery_note"] = "provider-side reset completed"

    with pytest.raises(HandoffEvidenceValidationError, match="provider-side reset"):
        validate_handoff_evidence(_write_evidence(tmp_path, document))
