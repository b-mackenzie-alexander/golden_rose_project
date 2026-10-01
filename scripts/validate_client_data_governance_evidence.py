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

EVIDENCE_TYPE = "client-production-data-governance-review-not-live-data-admission"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_data_governance_evidence.py "
    "<operator-held-data-governance.json>"
)
REQUIRED_BOUNDARIES = {
    "cloud_execution": "separate-approval-required",
    "production_deployment": "separate-approval-required",
    "live_data_admission": "separate-approval-required",
    "data_export_execution": "separate-approval-required",
    "disclosure_execution": "separate-approval-required",
    "destructive_deletion": "separate-approval-required",
}
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "data_governance",
    "evidence",
)
READY_GOVERNANCE_KEYS = (
    "classification_status",
    "retention_policy_status",
    "deletion_policy_status",
    "export_policy_status",
    "disclosure_policy_status",
    "restricted_history_recipient_status",
)
REQUIRED_EVIDENCE_TEXT = (
    "classification_matrix_receipt",
    "retention_schedule_receipt",
    "deletion_workflow_receipt",
    "export_workflow_receipt",
    "disclosure_rule_receipt",
    "restricted_history_recipient_receipt",
    "governance_owner",
    "next_review_note",
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
    "live data admitted",
    "production deployed",
    "shared runtime rolled out",
    "terraform apply",
    "gcloud",
    "client data exported",
    "data export completed",
    "disclosure completed",
    "production data deleted",
    "destructive deletion completed",
    "raw export",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class DataGovernanceEvidenceValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataGovernanceEvidenceValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise DataGovernanceEvidenceValidationError(
            "data governance evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise DataGovernanceEvidenceValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise DataGovernanceEvidenceValidationError(f"{section}.{key} must be a non-empty string")
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
            raise DataGovernanceEvidenceValidationError(
                "data governance evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise DataGovernanceEvidenceValidationError(
                "data governance evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise DataGovernanceEvidenceValidationError(
                    f"data governance evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise DataGovernanceEvidenceValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise DataGovernanceEvidenceValidationError(f"{section}.{key} is not value-safe text")


def validate_data_governance_evidence(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise DataGovernanceEvidenceValidationError(f"evidence_type must be {EVIDENCE_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise DataGovernanceEvidenceValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise DataGovernanceEvidenceValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise DataGovernanceEvidenceValidationError(
            "source.source_commit must be a 40-character SHA"
        )
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise DataGovernanceEvidenceValidationError("source.migration_revision has invalid format")

    for key in READY_GOVERNANCE_KEYS:
        if _string(document, "data_governance", key) != "ready":
            raise DataGovernanceEvidenceValidationError(f"data_governance.{key} must be ready")

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client data governance evidence JSON."
    )
    parser.add_argument(
        "data_governance_json",
        type=Path,
        help="Operator-held value-safe data governance evidence JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_data_governance_evidence(args.data_governance_json)
    except DataGovernanceEvidenceValidationError as exc:
        print(f"client data governance evidence validation failed: {exc}", file=sys.stderr)
        return 1
    print("client data governance evidence validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
