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

CHECKLIST_TYPE = "deployable-package-review-not-production-activation"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_readiness_checklist.py <operator-held-readiness.json>"
)
REQUIRED_BOUNDARIES = {
    "cloud_execution": "separate-approval-required",
    "terraform_plan": "separate-approval-required",
    "production_deployment": "separate-approval-required",
    "live_data_admission": "separate-approval-required",
    "provider_side_identity_activation": "separate-approval-required",
}
READY_SECTIONS = (
    "package_artifacts",
    "staff_identity",
    "terraform_plan_review",
    "artifact_admission",
    "handoff_evidence",
    "backup_restore_rehearsal",
    "operations_owners",
)
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


class ReadinessChecklistValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReadinessChecklistValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise ReadinessChecklistValidationError("readiness checklist must contain a JSON object")
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise ReadinessChecklistValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReadinessChecklistValidationError(f"{section}.{key} must be a non-empty string")
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
            raise ReadinessChecklistValidationError("readiness checklist contains email-like value")
        if HTTP_URL_PATTERN.search(text):
            raise ReadinessChecklistValidationError("readiness checklist contains concrete URL")
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise ReadinessChecklistValidationError(
                    f"readiness checklist contains forbidden fragment: {fragment}"
                )


def _validate_safe_evidence(section: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise ReadinessChecklistValidationError(f"{section}.evidence must be filled")
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise ReadinessChecklistValidationError(f"{section}.evidence is not value-safe text")


def validate_readiness_checklist(path: Path) -> list[str]:
    document = _load_document(path)
    _validate_value_safe(document)

    if document.get("checklist_type") != CHECKLIST_TYPE:
        raise ReadinessChecklistValidationError(f"checklist_type must be {CHECKLIST_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise ReadinessChecklistValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise ReadinessChecklistValidationError(f"authority_boundary.{key} must be {expected}")

    required_sections = document.get("required_sections")
    if required_sections != list(READY_SECTIONS) + ["manual_acceptance_boundary"]:
        raise ReadinessChecklistValidationError("required_sections does not match package contract")

    checked = ["authority_boundary"]
    for section_name in READY_SECTIONS:
        section = _section(document, section_name)
        if section.get("status") != "ready":
            raise ReadinessChecklistValidationError(f"{section_name}.status must be ready")
        evidence = section.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ReadinessChecklistValidationError(f"{section_name}.evidence is required")
        _validate_safe_evidence(section_name, evidence)
        checked.append(section_name)

    manual = _section(document, "manual_acceptance_boundary")
    for key in MANUAL_ACCEPTANCE_KEYS:
        value = manual.get(key)
        if value != "separate-review-required":
            raise ReadinessChecklistValidationError(
                f"manual_acceptance_boundary.{key} must be separate-review-required"
            )
    checked.append("manual_acceptance_boundary")

    activation = _section(document, "activation_boundary")
    for key, expected in REQUIRED_ACTIVATION_BOUNDARY.items():
        if activation.get(key) != expected:
            raise ReadinessChecklistValidationError(f"activation_boundary.{key} must be {expected}")
    checked.append("activation_boundary")
    return checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client deployable-package readiness JSON."
    )
    parser.add_argument(
        "readiness_json",
        type=Path,
        help="Operator-held value-safe readiness checklist JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_readiness_checklist(args.readiness_json)
    except ReadinessChecklistValidationError as exc:
        print(f"client readiness checklist validation failed: {exc}", file=sys.stderr)
        return 1
    print("client readiness checklist validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
