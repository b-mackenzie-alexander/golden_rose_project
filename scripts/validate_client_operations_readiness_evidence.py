from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EMAIL_PATTERN = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HTTP_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
REVISION_PATTERN = re.compile(r"^[0-9a-z_]{4,64}$")
SAFE_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:/()#-]{2,240}$")

EVIDENCE_TYPE = "client-production-operations-readiness-not-activation"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_operations_readiness_evidence.py "
    "<operator-held-operations-readiness.json>"
)
REQUIRED_BOUNDARIES = {
    "cloud_execution": "separate-approval-required",
    "production_deployment": "separate-approval-required",
    "live_data_admission": "separate-approval-required",
    "incident_contact_activation": "separate-approval-required",
}
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "operations",
    "evidence",
)
READY_OPERATION_KEYS = (
    "monitoring_configuration_status",
    "alerting_configuration_status",
    "log_retention_status",
    "incident_routing_status",
    "support_routing_status",
)
REQUIRED_EVIDENCE_TEXT = (
    "monitoring_receipt",
    "alerting_receipt",
    "log_retention_receipt",
    "incident_routing_receipt",
    "support_routing_receipt",
    "monitoring_owner",
    "incident_owner",
    "support_owner",
    "escalation_review_note",
)
FORBIDDEN_FRAGMENTS = (
    "allUsers",
    "allAuthenticatedUsers",
    "credential",
    "password",
    "payload",
    "secret",
    "token",
    "live client data",
    "production deployed",
    "shared runtime rolled out",
    "terraform apply",
    "gcloud",
    "pagerduty.com",
    "slack.com",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class OperationsReadinessEvidenceValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OperationsReadinessEvidenceValidationError(
            f"{path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise OperationsReadinessEvidenceValidationError(
            "operations readiness evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise OperationsReadinessEvidenceValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise OperationsReadinessEvidenceValidationError(
            f"{section}.{key} must be a non-empty string"
        )
    return value


def _walk_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            strings.extend(_walk_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return strings


def _validate_value_safe(document: dict[str, Any]) -> None:
    for text in _walk_strings(document):
        if EMAIL_PATTERN.search(text):
            raise OperationsReadinessEvidenceValidationError(
                "operations readiness evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise OperationsReadinessEvidenceValidationError(
                "operations readiness evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise OperationsReadinessEvidenceValidationError(
                    f"operations readiness evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise OperationsReadinessEvidenceValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise OperationsReadinessEvidenceValidationError(f"{section}.{key} is not value-safe text")


def validate_operations_readiness_evidence(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise OperationsReadinessEvidenceValidationError(f"evidence_type must be {EVIDENCE_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise OperationsReadinessEvidenceValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise OperationsReadinessEvidenceValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise OperationsReadinessEvidenceValidationError(
            "source.source_commit must be a 40-character SHA"
        )
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise OperationsReadinessEvidenceValidationError(
            "source.migration_revision has invalid format"
        )

    for key in READY_OPERATION_KEYS:
        if _string(document, "operations", key) != "ready":
            raise OperationsReadinessEvidenceValidationError(f"operations.{key} must be ready")

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client operations readiness evidence JSON."
    )
    parser.add_argument(
        "operations_readiness_json",
        type=Path,
        help="Operator-held value-safe operations readiness evidence JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_operations_readiness_evidence(args.operations_readiness_json)
    except OperationsReadinessEvidenceValidationError as exc:
        print(f"client operations readiness evidence validation failed: {exc}", file=sys.stderr)
        return 1
    print("client operations readiness evidence validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
