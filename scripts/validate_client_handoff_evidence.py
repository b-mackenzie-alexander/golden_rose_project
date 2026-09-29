from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
REVISION_PATTERN = re.compile(r"^[0-9a-z_]{4,64}$")
SAFE_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:/()#-]{2,240}$")
EMAIL_PATTERN = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HTTP_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")

REQUIRED_BOUNDARIES = {
    "production_deployment": "separate-approval-required",
    "live_data_admission": "separate-approval-required",
    "cloud_execution": "separate-approval-required",
}
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "artifact_admission",
    "plan_review",
    "database_authority",
    "smoke",
    "recovery",
    "operations",
    "owner_acceptance",
)
REQUIRED_ARTIFACT_TEXT = (
    "signature_evidence",
    "sbom_evidence",
    "provenance_evidence",
    "repository_subject_restriction",
)
REQUIRED_OPERATIONS_TEXT = (
    "backup_restore_owner",
    "monitoring_owner",
    "incident_owner",
    "support_owner",
)
REQUIRED_PASS_STATUSES = {
    ("plan_review", "status"),
    ("database_authority", "status"),
    ("smoke", "health"),
    ("smoke", "readiness"),
    ("smoke", "staff_entry_boundary"),
}
FORBIDDEN_FRAGMENTS = (
    "GOLDEN_ROSE_AUTH_MODE=synthetic",
    "GOLDEN_ROSE_DEMO_ACCESS_ENABLED=true",
    "GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED=true",
    "allUsers",
    "allAuthenticatedUsers",
    "credential",
    "payload",
    "password",
    "secret",
    "secret_data",
    "token",
    "live client data",
    "provider-side reset completed",
    "provider-side session revocation completed",
)
EXPECTED_PLAN_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_production_plan.py <operator-held-plan.json>"
)


class HandoffEvidenceValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HandoffEvidenceValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise HandoffEvidenceValidationError("handoff evidence must contain a JSON object")
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise HandoffEvidenceValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise HandoffEvidenceValidationError(f"{section}.{key} must be a non-empty string")
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
            raise HandoffEvidenceValidationError("handoff evidence contains email-like value")
        if HTTP_URL_PATTERN.search(text):
            raise HandoffEvidenceValidationError("handoff evidence contains concrete URL")
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise HandoffEvidenceValidationError(
                    f"handoff evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise HandoffEvidenceValidationError(f"{section}.{key} must be filled, not placeholder")
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise HandoffEvidenceValidationError(f"{section}.{key} is not value-safe text")


def _validate_status(document: dict[str, Any], section: str, key: str, expected: str) -> None:
    value = _string(document, section, key)
    if value != expected:
        raise HandoffEvidenceValidationError(f"{section}.{key} must be {expected}")


def validate_handoff_evidence(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise HandoffEvidenceValidationError(f"authority_boundary.{key} must be {expected}")

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise HandoffEvidenceValidationError("source.source_commit must be a 40-character SHA")
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise HandoffEvidenceValidationError("source.migration_revision has invalid format")

    image_digest = _string(document, "artifact_admission", "image_digest")
    if not DIGEST_PATTERN.fullmatch(image_digest):
        raise HandoffEvidenceValidationError("artifact_admission.image_digest must be sha256")
    for key in REQUIRED_ARTIFACT_TEXT:
        _validate_safe_text("artifact_admission", key, _string(document, "artifact_admission", key))

    if _string(document, "plan_review", "validator_command") != EXPECTED_PLAN_COMMAND:
        raise HandoffEvidenceValidationError("plan_review.validator_command is not expected")
    for section, key in REQUIRED_PASS_STATUSES:
        _validate_status(document, section, key, "passed")

    _validate_safe_text(
        "database_authority",
        "receipt",
        _string(document, "database_authority", "receipt"),
    )
    _validate_safe_text(
        "recovery",
        "rollback_or_forward_recovery_note",
        _string(document, "recovery", "rollback_or_forward_recovery_note"),
    )
    if _string(document, "recovery", "status") != "recorded":
        raise HandoffEvidenceValidationError("recovery.status must be recorded")
    for key in REQUIRED_OPERATIONS_TEXT:
        _validate_safe_text("operations", key, _string(document, "operations", key))
    _validate_safe_text(
        "owner_acceptance",
        "acceptance_checklist",
        _string(document, "owner_acceptance", "acceptance_checklist"),
    )
    if _string(document, "owner_acceptance", "status") != "accepted":
        raise HandoffEvidenceValidationError("owner_acceptance.status must be accepted")

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client production handoff evidence JSON."
    )
    parser.add_argument(
        "handoff_json",
        type=Path,
        help="Operator-held value-safe handoff evidence JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_handoff_evidence(args.handoff_json)
    except HandoffEvidenceValidationError as exc:
        print(f"client handoff evidence validation failed: {exc}", file=sys.stderr)
        return 1
    print("client handoff evidence validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
