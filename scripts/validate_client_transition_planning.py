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

EVIDENCE_TYPE = "client-environment-transition-planning-not-execution"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_transition_planning.py "
    "<operator-held-client-transition-planning.json>"
)
REQUIRED_BOUNDARIES = {
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
}
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "transition_planning",
    "evidence",
)
READY_REVIEW_KEYS = (
    "management_model_status",
    "current_environment_record_inventory_status",
    "data_classification_status",
    "migration_candidate_scope_status",
    "export_import_strategy_status",
    "identity_access_transition_status",
    "repository_stewardship_status",
    "business_account_decision_status",
    "support_ownership_status",
    "rollback_or_abandonment_status",
    "known_limitations_status",
)
REQUIRED_EVIDENCE_TEXT = (
    "management_model_note",
    "record_inventory_note",
    "data_classification_note",
    "migration_candidate_scope_note",
    "export_import_strategy_note",
    "identity_access_transition_note",
    "repository_stewardship_note",
    "business_account_decision_note",
    "support_ownership_note",
    "rollback_or_abandonment_note",
    "known_limitations_acknowledgement",
    "transition_owner",
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
    "data exported",
    "data imported",
    "data migrated",
    "export executed",
    "import executed",
    "destructive cleanup executed",
    "client environment transitioned",
    "client-owned environment transitioned",
    "github account created",
    "business account created",
    "repository transferred",
    "credential rotated",
    "support channel activated",
    "product complete",
    "complete product",
    "final product",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class ClientTransitionPlanningValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ClientTransitionPlanningValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise ClientTransitionPlanningValidationError(
            "client transition planning evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise ClientTransitionPlanningValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise ClientTransitionPlanningValidationError(f"{section}.{key} must be a non-empty string")
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
            raise ClientTransitionPlanningValidationError(
                "client transition planning evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise ClientTransitionPlanningValidationError(
                "client transition planning evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise ClientTransitionPlanningValidationError(
                    f"client transition planning evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise ClientTransitionPlanningValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise ClientTransitionPlanningValidationError(f"{section}.{key} is not value-safe text")


def validate_client_transition_planning(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise ClientTransitionPlanningValidationError(f"evidence_type must be {EVIDENCE_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise ClientTransitionPlanningValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise ClientTransitionPlanningValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise ClientTransitionPlanningValidationError(
            "source.source_commit must be a 40-character SHA"
        )
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise ClientTransitionPlanningValidationError(
            "source.migration_revision has invalid format"
        )

    for key in READY_REVIEW_KEYS:
        if _string(document, "transition_planning", key) != "ready":
            raise ClientTransitionPlanningValidationError(
                f"transition_planning.{key} must be ready"
            )

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client transition planning evidence JSON."
    )
    parser.add_argument(
        "client_transition_planning_json",
        type=Path,
        help="Operator-held value-safe client transition planning evidence JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_client_transition_planning(args.client_transition_planning_json)
    except ClientTransitionPlanningValidationError as exc:
        print(f"client transition planning validation failed: {exc}", file=sys.stderr)
        return 1
    print("client transition planning validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
