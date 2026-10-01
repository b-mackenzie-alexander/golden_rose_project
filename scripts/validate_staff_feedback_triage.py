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

EVIDENCE_TYPE = "staff-feedback-triage-review-not-acceptance"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_staff_feedback_triage.py "
    "<operator-held-staff-feedback-triage.json>"
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
}
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "triage_summary",
    "issue_counts",
    "evidence",
)
RECORDED_REVIEW_KEYS = (
    "feedback_window_scope_status",
    "issue_inventory_status",
    "blocker_disposition_status",
    "accessibility_impact_status",
    "privacy_impact_status",
    "security_impact_status",
    "defect_disposition_status",
    "retest_status",
    "migration_disposition_status",
    "known_limitations_status",
)
ISSUE_COUNT_KEYS = (
    "blocker_count",
    "high_count",
    "medium_count",
    "low_count",
    "open_count",
    "fixed_count",
    "deferred_count",
    "accepted_risk_count",
    "not_a_defect_count",
)
REQUIRED_EVIDENCE_TEXT = (
    "feedback_window_scope_note",
    "issue_inventory_note",
    "blocker_disposition_note",
    "accessibility_impact_note",
    "privacy_impact_note",
    "security_impact_note",
    "defect_disposition_note",
    "retest_note",
    "migration_disposition_note",
    "known_limitations_acknowledgement",
    "triage_owner",
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
    "staff feedback accepted",
    "client accepted",
    "client acceptance complete",
    "support channel activated",
    "business repository transferred",
    "github account created",
    "business account created",
    "data exported",
    "data imported",
    "data migrated",
    "current environment data migrated",
    "product complete",
    "complete product",
    "final product",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class StaffFeedbackTriageValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StaffFeedbackTriageValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise StaffFeedbackTriageValidationError(
            "staff feedback triage evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise StaffFeedbackTriageValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise StaffFeedbackTriageValidationError(f"{section}.{key} must be a non-empty string")
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
            raise StaffFeedbackTriageValidationError(
                "staff feedback triage evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise StaffFeedbackTriageValidationError(
                "staff feedback triage evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise StaffFeedbackTriageValidationError(
                    f"staff feedback triage evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise StaffFeedbackTriageValidationError(f"{section}.{key} must be filled")
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise StaffFeedbackTriageValidationError(f"{section}.{key} is not value-safe text")


def _validate_counts(document: dict[str, Any]) -> None:
    counts = _section(document, "issue_counts")
    for key in ISSUE_COUNT_KEYS:
        value = counts.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise StaffFeedbackTriageValidationError(
                f"issue_counts.{key} must be a non-negative integer"
            )
    severity_total = (
        counts["blocker_count"]
        + counts["high_count"]
        + counts["medium_count"]
        + counts["low_count"]
    )
    disposition_total = (
        counts["open_count"]
        + counts["fixed_count"]
        + counts["deferred_count"]
        + counts["accepted_risk_count"]
        + counts["not_a_defect_count"]
    )
    if severity_total != disposition_total:
        raise StaffFeedbackTriageValidationError(
            "issue_counts severity and disposition totals must match"
        )


def validate_staff_feedback_triage(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise StaffFeedbackTriageValidationError(f"evidence_type must be {EVIDENCE_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise StaffFeedbackTriageValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise StaffFeedbackTriageValidationError(f"authority_boundary.{key} must be {expected}")

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise StaffFeedbackTriageValidationError("source.source_commit must be a 40-character SHA")
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise StaffFeedbackTriageValidationError("source.migration_revision has invalid format")

    for key in RECORDED_REVIEW_KEYS:
        if _string(document, "triage_summary", key) != "recorded":
            raise StaffFeedbackTriageValidationError(f"triage_summary.{key} must be recorded")

    _validate_counts(document)

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe staff feedback triage evidence JSON."
    )
    parser.add_argument(
        "staff_feedback_triage_json",
        type=Path,
        help="Operator-held value-safe staff feedback triage evidence JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_staff_feedback_triage(args.staff_feedback_triage_json)
    except StaffFeedbackTriageValidationError as exc:
        print(f"staff feedback triage validation failed: {exc}", file=sys.stderr)
        return 1
    print("staff feedback triage validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
