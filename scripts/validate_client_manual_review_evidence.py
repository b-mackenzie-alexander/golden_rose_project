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

EVIDENCE_TYPE = "client-production-manual-accessibility-language-review-not-activation"
EXPECTED_VALIDATOR_COMMAND = (
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_client_manual_review_evidence.py "
    "<operator-held-manual-review.json>"
)
REQUIRED_BOUNDARIES = {
    "cloud_execution": "separate-approval-required",
    "production_deployment": "separate-approval-required",
    "live_data_admission": "separate-approval-required",
    "public_accessibility_claim": "separate-approval-required",
    "translation_certification": "separate-approval-required",
}
REQUIRED_SECTIONS = (
    "authority_boundary",
    "source",
    "manual_review",
    "evidence",
)
READY_REVIEW_KEYS = (
    "keyboard_navigation_status",
    "screen_reader_status",
    "reflow_status",
    "contrast_status",
    "fluent_spanish_status",
    "bilingual_parity_status",
)
REQUIRED_EVIDENCE_TEXT = (
    "keyboard_review_receipt",
    "screen_reader_review_receipt",
    "reflow_review_receipt",
    "contrast_review_receipt",
    "fluent_spanish_review_receipt",
    "bilingual_parity_receipt",
    "manual_review_owner",
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
    "public site published",
    "accessibility certified",
    "certified accessible",
    "wcag certified",
    "translation certified",
    "provider-side reset completed",
    "provider-side session revocation completed",
)


class ManualReviewEvidenceValidationError(ValueError):
    pass


def _load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManualReviewEvidenceValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise ManualReviewEvidenceValidationError(
            "manual review evidence must contain a JSON object"
        )
    return document


def _section(document: dict[str, Any], section: str) -> dict[str, Any]:
    value = document.get(section)
    if not isinstance(value, dict):
        raise ManualReviewEvidenceValidationError(f"missing object: {section}")
    return value


def _string(document: dict[str, Any], section: str, key: str) -> str:
    value = _section(document, section).get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManualReviewEvidenceValidationError(f"{section}.{key} must be a non-empty string")
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
            raise ManualReviewEvidenceValidationError(
                "manual review evidence contains email-like value"
            )
        if HTTP_URL_PATTERN.search(text):
            raise ManualReviewEvidenceValidationError(
                "manual review evidence contains concrete URL"
            )
        lowered = text.lower()
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in lowered:
                raise ManualReviewEvidenceValidationError(
                    f"manual review evidence contains forbidden fragment: {fragment}"
                )


def _validate_safe_text(section: str, key: str, value: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        raise ManualReviewEvidenceValidationError(
            f"{section}.{key} must be filled, not placeholder"
        )
    if not SAFE_TEXT_PATTERN.fullmatch(value):
        raise ManualReviewEvidenceValidationError(f"{section}.{key} is not value-safe text")


def validate_manual_review_evidence(path: Path) -> list[str]:
    document = _load_document(path)
    for section in REQUIRED_SECTIONS:
        _section(document, section)
    _validate_value_safe(document)

    if document.get("evidence_type") != EVIDENCE_TYPE:
        raise ManualReviewEvidenceValidationError(f"evidence_type must be {EVIDENCE_TYPE}")
    if document.get("validator_command") != EXPECTED_VALIDATOR_COMMAND:
        raise ManualReviewEvidenceValidationError("validator_command is not expected")

    boundary = _section(document, "authority_boundary")
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundary.get(key) != expected:
            raise ManualReviewEvidenceValidationError(
                f"authority_boundary.{key} must be {expected}"
            )

    source_commit = _string(document, "source", "source_commit")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise ManualReviewEvidenceValidationError("source.source_commit must be a 40-character SHA")
    migration_revision = _string(document, "source", "migration_revision")
    if not REVISION_PATTERN.fullmatch(migration_revision):
        raise ManualReviewEvidenceValidationError("source.migration_revision has invalid format")

    for key in READY_REVIEW_KEYS:
        if _string(document, "manual_review", key) != "ready":
            raise ManualReviewEvidenceValidationError(f"manual_review.{key} must be ready")

    for key in REQUIRED_EVIDENCE_TEXT:
        _validate_safe_text("evidence", key, _string(document, "evidence", key))

    return list(REQUIRED_SECTIONS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate value-safe client manual review evidence JSON."
    )
    parser.add_argument(
        "manual_review_json",
        type=Path,
        help="Operator-held value-safe manual accessibility and language review evidence JSON.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_manual_review_evidence(args.manual_review_json)
    except ManualReviewEvidenceValidationError as exc:
        print(f"client manual review evidence validation failed: {exc}", file=sys.stderr)
        return 1
    print("client manual review evidence validation passed")
    for section in checked:
        print(f"- {section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
