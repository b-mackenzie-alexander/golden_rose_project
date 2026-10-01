from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EMAIL_PATTERN = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HTTP_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
SAFE_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:/()#-]{2,240}$")

INDEX_TYPE = "client-owned-deployable-package-index-not-production-activation"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_package_index.py <operator-held-package-index.json>"
)
REQUIRED_BOUNDARIES = {
    "cloud_execution": "separate-approval-required",
    "terraform_plan": "separate-approval-required",
    "production_deployment": "separate-approval-required",
    "live_data_admission": "separate-approval-required",
    "provider_side_identity_activation": "separate-approval-required",
}
REQUIRED_SOURCE_ARTIFACTS = (
    "deploy/gcp/client-owned-production-package-runbook.md",
    "deploy/gcp/staff-identity-production-runbook.md",
    "deploy/gcp/templates/client-production.env.example",
    "deploy/gcp/templates/client-owned-gcp-inputs.example.json",
    "deploy/gcp/templates/client-production-policy.example.json",
    "deploy/gcp/templates/client-production-handoff.example.json",
    "deploy/gcp/templates/client-production-readiness-checklist.example.json",
    "deploy/gcp/templates/client-production-package-index.example.json",
    "deploy/gcp/templates/client-production-backup-restore.example.json",
    "deploy/gcp/templates/client-production-operations-readiness.example.json",
    "scripts/validate_deployable_package.py",
    "scripts/validate_client_production_plan.py",
    "scripts/validate_client_handoff_evidence.py",
    "scripts/validate_client_readiness_checklist.py",
    "scripts/validate_client_package_index.py",
    "scripts/validate_client_backup_restore_evidence.py",
    "scripts/validate_client_operations_readiness_evidence.py",
)
REQUIRED_VALIDATOR_COMMANDS = {
    "deployable_package": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_deployable_package.py"
    ),
    "terraform_plan": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_production_plan.py <operator-held-plan.json>"
    ),
    "handoff_evidence": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_handoff_evidence.py <operator-held-handoff.json>"
    ),
    "readiness_checklist": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_readiness_checklist.py <operator-held-readiness.json>"
    ),
    "package_index": EXPECTED_VALIDATOR_COMMAND,
    "backup_restore_evidence": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_backup_restore_evidence.py <operator-held-backup-restore.json>"
    ),
    "operations_readiness_evidence": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_operations_readiness_evidence.py "
        "<operator-held-operations-readiness.json>"
    ),
}
MANUAL_ACCEPTANCE_KEYS = (
    "accessibility_review",
    "fluent_spanish_review",
    "staff_workflow_acceptance",
)
REQUIRED_ACTIVATION_BOUNDARY = {
    "production_deployment": "not-executed-without-separate-approval",
    "live_data_admission": "not-admitted-without-separate-approval",
    "shared_runtime_rollout": "not-executed-without-separate-approval",
}
FORBIDDEN_FRAGMENTS = (
    "allUsers",
    "allAuthenticatedUsers",
    "credential",
    "password",
    "payload",
    "secret",
    "token",
    "live client data admitted",
    "production deployed",
    "shared runtime rolled out",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class PackageIndexValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackageIndexValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PackageIndexValidationError("package index must contain a JSON object")
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise PackageIndexValidationError(f"missing object: {section}")
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
            raise PackageIndexValidationError("package index contains email-like value")
        if HTTP_URL_PATTERN.search(text):
            raise PackageIndexValidationError("package index contains concrete URL")
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise PackageIndexValidationError(
                    f"package index contains forbidden fragment: {fragment}"
                )


def _validate_safe_evidence(path: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise PackageIndexValidationError(f"{path} evidence must be filled")
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise PackageIndexValidationError(f"{path} evidence is not value-safe text")


def _validate_source_artifacts(document: dict[str, Any]) -> list[str]:
    value = document.get("source_artifacts")
    if not isinstance(value, list):
        raise PackageIndexValidationError("source_artifacts must be a list")
    seen_paths: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            raise PackageIndexValidationError("source_artifacts entries must be objects")
        path = item.get("path")
        if not isinstance(path, str):
            raise PackageIndexValidationError("source artifact path must be a string")
        if item.get("status") != "reviewed":
            raise PackageIndexValidationError(f"{path} status must be reviewed")
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise PackageIndexValidationError(f"{path} evidence is required")
        _validate_safe_evidence(path, evidence)
        seen_paths.append(path)
    if tuple(seen_paths) != REQUIRED_SOURCE_ARTIFACTS:
        raise PackageIndexValidationError("source_artifacts do not match package contract")
    return seen_paths


def validate_package_index(path: Path) -> list[str]:
    document = _load_document(path)
    _validate_value_safe(document)

    if document.get("index_type") != INDEX_TYPE:
        raise PackageIndexValidationError(f"index_type must be {INDEX_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise PackageIndexValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise PackageIndexValidationError(f"authority_boundary.{key} must be {expected}")

    checked = ["authority_boundary"]
    checked.extend(_validate_source_artifacts(document))

    commands = _section(document, "validator_commands")
    if commands != REQUIRED_VALIDATOR_COMMANDS:
        raise PackageIndexValidationError("validator_commands do not match package contract")
    checked.append("validator_commands")

    manual = _section(document, "manual_acceptance_boundary")
    for key in MANUAL_ACCEPTANCE_KEYS:
        value = manual.get(key)
        if value != "separate-review-required":
            raise PackageIndexValidationError(
                f"manual_acceptance_boundary.{key} must be separate-review-required"
            )
    checked.append("manual_acceptance_boundary")

    activation = _section(document, "activation_boundary")
    for key, expected in REQUIRED_ACTIVATION_BOUNDARY.items():
        if activation.get(key) != expected:
            raise PackageIndexValidationError(f"activation_boundary.{key} must be {expected}")
    checked.append("activation_boundary")
    return checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client deployable-package index JSON."
    )
    parser.add_argument(
        "package_index_json",
        type=Path,
        help="Operator-held value-safe package index JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_package_index(args.package_index_json)
    except PackageIndexValidationError as exc:
        print(f"client package index validation failed: {exc}", file=sys.stderr)
        return 1
    print("client package index validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
