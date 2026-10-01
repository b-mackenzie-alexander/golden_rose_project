import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_package_index import (
    EXPECTED_VALIDATOR_COMMAND,
    REQUIRED_SOURCE_ARTIFACTS,
    REQUIRED_VALIDATOR_COMMANDS,
    PackageIndexValidationError,
    validate_package_index,
)


def _valid_package_index() -> dict[str, Any]:
    return {
        "index_type": "client-owned-deployable-package-index-not-production-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "terraform_plan": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "provider_side_identity_activation": "separate-approval-required",
        },
        "source_artifacts": [
            {
                "path": path,
                "status": "reviewed",
                "evidence": f"{Path(path).name} reviewed in source package",
            }
            for path in REQUIRED_SOURCE_ARTIFACTS
        ],
        "validator_commands": dict(REQUIRED_VALIDATOR_COMMANDS),
        "manual_acceptance_boundary": {
            "staff_workflow_acceptance": "separate-review-required",
        },
        "activation_boundary": {
            "production_deployment": "not-executed-without-separate-approval",
            "live_data_admission": "not-admitted-without-separate-approval",
            "shared_runtime_rollout": "not-executed-without-separate-approval",
        },
    }


def _write_index(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "package-index.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_client_package_index_accepts_value_safe_source_review(tmp_path: Path) -> None:
    checked = validate_package_index(_write_index(tmp_path, _valid_package_index()))

    assert checked == [
        "authority_boundary",
        *REQUIRED_SOURCE_ARTIFACTS,
        "validator_commands",
        "manual_acceptance_boundary",
        "activation_boundary",
    ]


def test_client_package_index_rejects_wrong_index_type(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["index_type"] = "production-activation"

    with pytest.raises(PackageIndexValidationError, match="index_type"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_missing_artifact(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["source_artifacts"].pop()

    with pytest.raises(PackageIndexValidationError, match="source_artifacts"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_blocked_artifact(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["source_artifacts"][0]["status"] = "blocked"

    with pytest.raises(PackageIndexValidationError, match="status"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_placeholder_evidence(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["source_artifacts"][1]["evidence"] = "<value-safe-review-record>"

    with pytest.raises(PackageIndexValidationError, match="must be filled"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["source_artifacts"][2]["evidence"] = "see https://private.invalid/evidence"

    with pytest.raises(PackageIndexValidationError, match="concrete URL"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_email_like_owner(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["source_artifacts"][3]["evidence"] = "owner@example.invalid"

    with pytest.raises(PackageIndexValidationError, match="email-like"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["source_artifacts"][4]["evidence"] = "secret token reviewed"

    with pytest.raises(PackageIndexValidationError, match="secret"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_validator_command_drift(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["validator_commands"]["terraform_plan"] = "terraform apply"

    with pytest.raises(PackageIndexValidationError, match="validator_commands"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_manual_acceptance_overclaim(
    tmp_path: Path,
) -> None:
    document = _valid_package_index()
    document["manual_acceptance_boundary"]["staff_workflow_acceptance"] = "passed"

    with pytest.raises(PackageIndexValidationError, match="staff_workflow_acceptance"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_live_data_admission(tmp_path: Path) -> None:
    document = _valid_package_index()
    document["activation_boundary"]["live_data_admission"] = "admitted"

    with pytest.raises(PackageIndexValidationError, match="live_data_admission"):
        validate_package_index(_write_index(tmp_path, document))


def test_client_package_index_rejects_production_deployment_claim(
    tmp_path: Path,
) -> None:
    document = _valid_package_index()
    document["activation_boundary"]["production_deployment"] = "production deployed"

    with pytest.raises(PackageIndexValidationError, match="production deployed"):
        validate_package_index(_write_index(tmp_path, document))
