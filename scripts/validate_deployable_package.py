from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

RUNBOOK_PATH = Path("deploy/gcp/client-owned-production-package-runbook.md")
ENV_TEMPLATE_PATH = Path("deploy/gcp/templates/client-production.env.example")
INPUTS_TEMPLATE_PATH = Path("deploy/gcp/templates/client-owned-gcp-inputs.example.json")
POLICY_TEMPLATE_PATH = Path("deploy/gcp/templates/client-production-policy.example.json")

REQUIRED_RUNBOOK_PHRASES = (
    "not an approval to inspect or",
    "client-owned deployment requires a separate explicit approval packet",
    "placeholder-only package",
    "Real project IDs",
    "Staff identity provider issuer",
    "recovery/session-revocation provider runbook owner",
    "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
    "scripts/validate_deployable_package.py",
    "authenticate to GCP",
    "Stop before drafting or executing any production deployment packet",
    "provider-side factor reset",
    "state backend lineage identifier",
    "client-production-policy.example.json",
    "scripts/validate_client_production_plan.py",
    "delete/replace actions",
    "public SQL exposure",
    "broad IAM",
    "missing staff identity configuration",
    "signed image/SBOM/provenance evidence",
)

REQUIRED_ENV_VALUES = {
    "GOLDEN_ROSE_ENVIRONMENT": "production",
    "GOLDEN_ROSE_AUTH_MODE": "staff_oidc",
    "GOLDEN_ROSE_SYNTHETIC_STAFF_ID": "<unset>",
    "GOLDEN_ROSE_DEMO_ACCESS_ENABLED": "false",
    "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD": "<unset>",
    "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT": "<unset>",
    "GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED": "false",
}

REQUIRED_ENV_PLACEHOLDERS = {
    "GOLDEN_ROSE_DATABASE_URL",
    "GOLDEN_ROSE_STAFF_OIDC_ISSUER",
    "GOLDEN_ROSE_STAFF_OIDC_AUDIENCE",
    "GOLDEN_ROSE_STAFF_OIDC_JWKS_URL",
}

REQUIRED_INPUT_POINTERS = (
    ("client_gcp", "project_id"),
    ("client_gcp", "region"),
    ("client_gcp", "billing_account_id"),
    ("state_backend", "bucket"),
    ("state_backend", "prefix"),
    ("artifact", "repository"),
    ("artifact", "image_digest"),
    ("identity", "workload_identity_provider"),
    ("identity", "staff_oidc_issuer"),
    ("identity", "staff_oidc_audience"),
    ("identity", "staff_oidc_jwks_url"),
    ("identity", "mfa_claim_mapping"),
    ("identity", "recovery_and_session_revocation_runbook"),
    ("secrets", "runtime_database_url"),
    ("secrets", "migration_database_url"),
    ("operations", "backup_restore_owner"),
    ("operations", "monitoring_owner"),
    ("operations", "incident_owner"),
    ("operations", "support_owner"),
    ("operations", "acceptance_owner"),
)

REQUIRED_POLICY_STRING_VALUES = {
    ("authority_boundary", "cloud_execution"): "separate-approval-required",
    ("authority_boundary", "terraform_plan"): "separate-approval-required",
    ("authority_boundary", "production_deployment"): "separate-approval-required",
    ("authority_boundary", "live_data_admission"): "separate-approval-required",
    ("authority_boundary", "provider_side_identity_activation"): "separate-approval-required",
    ("plan_review", "validator_command"): (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_production_plan.py <operator-held-plan.json>"
    ),
    ("production_environment", "environment"): "production",
    ("production_environment", "auth_mode"): "staff_oidc",
    ("production_environment", "synthetic_staff_id"): "<unset>",
}

REQUIRED_POLICY_BOOL_VALUES = {
    ("production_environment", "demo_access_enabled"): False,
    ("production_environment", "presentation_demo_seed_enabled"): False,
    ("production_environment", "staff_oidc_required"): True,
    ("production_environment", "mfa_claim_mapping_required"): True,
}

REQUIRED_POLICY_PLACEHOLDERS = (
    ("artifact_admission", "signature_evidence"),
    ("artifact_admission", "sbom_evidence"),
    ("artifact_admission", "provenance_evidence"),
    ("artifact_admission", "repository_subject_restriction"),
    ("handoff_evidence", "source_commit"),
    ("handoff_evidence", "migration_revision"),
    ("handoff_evidence", "database_authority_receipt"),
    ("handoff_evidence", "smoke_evidence"),
    ("handoff_evidence", "rollback_or_forward_recovery_note"),
    ("handoff_evidence", "owner_acceptance_checklist"),
)

REQUIRED_ALLOWED_PLAN_ACTIONS = ("no-op", "create", "update-in-place")
REQUIRED_FORBIDDEN_PLAN_ACTIONS = ("delete", "replace")
REQUIRED_FAIL_CLOSED_CHECKS = (
    "no_delete_or_replace_without_separate_approval",
    "no_public_sql_or_authorized_networks",
    "no_broad_iam_members",
    "immutable_image_digest_required",
    "staff_oidc_configuration_required",
    "demo_access_forbidden_in_production",
    "presentation_seed_forbidden_in_production",
    "secret_payloads_forbidden_in_source_or_plan",
    "database_authority_receipt_required",
    "backup_restore_owner_required",
    "monitoring_incident_support_owners_required",
)

FORBIDDEN_PACKAGE_FRAGMENTS = (
    "gcp-develop-private-synthetic",
    "golden-rose-dev",
    "staff-tracer-pr",
    "demo-access-password",
    "synthetic-staff-id",
    "allUsers",
    "allAuthenticatedUsers",
    "terraform apply",
    "gcloud run services update",
    "GOLDEN_ROSE_AUTH_MODE=synthetic",
    "GOLDEN_ROSE_DEMO_ACCESS_ENABLED=true",
    "GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED=true",
    '"auth_mode": "synthetic"',
    '"environment": "develop"',
    '"demo_access_enabled": true',
    '"presentation_demo_seed_enabled": true',
)

EMAIL_PATTERN = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HTTP_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


class PackageValidationError(ValueError):
    pass


def _read(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    if not path.is_file():
        raise PackageValidationError(f"missing required package file: {relative_path}")
    return path.read_text(encoding="utf-8")


def _validate_no_forbidden_values(relative_path: Path, text: str) -> None:
    for fragment in FORBIDDEN_PACKAGE_FRAGMENTS:
        if fragment in text:
            raise PackageValidationError(f"{relative_path} contains forbidden fragment: {fragment}")
    for match in EMAIL_PATTERN.findall(text):
        raise PackageValidationError(f"{relative_path} contains email-like value: {match}")
    for match in HTTP_URL_PATTERN.findall(text):
        raise PackageValidationError(f"{relative_path} contains concrete URL: {match}")


def _parse_env_template(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise PackageValidationError(f"{ENV_TEMPLATE_PATH}:{line_number} is not KEY=VALUE")
        key, value = line.split("=", 1)
        if not key or key in values:
            raise PackageValidationError(
                f"{ENV_TEMPLATE_PATH}:{line_number} has duplicate or empty key"
            )
        values[key] = value
    return values


def _validate_env_template(text: str) -> None:
    values = _parse_env_template(text)
    expected_keys = set(REQUIRED_ENV_VALUES) | REQUIRED_ENV_PLACEHOLDERS
    if set(values) != expected_keys:
        missing = sorted(expected_keys - set(values))
        extra = sorted(set(values) - expected_keys)
        raise PackageValidationError(
            f"{ENV_TEMPLATE_PATH} key mismatch; missing={missing} extra={extra}"
        )
    for key, expected in REQUIRED_ENV_VALUES.items():
        if values[key] != expected:
            raise PackageValidationError(f"{ENV_TEMPLATE_PATH} {key} must be {expected}")
    for key in REQUIRED_ENV_PLACEHOLDERS:
        value = values[key]
        if not (value.startswith("<") and value.endswith(">")):
            raise PackageValidationError(f"{ENV_TEMPLATE_PATH} {key} must remain a placeholder")


def _get_pointer(document: dict[str, Any], relative_path: Path, section: str, key: str) -> Any:
    value = document.get(section)
    if not isinstance(value, dict):
        raise PackageValidationError(f"{relative_path} missing object: {section}")
    if key not in value:
        raise PackageValidationError(f"{relative_path} missing key: {section}.{key}")
    return value[key]


def _is_placeholder(value: str) -> bool:
    return value.startswith("<") and value.endswith(">")


def _validate_inputs_template(text: str) -> None:
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PackageValidationError(f"{INPUTS_TEMPLATE_PATH} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PackageValidationError(f"{INPUTS_TEMPLATE_PATH} must contain a JSON object")
    for section, key in REQUIRED_INPUT_POINTERS:
        value = _get_pointer(document, INPUTS_TEMPLATE_PATH, section, key)
        if not isinstance(value, str) or not value.strip():
            raise PackageValidationError(
                f"{INPUTS_TEMPLATE_PATH} {section}.{key} must be a non-empty string"
            )
        if key == "image_digest":
            if value != "sha256:<64-hex-digest>":
                raise PackageValidationError(
                    f"{INPUTS_TEMPLATE_PATH} artifact.image_digest must remain a digest placeholder"
                )
        elif not _is_placeholder(value):
            raise PackageValidationError(
                f"{INPUTS_TEMPLATE_PATH} {section}.{key} must remain a placeholder"
            )


def _load_json_object(text: str, relative_path: Path) -> dict[str, Any]:
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PackageValidationError(f"{relative_path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PackageValidationError(f"{relative_path} must contain a JSON object")
    return document


def _expect_exact_list(
    *,
    document: dict[str, Any],
    section: str,
    key: str,
    expected: tuple[str, ...],
) -> None:
    value = _get_pointer(document, POLICY_TEMPLATE_PATH, section, key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PackageValidationError(
            f"{POLICY_TEMPLATE_PATH} {section}.{key} must be a string list"
        )
    if tuple(value) != expected:
        raise PackageValidationError(
            f"{POLICY_TEMPLATE_PATH} {section}.{key} must remain {list(expected)}"
        )


def _validate_policy_template(text: str) -> None:
    document = _load_json_object(text, POLICY_TEMPLATE_PATH)
    for (section, key), expected_text in REQUIRED_POLICY_STRING_VALUES.items():
        value = _get_pointer(document, POLICY_TEMPLATE_PATH, section, key)
        if value != expected_text:
            raise PackageValidationError(
                f"{POLICY_TEMPLATE_PATH} {section}.{key} must be {expected_text}"
            )
    for (section, key), expected_bool in REQUIRED_POLICY_BOOL_VALUES.items():
        value = _get_pointer(document, POLICY_TEMPLATE_PATH, section, key)
        if value is not expected_bool:
            raise PackageValidationError(
                f"{POLICY_TEMPLATE_PATH} {section}.{key} must be {expected_bool}"
            )
    for section, key in REQUIRED_POLICY_PLACEHOLDERS:
        value = _get_pointer(document, POLICY_TEMPLATE_PATH, section, key)
        if not isinstance(value, str) or not _is_placeholder(value):
            raise PackageValidationError(
                f"{POLICY_TEMPLATE_PATH} {section}.{key} must remain a placeholder"
            )
    image_digest = _get_pointer(
        document, POLICY_TEMPLATE_PATH, "artifact_admission", "image_digest"
    )
    if image_digest != "sha256:<64-hex-digest>":
        raise PackageValidationError(
            f"{POLICY_TEMPLATE_PATH} artifact_admission.image_digest must remain "
            "a digest placeholder"
        )
    _expect_exact_list(
        document=document,
        section="plan_review",
        key="allowed_actions",
        expected=REQUIRED_ALLOWED_PLAN_ACTIONS,
    )
    _expect_exact_list(
        document=document,
        section="plan_review",
        key="forbidden_actions",
        expected=REQUIRED_FORBIDDEN_PLAN_ACTIONS,
    )
    _expect_exact_list(
        document=document,
        section="plan_review",
        key="fail_closed_checks",
        expected=REQUIRED_FAIL_CLOSED_CHECKS,
    )


def _validate_runbook(text: str) -> None:
    for phrase in REQUIRED_RUNBOOK_PHRASES:
        if phrase not in text:
            raise PackageValidationError(f"{RUNBOOK_PATH} missing required phrase: {phrase}")


def validate(root: Path = ROOT) -> list[str]:
    runbook = _read(root, RUNBOOK_PATH)
    env_template = _read(root, ENV_TEMPLATE_PATH)
    inputs_template = _read(root, INPUTS_TEMPLATE_PATH)
    policy_template = _read(root, POLICY_TEMPLATE_PATH)
    for relative_path, text in (
        (RUNBOOK_PATH, runbook),
        (ENV_TEMPLATE_PATH, env_template),
        (INPUTS_TEMPLATE_PATH, inputs_template),
        (POLICY_TEMPLATE_PATH, policy_template),
    ):
        _validate_no_forbidden_values(relative_path, text)
    _validate_runbook(runbook)
    _validate_env_template(env_template)
    _validate_inputs_template(inputs_template)
    _validate_policy_template(policy_template)
    return [
        str(RUNBOOK_PATH),
        str(ENV_TEMPLATE_PATH),
        str(INPUTS_TEMPLATE_PATH),
        str(POLICY_TEMPLATE_PATH),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate placeholder-only deployable package artifacts."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root containing deploy/gcp package artifacts.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate(args.root)
    except PackageValidationError as exc:
        print(f"deployable package validation failed: {exc}", file=sys.stderr)
        return 1
    print("deployable package validation passed")
    for path in checked:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
