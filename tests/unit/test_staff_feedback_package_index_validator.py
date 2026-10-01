import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_staff_feedback_package_index import (
    EXPECTED_VALIDATOR_COMMAND,
    REQUIRED_SOURCE_ARTIFACTS,
    REQUIRED_VALIDATOR_COMMANDS,
    StaffFeedbackPackageIndexValidationError,
    validate_staff_feedback_package_index,
)


def _valid_staff_feedback_package_index() -> dict[str, Any]:
    return {
        "index_type": "staff-feedback-package-index-not-activation",
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
            "data_export_execution": "separate-approval-required",
            "data_import_execution": "separate-approval-required",
            "destructive_cleanup": "separate-approval-required",
        },
        "source_artifacts": [
            {
                "path": path,
                "status": "reviewed",
                "evidence": f"{Path(path).name} reviewed for feedback package",
            }
            for path in REQUIRED_SOURCE_ARTIFACTS
        ],
        "validator_commands": dict(REQUIRED_VALIDATOR_COMMANDS),
        "activation_boundary": {
            "staff_feedback_window": "not-activated-without-separate-approval",
            "runtime_access_change": "not-executed-without-separate-approval",
            "production_deployment": "not-executed-without-separate-approval",
            "live_data_admission": "not-admitted-without-separate-approval",
            "support_channel_activation": "not-activated-without-separate-approval",
            "current_environment_data_migration": "not-executed-without-separate-approval",
            "client_owned_environment_transition": "not-executed-without-separate-approval",
            "data_export_execution": "not-executed-without-separate-approval",
            "data_import_execution": "not-executed-without-separate-approval",
            "github_account_creation": "not-executed-without-separate-approval",
            "business_repository_transfer": "not-executed-without-separate-approval",
            "shared_runtime_rollout": "not-executed-without-separate-approval",
        },
    }


def _write_index(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "staff-feedback-package-index.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_staff_feedback_package_index_accepts_value_safe_source_review(
    tmp_path: Path,
) -> None:
    checked = validate_staff_feedback_package_index(
        _write_index(tmp_path, _valid_staff_feedback_package_index())
    )

    assert checked == [
        "authority_boundary",
        *REQUIRED_SOURCE_ARTIFACTS,
        "validator_commands",
        "activation_boundary",
    ]


def test_staff_feedback_package_index_rejects_wrong_index_type(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["index_type"] = "staff-feedback-activation"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="index_type"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_missing_artifact(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"].pop()

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="source_artifacts"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_blocked_artifact(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][0]["status"] = "blocked"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="status"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][1]["evidence"] = "<value-safe-review-record>"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="must be filled"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][2]["evidence"] = "see https://private.invalid/evidence"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="concrete URL"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][3]["evidence"] = "owner@example.invalid"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="email-like"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][4]["evidence"] = "secret token reviewed"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="secret"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_validator_command_drift(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["validator_commands"]["staff_feedback_readiness"] = (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_staff_feedback_readiness_drift.py "
        "<operator-held-staff-feedback-readiness.json>"
    )

    with pytest.raises(
        StaffFeedbackPackageIndexValidationError,
        match="validator_commands",
    ):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_staff_feedback_activation_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][1]["evidence"] = "staff feedback activated"

    with pytest.raises(
        StaffFeedbackPackageIndexValidationError,
        match="staff feedback activated",
    ):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_live_data_admission(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["activation_boundary"]["live_data_admission"] = "admitted"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="live_data_admission"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_migration_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][4]["evidence"] = "data migrated"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="data migrated"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_github_account_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][6]["evidence"] = "GitHub account created"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="github account"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_repository_transfer_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][7]["evidence"] = "repository transferred"

    with pytest.raises(
        StaffFeedbackPackageIndexValidationError,
        match="repository transferred",
    ):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))


def test_staff_feedback_package_index_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_staff_feedback_package_index()
    document["source_artifacts"][8]["evidence"] = "product complete"

    with pytest.raises(StaffFeedbackPackageIndexValidationError, match="product complete"):
        validate_staff_feedback_package_index(_write_index(tmp_path, document))
