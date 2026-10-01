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

INDEX_TYPE = "staff-feedback-package-index-not-activation"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_staff_feedback_package_index.py "
    "<operator-held-staff-feedback-package-index.json>"
)
REQUIRED_BOUNDARIES = {
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
}
REQUIRED_SOURCE_ARTIFACTS = (
    "docs/planning/2026-09-27-production-readiness-plan.md",
    "deploy/gcp/staff-feedback-readiness-runbook.md",
    "deploy/gcp/templates/staff-feedback-readiness.example.json",
    "scripts/validate_staff_feedback_readiness.py",
    "deploy/gcp/client-transition-planning-runbook.md",
    "deploy/gcp/templates/client-transition-planning.example.json",
    "scripts/validate_client_transition_planning.py",
    "deploy/gcp/human-feedback-template.md",
    "deploy/gcp/human-qualification-checklist.md",
    "deploy/gcp/qualification-status-contract.md",
    "deploy/gcp/templates/staff-feedback-triage.example.json",
    "scripts/validate_staff_feedback_triage.py",
    "deploy/gcp/templates/staff-feedback-package-index.example.json",
    "scripts/validate_staff_feedback_package_index.py",
)
REQUIRED_VALIDATOR_COMMANDS = {
    "staff_feedback_readiness": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_staff_feedback_readiness.py "
        "<operator-held-staff-feedback-readiness.json>"
    ),
    "client_transition_planning": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_transition_planning.py "
        "<operator-held-client-transition-planning.json>"
    ),
    "staff_feedback_triage": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_staff_feedback_triage.py "
        "<operator-held-staff-feedback-triage.json>"
    ),
    "staff_feedback_package_index": EXPECTED_VALIDATOR_COMMAND,
}
REQUIRED_ACTIVATION_BOUNDARY = {
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
}
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
    "staff feedback activated",
    "daily staff use activated",
    "runtime access changed",
    "support channel activated",
    "business repository transferred",
    "github account created",
    "business account created",
    "repository transferred",
    "data exported",
    "data imported",
    "data migrated",
    "current environment data migrated",
    "client environment transitioned",
    "client-owned environment transitioned",
    "product complete",
    "complete product",
    "final product",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class StaffFeedbackPackageIndexValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StaffFeedbackPackageIndexValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise StaffFeedbackPackageIndexValidationError(
            "staff feedback package index must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise StaffFeedbackPackageIndexValidationError(f"missing object: {section}")
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
            raise StaffFeedbackPackageIndexValidationError(
                "staff feedback package index contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise StaffFeedbackPackageIndexValidationError(
                "staff feedback package index contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise StaffFeedbackPackageIndexValidationError(
                    f"staff feedback package index contains forbidden fragment: {fragment}"
                )


def _validate_safe_evidence(path: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise StaffFeedbackPackageIndexValidationError(f"{path} evidence must be filled")
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise StaffFeedbackPackageIndexValidationError(f"{path} evidence is not value-safe text")


def _validate_source_artifacts(document: dict[str, Any]) -> list[str]:
    value = document.get("source_artifacts")
    if not isinstance(value, list):
        raise StaffFeedbackPackageIndexValidationError("source_artifacts must be a list")
    seen_paths: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            raise StaffFeedbackPackageIndexValidationError(
                "source_artifacts entries must be objects"
            )
        path = item.get("path")
        if not isinstance(path, str):
            raise StaffFeedbackPackageIndexValidationError("source artifact path must be a string")
        if item.get("status") != "reviewed":
            raise StaffFeedbackPackageIndexValidationError(f"{path} status must be reviewed")
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise StaffFeedbackPackageIndexValidationError(f"{path} evidence is required")
        _validate_safe_evidence(path, evidence)
        seen_paths.append(path)
    if tuple(seen_paths) != REQUIRED_SOURCE_ARTIFACTS:
        raise StaffFeedbackPackageIndexValidationError(
            "source_artifacts do not match staff feedback package contract"
        )
    return seen_paths


def validate_staff_feedback_package_index(path: Path) -> list[str]:
    document = _load_document(path)
    _validate_value_safe(document)

    if document.get("index_type") != INDEX_TYPE:
        raise StaffFeedbackPackageIndexValidationError(f"index_type must be {INDEX_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise StaffFeedbackPackageIndexValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise StaffFeedbackPackageIndexValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    checked = ["authority_boundary"]
    checked.extend(_validate_source_artifacts(document))

    commands = _section(document, "validator_commands")
    if commands != REQUIRED_VALIDATOR_COMMANDS:
        raise StaffFeedbackPackageIndexValidationError(
            "validator_commands do not match staff feedback package contract"
        )
    checked.append("validator_commands")

    activation = _section(document, "activation_boundary")
    for key, expected in REQUIRED_ACTIVATION_BOUNDARY.items():
        if activation.get(key) != expected:
            raise StaffFeedbackPackageIndexValidationError(
                f"activation_boundary.{key} must be {expected}"
            )
    checked.append("activation_boundary")
    return checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe staff feedback package index JSON."
    )
    parser.add_argument(
        "staff_feedback_package_index_json",
        type=Path,
        help="Operator-held value-safe staff feedback package index JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_staff_feedback_package_index(args.staff_feedback_package_index_json)
    except StaffFeedbackPackageIndexValidationError as exc:
        print(f"staff feedback package index validation failed: {exc}", file=sys.stderr)
        return 1
    print("staff feedback package index validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
