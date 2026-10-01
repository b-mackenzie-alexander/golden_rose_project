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

EVIDENCE_TYPE = "staff-feedback-activation-receipt-not-production"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_staff_feedback_activation_receipt.py "
    "<operator-held-staff-feedback-activation-receipt.json>"
)
REQUIRED_BOUNDARIES = {
    "cloud_execution": "operator-held-separate-approval-required",
    "runtime_access_change": "operator-held-separate-approval-required",
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
    "preconditions",
    "execution_receipt",
    "retained_boundaries",
    "evidence",
)
READY_PRECONDITION_KEYS = (
    "activation_approval_status",
    "staff_feedback_package_index_status",
    "staff_feedback_readiness_status",
    "staff_access_scope_status",
    "data_entry_scope_status",
    "expiration_or_closeout_status",
    "rollback_status",
)
REQUIRED_EXECUTION_RECEIPT = {
    "receipt_scope": "current-environment-feedback-only",
    "source_artifact_effect": "records-operator-held-execution-only",
    "feedback_window_status": "opened_for_bounded_current_environment_feedback",
    "staff_access_scope": "bounded_current_environment_staff_access",
    "data_entry_scope": "bounded_by_approved_feedback_scope",
    "expiration_or_closeout": "required",
}
REQUIRED_RETAINED_BOUNDARIES = {
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
    "product_completion_claim": "not-claimed",
}
REQUIRED_EVIDENCE_TEXT = (
    "activation_approval_receipt",
    "package_index_receipt",
    "staff_access_scope_receipt",
    "data_entry_scope_receipt",
    "expiration_or_closeout_receipt",
    "rollback_receipt",
    "no_store_auth_sensitive_receipt",
    "support_escalation_note",
    "operator_owner",
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


class StaffFeedbackActivationReceiptValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StaffFeedbackActivationReceiptValidationError(
            f"{path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise StaffFeedbackActivationReceiptValidationError(
            "staff feedback activation receipt must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise StaffFeedbackActivationReceiptValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise StaffFeedbackActivationReceiptValidationError(
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
            raise StaffFeedbackActivationReceiptValidationError(
                "staff feedback activation receipt contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise StaffFeedbackActivationReceiptValidationError(
                "staff feedback activation receipt contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise StaffFeedbackActivationReceiptValidationError(
                    f"staff feedback activation receipt contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise StaffFeedbackActivationReceiptValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise StaffFeedbackActivationReceiptValidationError(
            f"{section}.{key} is not value-safe text"
        )


def validate_staff_feedback_activation_receipt(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise StaffFeedbackActivationReceiptValidationError(
            f"evidence_type must be {EVIDENCE_TYPE}"
        )
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise StaffFeedbackActivationReceiptValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise StaffFeedbackActivationReceiptValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise StaffFeedbackActivationReceiptValidationError(
            "source.source_commit must be a 40-character SHA"
        )
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise StaffFeedbackActivationReceiptValidationError(
            "source.migration_revision has invalid format"
        )

    for key in READY_PRECONDITION_KEYS:
        if _string(document, "preconditions", key) != "ready":
            raise StaffFeedbackActivationReceiptValidationError(
                f"preconditions.{key} must be ready"
            )

    receipt = _section(document, "execution_receipt")
    for key, expected in REQUIRED_EXECUTION_RECEIPT.items():
        if receipt.get(key) != expected:
            raise StaffFeedbackActivationReceiptValidationError(
                f"execution_receipt.{key} must be {expected}"
            )

    retained = _section(document, "retained_boundaries")
    for key, expected in REQUIRED_RETAINED_BOUNDARIES.items():
        if retained.get(key) != expected:
            raise StaffFeedbackActivationReceiptValidationError(
                f"retained_boundaries.{key} must be {expected}"
            )

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe staff feedback activation receipt JSON."
    )
    parser.add_argument(
        "staff_feedback_activation_receipt_json",
        type=Path,
        help="Operator-held value-safe staff feedback activation receipt JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_staff_feedback_activation_receipt(
            args.staff_feedback_activation_receipt_json
        )
    except StaffFeedbackActivationReceiptValidationError as exc:
        print(f"staff feedback activation receipt validation failed: {exc}", file=sys.stderr)
        return 1
    print("staff feedback activation receipt validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
