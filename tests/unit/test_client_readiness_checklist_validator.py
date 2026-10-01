import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_readiness_checklist import (
    EXPECTED_VALIDATOR_COMMAND,
    ReadinessChecklistValidationError,
    validate_readiness_checklist,
)

READY_SECTIONS = (
    "package_artifacts",
    "staff_identity",
    "terraform_plan_review",
    "artifact_admission",
    "handoff_evidence",
    "backup_restore_rehearsal",
    "operations_readiness",
    "runtime_lifecycle_review",
    "data_governance_review",
    "copy_approval_review",
    "manual_accessibility_language_review",
    "training_acceptance_review",
    "operations_owners",
)


def _valid_checklist() -> dict[str, Any]:
    return {
        "checklist_type": "deployable-package-review-not-production-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "terraform_plan": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "provider_side_identity_activation": "separate-approval-required",
        },
        "required_sections": [
            "package_artifacts",
            "staff_identity",
            "terraform_plan_review",
            "artifact_admission",
            "handoff_evidence",
            "backup_restore_rehearsal",
            "operations_readiness",
            "runtime_lifecycle_review",
            "data_governance_review",
            "copy_approval_review",
            "manual_accessibility_language_review",
            "training_acceptance_review",
            "operations_owners",
            "manual_acceptance_boundary",
        ],
        "package_artifacts": {
            "status": "ready",
            "evidence": "package validator passed 2026-09-29",
        },
        "staff_identity": {
            "status": "ready",
            "evidence": "staff identity readiness source guard passed",
        },
        "terraform_plan_review": {
            "status": "ready",
            "evidence": "plan validator passed with zero forbidden findings",
        },
        "artifact_admission": {
            "status": "ready",
            "evidence": "artifact admission evidence value safe",
        },
        "handoff_evidence": {
            "status": "ready",
            "evidence": "handoff evidence validator passed",
        },
        "backup_restore_rehearsal": {
            "status": "ready",
            "evidence": "backup restore evidence validator passed",
        },
        "operations_readiness": {
            "status": "ready",
            "evidence": "operations readiness evidence validator passed",
        },
        "runtime_lifecycle_review": {
            "status": "ready",
            "evidence": "runtime lifecycle evidence validator passed",
        },
        "data_governance_review": {
            "status": "ready",
            "evidence": "data governance evidence validator passed",
        },
        "copy_approval_review": {
            "status": "ready",
            "evidence": "copy approval evidence validator passed",
        },
        "manual_accessibility_language_review": {
            "status": "ready",
            "evidence": "manual accessibility language validator passed",
        },
        "training_acceptance_review": {
            "status": "ready",
            "evidence": "training acceptance validator passed",
        },
        "operations_owners": {
            "status": "ready",
            "evidence": "operations owner records identified privately",
        },
        "manual_acceptance_boundary": {},
        "activation_boundary": {
            "production_deployment": "not-executed-without-separate-approval",
            "live_data_admission": "not-admitted-without-separate-approval",
            "shared_runtime_rollout": "not-executed-without-separate-approval",
        },
    }


def _write_checklist(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_client_readiness_checklist_accepts_value_safe_package_review(
    tmp_path: Path,
) -> None:
    checked = validate_readiness_checklist(_write_checklist(tmp_path, _valid_checklist()))

    assert checked == [
        "authority_boundary",
        *READY_SECTIONS,
        "manual_acceptance_boundary",
        "activation_boundary",
    ]


def test_client_readiness_checklist_rejects_wrong_checklist_type(tmp_path: Path) -> None:
    document = _valid_checklist()
    document["checklist_type"] = "production-activation"

    with pytest.raises(ReadinessChecklistValidationError, match="checklist_type"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_missing_required_section(
    tmp_path: Path,
) -> None:
    document = _valid_checklist()
    del document["artifact_admission"]

    with pytest.raises(ReadinessChecklistValidationError, match="artifact_admission"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_blocked_package_section(
    tmp_path: Path,
) -> None:
    document = _valid_checklist()
    document["terraform_plan_review"]["status"] = "blocked"

    with pytest.raises(ReadinessChecklistValidationError, match="terraform_plan_review"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_placeholder_evidence(tmp_path: Path) -> None:
    document = _valid_checklist()
    document["handoff_evidence"]["evidence"] = "<value-safe-handoff-validator-record>"

    with pytest.raises(ReadinessChecklistValidationError, match="must be filled"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_checklist()
    document["package_artifacts"]["evidence"] = "see https://private.invalid/evidence"

    with pytest.raises(ReadinessChecklistValidationError, match="concrete URL"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_email_like_owner(tmp_path: Path) -> None:
    document = _valid_checklist()
    document["operations_owners"]["evidence"] = "owner@example.invalid"

    with pytest.raises(ReadinessChecklistValidationError, match="email-like"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_checklist()
    document["artifact_admission"]["evidence"] = "secret token reviewed"

    with pytest.raises(ReadinessChecklistValidationError, match="secret"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_manual_acceptance_overclaim(
    tmp_path: Path,
) -> None:
    document = _valid_checklist()
    document["manual_acceptance_boundary"]["staff_workflow_acceptance"] = "passed"

    with pytest.raises(ReadinessChecklistValidationError, match="must be empty"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_live_data_admission(tmp_path: Path) -> None:
    document = _valid_checklist()
    document["activation_boundary"]["live_data_admission"] = "admitted"

    with pytest.raises(ReadinessChecklistValidationError, match="live_data_admission"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))


def test_client_readiness_checklist_rejects_production_deployment_claim(
    tmp_path: Path,
) -> None:
    document = _valid_checklist()
    document["activation_boundary"]["production_deployment"] = "production deployed"

    with pytest.raises(ReadinessChecklistValidationError, match="production deployed"):
        validate_readiness_checklist(_write_checklist(tmp_path, document))
