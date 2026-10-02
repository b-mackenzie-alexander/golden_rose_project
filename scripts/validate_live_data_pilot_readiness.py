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

EVIDENCE_TYPE = "controlled-live-data-staff-pilot-readiness"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_live_data_pilot_readiness.py "
    "<operator-held-live-data-pilot-readiness.json>"
)
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "pilot_readiness",
    "deployment_preconditions",
    "retained_boundaries",
    "evidence",
)
REQUIRED_AUTHORITY_BOUNDARIES = {
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
}
READY_REVIEW_KEYS = (
    "operating_boundary_status",
    "live_data_scope_status",
    "staff_identity_status",
    "staff_account_status",
    "no_store_auth_sensitive_status",
    "demo_and_seed_removal_status",
    "static_fallback_status",
    "backup_restore_status",
    "migration_disposition_status",
    "data_governance_status",
    "support_escalation_status",
    "staff_training_status",
    "manual_acceptance_status",
    "rollback_closeout_status",
    "known_limitations_status",
)
REQUIRED_DEPLOYMENT_PRECONDITIONS = {
    "runtime_environment": "production-mode-controlled-staff-pilot",
    "auth_mode": "staff_oidc",
    "environment_marker": "controlled-live-data-staff-pilot",
    "presentation_seed": "disabled",
    "shared_demo_access": "disabled",
    "static_operational_examples": "disabled",
    "named_staff_accounts": "required",
    "live_data_scope": "worker-and-employer-intake-records-only",
}
REQUIRED_RETAINED_BOUNDARIES = {
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
}
REQUIRED_EVIDENCE_TEXT = (
    "operating_boundary_note",
    "live_data_scope_note",
    "staff_identity_receipt",
    "staff_account_receipt",
    "no_store_auth_sensitive_receipt",
    "demo_and_seed_removal_receipt",
    "static_fallback_receipt",
    "backup_restore_receipt",
    "migration_disposition_note",
    "data_governance_note",
    "support_escalation_note",
    "staff_training_note",
    "manual_acceptance_note",
    "rollback_closeout_note",
    "known_limitations_acknowledgement",
    "readiness_owner",
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
    "synthetic",
    "fictional",
    "sample data",
    "test data",
    "presentation seed enabled",
    "shared demo access enabled",
    "production deployed",
    "shared runtime rolled out",
    "terraform apply",
    "gcloud",
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
    "destructive cleanup completed",
    "records deleted",
    "product complete",
    "complete product",
    "final product",
    "public portal activated",
    "automated matching",
    "automated ranking",
    "automated referral",
    "automated placement",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class LiveDataPilotReadinessValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LiveDataPilotReadinessValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise LiveDataPilotReadinessValidationError(
            "live-data pilot readiness evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise LiveDataPilotReadinessValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise LiveDataPilotReadinessValidationError(f"{section}.{key} must be a non-empty string")
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
            raise LiveDataPilotReadinessValidationError(
                "live-data pilot readiness evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise LiveDataPilotReadinessValidationError(
                "live-data pilot readiness evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise LiveDataPilotReadinessValidationError(
                    f"live-data pilot readiness evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise LiveDataPilotReadinessValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise LiveDataPilotReadinessValidationError(f"{section}.{key} is not value-safe text")


def validate_live_data_pilot_readiness(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise LiveDataPilotReadinessValidationError(f"evidence_type must be {EVIDENCE_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise LiveDataPilotReadinessValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_AUTHORITY_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise LiveDataPilotReadinessValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise LiveDataPilotReadinessValidationError(
            "source.source_commit must be a 40-character SHA"
        )
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise LiveDataPilotReadinessValidationError("source.migration_revision has invalid format")

    for key in READY_REVIEW_KEYS:
        if _string(document, "pilot_readiness", key) != "ready":
            raise LiveDataPilotReadinessValidationError(f"pilot_readiness.{key} must be ready")

    preconditions = _section(document, "deployment_preconditions")
    for key, expected in REQUIRED_DEPLOYMENT_PRECONDITIONS.items():
        if preconditions.get(key) != expected:
            raise LiveDataPilotReadinessValidationError(
                f"deployment_preconditions.{key} must be {expected}"
            )

    retained = _section(document, "retained_boundaries")
    for key, expected in REQUIRED_RETAINED_BOUNDARIES.items():
        if retained.get(key) != expected:
            raise LiveDataPilotReadinessValidationError(
                f"retained_boundaries.{key} must be {expected}"
            )

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe controlled live-data staff pilot readiness JSON."
    )
    parser.add_argument(
        "live_data_pilot_readiness_json",
        type=Path,
        help="Operator-held value-safe live-data pilot readiness JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_live_data_pilot_readiness(args.live_data_pilot_readiness_json)
    except LiveDataPilotReadinessValidationError as exc:
        print(f"live-data pilot readiness validation failed: {exc}", file=sys.stderr)
        return 1
    print("live-data pilot readiness validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
