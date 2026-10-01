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
HANDOFF_TEMPLATE_PATH = Path("deploy/gcp/templates/client-production-handoff.example.json")
READINESS_CHECKLIST_PATH = Path(
    "deploy/gcp/templates/client-production-readiness-checklist.example.json"
)
PACKAGE_INDEX_PATH = Path("deploy/gcp/templates/client-production-package-index.example.json")
BACKUP_RESTORE_TEMPLATE_PATH = Path(
    "deploy/gcp/templates/client-production-backup-restore.example.json"
)
OPERATIONS_READINESS_TEMPLATE_PATH = Path(
    "deploy/gcp/templates/client-production-operations-readiness.example.json"
)

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
    "client-production-handoff.example.json",
    "client-production-readiness-checklist.example.json",
    "client-production-package-index.example.json",
    "client-production-backup-restore.example.json",
    "client-production-operations-readiness.example.json",
    "scripts/validate_client_production_plan.py",
    "scripts/validate_client_handoff_evidence.py",
    "scripts/validate_client_readiness_checklist.py",
    "scripts/validate_client_package_index.py",
    "scripts/validate_client_backup_restore_evidence.py",
    "scripts/validate_client_operations_readiness_evidence.py",
    "delete/replace actions",
    "public SQL exposure",
    "broad IAM",
    "missing staff identity configuration",
    "signed image/SBOM/provenance evidence",
    "validate_client_backup_restore_evidence.py <operator-held-backup-restore.json>",
    "validate_client_operations_readiness_evidence.py <operator-held-operations-readiness.json>",
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

REQUIRED_HANDOFF_STRING_VALUES = {
    ("authority_boundary", "cloud_execution"): "separate-approval-required",
    ("authority_boundary", "production_deployment"): "separate-approval-required",
    ("authority_boundary", "live_data_admission"): "separate-approval-required",
    ("plan_review", "validator_command"): (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_production_plan.py <operator-held-plan.json>"
    ),
}

REQUIRED_HANDOFF_PLACEHOLDERS = (
    ("source", "source_commit"),
    ("source", "migration_revision"),
    ("artifact_admission", "signature_evidence"),
    ("artifact_admission", "sbom_evidence"),
    ("artifact_admission", "provenance_evidence"),
    ("artifact_admission", "repository_subject_restriction"),
    ("plan_review", "status"),
    ("database_authority", "receipt"),
    ("database_authority", "status"),
    ("smoke", "health"),
    ("smoke", "readiness"),
    ("smoke", "staff_entry_boundary"),
    ("recovery", "rollback_or_forward_recovery_note"),
    ("recovery", "status"),
    ("operations", "backup_restore_owner"),
    ("operations", "monitoring_owner"),
    ("operations", "incident_owner"),
    ("operations", "support_owner"),
    ("owner_acceptance", "acceptance_checklist"),
    ("owner_acceptance", "status"),
)

REQUIRED_READINESS_STRING_VALUES = {
    ("authority_boundary", "cloud_execution"): "separate-approval-required",
    ("authority_boundary", "terraform_plan"): "separate-approval-required",
    ("authority_boundary", "production_deployment"): "separate-approval-required",
    ("authority_boundary", "live_data_admission"): "separate-approval-required",
    ("authority_boundary", "provider_side_identity_activation"): "separate-approval-required",
    ("activation_boundary", "production_deployment"): ("not-executed-without-separate-approval"),
    ("activation_boundary", "live_data_admission"): "not-admitted-without-separate-approval",
    ("activation_boundary", "shared_runtime_rollout"): ("not-executed-without-separate-approval"),
}

REQUIRED_READINESS_PLACEHOLDERS = (
    ("package_artifacts", "status"),
    ("package_artifacts", "evidence"),
    ("staff_identity", "status"),
    ("staff_identity", "evidence"),
    ("terraform_plan_review", "status"),
    ("terraform_plan_review", "evidence"),
    ("artifact_admission", "status"),
    ("artifact_admission", "evidence"),
    ("handoff_evidence", "status"),
    ("handoff_evidence", "evidence"),
    ("backup_restore_rehearsal", "status"),
    ("backup_restore_rehearsal", "evidence"),
    ("operations_readiness", "status"),
    ("operations_readiness", "evidence"),
    ("operations_owners", "status"),
    ("operations_owners", "evidence"),
    ("manual_acceptance_boundary", "accessibility_review"),
    ("manual_acceptance_boundary", "fluent_spanish_review"),
    ("manual_acceptance_boundary", "staff_workflow_acceptance"),
)

REQUIRED_READINESS_SECTIONS = (
    "package_artifacts",
    "staff_identity",
    "terraform_plan_review",
    "artifact_admission",
    "handoff_evidence",
    "backup_restore_rehearsal",
    "operations_readiness",
    "operations_owners",
    "manual_acceptance_boundary",
)

REQUIRED_PACKAGE_INDEX_STRING_VALUES = {
    ("authority_boundary", "cloud_execution"): "separate-approval-required",
    ("authority_boundary", "terraform_plan"): "separate-approval-required",
    ("authority_boundary", "production_deployment"): "separate-approval-required",
    ("authority_boundary", "live_data_admission"): "separate-approval-required",
    ("authority_boundary", "provider_side_identity_activation"): "separate-approval-required",
    ("activation_boundary", "production_deployment"): ("not-executed-without-separate-approval"),
    ("activation_boundary", "live_data_admission"): "not-admitted-without-separate-approval",
    ("activation_boundary", "shared_runtime_rollout"): ("not-executed-without-separate-approval"),
}

REQUIRED_PACKAGE_INDEX_SOURCE_ARTIFACTS = (
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

REQUIRED_PACKAGE_INDEX_VALIDATOR_COMMANDS = {
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
    "package_index": (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_package_index.py <operator-held-package-index.json>"
    ),
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

REQUIRED_PACKAGE_INDEX_MANUAL_BOUNDARY = {
    "accessibility_review": "<not-run-or-separate-record>",
    "fluent_spanish_review": "<not-run-or-separate-record>",
    "staff_workflow_acceptance": "<not-run-or-separate-record>",
}

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


def _validate_handoff_template(text: str) -> None:
    document = _load_json_object(text, HANDOFF_TEMPLATE_PATH)
    for (section, key), expected_text in REQUIRED_HANDOFF_STRING_VALUES.items():
        value = _get_pointer(document, HANDOFF_TEMPLATE_PATH, section, key)
        if value != expected_text:
            raise PackageValidationError(
                f"{HANDOFF_TEMPLATE_PATH} {section}.{key} must be {expected_text}"
            )
    image_digest = _get_pointer(
        document, HANDOFF_TEMPLATE_PATH, "artifact_admission", "image_digest"
    )
    if image_digest != "sha256:<64-hex-digest>":
        raise PackageValidationError(
            f"{HANDOFF_TEMPLATE_PATH} artifact_admission.image_digest must remain "
            "a digest placeholder"
        )
    for section, key in REQUIRED_HANDOFF_PLACEHOLDERS:
        value = _get_pointer(document, HANDOFF_TEMPLATE_PATH, section, key)
        if not isinstance(value, str) or not _is_placeholder(value):
            raise PackageValidationError(
                f"{HANDOFF_TEMPLATE_PATH} {section}.{key} must remain a placeholder"
            )


def _validate_readiness_checklist_template(text: str) -> None:
    document = _load_json_object(text, READINESS_CHECKLIST_PATH)
    if document.get("checklist_type") != "deployable-package-review-not-production-activation":
        raise PackageValidationError(
            f"{READINESS_CHECKLIST_PATH} checklist_type must distinguish package review"
        )
    expected_command = (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_readiness_checklist.py <operator-held-readiness.json>"
    )
    if document.get("validator_command") != expected_command:
        raise PackageValidationError(
            f"{READINESS_CHECKLIST_PATH} validator_command must be {expected_command}"
        )
    required_sections = document.get("required_sections")
    if required_sections != list(REQUIRED_READINESS_SECTIONS):
        raise PackageValidationError(
            f"{READINESS_CHECKLIST_PATH} required_sections must remain package-review scoped"
        )
    for (section, key), expected_text in REQUIRED_READINESS_STRING_VALUES.items():
        value = _get_pointer(document, READINESS_CHECKLIST_PATH, section, key)
        if value != expected_text:
            raise PackageValidationError(
                f"{READINESS_CHECKLIST_PATH} {section}.{key} must be {expected_text}"
            )
    for section, key in REQUIRED_READINESS_PLACEHOLDERS:
        value = _get_pointer(document, READINESS_CHECKLIST_PATH, section, key)
        if not isinstance(value, str) or not _is_placeholder(value):
            raise PackageValidationError(
                f"{READINESS_CHECKLIST_PATH} {section}.{key} must remain a placeholder"
            )


def _validate_package_index_template(text: str) -> None:
    document = _load_json_object(text, PACKAGE_INDEX_PATH)
    if (
        document.get("index_type")
        != "client-owned-deployable-package-index-not-production-activation"
    ):
        raise PackageValidationError(
            f"{PACKAGE_INDEX_PATH} index_type must distinguish package review"
        )
    expected_command = (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_package_index.py <operator-held-package-index.json>"
    )
    if document.get("validator_command") != expected_command:
        raise PackageValidationError(
            f"{PACKAGE_INDEX_PATH} validator_command must be {expected_command}"
        )
    for (section, key), expected_text in REQUIRED_PACKAGE_INDEX_STRING_VALUES.items():
        value = _get_pointer(document, PACKAGE_INDEX_PATH, section, key)
        if value != expected_text:
            raise PackageValidationError(
                f"{PACKAGE_INDEX_PATH} {section}.{key} must be {expected_text}"
            )
    commands = document.get("validator_commands")
    if commands != REQUIRED_PACKAGE_INDEX_VALIDATOR_COMMANDS:
        raise PackageValidationError(
            f"{PACKAGE_INDEX_PATH} validator_commands must remain package-review scoped"
        )
    manual = document.get("manual_acceptance_boundary")
    if manual != REQUIRED_PACKAGE_INDEX_MANUAL_BOUNDARY:
        raise PackageValidationError(
            f"{PACKAGE_INDEX_PATH} manual_acceptance_boundary must remain separate"
        )
    artifacts = document.get("source_artifacts")
    if not isinstance(artifacts, list):
        raise PackageValidationError(f"{PACKAGE_INDEX_PATH} source_artifacts must be a list")
    seen_paths: list[str] = []
    for item in artifacts:
        if not isinstance(item, dict):
            raise PackageValidationError(
                f"{PACKAGE_INDEX_PATH} source_artifacts entries must be objects"
            )
        path = item.get("path")
        if not isinstance(path, str):
            raise PackageValidationError(
                f"{PACKAGE_INDEX_PATH} source_artifacts path must be a string"
            )
        seen_paths.append(path)
        status = item.get("status")
        evidence = item.get("evidence")
        if not isinstance(status, str) or not _is_placeholder(status):
            raise PackageValidationError(
                f"{PACKAGE_INDEX_PATH} {path} status must remain a placeholder"
            )
        if not isinstance(evidence, str) or not _is_placeholder(evidence):
            raise PackageValidationError(
                f"{PACKAGE_INDEX_PATH} {path} evidence must remain a placeholder"
            )
    if tuple(seen_paths) != REQUIRED_PACKAGE_INDEX_SOURCE_ARTIFACTS:
        raise PackageValidationError(
            f"{PACKAGE_INDEX_PATH} source_artifacts must match package contract"
        )


def _validate_backup_restore_template(text: str) -> None:
    document = _load_json_object(text, BACKUP_RESTORE_TEMPLATE_PATH)
    if document.get("evidence_type") != "client-production-backup-restore-rehearsal-not-activation":
        raise PackageValidationError(
            f"{BACKUP_RESTORE_TEMPLATE_PATH} evidence_type must distinguish rehearsal"
        )
    expected_command = (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_backup_restore_evidence.py <operator-held-backup-restore.json>"
    )
    if document.get("validator_command") != expected_command:
        raise PackageValidationError(
            f"{BACKUP_RESTORE_TEMPLATE_PATH} validator_command must be {expected_command}"
        )
    for key in (
        "cloud_execution",
        "production_deployment",
        "live_data_admission",
        "destructive_recovery",
    ):
        value = _get_pointer(document, BACKUP_RESTORE_TEMPLATE_PATH, "authority_boundary", key)
        if value != "separate-approval-required":
            raise PackageValidationError(
                f"{BACKUP_RESTORE_TEMPLATE_PATH} authority_boundary.{key} "
                "must preserve approval boundary"
            )
    for section, key in (
        ("source", "source_commit"),
        ("source", "migration_revision"),
        ("rehearsal", "backup_rehearsal_status"),
        ("rehearsal", "restore_rehearsal_status"),
        ("rehearsal", "restore_target"),
        ("evidence", "backup_receipt"),
        ("evidence", "restore_receipt"),
        ("evidence", "integrity_check"),
        ("evidence", "database_authority_receipt"),
        ("evidence", "rollback_or_forward_recovery_note"),
        ("evidence", "backup_restore_owner"),
    ):
        value = _get_pointer(document, BACKUP_RESTORE_TEMPLATE_PATH, section, key)
        if not isinstance(value, str) or not _is_placeholder(value):
            raise PackageValidationError(
                f"{BACKUP_RESTORE_TEMPLATE_PATH} {section}.{key} must remain a placeholder"
            )
    live_data_value = _get_pointer(
        document, BACKUP_RESTORE_TEMPLATE_PATH, "rehearsal", "live_data_in_source"
    )
    if live_data_value != "not-included":
        raise PackageValidationError(
            f"{BACKUP_RESTORE_TEMPLATE_PATH} rehearsal.live_data_in_source must be not-included"
        )
    if (
        _get_pointer(document, BACKUP_RESTORE_TEMPLATE_PATH, "rehearsal", "destructive_recovery")
        != "not-executed-without-separate-approval"
    ):
        raise PackageValidationError(
            f"{BACKUP_RESTORE_TEMPLATE_PATH} rehearsal.destructive_recovery "
            "must preserve approval boundary"
        )


def _validate_operations_readiness_template(text: str) -> None:
    document = _load_json_object(text, OPERATIONS_READINESS_TEMPLATE_PATH)
    expected_type = "client-production-operations-readiness-not-activation"
    if document.get("evidence_type") != expected_type:
        raise PackageValidationError(
            f"{OPERATIONS_READINESS_TEMPLATE_PATH} evidence_type must distinguish readiness"
        )
    expected_command = (
        "UV_CACHE_DIR=/private/tmp/golden-rose-uv-cache uv run python "
        "scripts/validate_client_operations_readiness_evidence.py "
        "<operator-held-operations-readiness.json>"
    )
    if document.get("validator_command") != expected_command:
        raise PackageValidationError(
            f"{OPERATIONS_READINESS_TEMPLATE_PATH} validator_command must be {expected_command}"
        )
    for key in (
        "cloud_execution",
        "production_deployment",
        "live_data_admission",
        "incident_contact_activation",
    ):
        value = _get_pointer(
            document, OPERATIONS_READINESS_TEMPLATE_PATH, "authority_boundary", key
        )
        if value != "separate-approval-required":
            raise PackageValidationError(
                f"{OPERATIONS_READINESS_TEMPLATE_PATH} authority_boundary.{key} "
                "must preserve approval boundary"
            )
    for section, key in (
        ("source", "source_commit"),
        ("source", "migration_revision"),
        ("operations", "monitoring_configuration_status"),
        ("operations", "alerting_configuration_status"),
        ("operations", "log_retention_status"),
        ("operations", "incident_routing_status"),
        ("operations", "support_routing_status"),
        ("evidence", "monitoring_receipt"),
        ("evidence", "alerting_receipt"),
        ("evidence", "log_retention_receipt"),
        ("evidence", "incident_routing_receipt"),
        ("evidence", "support_routing_receipt"),
        ("evidence", "monitoring_owner"),
        ("evidence", "incident_owner"),
        ("evidence", "support_owner"),
        ("evidence", "escalation_review_note"),
    ):
        value = _get_pointer(document, OPERATIONS_READINESS_TEMPLATE_PATH, section, key)
        if not isinstance(value, str) or not _is_placeholder(value):
            raise PackageValidationError(
                f"{OPERATIONS_READINESS_TEMPLATE_PATH} {section}.{key} must remain a placeholder"
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
    handoff_template = _read(root, HANDOFF_TEMPLATE_PATH)
    readiness_checklist = _read(root, READINESS_CHECKLIST_PATH)
    package_index = _read(root, PACKAGE_INDEX_PATH)
    backup_restore_template = _read(root, BACKUP_RESTORE_TEMPLATE_PATH)
    operations_readiness_template = _read(root, OPERATIONS_READINESS_TEMPLATE_PATH)
    for relative_path, text in (
        (RUNBOOK_PATH, runbook),
        (ENV_TEMPLATE_PATH, env_template),
        (INPUTS_TEMPLATE_PATH, inputs_template),
        (POLICY_TEMPLATE_PATH, policy_template),
        (HANDOFF_TEMPLATE_PATH, handoff_template),
        (READINESS_CHECKLIST_PATH, readiness_checklist),
        (PACKAGE_INDEX_PATH, package_index),
        (BACKUP_RESTORE_TEMPLATE_PATH, backup_restore_template),
        (OPERATIONS_READINESS_TEMPLATE_PATH, operations_readiness_template),
    ):
        _validate_no_forbidden_values(relative_path, text)
    _validate_runbook(runbook)
    _validate_env_template(env_template)
    _validate_inputs_template(inputs_template)
    _validate_policy_template(policy_template)
    _validate_handoff_template(handoff_template)
    _validate_readiness_checklist_template(readiness_checklist)
    _validate_package_index_template(package_index)
    _validate_backup_restore_template(backup_restore_template)
    _validate_operations_readiness_template(operations_readiness_template)
    return [
        str(RUNBOOK_PATH),
        str(ENV_TEMPLATE_PATH),
        str(INPUTS_TEMPLATE_PATH),
        str(POLICY_TEMPLATE_PATH),
        str(HANDOFF_TEMPLATE_PATH),
        str(READINESS_CHECKLIST_PATH),
        str(PACKAGE_INDEX_PATH),
        str(BACKUP_RESTORE_TEMPLATE_PATH),
        str(OPERATIONS_READINESS_TEMPLATE_PATH),
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
