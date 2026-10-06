import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_transition_planning import (
    EXPECTED_VALIDATOR_COMMAND,
    ClientTransitionPlanningValidationError,
    validate_client_transition_planning,
)


def _valid_transition_planning() -> dict[str, Any]:
    return {
        "evidence_type": "client-environment-transition-planning-not-execution",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "data_export_execution": "separate-approval-required",
            "data_import_execution": "separate-approval-required",
            "destructive_cleanup": "separate-approval-required",
            "client_owned_environment_transition": "separate-approval-required",
            "github_account_creation": "separate-approval-required",
            "business_repository_transfer": "separate-approval-required",
            "credential_rotation": "separate-approval-required",
            "support_channel_activation": "separate-approval-required",
        },
        "source": {
            "source_commit": "e" * 40,
            "migration_revision": "0015_staff_account_corrections",
        },
        "transition_planning": {
            "management_model_status": "ready",
            "current_environment_record_inventory_status": "ready",
            "data_classification_status": "ready",
            "migration_candidate_scope_status": "ready",
            "export_import_strategy_status": "ready",
            "identity_access_transition_status": "ready",
            "repository_stewardship_status": "ready",
            "business_account_decision_status": "ready",
            "support_ownership_status": "ready",
            "rollback_or_abandonment_status": "ready",
            "known_limitations_status": "ready",
        },
        "evidence": {
            "management_model_note": "Management model note recorded",
            "record_inventory_note": "Record inventory note recorded",
            "data_classification_note": "Data classification note recorded",
            "migration_candidate_scope_note": "Migration candidate scope recorded",
            "export_import_strategy_note": "Export import strategy recorded",
            "identity_access_transition_note": "Identity access transition recorded",
            "repository_stewardship_note": "Repository stewardship note recorded",
            "business_account_decision_note": "Business account decision recorded",
            "support_ownership_note": "Support ownership note recorded",
            "rollback_or_abandonment_note": "Rollback abandonment note recorded",
            "known_limitations_acknowledgement": "Known limitations acknowledgement recorded",
            "transition_owner": "Private transition owner record",
            "next_review_note": "Next transition review noted",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "client-transition-planning.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_client_transition_planning_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_client_transition_planning(
        _write_evidence(tmp_path, _valid_transition_planning())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "transition_planning",
        "evidence",
    ]


def test_client_transition_planning_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_transition_planning()
    document["evidence_type"] = "production-activation"

    with pytest.raises(ClientTransitionPlanningValidationError, match="evidence_type"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_transition_planning()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(ClientTransitionPlanningValidationError, match="40-character SHA"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_blocked_management_model(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["transition_planning"]["management_model_status"] = "blocked"

    with pytest.raises(ClientTransitionPlanningValidationError, match="management_model"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_blocked_export_import_strategy(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["transition_planning"]["export_import_strategy_status"] = "blocked"

    with pytest.raises(
        ClientTransitionPlanningValidationError,
        match="export_import_strategy_status",
    ):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["record_inventory_note"] = "<value-safe-record-inventory-record>"

    with pytest.raises(ClientTransitionPlanningValidationError, match="record_inventory"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_transition_planning()
    document["evidence"]["repository_stewardship_note"] = "see https://private.invalid/repo"

    with pytest.raises(ClientTransitionPlanningValidationError, match="concrete URL"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["transition_owner"] = "owner@example.invalid"

    with pytest.raises(ClientTransitionPlanningValidationError, match="email-like"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_transition_planning()
    document["evidence"]["identity_access_transition_note"] = "secret token reviewed"

    with pytest.raises(ClientTransitionPlanningValidationError, match="secret"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_export_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["export_import_strategy_note"] = "data exported"

    with pytest.raises(ClientTransitionPlanningValidationError, match="data exported"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_migration_execution_claim(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["migration_candidate_scope_note"] = "data migrated"

    with pytest.raises(ClientTransitionPlanningValidationError, match="data migrated"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_github_account_claim(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["business_account_decision_note"] = "GitHub account created"

    with pytest.raises(ClientTransitionPlanningValidationError, match="github account"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_repository_transfer_claim(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["repository_stewardship_note"] = "repository transferred"

    with pytest.raises(ClientTransitionPlanningValidationError, match="repository transferred"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))


def test_client_transition_planning_rejects_complete_product_claim(
    tmp_path: Path,
) -> None:
    document = _valid_transition_planning()
    document["evidence"]["known_limitations_acknowledgement"] = "product complete"

    with pytest.raises(ClientTransitionPlanningValidationError, match="product complete"):
        validate_client_transition_planning(_write_evidence(tmp_path, document))
