import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_runtime_lifecycle_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    RuntimeLifecycleEvidenceValidationError,
    validate_runtime_lifecycle_evidence,
)


def _valid_runtime_lifecycle_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-runtime-lifecycle-review-not-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "dependency_update_execution": "separate-approval-required",
            "shared_runtime_rollout": "separate-approval-required",
        },
        "source": {
            "source_commit": "c" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "runtime_lifecycle": {
            "github_actions_runtime_status": "ready",
            "runner_image_status": "ready",
            "node_runtime_status": "ready",
            "python_runtime_status": "ready",
            "dependency_audit_status": "ready",
            "container_base_image_status": "ready",
        },
        "evidence": {
            "github_actions_runtime_receipt": "Actions runtime receipt recorded",
            "runner_image_receipt": "Runner image receipt recorded",
            "node_runtime_receipt": "Node runtime receipt recorded",
            "python_runtime_receipt": "Python runtime receipt recorded",
            "dependency_audit_receipt": "Dependency audit receipt recorded",
            "container_base_image_receipt": "Container image receipt recorded",
            "runtime_review_owner": "Private runtime owner record",
            "next_review_note": "Next lifecycle review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "runtime-lifecycle.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_runtime_lifecycle_evidence_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_runtime_lifecycle_evidence(
        _write_evidence(tmp_path, _valid_runtime_lifecycle_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "runtime_lifecycle",
        "evidence",
    ]


def test_runtime_lifecycle_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="evidence_type"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="40-character SHA"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_blocked_runner_image(
    tmp_path: Path,
) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["runtime_lifecycle"]["runner_image_status"] = "blocked"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="runner_image_status"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_blocked_dependency_audit(
    tmp_path: Path,
) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["runtime_lifecycle"]["dependency_audit_status"] = "blocked"

    with pytest.raises(
        RuntimeLifecycleEvidenceValidationError,
        match="dependency_audit_status",
    ):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence"]["node_runtime_receipt"] = "<value-safe-node-runtime-record>"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="node_runtime_receipt"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence"]["github_actions_runtime_receipt"] = "see https://private.invalid/run"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="concrete URL"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence"]["runtime_review_owner"] = "owner@example.invalid"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="email-like"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence"]["dependency_audit_receipt"] = "secret token scanned"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="secret"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_dependency_update_execution(
    tmp_path: Path,
) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence"]["next_review_note"] = "npm publish completed"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="npm publish"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))


def test_runtime_lifecycle_evidence_rejects_cloud_command(tmp_path: Path) -> None:
    document = _valid_runtime_lifecycle_evidence()
    document["evidence"]["container_base_image_receipt"] = "gcloud artifacts list"

    with pytest.raises(RuntimeLifecycleEvidenceValidationError, match="gcloud"):
        validate_runtime_lifecycle_evidence(_write_evidence(tmp_path, document))
