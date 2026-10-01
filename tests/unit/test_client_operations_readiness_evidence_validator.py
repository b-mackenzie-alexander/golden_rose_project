import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_operations_readiness_evidence import (
    EXPECTED_VALIDATOR_COMMAND,
    OperationsReadinessEvidenceValidationError,
    validate_operations_readiness_evidence,
)


def _valid_operations_readiness_evidence() -> dict[str, Any]:
    return {
        "evidence_type": "client-production-operations-readiness-not-activation",
        "validator_command": EXPECTED_VALIDATOR_COMMAND,
        "authority_boundary": {
            "cloud_execution": "separate-approval-required",
            "production_deployment": "separate-approval-required",
            "live_data_admission": "separate-approval-required",
            "incident_contact_activation": "separate-approval-required",
        },
        "source": {
            "source_commit": "b" * 40,
            "migration_revision": "0014_request_shift_review",
        },
        "operations": {
            "monitoring_configuration_status": "ready",
            "alerting_configuration_status": "ready",
            "log_retention_status": "ready",
            "incident_routing_status": "ready",
            "support_routing_status": "ready",
        },
        "evidence": {
            "monitoring_receipt": "Monitoring receipt recorded by operator",
            "alerting_receipt": "Alerting receipt recorded by operator",
            "log_retention_receipt": "Log retention receipt recorded",
            "incident_routing_receipt": "Incident routing receipt recorded",
            "support_routing_receipt": "Support routing receipt recorded",
            "monitoring_owner": "Private monitoring owner record",
            "incident_owner": "Private incident owner record",
            "support_owner": "Private support owner record",
            "escalation_review_note": "Escalation review note recorded",
        },
    }


def _write_evidence(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "operations-readiness.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_operations_readiness_evidence_accepts_value_safe_record(
    tmp_path: Path,
) -> None:
    checked = validate_operations_readiness_evidence(
        _write_evidence(tmp_path, _valid_operations_readiness_evidence())
    )

    assert checked == [
        "authority_boundary",
        "source",
        "operations",
        "evidence",
    ]


def test_operations_readiness_evidence_rejects_wrong_type(tmp_path: Path) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence_type"] = "production-activation"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="evidence_type"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_short_commit(tmp_path: Path) -> None:
    document = _valid_operations_readiness_evidence()
    document["source"]["source_commit"] = "abc123"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="40-character SHA"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_blocked_monitoring(
    tmp_path: Path,
) -> None:
    document = _valid_operations_readiness_evidence()
    document["operations"]["monitoring_configuration_status"] = "blocked"

    with pytest.raises(
        OperationsReadinessEvidenceValidationError,
        match="monitoring_configuration_status",
    ):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_blocked_incident_routing(
    tmp_path: Path,
) -> None:
    document = _valid_operations_readiness_evidence()
    document["operations"]["incident_routing_status"] = "blocked"

    with pytest.raises(
        OperationsReadinessEvidenceValidationError,
        match="incident_routing_status",
    ):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_placeholder_evidence(
    tmp_path: Path,
) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence"]["monitoring_receipt"] = "<value-safe-monitoring-record>"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="monitoring_receipt"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_concrete_url(tmp_path: Path) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence"]["alerting_receipt"] = "see https://private.invalid/alerts"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="concrete URL"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_email_like_owner(
    tmp_path: Path,
) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence"]["incident_owner"] = "owner@example.invalid"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="email-like"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_secret_terms(tmp_path: Path) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence"]["support_routing_receipt"] = "secret token stored"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="secret"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_cloud_command(tmp_path: Path) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence"]["monitoring_receipt"] = "gcloud monitoring channels list"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="gcloud"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))


def test_operations_readiness_evidence_rejects_external_contact_url(
    tmp_path: Path,
) -> None:
    document = _valid_operations_readiness_evidence()
    document["evidence"]["incident_routing_receipt"] = "pagerduty.com route tested"

    with pytest.raises(OperationsReadinessEvidenceValidationError, match="pagerduty"):
        validate_operations_readiness_evidence(_write_evidence(tmp_path, document))
