import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_live_data_pilot_readiness import (
    EXPECTED_VALIDATOR_COMMAND,
    LiveDataPilotReadinessValidationError,
    validate_live_data_pilot_readiness,
)


def _valid_live_data_pilot_readiness() -> dict[str, Any]:
    return {
        "evidence_type": "controlled-live-data-staff-pilot-readiness",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "not-production-activation",
            "live_data_admission": "controlled-staff-pilot-approved",
            "runtime_access_change": "separate-approval-required",
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
        "source": {
            "source_commit": "f" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "pilot_readiness": {
            "operating_boundary_status": "ready",
            "live_data_scope_status": "ready",
            "staff_identity_status": "ready",
            "staff_account_status": "ready",
            "no_store_auth_sensitive_status": "ready",
            "demo_and_seed_removal_status": "ready",
            "static_fallback_status": "ready",
            "backup_restore_status": "ready",
            "migration_disposition_status": "ready",
            "data_governance_status": "ready",
            "support_escalation_status": "ready",
            "staff_training_status": "ready",
            "manual_acceptance_status": "ready",
            "rollback_closeout_status": "ready",
            "known_limitations_status": "ready",
        },
        "deployment_preconditions": {
            "runtime_environment": "production-mode-controlled-staff-pilot",
            "auth_mode": "staff_oidc",
            "environment_marker": "controlled-live-data-staff-pilot",
            "presentation_seed": "disabled",
            "shared_demo_access": "disabled",
            "static_operational_examples": "disabled",
            "named_staff_accounts": "required",
            "live_data_scope": "worker-and-employer-intake-records-only",
        },
        "retained_boundaries": {
            "public_worker_or_employer_portal": "not-activated",
            "automated_matching_ranking_referral_placement": "not-implemented",
            "production_completion_claim": "not-claimed",
            "client_owned_environment_transition": "not-executed-without-separate-approval",
            "current_environment_data_migration": "not-executed-without-separate-approval",
            "data_export_execution": "not-executed-without-separate-approval",
            "data_import_execution": "not-executed-without-separate-approval",
            "github_account_creation": "not-executed-without-separate-approval",
            "business_repository_transfer": "not-executed-without-separate-approval",
            "support_channel_activation": "not-activated-without-separate-approval",
            "provider_side_recovery_or_session_revocation": "not-performed-by-application",
            "shared_runtime_rollout": "not-executed-without-separate-approval",
        },
        "evidence": {
            "operating_boundary_note": "Controlled staff pilot boundary recorded",
            "live_data_scope_note": "Worker employer intake scope approved",
            "staff_identity_receipt": "Staff identity receipt recorded",
            "staff_account_receipt": "Named staff account receipt recorded",
            "no_store_auth_sensitive_receipt": "No store auth handling receipt recorded",
            "demo_and_seed_removal_receipt": "Presentation seed removal receipt recorded",
            "static_fallback_receipt": "Static fallback disablement receipt recorded",
            "backup_restore_receipt": "Backup restore posture receipt recorded",
            "migration_disposition_note": "Later environment move disposition recorded",
            "data_governance_note": "Access correction retention governance recorded",
            "support_escalation_note": "Staff support escalation owner recorded",
            "staff_training_note": "Staff working instructions recorded",
            "manual_acceptance_note": "Manual dashboard review acceptance recorded",
            "rollback_closeout_note": "Rollback closeout owner recorded",
            "known_limitations_acknowledgement": "Known limitations acknowledgement recorded",
            "readiness_owner": "Private readiness owner record",
            "next_review_note": "Next readiness review recorded",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "live-data-pilot-readiness.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_live_data_pilot_readiness_accepts_value_safe_record(tmp_path: Path) -> None:
    checked = validate_live_data_pilot_readiness(
        _write_evidence(tmp_path, _valid_live_data_pilot_readiness())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "pilot_readiness",
        "deployment_preconditions",
        "retained_boundaries",
        "evidence",
    ]


def test_live_data_pilot_readiness_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence_type"] = "staff-feedback"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="evidence_type"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="40-character SHA"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_blocked_live_data_scope(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["pilot_readiness"]["live_data_scope_status"] = "blocked"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="live_data_scope"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_placeholder_evidence(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["operating_boundary_note"] = "<value-safe-boundary-record>"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="operating_boundary"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["support_escalation_note"] = "see https://private.invalid/support"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="concrete URL"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_email_like_owner(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["readiness_owner"] = "owner@example.invalid"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="email-like"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["staff_identity_receipt"] = "secret token reviewed"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="secret"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_synthetic_or_fictional_framing(
    tmp_path: Path,
) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["live_data_scope_note"] = "synthetic worker data only"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="synthetic"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_static_seed_enabled_claim(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["demo_and_seed_removal_receipt"] = "presentation seed enabled"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="presentation seed"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_wrong_auth_mode(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["deployment_preconditions"]["auth_mode"] = "shared_gate"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="auth_mode"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_product_completion_claim(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["known_limitations_acknowledgement"] = "product complete"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="product complete"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_migration_execution_claim(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["migration_disposition_note"] = "data migrated"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="data migrated"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_public_portal_activation(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["retained_boundaries"]["public_worker_or_employer_portal"] = "activated"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="public_worker"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))


def test_live_data_pilot_readiness_rejects_automated_matching_claim(tmp_path: Path) -> None:
    document = _valid_live_data_pilot_readiness()
    document["evidence"]["operating_boundary_note"] = "automated matching enabled"

    with pytest.raises(LiveDataPilotReadinessValidationError, match="automated matching"):
        validate_live_data_pilot_readiness(_write_evidence(tmp_path, document))
