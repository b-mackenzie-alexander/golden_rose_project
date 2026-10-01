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

EVIDENCE_TYPE = "staff-feedback-activation-approval-not-execution"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_staff_feedback_activation_approval.py "
    "<operator-held-staff-feedback-activation-approval.json>"
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
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "prerequisites",
    "approval_decision",
    "activation_boundary",
    "evidence",
)
READY_PREREQUISITE_KEYS = (
    "staff_feedback_readiness_status",
    "staff_feedback_package_index_status",
    "staff_feedback_triage_process_status",
    "training_known_limitations_status",
    "staff_access_scope_status",
    "data_entry_scope_status",
    "support_escalation_status",
    "rollback_closeout_status",
    "migration_disposition_status",
)
REQUIRED_APPROVAL_DECISION = {
    "decision_status": "approved_for_bounded_staff_feedback",
    "scope_limit": "current-environment-feedback-only",
    "activation_execution": "not-executed-by-this-record",
    "live_data_boundary": "not-admitted-without-separate-approval",
    "support_boundary": "not-activated-without-separate-approval",
}
REQUIRED_ACTIVATION_BOUNDARY = {
    "staff_feedback_window": "not-activated-by-this-record",
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
REQUIRED_EVIDENCE_TEXT = (
    "readiness_review_receipt",
    "package_index_receipt",
    "triage_process_receipt",
    "training_known_limitations_receipt",
    "staff_access_scope_note",
    "data_entry_scope_note",
    "support_escalation_note",
    "rollback_closeout_note",
    "migration_disposition_note",
    "approval_owner",
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
    "staff feedback activated",
    "daily staff use activated",
    "runtime access changed",
    "support channel activated",
    "business repository transferred",
    "github account created",
    "business account created",
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


class StaffFeedbackActivationApprovalValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StaffFeedbackActivationApprovalValidationError(
            f"{path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise StaffFeedbackActivationApprovalValidationError(
            "staff feedback activation approval evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise StaffFeedbackActivationApprovalValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise StaffFeedbackActivationApprovalValidationError(
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
            raise StaffFeedbackActivationApprovalValidationError(
                "staff feedback activation approval evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise StaffFeedbackActivationApprovalValidationError(
                "staff feedback activation approval evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise StaffFeedbackActivationApprovalValidationError(
                    "staff feedback activation approval evidence contains "
                    f"forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise StaffFeedbackActivationApprovalValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise StaffFeedbackActivationApprovalValidationError(
            f"{section}.{key} is not value-safe text"
        )


def validate_staff_feedback_activation_approval(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise StaffFeedbackActivationApprovalValidationError(
            f"evidence_type must be {EVIDENCE_TYPE}"
        )
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise StaffFeedbackActivationApprovalValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise StaffFeedbackActivationApprovalValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise StaffFeedbackActivationApprovalValidationError(
            "source.source_commit must be a 40-character SHA"
        )
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise StaffFeedbackActivationApprovalValidationError(
            "source.migration_revision has invalid format"
        )

    for key in READY_PREREQUISITE_KEYS:
        if _string(document, "prerequisites", key) != "ready":
            raise StaffFeedbackActivationApprovalValidationError(
                f"prerequisites.{key} must be ready"
            )

    decision = _section(document, "approval_decision")
    for key, expected in REQUIRED_APPROVAL_DECISION.items():
        if decision.get(key) != expected:
            raise StaffFeedbackActivationApprovalValidationError(
                f"approval_decision.{key} must be {expected}"
            )

    activation = _section(document, "activation_boundary")
    for key, expected in REQUIRED_ACTIVATION_BOUNDARY.items():
        if activation.get(key) != expected:
            raise StaffFeedbackActivationApprovalValidationError(
                f"activation_boundary.{key} must be {expected}"
            )

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe staff feedback activation approval JSON."
    )
    parser.add_argument(
        "staff_feedback_activation_approval_json",
        type=Path,
        help="Operator-held value-safe staff feedback activation approval JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_staff_feedback_activation_approval(
            args.staff_feedback_activation_approval_json
        )
    except StaffFeedbackActivationApprovalValidationError as exc:
        print(f"staff feedback activation approval validation failed: {exc}", file=sys.stderr)
        return 1
    print("staff feedback activation approval validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
