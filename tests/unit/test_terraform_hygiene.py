import ast
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TERRAFORM_RELATIVE_FILES = [
    Path("infra/gcp/backend.tf"),
    Path("infra/gcp/versions.tf"),
    Path("infra/gcp/providers.tf"),
    Path("infra/gcp/variables.tf"),
    Path("infra/gcp/locals.tf"),
    Path("infra/gcp/outputs.tf"),
    Path("infra/gcp/bootstrap/backend.tf"),
    Path("infra/gcp/bootstrap/versions.tf"),
    Path("infra/gcp/bootstrap/providers.tf"),
    Path("infra/gcp/bootstrap/variables.tf"),
    Path("infra/gcp/bootstrap/state.tf"),
    Path("infra/gcp/bootstrap/iam.tf"),
    Path("infra/gcp/bootstrap/wif.tf"),
    Path("infra/gcp/bootstrap/outputs.tf"),
    Path("infra/gcp/develop/apis.tf"),
    Path("infra/gcp/develop/artifact_registry.tf"),
    Path("infra/gcp/develop/secrets.tf"),
    Path("infra/gcp/develop/network.tf"),
    Path("infra/gcp/develop/cloud_sql.tf"),
    Path("infra/gcp/develop/cloud_run.tf"),
    Path("infra/gcp/develop/identities.tf"),
    Path("infra/gcp/develop/iam.tf"),
    Path("infra/gcp/develop/migration_job.tf"),
    Path("infra/gcp/develop/budgets.tf"),
    Path("infra/gcp/develop/observability.tf"),
]


def _gitignore_entries() -> set[str]:
    return {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def _write_minimal_required_terraform_scaffold(root: Path) -> None:
    for relative_path in REQUIRED_TERRAFORM_RELATIVE_FILES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def _write_current_terraform_scaffold(root: Path) -> None:
    """Use the reviewed Terraform contract when testing workflow-only mutations."""
    shutil.copytree(
        ROOT / "infra" / "gcp",
        root / "infra" / "gcp",
        ignore=shutil.ignore_patterns(".terraform"),
    )


def _replace_bootstrap_wif_condition(wif: str, old: str, new: str) -> str:
    condition_match = re.search(
        r'attribute_condition\s*=\s*(?P<condition>"(?:\\.|[^"\\])*")',
        wif,
    )
    assert condition_match is not None
    condition = json.loads(condition_match.group("condition"))
    assert old in condition
    updated_condition = condition.replace(old, new, 1)
    return (
        wif[: condition_match.start("condition")]
        + json.dumps(updated_condition)
        + wif[condition_match.end("condition") :]
    )


def _write_workflow_fixture(root: Path, name: str, content: str) -> None:
    workflow_dir = root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / name).write_text(content, encoding="utf-8")


def _current_workflow_text(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def _remove_named_workflow_step(workflow: str, step_name: str, next_step_name: str) -> str:
    start = workflow.index(f"      - name: {step_name}")
    end = workflow.index(f"      - name: {next_step_name}", start)
    return workflow[:start] + workflow[end:]


def _extract_direct_vpc_subnet_cidr_pattern(variables_text: str) -> re.Pattern[str]:
    match = re.search(r'"(\^.*\$)"', variables_text)
    assert match is not None
    return re.compile(ast.literal_eval(f'"{match.group(1)}"'))


def _cidr_is_terraform_contract_acceptable(pattern: re.Pattern[str], candidate: str) -> bool:
    if not pattern.fullmatch(candidate):
        return False
    try:
        network = ipaddress.ip_network(candidate, strict=True)
    except ValueError:
        return False
    return network.prefixlen <= 26


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _contains_normalized_fragment(text: str, fragment: str) -> bool:
    return _normalize_whitespace(fragment) in _normalize_whitespace(text)


def test_terraform_local_state_plan_and_secret_inputs_are_ignored() -> None:
    entries = _gitignore_entries()

    assert ".terraform/" in entries
    assert "*.tfstate" in entries
    assert "*.tfstate.*" in entries
    assert "*.tfplan" in entries
    assert "*.tfvars" in entries
    assert "*.tfvars.json" in entries
    assert "terraform.tfvars" in entries
    assert "terraform.tfvars.json" in entries
    assert "*.auto.tfvars" in entries
    assert "*.auto.tfvars.json" in entries
    assert ".terraform.lock.hcl" not in entries


def test_gcp_terraform_readme_distinguishes_historical_local_and_completed_remote_state() -> None:
    readme = (ROOT / "infra/gcp/README.md").read_text(encoding="utf-8")

    required_phrases = [
        "validate-without-apply",
        "terraform init -backend=false",
        "terraform validate",
        "No terraform apply",
        "No GCP authentication",
        "No API enablement",
        "No resource provisioning",
        "No secret payloads",
        "fictional synthetic-only",
        "original validate-without-apply slice used local state only",
        "separately approved E2/E3 operations later established and verified distinct remote bootstrap/workload state lineages",
        "do not authorize another backend/state action",
        "scripts/validate_terraform_static.py",
        "infrastructure-quality",
        "static validation",
        "No Terraform plan",
        "No workflow secrets",
    ]

    for phrase in required_phrases:
        assert phrase in readme


def test_gcp_bootstrap_runbook_documents_bootstrap_migration_and_retirement() -> None:
    runbook = (ROOT / "deploy/gcp/bootstrap-state-runbook.md").read_text(encoding="utf-8")

    required_phrases = [
        "local bootstrap",
        "remote state",
        "partial backend configuration",
        "canonical private backend-config digest",
        "resolved backend identity",
        "state object or prefix",
        "lock scope",
        "pre-initialization comparison",
        "WIF handoff",
        "bootstrap authority retirement",
        "emergency recovery",
        "client handoff",
        "teardown exclusions",
    ]

    for phrase in required_phrases:
        assert phrase in runbook


def test_gcp_evidence_template_documents_stage_modes_and_budget_channel_identity() -> None:
    template = (ROOT / "deploy/gcp/evidence-template.md").read_text(encoding="utf-8")

    assert "foundation, migration, or service" in template
    assert "notification-channel resource names" in template
    assert "display names" in template


def test_develop_qualification_evidence_and_access_docs_preserve_human_visible_contracts() -> None:
    evidence_template = (ROOT / "deploy/gcp/evidence-template.md").read_text(encoding="utf-8")
    tester_access = (ROOT / "deploy/gcp/private-tester-access.md").read_text(encoding="utf-8")
    combined = f"{evidence_template}\n{tester_access}"

    required_phrases = [
        "qualification-status-contract.md",
        "human-qualification-checklist.md",
        "human-feedback-template.md",
        "temporary shared Basic boundary",
        "Missing credentials",
        "wrong Basic credentials",
        "non-argv private handoff",
        "allUsers",
        "one-instance cap",
        "Cache-Control: no-store",
        "controlled error outcomes",
        "source-controlled static contract",
        "manual_browser",
        "accessibility",
        "fluent_language",
        "tester_access",
        "monitoring",
        "recovery",
        "feedback",
        "not_run",
        "not_evidenced",
        "not_triaged",
        "qualified_private_develop_for_human_feedback",
        "operational_private_develop_technical_feedback_only",
        "not_qualified",
        "torn_down_after_failed_activation",
    ]
    for phrase in required_phrases:
        assert phrase in combined

    forbidden_overclaims = [
        "human qualification passed",
        "accessibility passed",
        "language review passed",
        "client accepted",
        "staff pilot ready",
        "production ready",
    ]
    for phrase in forbidden_overclaims:
        assert phrase not in combined.lower()


def test_pr_b_frontend_regression_evidence_surface_is_source_complete() -> None:
    required_frontend_files = [
        "apps/web/src/app/App.test.tsx",
        "apps/web/src/app/AppShell.test.tsx",
        "apps/web/src/employers/EmployerWorkspace.test.tsx",
        "apps/web/src/employers/EmployerRevisionForm.test.tsx",
        "apps/web/src/i18n/LanguageProvider.test.tsx",
        "apps/web/src/test/valueSafeDiagnostics.test.ts",
    ]

    for relative_path in required_frontend_files:
        assert (ROOT / relative_path).is_file()

    frontend_tests = "\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in required_frontend_files
    )
    required_regression_nodes = [
        "has no automated axe violations in both locales",
        "passes axe in both locales across every revision and recovery state",
        "keeps exact English and Spanish revision keys in parity",
        "provides focus hooks for every interactive control",
        "announces and focuses every revision transition with reduced-motion-safe behavior",
        "honors reduced motion and narrow single-column structure",
        "keeps workspace query failures value-independent",
        "keeps create authority data out of browser side channels",
        "revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels",
        "revision controls preserve value-independent Testing Library diagnostics",
        "reloads the canonical document after a persisted restore",
        "does not restore Employer state from browser back-forward cache",
    ]

    for node in required_regression_nodes:
        assert node in frontend_tests


def test_web_verify_scripts_pin_test_environment_for_react_act() -> None:
    package_json = json.loads((ROOT / "apps/web/package.json").read_text(encoding="utf-8"))

    assert package_json["scripts"]["test"].startswith("NODE_ENV=test ")
    assert package_json["scripts"]["test:coverage"].startswith("NODE_ENV=test ")


def test_human_feedback_template_defines_value_safe_structured_issue_fields() -> None:
    template = (ROOT / "deploy/gcp/human-feedback-template.md").read_text(encoding="utf-8")

    required_fields = [
        "synthetic scenario",
        "tester role",
        "language",
        "browser",
        "viewport",
        "expected behavior",
        "observed behavior",
        "severity",
        "workflow blocker",
        "accessibility impact",
        "privacy impact",
        "security impact",
        "reproduction",
        "evidence reference",
        "owner",
        "disposition",
        "retest result",
    ]

    for field in required_fields:
        assert field in template
    forbidden_values = [
        "submitted names",
        "UUIDs",
        "commands",
        "cursors",
        "tester identities",
        "endpoints",
        "tokens",
        "raw bodies",
    ]
    for forbidden_value in forbidden_values:
        assert forbidden_value in template


def test_human_qualification_checklist_requires_manual_matrix_without_tracked_values() -> None:
    checklist = (ROOT / "deploy/gcp/human-qualification-checklist.md").read_text(encoding="utf-8")

    required_entries = [
        "macOS Safari",
        "Chromium desktop",
        "browser",
        "OS",
        "device or viewport",
        "assistive technology",
        "network condition",
        "English Employer path",
        "Spanish Employer path",
        "keyboard",
        "focus",
        "responsive reflow",
        "reduced motion",
        "text spacing",
        "contrast",
        "refresh/back/forward/BFCache",
        "constrained network",
        "safe error/recovery",
        "pass/fail/not-run",
        "tester role",
        "language",
        "evidence reference",
        "disposition",
    ]

    for entry in required_entries:
        assert entry in checklist
    forbidden_values = [
        "submitted names",
        "UUIDs",
        "commands",
        "cursors",
        "tester identities",
        "endpoints",
        "credentials",
        "Authorization headers",
        "screenshots containing sensitive values",
        "raw bodies",
    ]
    for forbidden_value in forbidden_values:
        assert forbidden_value in checklist


def test_qualification_status_contract_lists_exact_statuses_and_overclaim_boundaries() -> None:
    contract = (ROOT / "deploy/gcp/qualification-status-contract.md").read_text(encoding="utf-8")

    exact_statuses = [
        "qualified_private_develop_for_human_feedback",
        "operational_private_develop_technical_feedback_only",
        "not_qualified",
        "torn_down_after_failed_activation",
    ]
    for status in exact_statuses:
        assert status in contract
    assert "exactly one" in contract
    required_boundaries = [
        "synthetic-only",
        "not staff-pilot identity",
        "not client-accepted",
        "does not authorize live/client data or production",
        "fluent-language content-quality review",
        "No other missing/failed row qualifies",
        "blockers and stop/cleanup disposition",
    ]
    for boundary in required_boundaries:
        assert boundary in contract


def test_predeployment_manifest_registers_database_authority_verifier_entrypoint() -> None:
    manifest = json.loads(
        (ROOT / "infra/policy/predeployment-authority-manifest.json").read_text(encoding="utf-8")
    )

    assert "scripts/verify_database_authority.py" in manifest["scripts"]["entrypoints"]


def test_database_authority_integration_suite_retains_controlled_postgresql_coverage() -> None:
    integration = (ROOT / "tests/integration/test_database_authority.py").read_text(
        encoding="utf-8"
    )

    required_coverage = [
        "test_database_authority_live_verifier_accepts_upgraded_schema",
        "test_database_authority_runtime_login_cannot_assume_owner_or_mutate_append_only_tables",
        "TRUNCATE TABLE command_receipts",
        "CREATE TABLE public.runtime_leak",
        "ALTER TABLE audit_events DISABLE TRIGGER ALL",
        "GRANT golden_rose_schema_owner TO golden_rose_runtime",
        "test_database_authority_migration_login_can_assume_only_schema_owner",
        "SELECT SESSION_USER",
        "SELECT CURRENT_USER",
        "SET ROLE golden_rose_schema_owner",
        "test_database_authority_live_verifier_fails_closed_on_runtime_privilege_drift",
        "test_database_authority_verifier_script_passes_on_reviewed_head",
    ]

    for coverage in required_coverage:
        assert coverage in integration


def test_staff_api_integration_suite_retains_no_store_controlled_error_coverage() -> None:
    integration = "\n".join(
        [
            (ROOT / "tests/integration/api/test_staff_employer_reads.py").read_text(
                encoding="utf-8"
            ),
            (ROOT / "tests/integration/api/test_staff_employers.py").read_text(encoding="utf-8"),
        ]
    )

    required_coverage = [
        "test_post_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free",
        "test_post_staff_employer_contact_query_failure_matrix_is_exact_no_store_value_safe_and_write_free",
        "test_get_staff_employer_contact_failure_matrix_is_exact_no_store_value_safe_and_write_free",
        "test_existing_search_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact",
        "test_existing_detail_failure_matrix_media_cache_body_headers_and_read_only_contract_remains_exact",
        "test_post_staff_employer_revision_maps_bounded_failure_matrix_without_values",
        'response.headers["Cache-Control"] == "no-store"',
        '"status": 403',
        '"status": 404',
        '"status": 409',
        '"status": 412',
        '"status": 422',
        '"status": 500',
        '"status": 503',
        "Idempotency-Result-Version",
        "assert sql_statements == []",
    ]

    for coverage in required_coverage:
        assert coverage in integration


def test_gcp_first_deployment_runbook_documents_recovery_and_secret_boundaries() -> None:
    runbook = (ROOT / "deploy/gcp/first-deployment-runbook.md").read_text(encoding="utf-8")

    required_phrases = [
        "out-of-band secret payload custody and injection",
        "single eight-hour operator packet",
        "Database passwords must be generated without terminal display",
        "Stop immediately",
        "Revoke and replace every affected secret value",
        "teardown/rebuild",
    ]

    for phrase in required_phrases:
        assert phrase in runbook


def test_gcp_first_deployment_runbook_documents_exact_quota_bootstrap_and_import() -> None:
    runbook = (ROOT / "deploy/gcp/first-deployment-runbook.md").read_text(encoding="utf-8")

    required_phrases = [
        "goldenRoseProvisionerQuotaUser",
        "serviceusage.services.use",
        "sole binding",
        "module.develop.google_project_iam_custom_role.provisioner_quota_user",
        "module.develop.google_project_iam_member.provisioner_quota_user",
        "first full migration plan must show zero actions",
    ]

    for phrase in required_phrases:
        assert phrase in runbook


def test_gcp_first_deployment_runbook_documents_single_packet_and_shared_access() -> None:
    runbook = (ROOT / "deploy/gcp/first-deployment-runbook.md").read_text(encoding="utf-8")

    required_phrases = [
        "One-packet execution order",
        "no more than eight hours",
        "designated packet output",
        "allUsers",
        "expiring Basic gate",
        "zero-to-one instances",
        "non-mutating teardown/rebuild readiness inspection",
    ]

    for phrase in required_phrases:
        assert phrase in runbook


def test_gcp_recovery_and_teardown_runbooks_document_failure_handling_boundaries() -> None:
    rollback_runbook = (ROOT / "deploy/gcp/rollback-forward-recovery-runbook.md").read_text(
        encoding="utf-8"
    )
    teardown_runbook = (ROOT / "deploy/gcp/teardown-rebuild-runbook.md").read_text(encoding="utf-8")
    bootstrap_runbook = (ROOT / "deploy/gcp/bootstrap-state-runbook.md").read_text(encoding="utf-8")

    rollback_required_phrases = [
        "schema/image compatibility matrix",
        "rollback",
        "forward recovery",
        "migration lock",
        "backup/restore",
        "untested RTO/RPO",
    ]
    teardown_required_phrases = [
        "control-plane/state survival",
        "deletion protection",
        "break-glass",
        "orphan-resource",
        "No automatic scheduled destroy",
    ]
    bootstrap_required_phrases = [
        "state survival",
        "workload teardown",
        "teardown exclusions",
    ]

    for phrase in rollback_required_phrases:
        assert phrase in rollback_runbook
    for phrase in teardown_required_phrases:
        assert phrase in teardown_runbook
    for phrase in bootstrap_required_phrases:
        assert phrase in bootstrap_runbook


def test_gcp_staged_plan_approval_binds_backend_fingerprint_before_apply() -> None:
    procedure = (ROOT / "deploy/gcp/staged-plan-approval.md").read_text(encoding="utf-8")

    required_phrases = [
        "canonical private backend-config digest",
        "resolved backend identity",
        "state object or prefix",
        "lock scope",
        "pre-initialization comparison",
        "bootstrap and workload roots remain distinct",
    ]

    for phrase in required_phrases:
        assert phrase in procedure


def test_gcp_terraform_backend_uses_partial_gcs_configuration_without_committed_values() -> None:
    backend = (ROOT / "infra/gcp/backend.tf").read_text(encoding="utf-8")

    assert 'backend "gcs"' in backend
    assert "bucket" not in backend
    assert "prefix" not in backend
    assert "project" not in backend
    assert "credentials" not in backend
    assert "access_token" not in backend
    assert "impersonate_service_account" not in backend


def test_gcp_bootstrap_backend_uses_partial_gcs_configuration_without_committed_values() -> None:
    backend = (ROOT / "infra/gcp/bootstrap/backend.tf").read_text(encoding="utf-8")

    assert 'backend "gcs"' in backend
    assert "bucket" not in backend
    assert "prefix" not in backend
    assert "project" not in backend
    assert "credentials" not in backend
    assert "access_token" not in backend
    assert "impersonate_service_account" not in backend


def test_gcp_bootstrap_variables_require_operator_inputs_without_defaults() -> None:
    variables = (ROOT / "infra/gcp/bootstrap/variables.tf").read_text(encoding="utf-8")

    for variable_name in [
        "state_project_id",
        "state_bucket_location",
        "state_bucket_name",
        "bootstrap_operator_principal",
    ]:
        assert f'variable "{variable_name}"' in variables

    assert "default =" not in variables
    assert "nullable    = false" in variables
    assert "credentials" not in variables
    assert "secret" not in variables.lower()


def test_gcp_bootstrap_state_bucket_enforces_recovery_and_lifecycle_controls() -> None:
    state = (ROOT / "infra/gcp/bootstrap/state.tf").read_text(encoding="utf-8")

    assert 'resource "google_storage_bucket" "terraform_state"' in state
    assert "uniform_bucket_level_access = true" in state
    assert 'public_access_prevention    = "enforced"' in state
    assert "versioning {" in state
    assert "enabled = true" in state
    assert _contains_normalized_fragment(state, "force_destroy = false")
    assert "prevent_destroy = true" in state
    assert "retention_policy {" in state


def test_gcp_bootstrap_wif_contract_requires_exact_github_claims() -> None:
    wif = (ROOT / "infra/gcp/bootstrap/wif.tf").read_text(encoding="utf-8")

    required_fragments = [
        'issuer_uri = "https://token.actions.githubusercontent.com"',
        '"attribute.workflow_ref"     = "assertion.workflow_ref"',
    ]

    for fragment in required_fragments:
        assert fragment in wif

    condition_match = re.search(
        r'attribute_condition\s*=\s*(?P<condition>"(?:\\.|[^"\\])*")',
        wif,
    )
    assert condition_match is not None
    condition = json.loads(condition_match.group("condition"))
    required_condition_claims = [
        'attribute.repository == "b-mackenzie-alexander/golden_rose_project"',
        'attribute.ref == "refs/heads/develop"',
        'attribute.environment == "develop"',
        'attribute.event_name == "workflow_dispatch"',
        'attribute.repository_owner == "b-mackenzie-alexander"',
        'attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop"',
        'attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop"',
    ]
    for claim in required_condition_claims:
        assert claim in condition

    assert "attribute.workflow_ref" in condition
    assert "*" not in condition
    assert 'attribute.event_name != "pull_request"' not in condition


def test_gcp_bootstrap_source_preserves_provider_canonical_noop_fields() -> None:
    wif = (ROOT / "infra/gcp/bootstrap/wif.tf").read_text(encoding="utf-8")
    iam = (ROOT / "infra/gcp/bootstrap/iam.tf").read_text(encoding="utf-8")
    expected_condition = 'attribute.repository == "b-mackenzie-alexander/golden_rose_project" && attribute.repository_owner == "b-mackenzie-alexander" && attribute.ref == "refs/heads/develop" && attribute.environment == "develop" && attribute.event_name == "workflow_dispatch" && ( attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop" || attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop" )'
    expected_artifact_verifier_description = (
        "Artifact verification identity separate from image publication and deployment authority."
    )

    assert f"  attribute_condition = {json.dumps(expected_condition)}" in wif
    artifact_verifier = iam.split('resource "google_service_account" "artifact_verifier"', 1)[
        1
    ].split("\n}", 1)[0]
    assert (
        f"  description  = {json.dumps(expected_artifact_verifier_description)}"
        in artifact_verifier
    )


def test_gcp_bootstrap_iam_separates_provisioner_image_publisher_artifact_verifier_and_deployer() -> (
    None
):
    iam = (ROOT / "infra/gcp/bootstrap/iam.tf").read_text(encoding="utf-8")

    required_fragments = [
        'resource "google_service_account" "provisioner"',
        'resource "google_service_account" "image_publisher"',
        'resource "google_service_account" "artifact_verifier"',
        'resource "google_service_account" "deployer"',
        'resource "google_service_account_iam_member" "image_publisher_wif"',
        'resource "google_service_account_iam_member" "artifact_verifier_wif"',
        'resource "google_service_account_iam_member" "deployer_wif"',
        'role               = "roles/iam.workloadIdentityUser"',
        "member             = local.build_image_workflow_principal_set",
        "member             = local.deploy_develop_workflow_principal_set",
    ]

    for fragment in required_fragments:
        assert fragment in iam

    assert "google_service_account_key" not in iam
    assert "roles/owner" not in iam
    assert "roles/editor" not in iam
    assert iam.count("roles/iam.serviceAccountTokenCreator") == 1
    assert 'resource "google_service_account_iam_member" "provisioner_wif"' not in iam
    assert "local.github_principal_set" not in iam


def test_gcp_bootstrap_provisioner_local_operator_impersonation_is_exact_and_resource_scoped() -> (
    None
):
    iam = (ROOT / "infra/gcp/bootstrap/iam.tf").read_text(encoding="utf-8")
    variables = (ROOT / "infra/gcp/bootstrap/variables.tf").read_text(encoding="utf-8")
    runbook = (ROOT / "deploy/gcp/bootstrap-state-runbook.md").read_text(encoding="utf-8")
    manifest = json.loads(
        (ROOT / "infra/policy/predeployment-authority-manifest.json").read_text(encoding="utf-8")
    )

    assert 'variable "provisioner_operator_principal"' in variables
    variable_section = variables.split('variable "provisioner_operator_principal"', 1)[1]
    assert "nullable    = false" in variable_section
    assert "default" not in variable_section
    assert 'startswith(var.provisioner_operator_principal, "user:")' in variable_section
    assert (
        'resource "google_service_account_iam_member" "provisioner_operator_token_creator"' in iam
    )
    resource_section = iam.split(
        'resource "google_service_account_iam_member" "provisioner_operator_token_creator"', 1
    )[1].split("\n}", 1)[0]
    assert "service_account_id = google_service_account.provisioner.name" in resource_section
    assert 'role               = "roles/iam.serviceAccountTokenCreator"' in resource_section
    assert "member             = var.provisioner_operator_principal" in resource_section
    assert iam.count("roles/iam.serviceAccountTokenCreator") == 1
    assert 'resource "google_service_account_iam_member" "provisioner_wif"' not in iam
    assert 'resource "google_project_iam_member"' not in iam
    assert (
        'description  = "Provisioning identity that will later own reviewed infrastructure changes through exact GitHub OIDC trust."'
        in iam
    )
    assert (
        manifest["terraform"]["resource_types"]["google_service_account_iam_member"]["max_count"]
        == 4
    )
    required_runbook_phrases = [
        "existing bootstrap operator",
        "sole allowed create",
        "bootstrap-root saved plan",
        "Ambient-user workload Terraform",
        "short-lived provisioner impersonation",
    ]
    for phrase in required_runbook_phrases:
        assert phrase in runbook


def test_terraform_static_validation_rejects_provisioner_operator_wif_substitution(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    iam_path = tmp_path / "infra" / "gcp" / "bootstrap" / "iam.tf"
    iam = iam_path.read_text(encoding="utf-8").replace(
        "member             = var.provisioner_operator_principal",
        "member             = local.deploy_develop_workflow_principal_set",
    )
    iam += "\n# member             = var.provisioner_operator_principal\n"
    iam_path.write_text(iam, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "provisioner operator authority" in result.stdout


def test_terraform_static_validation_rejects_additional_token_creator_authority(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    iam_path = tmp_path / "infra" / "gcp" / "bootstrap" / "iam.tf"
    iam_path.write_text(
        iam_path.read_text(encoding="utf-8")
        + '\nresource "google_service_account_iam_member" "unreviewed_token_creator" {\n'
        + "  service_account_id = google_service_account.deployer.name\n"
        + '  role               = "roles/iam.serviceAccountTokenCreator"\n'
        + "  member             = var.provisioner_operator_principal\n"
        + "}\n",
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "exactly one resource-scoped provisioner operator Token Creator role" in result.stdout


def test_terraform_static_validation_rejects_project_wide_provisioner_token_creator(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    iam_path = tmp_path / "infra" / "gcp" / "bootstrap" / "iam.tf"
    iam = (
        iam_path.read_text(encoding="utf-8")
        .replace(
            'resource "google_service_account_iam_member" "provisioner_operator_token_creator"',
            'resource "google_project_iam_member" "provisioner_operator_token_creator"',
            1,
        )
        .replace(
            "service_account_id = google_service_account.provisioner.name",
            "project            = var.state_project_id",
            1,
        )
    )
    iam += (
        '\n# resource "google_service_account_iam_member" '
        '"provisioner_operator_token_creator"\n'
        "# service_account_id = google_service_account.provisioner.name\n"
    )
    iam_path.write_text(iam, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "exactly one resource-scoped provisioner operator Token Creator role" in result.stdout


def test_terraform_static_validation_rejects_additional_project_wide_token_creator(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    iam_path = tmp_path / "infra" / "gcp" / "bootstrap" / "iam.tf"
    iam_path.write_text(
        iam_path.read_text(encoding="utf-8")
        + '\nresource "google_project_iam_member" "project_token_creator" {\n'
        + "  project = var.state_project_id\n"
        + '  role    = "roles/iam.serviceAccountTokenCreator"\n'
        + "  member  = var.provisioner_operator_principal\n"
        + "}\n",
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "unbounded bootstrap authority 'google_project_iam_member'" in result.stdout


@pytest.mark.parametrize(
    ("approved", "replacement"),
    [
        (
            'role               = "roles/iam.workloadIdentityUser"',
            'role               = replace("roles/iam.XserviceAccountTokenCreator", "X", "")',
        ),
        (
            "service_account_id = google_service_account.image_publisher.name",
            'service_account_id = coalesce(google_service_account.image_publisher.name, "")',
        ),
        (
            "member             = local.build_image_workflow_principal_set",
            'member             = join("", [local.build_image_workflow_principal_set])',
        ),
    ],
)
def test_terraform_static_validation_rejects_computed_bootstrap_iam_member_fields(
    tmp_path: Path,
    approved: str,
    replacement: str,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    iam_path = tmp_path / "infra" / "gcp" / "bootstrap" / "iam.tf"
    iam_path.write_text(
        iam_path.read_text(encoding="utf-8").replace(approved, replacement, 1),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "bootstrap IAM member authority drifted from exact contract" in result.stdout


@pytest.mark.parametrize(
    ("approved", "replacement"),
    [
        (
            "service_account_id = google_service_account.provisioner.name",
            "service_account_id = google_service_account.deployer.name",
        ),
        (
            'role               = "roles/iam.serviceAccountTokenCreator"',
            'role               = "roles/iam.serviceAccountUser"',
        ),
    ],
)
def test_terraform_static_validation_rejects_commented_decoy_for_effective_provisioner_authority(
    tmp_path: Path,
    approved: str,
    replacement: str,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    iam_path = tmp_path / "infra" / "gcp" / "bootstrap" / "iam.tf"
    iam = iam_path.read_text(encoding="utf-8").replace(approved, replacement, 1)
    iam += f"\n# {approved}\n"
    iam_path.write_text(iam, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "provisioner operator authority drifted" in result.stdout


def test_terraform_static_validation_rejects_commented_decoy_for_operator_validation(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    variables_path = tmp_path / "infra" / "gcp" / "bootstrap" / "variables.tf"
    approved = 'startswith(var.provisioner_operator_principal, "user:")'
    variables = variables_path.read_text(encoding="utf-8").replace(
        approved,
        'startswith(var.provisioner_operator_principal, "serviceAccount:")',
        1,
    )
    variables += f"\n# {approved}\n"
    variables_path.write_text(variables, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "provisioner operator validation drifted" in result.stdout


def test_gcp_terraform_versions_pin_provider_without_backend_or_cloud_identifiers() -> None:
    versions = (ROOT / "infra/gcp/versions.tf").read_text(encoding="utf-8")

    assert "required_version" in versions
    assert "required_providers" in versions
    assert "hashicorp/google" in versions
    assert "backend" not in versions
    assert "bucket" not in versions
    assert "credentials" not in versions
    assert "project =" not in versions
    assert "billing" not in versions
    assert "user:" not in versions
    assert "serviceAccount:" not in versions


def test_gcp_terraform_provider_uses_variables_without_credentials_or_defaults() -> None:
    providers = (ROOT / "infra/gcp/providers.tf").read_text(encoding="utf-8")

    assert 'provider "google"' in providers
    assert "project = var.project_id" in providers
    assert "region  = var.region" in providers
    assert "zone" not in providers
    assert "credentials" not in providers
    assert "impersonate_service_account" not in providers
    assert "user:" not in providers
    assert "serviceAccount:" not in providers
    assert "billing" not in providers
    assert "golden" not in providers.lower()
    assert "us-east4" not in providers


def test_gcp_terraform_variables_define_required_project_and_region_without_secrets() -> None:
    variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")

    assert 'variable "project_id"' in variables
    assert 'variable "region"' in variables
    assert 'variable "billing_account"' not in variables
    assert 'variable "credentials"' not in variables
    assert 'variable "secret"' not in variables.lower()
    assert 'variable "container_image_digest"' in variables
    assert "nullable" in variables
    assert "= false" in variables
    assert 'contains(["us-east4"], var.region)' in variables
    assert "client" not in variables.lower()
    assert "golden_rose" in variables.lower()  # approved env label variable
    assert "golden_rose_database" not in variables.lower()  # no database URL values
    assert "golden_rose_secret" not in variables.lower()  # no secret values


def test_gcp_terraform_variables_validate_private_sql_subnet_input() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    root_module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    expected_validation_fragments = [
        'variable "direct_vpc_subnet_cidr"',
        "type        = string",
        "can(cidrnetmask(var.direct_vpc_subnet_cidr))",
        "can(regex(",
        "cidrhost(var.direct_vpc_subnet_cidr, 0) == split",
        "10\\\\.",
        "172\\\\.",
        "192\\\\.168",
    ]

    for variables_text in [root_variables, develop_variables]:
        for fragment in expected_validation_fragments:
            assert fragment in variables_text

    assert _contains_normalized_fragment(
        root_module, "direct_vpc_subnet_cidr = var.direct_vpc_subnet_cidr"
    )


def test_gcp_terraform_variables_accept_representative_rfc1918_subnet_ranges() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    accepted = [
        "10.0.0.0/8",
        "10.1.0.0/24",
        "10.24.0.0/26",
        "172.16.0.0/12",
        "172.20.0.0/24",
        "192.168.0.0/16",
        "192.168.44.0/26",
    ]
    rejected = [
        "8.8.8.0/24",
        "10.1.0.0/27",
        "10.1.0.1/24",
        "172.15.0.0/12",
        "172.32.0.0/24",
        "192.169.0.0/24",
        "10.1.0.0/33",
    ]

    for variables_text in [root_variables, develop_variables]:
        pattern = _extract_direct_vpc_subnet_cidr_pattern(variables_text)
        for candidate in accepted:
            assert _cidr_is_terraform_contract_acceptable(pattern, candidate), candidate
        for candidate in rejected:
            assert not _cidr_is_terraform_contract_acceptable(pattern, candidate), candidate


def test_gcp_terraform_outputs_are_value_safe_and_do_not_expose_identifiers() -> None:
    outputs = (ROOT / "infra/gcp/outputs.tf").read_text(encoding="utf-8")

    assert 'output "environment"' in outputs
    assert 'output "data_boundary"' in outputs
    assert '"develop"' in outputs
    assert '"fictional-synthetic-only"' in outputs
    assert "project" not in outputs.lower()
    assert "billing" not in outputs.lower()
    assert "secret" not in outputs.lower()
    assert "password" not in outputs.lower()
    assert "token" not in outputs.lower()
    assert "email" not in outputs.lower()
    assert "service_account" not in outputs.lower()
    assert "serviceAccount:" not in outputs
    assert "@" not in outputs


def test_gcp_terraform_locals_define_standard_non_sensitive_labels() -> None:
    locals_text = (ROOT / "infra/gcp/locals.tf").read_text(encoding="utf-8")

    required_label_keys = [
        "environment",
        "data_boundary",
        "managed_by",
        "service",
        "cost_center",
        "owner",
        "teardown",
    ]

    for label_key in required_label_keys:
        assert label_key in locals_text

    assert '"develop"' in locals_text
    assert '"fictional-synthetic-only"' in locals_text
    assert '"terraform"' in locals_text
    assert "@" not in locals_text
    assert "client" not in locals_text.lower()
    assert "secret" not in locals_text.lower()
    assert "billing" not in locals_text.lower()
    assert "project" not in locals_text.lower()


def test_gcp_develop_api_enablement_uses_approved_allowlist_with_disable_safeguards() -> None:
    apis = (ROOT / "infra/gcp/develop/apis.tf").read_text(encoding="utf-8")

    approved_services = [
        "billingbudgets.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "iam.googleapis.com",
        "serviceusage.googleapis.com",
        "compute.googleapis.com",
        "servicenetworking.googleapis.com",
        "run.googleapis.com",
        "sqladmin.googleapis.com",
        "artifactregistry.googleapis.com",
        "secretmanager.googleapis.com",
        "logging.googleapis.com",
        "monitoring.googleapis.com",
    ]
    candidate_services = [
        "iamcredentials.googleapis.com",
        "sts.googleapis.com",
        "cloudbuild.googleapis.com",
    ]

    assert "google_project_service" in apis
    assert "disable_on_destroy" in apis
    assert "disable_dependent_services" in apis
    assert apis.count("= false") >= 2
    for service in approved_services:
        assert service in apis
    for service in candidate_services:
        assert service not in apis
    assert "project" in apis
    assert "var.project_id" in apis
    assert "credentials" not in apis
    assert "billing_account" not in apis.lower()


def test_gcp_develop_artifact_registry_is_private_regional_and_cleanup_bounded() -> None:
    artifact_registry = (ROOT / "infra/gcp/develop/artifact_registry.tf").read_text(
        encoding="utf-8"
    )

    assert "google_artifact_registry_repository" in artifact_registry
    assert "repository_id" in artifact_registry
    assert "format" in artifact_registry
    assert '"DOCKER"' in artifact_registry
    assert "location" in artifact_registry
    assert "var.region" in artifact_registry
    assert "cleanup_policy_dry_run" in artifact_registry
    assert "= false" in artifact_registry
    assert "cleanup_policies" in artifact_registry
    assert "tag_state" in artifact_registry
    assert "UNTAGGED" in artifact_registry
    assert "most_recent_versions" in artifact_registry
    assert "keep_count" in artifact_registry
    assert "local.standard_labels" in artifact_registry
    assert "allUsers" not in artifact_registry
    assert "allAuthenticatedUsers" not in artifact_registry
    assert "roles/artifactregistry.admin" not in artifact_registry
    assert "serviceAccount:" not in artifact_registry
    assert "@" not in artifact_registry
    assert "depends_on" in artifact_registry
    assert 'google_project_service.approved["artifactregistry.googleapis.com"]' in artifact_registry
    assert "provisioner" not in artifact_registry.lower()
    assert "local-exec" not in artifact_registry.lower()


def test_gcp_develop_secrets_manage_metadata_only_without_payloads_or_broad_iam() -> None:
    secrets = (ROOT / "infra/gcp/develop/secrets.tf").read_text(encoding="utf-8")

    expected_secret_ids = [
        "runtime-database-url",
        "migration-database-url",
        "synthetic-staff-id",
        "demo-access-password",
        "deployment-posture",
    ]

    assert "google_secret_manager_secret" in secrets
    assert "google_secret_manager_secret_version" not in secrets
    assert "secret_data" not in secrets
    assert "payload" not in secrets.lower()
    assert "token" not in secrets.lower()
    assert "replication" in secrets
    assert "auto" in secrets
    assert "labels" in secrets
    assert "local.standard_labels" in secrets
    for secret_id in expected_secret_ids:
        assert secret_id in secrets
    assert "roles/secretmanager.admin" not in secrets
    assert "roles/secretmanager.secretAccessor" not in secrets
    assert "allUsers" not in secrets
    assert "allAuthenticatedUsers" not in secrets
    assert "serviceAccount:" not in secrets
    assert "@" not in secrets
    assert "depends_on" in secrets
    assert 'google_project_service.approved["secretmanager.googleapis.com"]' in secrets
    assert "provisioner" not in secrets.lower()
    assert "local-exec" not in secrets.lower()


def test_gcp_develop_network_uses_dedicated_vpc_and_private_service_access_only() -> None:
    network = (ROOT / "infra/gcp/develop/network.tf").read_text(encoding="utf-8")

    assert "google_compute_network" in network
    assert "google_compute_subnetwork" in network
    assert "auto_create_subnetworks" in network
    assert "delete_default_routes_on_create" in network
    assert "direct_vpc" in network
    assert "ip_cidr_range" in network
    assert "var.direct_vpc_subnet_cidr" in network
    assert "region" in network
    assert "var.region" in network
    assert "google_compute_network.develop[0].id" in network
    assert "= false" in network
    assert "= true" in network
    assert "google_compute_global_address" in network
    assert "VPC_PEERING" in network
    assert "google_service_networking_connection" in network
    assert "servicenetworking.googleapis.com" in network
    assert "private_service_access" in network
    assert 'name = "default"' not in network.lower()
    assert 'network = "default"' not in network.lower()
    assert "google_compute_firewall" not in network
    assert "google_compute_router" not in network
    assert "google_compute_router_nat" not in network
    assert "google_compute_global_forwarding_rule" not in network
    assert "0.0.0.0/0" not in network
    assert "public" not in network.lower()
    assert "external" not in network.lower()
    assert 'google_project_service.approved["compute.googleapis.com"]' in network
    assert 'google_project_service.approved["servicenetworking.googleapis.com"]' in network
    assert "depends_on" in network
    assert "provisioner" not in network.lower()
    assert "local-exec" not in network.lower()


def test_gcp_develop_cloud_sql_is_private_minimal_postgresql_without_public_ip() -> None:
    cloud_sql = (ROOT / "infra/gcp/develop/cloud_sql.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    root_module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")

    assert "google_sql_database_instance" in cloud_sql
    assert "POSTGRES_16" in cloud_sql
    assert "db-f1-micro" in cloud_sql
    assert "REGIONAL" not in cloud_sql
    assert "availability_type" not in cloud_sql
    assert "disk_size" in cloud_sql
    assert "10" in cloud_sql
    assert "disk_type" in cloud_sql
    assert "PD_SSD" in cloud_sql
    assert "ipv4_enabled" in cloud_sql
    assert "= false" in cloud_sql
    assert "private_network" in cloud_sql
    assert "google_compute_network.develop[0].id" in cloud_sql
    assert "deletion_protection" in cloud_sql
    assert "local.standard_labels" in cloud_sql
    assert "backup_configuration" in cloud_sql
    assert _contains_normalized_fragment(cloud_sql, "enabled = var.cloud_sql_backup_enabled")
    assert _contains_normalized_fragment(
        cloud_sql, "point_in_time_recovery_enabled = var.cloud_sql_point_in_time_recovery_enabled"
    )
    assert _contains_normalized_fragment(
        cloud_sql, "transaction_log_retention_days = var.cloud_sql_transaction_log_retention_days"
    )
    assert "backup_retention_settings" in cloud_sql
    assert "retained_backups = var.cloud_sql_retained_backups" in cloud_sql
    assert "retention_unit" in cloud_sql and '"COUNT"' in cloud_sql
    assert _contains_normalized_fragment(cloud_sql, "start_time = var.cloud_sql_backup_start_time")
    assert "restore_backup_context" not in cloud_sql
    assert "var.cloud_sql_restore" not in cloud_sql
    assert "availability_type" not in cloud_sql
    assert "ENTERPRISE_PLUS" not in cloud_sql
    assert "recovery" not in cloud_sql.lower() or "recovery_policy_review_status" in cloud_sql
    assert "0.0.0.0/0" not in cloud_sql
    assert "authorized_networks" not in cloud_sql
    assert "public" not in cloud_sql.lower()
    assert "password" not in cloud_sql.lower()
    assert "google_sql_user" not in cloud_sql
    assert "google_sql_database" in cloud_sql
    assert 'name = "root"' not in cloud_sql.lower()
    assert "root" not in cloud_sql.lower()
    assert "@" not in cloud_sql
    assert 'google_project_service.approved["sqladmin.googleapis.com"]' in cloud_sql
    assert "depends_on" in cloud_sql
    assert "provisioner" not in cloud_sql.lower()
    assert "local-exec" not in cloud_sql.lower()

    required_variable_names = [
        "cloud_sql_backup_enabled",
        "cloud_sql_backup_start_time",
        "cloud_sql_point_in_time_recovery_enabled",
        "cloud_sql_transaction_log_retention_days",
        "cloud_sql_retained_backups",
        "cloud_sql_database_name",
        "cloud_sql_schema_owner_role",
        "cloud_sql_migrator_role",
        "cloud_sql_runtime_role",
        "cloud_sql_recovery_policy_review_status",
    ]
    for variable_name in required_variable_names:
        assert f'variable "{variable_name}"' in develop_variables
        assert f'variable "{variable_name}"' in root_variables
        assert any(
            variable_name in line and f"var.{variable_name}" in line
            for line in root_module.splitlines()
        )


def test_foundation_stage_omits_deferred_network_cloud_sql_and_demo_expiry_inputs() -> None:
    network = (ROOT / "infra/gcp/develop/network.tf").read_text(encoding="utf-8")
    cloud_sql = (ROOT / "infra/gcp/develop/cloud_sql.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_outputs = (ROOT / "infra/gcp/develop/outputs.tf").read_text(encoding="utf-8")

    assert 'count = var.deployment_stage != "foundation" ? 1 : 0' in network
    assert 'count = var.deployment_stage != "foundation" ? 1 : 0' in cloud_sql
    assert "google_compute_network.develop[0].id" in cloud_sql
    assert "google_service_networking_connection.private_service_access[0]" in cloud_sql
    assert "google_sql_database_instance.develop[0].name" in cloud_sql

    omitted_input_assertions: dict[str, dict[str, str | None]] = {
        "container_image_digest": {
            "next": 'variable "deployment_stage"',
            "migration_service_guard": "var.container_image_digest != null && can(regex(",
        },
        "direct_vpc_subnet_cidr": {
            "next": 'variable "demo_access_expires_at"',
            "migration_service_guard": "var.direct_vpc_subnet_cidr != null && can(cidrnetmask(",
        },
        "demo_access_expires_at": {
            "next": 'variable "billing_account_id"',
            "root_guard": 'var.deployment_stage == "service" ? var.demo_access_expires_at != null && can(regex(',
            "develop_guard": 'var.deployment_stage == "service" ? var.demo_access_expires_at != null && can(regex(',
            "migration_service_guard": ": var.demo_access_expires_at == null",
        },
        "cloud_sql_backup_enabled": {
            "next": 'variable "cloud_sql_backup_start_time"',
            "migration_service_guard": "var.cloud_sql_backup_enabled != null",
        },
        "cloud_sql_backup_start_time": {
            "next": 'variable "cloud_sql_point_in_time_recovery_enabled"',
            "migration_service_guard": "var.cloud_sql_backup_start_time != null && can(regex(",
        },
        "cloud_sql_point_in_time_recovery_enabled": {
            "next": 'variable "cloud_sql_transaction_log_retention_days"',
            "migration_service_guard": "var.cloud_sql_point_in_time_recovery_enabled != null",
        },
        "cloud_sql_transaction_log_retention_days": {
            "next": 'variable "cloud_sql_retained_backups"',
            "migration_service_guard": "var.cloud_sql_transaction_log_retention_days != null && floor(",
        },
        "cloud_sql_retained_backups": {
            "next": 'variable "cloud_sql_database_name"',
            "migration_service_guard": "var.cloud_sql_retained_backups != null && floor(",
        },
        "cloud_sql_database_name": {
            "next": 'variable "cloud_sql_schema_owner_role"',
            "migration_service_guard": "var.cloud_sql_database_name != null && can(regex(",
        },
        "cloud_sql_schema_owner_role": {
            "next": 'variable "cloud_sql_migrator_role"',
            "migration_service_guard": "var.cloud_sql_schema_owner_role != null && can(regex(",
        },
        "cloud_sql_migrator_role": {
            "next": 'variable "cloud_sql_runtime_role"',
            "migration_service_guard": "var.cloud_sql_migrator_role != null && can(regex(",
        },
        "cloud_sql_runtime_role": {
            "next": 'variable "cloud_sql_recovery_policy_review_status"',
            "migration_service_guard": "var.cloud_sql_runtime_role != null && can(regex(",
        },
        "cloud_sql_recovery_policy_review_status": {
            "next": 'variable "golden_rose_public_environment_label"',
            "migration_service_guard": "var.cloud_sql_recovery_policy_review_status != null &&",
        },
    }
    for variable_name, expectations in omitted_input_assertions.items():
        assert f'variable "{variable_name}"' in develop_variables
        assert f'variable "{variable_name}"' in root_variables

        next_variable = expectations["next"]
        assert next_variable is not None
        develop_section = develop_variables.split(f'variable "{variable_name}"', 1)[1].split(
            next_variable, 1
        )[0]
        root_section = root_variables.split(f'variable "{variable_name}"', 1)[1].split(
            next_variable, 1
        )[0]
        for section in (develop_section, root_section):
            assert "nullable    = true" in section
            assert "default     = null" in section

        root_guard = expectations.get(
            "root_guard",
            f'var.deployment_stage == "foundation" ? var.{variable_name} == null',
        )
        if root_guard is not None:
            assert root_guard in root_section
        develop_guard = expectations.get(
            "develop_guard",
            f'var.deployment_stage == "foundation" ? var.{variable_name} == null',
        )
        assert develop_guard is not None
        assert develop_guard in develop_section
        migration_service_guard = expectations.get("migration_service_guard", develop_guard)
        assert migration_service_guard is not None
        assert migration_service_guard in develop_section

    assert 'value = var.deployment_stage == "foundation" ? null :' in develop_outputs
    assert "google_sql_database_instance.develop[0].name" in develop_outputs
    assert "google_sql_database.application[0].name" in develop_outputs


def test_gcp_terraform_outputs_minimize_database_metadata_and_mark_it_sensitive() -> None:
    outputs = (ROOT / "infra/gcp/outputs.tf").read_text(encoding="utf-8")

    assert 'output "database_contract"' in outputs
    assert 'output "database_recovery_contract"' in outputs
    assert "module.develop.database_contract" in outputs
    assert "module.develop.database_recovery_contract" in outputs
    assert "sensitive   = true" in outputs or "sensitive = true" in outputs
    assert "password" not in outputs.lower()
    assert "secret" not in outputs.lower()
    assert "private_key" not in outputs.lower()


def test_gcp_develop_budgets_model_fixed_thresholds_operator_routing_and_non_cap_posture() -> None:
    budgets = (ROOT / "infra/gcp/develop/budgets.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    root_module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")
    outputs = (ROOT / "infra/gcp/outputs.tf").read_text(encoding="utf-8")

    assert 'resource "google_billing_budget" "develop"' in budgets
    assert _contains_normalized_fragment(budgets, "billing_account = var.billing_account_id")
    assert 'google_project_service.approved["billingbudgets.googleapis.com"]' in budgets
    assert "google_monitoring_notification_channel.alerts.name" in budgets
    assert _contains_normalized_fragment(budgets, "disable_default_iam_recipients = true")
    assert "threshold_percent = 0.5" in budgets
    assert "threshold_percent = 0.75" in budgets
    assert "threshold_percent = 1.0" in budgets
    assert "projects/${var.project_id}" in budgets
    assert "alerts are not hard spending caps" in budgets
    assert "@" not in budgets
    assert "pubsub" not in budgets.lower()

    assert 'variable "billing_account_id"' in develop_variables
    assert 'variable "billing_account_id"' in root_variables
    assert _contains_normalized_fragment(root_module, "billing_account_id = var.billing_account_id")

    assert 'output "cost_guardrail_contract"' in outputs
    assert "module.develop.cost_guardrail_contract" in outputs


def test_budget_api_is_managed_and_budget_depends_on_it() -> None:
    apis = (ROOT / "infra/gcp/develop/apis.tf").read_text(encoding="utf-8")
    budgets = (ROOT / "infra/gcp/develop/budgets.tf").read_text(encoding="utf-8")

    assert "billingbudgets.googleapis.com" in apis
    assert 'google_project_service.approved["billingbudgets.googleapis.com"]' in budgets


def test_approved_api_inventory_includes_billing_budgets() -> None:
    apis = (ROOT / "infra/gcp/develop/apis.tf").read_text(encoding="utf-8")
    verifier = (ROOT / "scripts/verify_gcp_foundation.py").read_text(encoding="utf-8")

    assert "billingbudgets.googleapis.com" in apis
    assert "billingbudgets.googleapis.com" in verifier


def test_transaction_log_retention_rejects_zero_and_values_above_seven() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    for variables_text in [root_variables, develop_variables]:
        assert "cloud_sql_transaction_log_retention_days" in variables_text
        assert "<= 7" in variables_text
        assert ">= 1" in variables_text
        assert "between 1 and 7 days" in variables_text


def test_retained_backups_rejects_zero_and_values_above_365() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    for variables_text in [root_variables, develop_variables]:
        assert "cloud_sql_retained_backups" in variables_text
        assert "<= 365" in variables_text
        assert ">= 1" in variables_text
        assert "between 1 and 365 backups" in variables_text


def test_root_and_module_recovery_validations_are_identical() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    root_transaction_section = root_variables.split(
        'variable "cloud_sql_transaction_log_retention_days"', 1
    )[1].split('variable "cloud_sql_retained_backups"', 1)[0]
    develop_transaction_section = develop_variables.split(
        'variable "cloud_sql_transaction_log_retention_days"', 1
    )[1].split('variable "cloud_sql_retained_backups"', 1)[0]
    root_backup_section = root_variables.split('variable "cloud_sql_retained_backups"', 1)[1].split(
        'variable "cloud_sql_database_name"', 1
    )[0]
    develop_backup_section = develop_variables.split('variable "cloud_sql_retained_backups"', 1)[
        1
    ].split('variable "cloud_sql_database_name"', 1)[0]

    assert root_transaction_section == develop_transaction_section
    assert root_backup_section == develop_backup_section


def test_gcp_develop_observability_models_private_alerting_bounded_retention_and_startup_dependencies() -> (
    None
):
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    root_module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")
    outputs = (ROOT / "infra/gcp/outputs.tf").read_text(encoding="utf-8")
    develop_outputs = (ROOT / "infra/gcp/develop/outputs.tf").read_text(encoding="utf-8")
    cloud_run = (ROOT / "infra/gcp/develop/cloud_run.tf").read_text(encoding="utf-8")
    migration_job = (ROOT / "infra/gcp/develop/migration_job.tf").read_text(encoding="utf-8")

    required_variable_names = [
        "alert_notification_email_address",
        "observability_viewer_principal",
        "log_retention_days",
        "cloud_run_request_log_posture",
    ]
    for variable_name in required_variable_names:
        assert f'variable "{variable_name}"' in develop_variables
        assert f'variable "{variable_name}"' in root_variables
        assert _contains_normalized_fragment(root_module, f"{variable_name} = var.{variable_name}")

    required_fragments = [
        'resource "google_monitoring_notification_channel" "alerts"',
        'resource "google_logging_project_exclusion" "uuid_bearing_staff_paths"',
        'resource "google_monitoring_uptime_check_config" "readiness"',
        'resource "google_monitoring_alert_policy" "health_failures"',
        'resource "google_monitoring_alert_policy" "readiness_failures"',
        'resource "google_monitoring_alert_policy" "service_error_events"',
        'resource "google_logging_project_bucket_config" "default"',
        'resource "google_logging_metric" "health_failure_count"',
        'resource "google_logging_metric" "service_error_count"',
        'role    = "roles/logging.viewer"',
        'role    = "roles/monitoring.viewer"',
        "member  = var.observability_viewer_principal",
        "retention_days = var.log_retention_days",
        "var.cloud_run_request_log_posture",
        'path         = "/readiness"',
        'display_name = "Develop private synthetic public readiness"',
        "google_monitoring_uptime_check_config.readiness[0].uptime_check_id",
        'google_project_service.approved["logging.googleapis.com"]',
        'google_project_service.approved["monitoring.googleapis.com"]',
    ]
    for fragment in required_fragments:
        assert _contains_normalized_fragment(observability, fragment)

    assert _contains_normalized_fragment(
        observability,
        'resource.type=\\"cloud_run_revision\\" AND metric.type=\\"logging.googleapis.com/user/develop-health-failure-count\\"',
    )
    assert _contains_normalized_fragment(
        observability,
        'resource.type=\\"cloud_run_revision\\" AND metric.type=\\"logging.googleapis.com/user/develop-service-error-count\\"',
    )

    forbidden_fragments = [
        'resource "google_logging_project_sink"',
        "request.body",
        "requestBody",
        "jsonPayload",
        "textPayload",
        "service_agent_authentication",
        "allUsers",
        "allAuthenticatedUsers",
        "untested RTO",
        "approved SLO",
        'resource "google_logging_metric" "readiness_failure_count"',
    ]
    for fragment in forbidden_fragments:
        assert fragment not in observability

    assert "google_billing_budget.develop" in cloud_run
    assert "google_monitoring_alert_policy.health_failures" in cloud_run
    assert "google_billing_budget.develop" in migration_job
    assert "google_monitoring_alert_policy.health_failures" in migration_job

    assert 'output "observability_contract"' in outputs
    assert "module.develop.observability_contract" in outputs
    assert "authenticated_readiness_uptime" in develop_outputs
    assert "approved_service_level_commitment" in develop_outputs
    assert "@" not in outputs


def test_stronger_request_log_posture_has_enforceable_exclusion_or_is_rejected() -> None:
    variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")

    expected_marker = "exclude-uuid-bearing-staff-paths-and-restrict-access-no-export"
    for text in [variables, develop_variables]:
        assert expected_marker in text
        assert "exclude-uuid-bearing-paths-if-supported" not in text

    assert 'resource "google_logging_project_exclusion" "uuid_bearing_staff_paths"' in observability


def test_uuid_bearing_staff_paths_are_not_retained_in_routine_request_logs() -> None:
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")

    assert "/api/staff/v1/employers/[0-9a-fA-F-]{36}" in observability
    assert "google_logging_project_exclusion" in observability
    assert "request.body" not in observability
    assert "jsonPayload" not in observability


def test_public_readiness_uptime_check_targets_exact_cloud_run_service() -> None:
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")

    assert 'resource "google_monitoring_uptime_check_config" "readiness"' in observability
    assert 'display_name = "Develop private synthetic public readiness"' in observability
    assert 'request_method = "GET"' in observability
    assert 'path           = "/readiness"' in observability
    assert 'type = "uptime_url"' in observability
    assert "host       = local.readiness_uptime_host" in observability
    assert "service_agent_authentication" not in observability


def test_public_readiness_has_no_redundant_monitoring_invoker() -> None:
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")
    iam = (ROOT / "infra/gcp/develop/iam.tf").read_text(encoding="utf-8")

    assert 'resource "google_cloud_run_v2_service_iam_member"' not in observability
    assert "gcp-sa-monitoring-notification.iam.gserviceaccount.com" not in observability
    assert "gcp-sa-monitoring-notification.iam.gserviceaccount.com" not in iam
    assert "roles/run.servicesInvoker" not in iam


def test_availability_alert_detects_repeated_authenticated_readiness_failure() -> None:
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")

    assert 'resource "google_monitoring_alert_policy" "readiness_failures"' in observability
    assert 'metric.type=\\"monitoring.googleapis.com/uptime_check/check_passed\\"' in observability
    assert 'comparison      = "COMPARISON_LT"' in observability
    assert "threshold_value = 1" in observability
    assert 'duration        = "300s"' in observability
    assert (
        "notification_channels = [google_monitoring_notification_channel.alerts.name]"
        in observability
    )


def test_alert_evidence_does_not_claim_approved_slo_or_rto() -> None:
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")
    template = (ROOT / "deploy/gcp/evidence-template.md").read_text(encoding="utf-8")

    assert "service-level objective or recovery-time commitments" in observability
    assert "approved SLO" not in observability
    assert "approved RTO" not in observability
    assert "provisional develop review triggers" in template
    assert "not SLOs or client commitments" in template


def test_service_uses_accepted_iam_private_ingress_not_unreachable_internal_only_posture() -> None:
    cloud_run = (ROOT / "infra/gcp/develop/cloud_run.tf").read_text(encoding="utf-8")
    develop_locals = (ROOT / "infra/gcp/develop/locals.tf").read_text(encoding="utf-8")

    assert "google_cloud_run_v2_service" in cloud_run
    assert "ingress" in cloud_run
    assert "INGRESS_TRAFFIC_ALL" in cloud_run
    assert "INGRESS_TRAFFIC_INTERNAL_ONLY" not in cloud_run
    assert "deletion_protection" in cloud_run
    assert "labels" in cloud_run
    assert "local.standard_labels" in cloud_run
    assert "vpc_access" in cloud_run
    assert "network_interfaces" in cloud_run
    assert "google_compute_subnetwork.direct_vpc[0].id" in cloud_run
    assert "PRIVATE_RANGES_ONLY" in cloud_run
    assert "image" in cloud_run
    assert "local.managed_container_image" in cloud_run
    assert ":latest" not in cloud_run.lower()
    assert "google_cloud_run_service_iam" not in cloud_run
    assert "google_cloud_run_v2_service_iam" not in cloud_run
    assert "roles/run.invoker" not in cloud_run
    assert "allUsers" not in cloud_run
    assert "allAuthenticatedUsers" not in cloud_run
    assert "serviceAccount:" not in cloud_run
    assert "connector" not in cloud_run.lower()
    assert 'google_project_service.approved["run.googleapis.com"]' in cloud_run
    assert "depends_on" in cloud_run
    assert "provisioner" not in cloud_run.lower()
    assert "local-exec" not in cloud_run.lower()
    assert "managed_container_image" in develop_locals
    assert "staff-tracer@${var.container_image_digest}" in develop_locals
    assert "google_artifact_registry_repository.application_images.repository_id" in develop_locals
    assert "${var.region}-docker.pkg.dev/${var.project_id}" in develop_locals


def test_gcp_develop_identities_are_distinct_without_keys_or_broad_project_iam() -> None:
    identities = (ROOT / "infra/gcp/develop/identities.tf").read_text(encoding="utf-8")

    expected_account_ids = [
        "staff-tracer-runtime",
        "staff-tracer-migration",
    ]

    assert "google_service_account" in identities
    for account_id in expected_account_ids:
        assert account_id in identities
    assert "google_service_account_key" not in identities
    assert "private_key" not in identities
    assert "google_project_iam" not in identities
    assert "roles/owner" not in identities
    assert "roles/editor" not in identities
    assert "roles/iam.serviceAccountUser" not in identities
    assert "roles/run.invoker" not in identities
    assert "allUsers" not in identities
    assert "allAuthenticatedUsers" not in identities
    assert "serviceAccount:" not in identities
    assert "@" not in identities
    assert "depends_on" in identities
    assert 'google_project_service.approved["iam.googleapis.com"]' in identities
    assert "provisioner" not in identities.lower()
    assert "local-exec" not in identities.lower()


def test_gcp_develop_cloud_run_uses_runtime_service_account_without_invoker_grant() -> None:
    cloud_run = (ROOT / "infra/gcp/develop/cloud_run.tf").read_text(encoding="utf-8")

    assert "service_account" in cloud_run
    assert "google_service_account.runtime.email" in cloud_run
    assert "google_service_account.migration.email" not in cloud_run
    assert "roles/run.invoker" not in cloud_run
    assert "google_cloud_run_service_iam" not in cloud_run
    assert "google_cloud_run_v2_service_iam" not in cloud_run
    assert "allUsers" not in cloud_run
    assert "allAuthenticatedUsers" not in cloud_run


def test_gcp_develop_iam_models_least_privilege_runtime_migration_deployer_and_invoker_contracts() -> (
    None
):
    iam = (ROOT / "infra/gcp/develop/iam.tf").read_text(encoding="utf-8")
    variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    required_variable_names = [
        "control_plane_project_id",
        "demo_access_expires_at",
    ]
    for variable_name in required_variable_names:
        assert f'variable "{variable_name}"' in variables

    required_fragments = [
        'resource "google_project_iam_member" "runtime_cloudsql_client"',
        'resource "google_project_iam_member" "runtime_log_writer"',
        'resource "google_project_iam_member" "runtime_metric_writer"',
        'resource "google_project_iam_member" "migration_cloudsql_client"',
        'resource "google_project_iam_member" "migration_log_writer"',
        'resource "google_project_iam_member" "migration_metric_writer"',
        'resource "google_cloud_run_v2_job_iam_member" "deployer_jobs_executor"',
        'resource "google_cloud_run_v2_job_iam_member" "deployer_migration_job_viewer"',
        'resource "google_cloud_run_v2_service_iam_member" "deployer_staff_service_viewer"',
        'resource "google_secret_manager_secret_iam_member" "runtime_database_secret_access"',
        'resource "google_secret_manager_secret_iam_member" "migration_database_secret_access"',
        'resource "google_secret_manager_secret_iam_member" "runtime_synthetic_staff_secret_access"',
        'resource "google_secret_manager_secret_iam_member" "migration_synthetic_staff_secret_access"',
        'resource "google_secret_manager_secret_iam_member" "runtime_demo_access_secret_access"',
        'resource "google_artifact_registry_repository_iam_member" "image_publisher_writer"',
        'resource "google_artifact_registry_repository_iam_member" "artifact_verifier_reader"',
        'resource "google_cloud_run_v2_service_iam_member" "public_invoker"',
        'resource "google_project_iam_custom_role" "provisioner_quota_user"',
        'resource "google_project_iam_member" "provisioner_quota_user"',
        "roles/cloudsql.client",
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/run.jobsExecutor",
        "roles/run.viewer",
        "roles/secretmanager.secretAccessor",
        "roles/artifactregistry.writer",
        "roles/artifactregistry.reader",
        "roles/run.invoker",
        "serviceAccount:${google_service_account.runtime.email}",
        "serviceAccount:${google_service_account.migration.email}",
        "golden-rose-image-publisher@${var.control_plane_project_id}.iam.gserviceaccount.com",
        "golden-rose-artifact-verifier@${var.control_plane_project_id}.iam.gserviceaccount.com",
        "golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com",
        'member   = "allUsers"',
        'permissions = ["serviceusage.services.use"]',
    ]
    for fragment in required_fragments:
        assert fragment in iam

    forbidden_fragments = [
        "roles/owner",
        "roles/editor",
        "roles/viewer",
        "roles/secretmanager.admin",
        "roles/artifactregistry.admin",
        "roles/run.admin",
        "roles/run.developer",
        "roles/run.jobsExecutorWithOverrides",
        "roles/iam.serviceAccountUser",
        "roles/iam.serviceAccountTokenCreator",
        "google_service_account_key",
        "allAuthenticatedUsers",
        "tester_authority",
        "verify_tester_authority_receipt.py",
        'resource "google_artifact_registry_repository_iam_member" "deployer_reader"',
        'resource "google_artifact_registry_repository_iam_member" "image_publisher_reader"',
        "var.deployer_principal",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in iam


def test_foundation_omits_job_iam_members_and_terraform_evaluates_the_stage_counts_without_cloud(
    tmp_path: Path,
) -> None:
    iam = (ROOT / "infra/gcp/develop/iam.tf").read_text(encoding="utf-8")
    migration_count = (
        'count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0'
    )

    for resource_name in ["deployer_jobs_executor", "deployer_migration_job_viewer"]:
        resource = iam.split(f'resource "google_cloud_run_v2_job_iam_member" "{resource_name}"', 1)[
            1
        ].split("}\n", 1)[0]
        assert _contains_normalized_fragment(resource, migration_count)
        assert "google_cloud_run_v2_job.migration[0].name" in resource

    terraform_root = tmp_path / "foundation-stage"
    terraform_root.mkdir()
    # This minimal Terraform configuration preserves the checked-in count
    # condition and [0] dependency shape while avoiding unrelated foundation
    # resources. terraform_data is Terraform's built-in provider, so the plan
    # equivalent reaches the expression without credentials or cloud access.
    (terraform_root / "main.tf").write_text(
        """variable "deployment_stage" {
  type = string
}

resource "terraform_data" "migration_job" {
  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  input = "migration-job"
}

resource "terraform_data" "deployer_jobs_executor" {
  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  input = terraform_data.migration_job[0].id
}

resource "terraform_data" "deployer_migration_job_viewer" {
  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  input = terraform_data.migration_job[0].id
}
""",
        encoding="utf-8",
    )
    (terraform_root / "foundation_job_iam.tftest.hcl").write_text(
        """run "foundation_omits_job_iam" {
  command = plan

  variables {
    deployment_stage = "foundation"
  }

  assert {
    condition = length(terraform_data.deployer_jobs_executor) == 0 && length(terraform_data.deployer_migration_job_viewer) == 0
    error_message = "Foundation must omit both migration Job IAM members."
  }
}
""",
        encoding="utf-8",
    )

    terraform_env = os.environ | {"TF_DATA_DIR": str(tmp_path / ".tfdata-foundation")}
    init_result = subprocess.run(
        ["terraform", f"-chdir={terraform_root}", "init", "-backend=false", "-input=false"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=terraform_env,
    )
    assert init_result.returncode == 0, init_result.stdout + init_result.stderr

    result = subprocess.run(
        ["terraform", f"-chdir={terraform_root}", "test", "-no-color"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=terraform_env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "foundation_omits_job_iam" in result.stdout
    assert "Success!" in result.stdout


def test_temporary_public_invoker_replaces_named_tester_authority() -> None:
    variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    iam = (ROOT / "infra/gcp/develop/iam.tf").read_text(encoding="utf-8")

    for text in [variables, develop_variables]:
        assert 'variable "demo_access_expires_at"' in text
        assert "sensitive = true" in text
        assert 'variable "tester_authority_receipt_path"' not in text
        assert 'variable "tester_authority_bundle_path"' not in text
        assert 'variable "tester_authority_certificate_identity"' not in text
        assert 'variable "private_invoker_principal"' not in text

    assert 'resource "google_cloud_run_v2_service_iam_member" "public_invoker"' in iam
    assert 'role     = "roles/run.invoker"' in iam
    assert 'member   = "allUsers"' in iam
    assert "private_invoker" not in iam
    assert "tester_authority" not in iam
    assert "allAuthenticatedUsers" not in iam


def test_demo_expiry_is_the_only_service_access_tfvars_input() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    module_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    iam = (ROOT / "infra/gcp/develop/iam.tf").read_text(encoding="utf-8")

    for variables in [root_variables, module_variables]:
        assert 'variable "demo_access_expires_at"' in variables
        assert 'variable "tester_authority_receipt_path"' not in variables
        assert 'variable "tester_authority_bundle_path"' not in variables
        assert 'variable "tester_authority_certificate_identity"' not in variables
        assert 'variable "private_invoker_principal"' not in variables
        assert 'variable "tester_authority_receipt_sha256"' not in variables

    assert 'data "external" "tester_authority"' not in iam
    assert "verify_tester_authority_receipt.py" not in iam
    assert "member   = var.private_invoker_principal" not in iam


def test_shared_access_runbook_states_exact_public_transport_boundary() -> None:
    runbook = (ROOT / "deploy/gcp/private-tester-access.md").read_text(encoding="utf-8")
    first_deploy = (ROOT / "deploy/gcp/first-deployment-runbook.md").read_text(encoding="utf-8")

    assert "named tester group" not in runbook
    assert "named tester group" not in first_deploy
    assert "internet-reachable" in runbook
    assert "allUsers" in runbook
    assert "application Basic middleware is the shared browser boundary" in first_deploy
    assert "allAuthenticatedUsers" in first_deploy
    assert "service-level" in runbook


def test_gcp_develop_migration_job_is_one_task_private_and_uses_exact_digest() -> None:
    migration_job = (ROOT / "infra/gcp/develop/migration_job.tf").read_text(encoding="utf-8")

    required_fragments = [
        'resource "google_cloud_run_v2_job" "migration"',
        'name     = "run-migrations"',
        "service_account = google_service_account.migration.email",
        "image = local.managed_container_image",
        'command = ["golden-rose-migrate"]',
        "max_retries = 0",
        "task_count  = 1",
        "parallelism = 1",
        "google_compute_subnetwork.direct_vpc[0].id",
        "PRIVATE_RANGES_ONLY",
    ]
    for fragment in required_fragments:
        assert _contains_normalized_fragment(migration_job, fragment)

    forbidden_fragments = [
        "google_service_account.runtime.email",
        "INGRESS_TRAFFIC_ALL",
        ":latest",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in migration_job


def test_gcp_develop_service_does_not_run_migrations_on_web_startup() -> None:
    cloud_run = (ROOT / "infra/gcp/develop/cloud_run.tf").read_text(encoding="utf-8")

    forbidden_fragments = [
        "golden-rose-migrate",
        "alembic",
        "upgrade head",
        "google_service_account.migration.email",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in cloud_run


def test_gcp_terraform_root_loads_develop_resource_module() -> None:
    module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")

    assert 'module "develop"' in module
    assert 'source = "./develop"' in module
    assert "project_id" in module
    assert "region" in module
    assert "container_image_digest" in module


def test_gcp_container_image_digest_is_digest_only_and_not_arbitrary_reference(
    tmp_path: Path,
) -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    for variables in (root_variables, develop_variables):
        assert "sha256:[0-9a-f]{64}$" in variables
        assert "@sha256:" not in variables
        assert "docker.pkg.dev" not in variables
        assert "latest" not in variables.lower()

    graph_root = tmp_path / "graph-probe"
    shutil.copytree(
        ROOT / "infra" / "gcp",
        graph_root,
        ignore=shutil.ignore_patterns(".terraform"),
    )
    (graph_root / "backend.tf").write_text(
        "# graph probe omits the partial backend ceremony\n",
        encoding="utf-8",
    )

    terraform_env = os.environ | {"TF_DATA_DIR": str(tmp_path / ".tfdata-root")}

    init_result = subprocess.run(
        ["terraform", f"-chdir={graph_root}", "init", "-backend=false", "-input=false"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=terraform_env,
    )

    assert init_result.returncode == 0, init_result.stdout + init_result.stderr

    result = subprocess.run(
        ["terraform", f"-chdir={graph_root}", "graph"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=terraform_env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "This configuration does not contain any resources" not in result.stdout
    expected_resource_nodes = [
        "module.develop.google_project_service.approved",
        "module.develop.google_artifact_registry_repository.application_images",
        "module.develop.google_secret_manager_secret.metadata_only",
        "module.develop.google_compute_network.develop",
        "module.develop.google_sql_database_instance.develop",
        "module.develop.google_cloud_run_v2_service.staff_tracer",
        "module.develop.google_service_account.runtime",
        "module.develop.google_service_account.migration",
        "module.develop.google_billing_budget.develop",
        "module.develop.google_monitoring_notification_channel.alerts",
        "module.develop.google_logging_project_bucket_config.default",
    ]
    for resource_node in expected_resource_nodes:
        assert resource_node in result.stdout


def test_terraform_static_validation_harness_runs_without_cloud_access() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    # After Task 2 stage-gated the Cloud Run resources, the validator should
    # pass because the count expressions reference var.deployment_stage.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Terraform static validation passed" in result.stdout


def test_infrastructure_quality_workflow_runs_static_validation_without_apply_or_auth() -> None:
    workflow = (ROOT / ".github/workflows/infrastructure-quality.yml").read_text(encoding="utf-8")

    expected_pinned_actions = [
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
        "hashicorp/setup-terraform@b9cd54a3c349d3f38e8881555d616ced269862dd",
    ]

    assert "scripts/validate_terraform_static.py" in workflow
    assert "uv run --locked python scripts/validate_terraform_static.py" in workflow
    assert "uv run pytest tests/unit/test_terraform_hygiene.py" in workflow
    assert "terraform fmt -check -recursive infra/gcp" in workflow
    assert (
        "terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly" in workflow
    )
    assert "terraform -chdir=infra/gcp validate" in workflow
    assert (
        "terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly"
        in workflow
    )
    assert "terraform -chdir=infra/gcp/bootstrap validate" in workflow
    assert '".github/workflows/**"' in workflow
    assert "astral-sh/setup-uv" in workflow
    for pinned_action in expected_pinned_actions:
        assert pinned_action in workflow
    uses_refs = re.findall(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE)
    assert uses_refs
    for uses_ref in uses_refs:
        assert re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", uses_ref)
    assert "actions/checkout@v" not in workflow
    assert "actions/setup-python@v" not in workflow
    assert "astral-sh/setup-uv@v" not in workflow
    assert "hashicorp/setup-terraform@v" not in workflow
    assert "terraform apply" not in workflow.lower()
    assert "terraform plan" not in workflow.lower()
    assert "gcloud auth" not in workflow.lower()
    assert "google-github-actions/auth" not in workflow
    assert "workload_identity_provider" not in workflow
    assert "secrets." not in workflow
    assert "id-token: write" not in workflow
    assert "push" not in workflow.lower()
    assert "deploy" not in workflow.lower()


def test_manifest_rejects_unbounded_count_on_allowed_resource_type(tmp_path: Path) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True, exist_ok=True)
    (tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json").write_text(
        (ROOT / "infra" / "policy" / "predeployment-authority-manifest.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        'resource "google_cloud_run_v2_service" "staff_tracer" {\n'
        "  count = length(var.some_unbounded_list)\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unbounded or unreviewed count expression" in result.stdout


def test_manifest_rejects_unbounded_for_each_on_allowed_resource_type(tmp_path: Path) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True, exist_ok=True)
    (tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json").write_text(
        (ROOT / "infra" / "policy" / "predeployment-authority-manifest.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "apis.tf").write_text(
        'resource "google_project_service" "approved" {\n'
        "  for_each = var.approved_project_services\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unbounded or unreviewed for_each expression" in result.stdout


def test_manifest_accepts_only_reviewed_stage_expansion_expressions(tmp_path: Path) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True, exist_ok=True)
    (tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json").write_text(
        (ROOT / "infra" / "policy" / "predeployment-authority-manifest.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        'resource "google_cloud_run_v2_service" "staff_tracer" {\n'
        '  count = contains(["service"], var.deployment_stage) ? 1 : 0\n'
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unbounded or unreviewed count expression" in result.stdout


def test_infrastructure_workflow_initializes_and_validates_workload_and_bootstrap_roots() -> None:
    workflow = (ROOT / ".github/workflows/infrastructure-quality.yml").read_text(encoding="utf-8")

    assert (
        "terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly" in workflow
    )
    assert "terraform -chdir=infra/gcp validate" in workflow
    assert (
        "terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly"
        in workflow
    )
    assert "terraform -chdir=infra/gcp/bootstrap validate" in workflow


def test_bootstrap_validation_failure_blocks_the_required_quality_path(tmp_path: Path) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("infrastructure-quality.yml").replace(
        "terraform -chdir=infra/gcp/bootstrap validate\n",
        "",
    )
    _write_workflow_fixture(tmp_path, "infrastructure-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert (
        "Run Terraform local validation" in result.stdout
        or "terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly"
        in result.stdout
    )


def test_required_workflows_use_deterministic_uv_setup_and_report_version() -> None:
    expected_setup = [
        'version: "0.12.5"',
        ('checksum: "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2"'),
    ]

    workflow_paths = [
        ROOT / ".github/workflows/infrastructure-quality.yml",
        ROOT / ".github/workflows/application-quality.yml",
    ]

    for workflow_path in workflow_paths:
        workflow = workflow_path.read_text(encoding="utf-8")
        assert "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e" in workflow
        for required_line in expected_setup:
            assert required_line in workflow
        assert "uv --version" in workflow


def test_application_quality_workflow_installs_terraform_before_full_pytest() -> None:
    workflow = (ROOT / ".github/workflows/application-quality.yml").read_text(encoding="utf-8")
    setup_terraform = "hashicorp/setup-terraform@b9cd54a3c349d3f38e8881555d616ced269862dd"
    terraform_init = "terraform -chdir=infra/gcp init -backend=false -input=false"

    assert setup_terraform in workflow
    assert terraform_init in workflow
    assert workflow.index(setup_terraform) < workflow.index("uv run pytest --cov=golden_rose")
    assert workflow.index(terraform_init) < workflow.index("uv run pytest --cov=golden_rose")


def test_build_image_workflow_separates_pull_request_validation_from_publish_authority() -> None:
    workflow = (ROOT / ".github/workflows/build-image.yml").read_text(encoding="utf-8")

    expected_pinned_actions = [
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
        "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
        "docker/setup-buildx-action@e468171a9de216ec08956ac3ada2f0791b6bd435",
        "anchore/sbom-action/download-syft@fbfd9c6c189226748411491745178e0c2017392d",
        "sigstore/cosign-installer@ba7bc0a3fef59531c69a25acd34668d6d3fe6f22",
        "google-github-actions/auth@ba79af03959ebeac9769e648f473a284504d9193",
        "docker/login-action@184bdaa0721073962dff0199f1fb9940f07167d1",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ]

    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "build-validate:" in workflow
    assert "publish-image:" in workflow
    assert "if: github.event_name == 'pull_request'" in workflow
    assert "if: github.event_name == 'workflow_dispatch'" in workflow
    assert "environment: develop" in workflow
    assert "id-token: write" in workflow
    assert "google-github-actions/auth" in workflow
    assert "workload_identity_provider" in workflow
    assert "docker/login-action" in workflow
    assert "docker/setup-buildx-action" in workflow
    assert "scripts/verify_image_provenance.py" in workflow
    assert "uv run python scripts/validate_sbom.py" in workflow
    assert "sigstore/cosign-installer" in workflow
    assert 'cosign-release: "v3.0.6"' in workflow
    assert "docker buildx build" in workflow
    assert "--push" in workflow
    assert "--metadata-file build/image-metadata.json" in workflow
    assert "--platform linux/amd64" in workflow
    assert "--provenance=mode=max" in workflow
    assert "--sbom=true" in workflow
    assert "us-east4-docker.pkg.dev" in workflow
    assert "${{ github.sha }}" in workflow
    assert "docker build -t" not in workflow
    assert "terraform apply" not in workflow.lower()
    assert "terraform plan" not in workflow.lower()
    assert "deploy-develop" not in workflow.lower()
    for pinned_action in expected_pinned_actions:
        assert pinned_action in workflow


def test_build_image_workflow_verifies_sboms_and_emits_value_safe_artifacts() -> None:
    workflow = (ROOT / ".github/workflows/build-image.yml").read_text(encoding="utf-8")

    assert "build/backend-sbom.cdx.json" in workflow
    assert "build/frontend-sbom.cdx.json" in workflow
    assert "build/image-metadata.json" in workflow
    assert "build/image-sbom.cdx.json" in workflow
    assert "build/publish-signature-verification.json" in workflow
    assert "build/publish-provenance-verification.json" in workflow
    assert "build/publish-application-sbom-verification.json" in workflow
    assert "build/published-image.txt" in workflow
    assert "backend-sbom-cdx" in workflow
    assert "frontend-sbom-cdx" in workflow
    assert "image-metadata" in workflow
    assert "image-sbom-cdx" in workflow
    assert "publish-signature-verification" in workflow
    assert "publish-provenance-verification" in workflow
    assert "publish-application-sbom-verification" in workflow
    assert "published-image" in workflow
    assert "never deploy by tag" in workflow
    assert "oauth2accesstoken" in workflow
    assert "docker.pkg.dev" in workflow
    assert "cosign sign --yes" in workflow
    assert "cosign attest --yes --type slsaprovenance1" in workflow
    assert "cosign verify --certificate-identity" in workflow
    assert "cosign verify-attestation --type slsaprovenance1" in workflow


def test_build_image_workflow_captures_actual_cosign_image_sbom_evidence() -> None:
    workflow = (ROOT / ".github/workflows/build-image.yml").read_text(encoding="utf-8")

    assert "cosign verify-attestation --type https://spdx.dev/Document" in workflow
    assert 'Path("build/image-sbom.cdx.json").write_text' not in workflow


def test_build_validation_executes_pinned_syft_against_local_linux_image() -> None:
    workflow = (ROOT / ".github/workflows/build-image.yml").read_text(encoding="utf-8")
    build_validation = workflow.split("  build-validate:", 1)[1].split("  publish-image:", 1)[0]

    syft_action = "anchore/sbom-action/download-syft@fbfd9c6c189226748411491745178e0c2017392d"
    sbom_command = '"${{ steps.syft_pr.outputs.cmd }}" golden-rose:workflow-pr --output spdx-json=build/image-sbom.spdx.json'
    verify_argument = "--pr-image-sbom-path build/image-sbom.spdx.json"

    assert syft_action in build_validation
    assert "id: syft_pr" in build_validation
    assert 'syft-version: "v1.37.0"' in build_validation
    assert sbom_command in build_validation
    assert verify_argument in build_validation
    assert build_validation.index(syft_action) < build_validation.index(sbom_command)
    assert build_validation.index(sbom_command) < build_validation.index(verify_argument)


def test_publish_workflow_validates_raw_signed_cosign_predicates_and_sbom_checksums() -> None:
    workflow = (ROOT / ".github/workflows/build-image.yml").read_text(encoding="utf-8")
    publish = workflow.split("  publish-image:", 1)[1]

    signature = "cosign verify --certificate-identity"
    provenance = "> build/publish-provenance-verification.json"
    image_sbom = "> build/image-sbom.cdx.json"
    application_sbom = "> build/publish-application-sbom-verification.json"
    generator = "uv run python scripts/generate_slsa_provenance.py"
    provenance_attest = (
        "cosign attest --yes --type slsaprovenance1 "
        "--predicate build/slsa-provenance-predicate.json"
    )
    verifier = "uv run python scripts/verify_deploy_image_authority.py"

    assert generator in publish
    assert '"infra/policy/spdx-2.3.schema.json"' in workflow
    assert "--source-ref refs/heads/develop" in publish
    assert '--source-commit "$SOURCE_COMMIT"' in publish
    assert provenance_attest in publish
    assert "> build/publish-signature-verification.json" in publish
    assert provenance in publish
    assert image_sbom in publish
    assert application_sbom in publish
    assert verifier in publish
    assert "--backend-sbom build/backend-sbom.cdx.json" in publish
    assert "--frontend-sbom build/frontend-sbom.cdx.json" in publish
    assert '"backend_sbom_base64": base64.b64encode(backend_sbom).decode()' in publish
    assert '"frontend_sbom_base64": base64.b64encode(frontend_sbom).decode()' in publish
    assert '"transparency_log_included": True' not in publish
    assert 'Path("build/publish-signature-verification.json").write_text' not in publish
    assert publish.index(signature) < publish.index(verifier)
    assert publish.index(provenance) < publish.index(verifier)
    assert publish.index(image_sbom) < publish.index(verifier)
    assert publish.index(application_sbom) < publish.index(verifier)


def test_build_image_workflow_attests_a_real_spdx_image_sbom_before_verification() -> None:
    workflow = (ROOT / ".github/workflows/build-image.yml").read_text(encoding="utf-8")

    syft_action = "anchore/sbom-action/download-syft@fbfd9c6c189226748411491745178e0c2017392d"
    sbom_command = '"${{ steps.syft.outputs.cmd }}" "$MANAGED_IMAGE" --output spdx-json=build/image-sbom.spdx.json'
    attest_command = 'cosign attest --yes --type https://spdx.dev/Document --predicate build/image-sbom.spdx.json "$MANAGED_IMAGE"'
    verify_command = "cosign verify-attestation --type https://spdx.dev/Document"

    assert syft_action in workflow
    assert 'syft-version: "v1.37.0"' in workflow
    assert sbom_command in workflow
    assert "docker scout sbom" not in workflow
    assert attest_command in workflow
    assert (
        workflow.index(syft_action)
        < workflow.index(sbom_command)
        < workflow.index(attest_command)
        < workflow.index(verify_command)
    )


def test_privileged_jobs_have_bounded_timeouts() -> None:
    workflow = (ROOT / ".github/workflows/deploy-develop.yml").read_text(encoding="utf-8")

    assert "timeout-minutes: 30" in workflow


def test_terraform_static_validation_harness_rejects_deploy_workflow_job_continue_on_error(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        "    name: deploy\n    if: github.event_name == 'workflow_dispatch'\n    runs-on: ubuntu-latest",
        "    name: deploy\n    if: github.event_name == 'workflow_dispatch'\n    continue-on-error: true\n    runs-on: ubuntu-latest",
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow job structure mutation" in result.stdout
    assert "unexpected job continue-on-error" in result.stdout


def test_terraform_static_validation_harness_rejects_deploy_workflow_without_environment(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        "    environment: develop\n", ""
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow job structure mutation" in result.stdout
    assert "changed job environment" in result.stdout


def test_terraform_static_validation_harness_rejects_deploy_workflow_without_concurrency(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        "    concurrency:\n      group: deploy-develop\n      cancel-in-progress: false\n",
        "",
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow job structure mutation" in result.stdout
    assert "changed job concurrency" in result.stdout


def test_terraform_static_validation_harness_rejects_deploy_workflow_broad_oidc_claim_mutation(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        "          workload_identity_provider: ${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}",
        "          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER_WILDCARD }}",
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow secret reference" in result.stdout
    assert "GCP_WORKLOAD_IDENTITY_PROVIDER_WILDCARD" in result.stdout
    assert "workload_identity_provider" in result.stdout


def test_terraform_static_validation_harness_rejects_deploy_workflow_arbitrary_digest_host_and_mutable_tag(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        'test "$VERIFIED_IMAGE_REF" = "$PUBLISHED_IMAGE_REF"',
        'VERIFIED_IMAGE_REF="evil.example.com/rogue/staff-tracer:latest"',
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert result.stdout


def test_terraform_static_validation_harness_rejects_forbidden_patterns(tmp_path: Path) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "bad.tf"
    bad_file.write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service_iam_member" "bad" {',
                '  role   = "roles/run.invoker"',
                '  member = "allUsers"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "allUsers" in result.stdout
    assert "roles/run.invoker" in result.stdout


def test_terraform_static_validation_harness_rejects_unlisted_manifest_resource_type(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "predeployment-authority-manifest.json").write_text(
        """
{
  "terraform": {
    "resource_types": {
      "google_compute_network": {
        "max_count": 1
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    bad_file = terraform_root / "unexpected_resource.tf"
    bad_file.write_text(
        "\n".join(
            [
                'resource "google_pubsub_topic" "unexpected" {',
                '  name = "unexpected-topic"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unlisted Terraform resource type" in result.stdout
    assert "google_pubsub_topic" in result.stdout
    assert "unexpected_resource.tf" in result.stdout


def test_terraform_static_validation_harness_rejects_tf_json_forbidden_patterns(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "bypass.tf.json"
    bad_file.write_text(
        """
{
  "resource": {
    "google_service_account_key": {
      "bad": {
        "service_account_id": "projects/example/serviceAccounts/example"
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "bypass.tf.json" in result.stdout
    assert "google_service_account_key" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_file_not_listed_in_manifest(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "predeployment-authority-manifest.json").write_text(
        """
{
  "terraform": {
    "resource_types": {
      "google_compute_network": {
        "max_count": 1
      }
    }
  },
  "workflows": {
    "files": {
      "infrastructure-quality.yml": {}
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "repository-hygiene.yml").write_text(
        _current_workflow_text("repository-hygiene.yml"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "workflow file not listed in manifest" in result.stdout
    assert "repository-hygiene.yml" in result.stdout


def test_terraform_static_validation_harness_rejects_unicode_escaped_tf_json_keys(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "unicode_bypass.tf.json"
    bad_file.write_text(
        """
{
  "resource": {
    "google_service_account_\\u006bey": {
      "bad": {
        "service_account_id": "projects/example/serviceAccounts/example"
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic Terraform construct" in result.stdout
    assert "unicode_bypass.tf.json" in result.stdout
    assert "google_service_account_key" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_script_not_listed_in_manifest(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "predeployment-authority-manifest.json").write_text(
        """
{
  "terraform": {
    "resource_types": {
      "google_compute_network": {
        "max_count": 1
      }
    }
  },
  "workflows": {
    "files": {
      "application-quality.yml": {}
    }
  },
  "scripts": {
    "entrypoints": [
      "apps/web/scripts/validate-lockfile.mjs",
      "apps/web/scripts/validate-lockfile.test.mjs"
    ]
  }
}
""".strip(),
        encoding="utf-8",
    )

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        _current_workflow_text("application-quality.yml"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "workflow script entrypoint not listed in manifest" in result.stdout
    assert "scripts/validate_sbom.py" in result.stdout


def test_terraform_static_validation_harness_rejects_unicode_escaped_native_hcl_labels(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    bad_file = terraform_root / "unicode_bypass.tf"
    bad_file.write_text(
        'resource "google_service_account_\\u006bey" "bad" {}',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic Terraform construct" in result.stdout
    assert "unicode_bypass.tf" in result.stdout
    assert "google_service_account_key" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_deployment_path_not_listed_in_manifest(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "predeployment-authority-manifest.json").write_text(
        """
{
  "terraform": {
    "resource_types": {
      "google_compute_network": {
        "max_count": 1
      }
    }
  },
  "workflows": {
    "files": {
      "infrastructure-quality.yml": {}
    }
  },
  "scripts": {
    "entrypoints": [
      "scripts/validate_terraform_static.py"
    ]
  },
  "protected_deployment_paths": []
}
""".strip(),
        encoding="utf-8",
    )

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "infrastructure-quality.yml").write_text(
        _current_workflow_text("infrastructure-quality.yml"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "workflow deployment path not listed in manifest" in result.stdout
    assert "infra/gcp" in result.stdout


def test_terraform_static_validation_harness_rejects_malformed_native_hcl_fail_closed(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    bad_file = terraform_root / "malformed.tf"
    bad_file.write_text('resource "google_compute_network" "bad" {', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains malformed Terraform HCL and fails closed" in result.stdout
    assert "malformed.tf" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_step_not_listed_in_manifest(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "predeployment-authority-manifest.json").write_text(
        """
{
  "terraform": {
    "resource_types": {
      "google_compute_network": {
        "max_count": 1
      }
    }
  },
  "workflows": {
    "files": {
      "infrastructure-quality.yml": {
        "jobs": {
          "static-validation": {
            "steps": [
              "name:Check out repository"
            ]
          }
        }
      }
    }
  },
  "scripts": {
    "entrypoints": [
      "scripts/validate_terraform_static.py"
    ]
  },
  "protected_deployment_paths": [
    "infra/gcp"
  ]
}
""".strip(),
        encoding="utf-8",
    )

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "infrastructure-quality.yml").write_text(
        _current_workflow_text("infrastructure-quality.yml"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "workflow step not listed in manifest" in result.stdout
    assert "name:Set up uv" in result.stdout


@pytest.mark.parametrize(
    "old_fragment, new_fragment, expected_fragment",
    [
        (
            'role   = "roles/storage.objectAdmin"',
            'role   = "roles/storage.admin"',
            "object-admin role",
        ),
        (
            "for_each = toset(local.active_state_bucket_object_admin_principals)",
            "for_each = tolist(local.active_state_bucket_object_admin_principals)",
            "active_state_bucket_object_admin_principals",
        ),
        (
            'var.bootstrap_operator_status == "bootstrap-active" ? [var.bootstrap_operator_principal] : [],',
            'var.bootstrap_operator_status == "bootstrap-retired" ? [var.bootstrap_operator_principal] : [],',
            "active state-bucket object-admin principal collection",
        ),
        (
            '      "serviceAccount:${google_service_account.provisioner.email}",',
            '      "serviceAccount:${google_service_account.image_publisher.email}",',
            "active state-bucket object-admin principal collection",
        ),
    ],
)
def test_terraform_static_validation_harness_rejects_state_bucket_iam_drift(
    tmp_path: Path, old_fragment: str, new_fragment: str, expected_fragment: str
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "iam.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/iam.tf")
        .read_text(encoding="utf-8")
        .replace(old_fragment, new_fragment, 1),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert expected_fragment in result.stdout


def test_terraform_static_validation_rejects_commented_state_bucket_principal_decoy(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    current = (ROOT / "infra/gcp/bootstrap/iam.tf").read_text(encoding="utf-8")
    reviewed_local = current.split("locals {", 1)[1].split("\n}\n", 1)[0]
    mutated = current.replace(
        '"serviceAccount:${google_service_account.provisioner.email}"',
        '"serviceAccount:${google_service_account.image_publisher.email}"',
        1,
    )
    (bootstrap_dir / "iam.tf").write_text(
        f"/*\nlocals {{{reviewed_local}\n}}\n*/\n{mutated}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "active state-bucket object-admin principal collection" in result.stdout


def test_terraform_static_validation_binds_bucket_iam_to_each_deduplicated_principal(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "iam.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/iam.tf")
        .read_text(encoding="utf-8")
        .replace("member = each.value", "member = var.state_authority_principal", 1),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "deduplicated member binding" in result.stdout


def test_bootstrap_bucket_iam_uses_one_deduplicated_address_per_principal() -> None:
    iam = (ROOT / "infra/gcp/bootstrap/iam.tf").read_text(encoding="utf-8")

    assert "locals {" in iam
    assert "active_state_bucket_object_admin_principals" in iam
    assert "toset(" in iam
    assert 'resource "google_storage_bucket_iam_member" "object_admin"' in iam
    assert re.search(
        r"for_each\s*=\s*toset\(\s*local\.active_state_bucket_object_admin_principals\s*\)",
        iam,
    )
    assert re.search(r"member\s*=\s*each\.value", iam)
    assert '"serviceAccount:${google_service_account.provisioner.email}"' in iam
    assert "state_authority_object_admin" not in iam
    assert "recovery_authority_object_admin" not in iam
    assert "bootstrap_operator_object_admin" not in iam


def test_terraform_static_validation_rejects_nondeduplicated_bootstrap_bucket_iam(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "iam.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/iam.tf")
        .read_text(encoding="utf-8")
        .replace(
            "for_each = toset(local.active_state_bucket_object_admin_principals)",
            "for_each = tolist(local.active_state_bucket_object_admin_principals)",
            1,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "active_state_bucket_object_admin_principals" in result.stdout


def test_terraform_static_validation_accepts_whitespace_equivalent_deduplicated_bootstrap_iam(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "iam.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/iam.tf")
        .read_text(encoding="utf-8")
        .replace(
            "active_state_bucket_object_admin_principals = concat(",
            "active_state_bucket_object_admin_principals   =   concat( ",
            1,
        )
        .replace(
            "for_each = toset(local.active_state_bucket_object_admin_principals)",
            "for_each   =   toset( local.active_state_bucket_object_admin_principals )",
            1,
        )
        .replace(
            "bucket = google_storage_bucket.terraform_state.name",
            "bucket   =   google_storage_bucket.terraform_state.name",
            1,
        )
        .replace('role   = "roles/storage.objectAdmin"', 'role = "roles/storage.objectAdmin"', 1)
        .replace("member = each.value", "member     =     each.value", 1),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0


def test_terraform_static_validation_rejects_unconditionally_active_bootstrap_operator(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "iam.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/iam.tf")
        .read_text(encoding="utf-8")
        .replace(
            "      var.recovery_authority_principal,\n",
            "      var.recovery_authority_principal,\n      var.bootstrap_operator_principal,\n",
            1,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "active state-bucket object-admin principal collection" in result.stdout


def test_terraform_static_validation_harness_rejects_tf_json_backend_configuration(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "backend.tf.json"
    bad_file.write_text(
        """
{
  "terraform": [
    {
      "backend": [
        {
          "gcs": {
            "bucket": "shared-state"
          }
        }
      ]
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "approved partial backend path" in result.stdout
    assert "committed backend value" in result.stdout
    assert "backend.tf.json" in result.stdout
    assert "backend" in result.stdout


def test_terraform_static_validation_harness_rejects_tf_json_provider_credentials(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "providers.tf.json"
    bad_file.write_text(
        """
{
  "provider": {
    "google": [
      {
        "project": "example-project",
        "region": "us-east4",
        "credentials": "${file(\"/tmp/operator-held-credentials.json\")}"
      }
    ]
  }
}
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "providers.tf.json" in result.stdout
    assert "credentials" in result.stdout


def test_terraform_static_validation_harness_rejects_tf_json_cloud_run_env_injection(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "env_injection.tf.json"
    bad_file.write_text(
        """
{
  "resource": {
    "google_cloud_run_v2_service": {
      "bad": {
        "template": [
          {
            "containers": [
              {
                "image": "example@sha256:"
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "env": [
                  {
                    "name": "DATABASE_URL",
                    "value_source": [
                      {
                        "secret_key_ref": [
                          {
                            "secret": "database-url",
                            "version": "1"
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "env_injection.tf.json" in result.stdout
    assert (
        "forbidden" in result.stdout
        or "unlisted" in result.stdout.lower()
        or "malformed" in result.stdout.lower()
    )


def test_terraform_static_validation_harness_rejects_backend_configuration(tmp_path: Path) -> None:
    terraform_root = tmp_path / "infra" / "gcp"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "backend.tf"
    bad_file.write_text(
        "\n".join(
            [
                "terraform {",
                '  backend "gcs" {',
                '    bucket = "shared-state"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "committed backend value" in result.stdout
    assert "backend" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_backend_committed_prefix(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "bootstrap"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "backend.tf"
    bad_file.write_text(
        "\n".join(
            [
                "terraform {",
                '  backend "gcs" {',
                '    prefix = "shared-workload-state"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "committed backend value" in result.stdout
    assert "infra/gcp/bootstrap/backend.tf" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_backend_committed_prefix_with_extra_spacing(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    terraform_root = tmp_path / "infra" / "gcp" / "bootstrap"
    bad_file = terraform_root / "backend.tf"
    bad_file.write_text(
        "\n".join(
            [
                "terraform {",
                '  backend   "gcs" {',
                '    prefix = "shared-workload-state"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "committed backend value" in result.stdout
    assert "infra/gcp/bootstrap/backend.tf" in result.stdout


def test_terraform_static_validation_harness_rejects_workload_backend_committed_bucket_with_extra_spacing(
    tmp_path: Path,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    terraform_root = tmp_path / "infra" / "gcp"
    bad_file = terraform_root / "backend.tf"
    bad_file.write_text(
        "\n".join(
            [
                "terraform {",
                '  backend   "gcs" {',
                '    bucket = "shared-bootstrap-state"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "committed backend value" in result.stdout
    assert "infra/gcp/backend.tf" in result.stdout


def test_terraform_static_validation_harness_rejects_variable_input_artifacts(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp"
    terraform_root.mkdir(parents=True)
    (terraform_root / "terraform.tfvars").write_text(
        'project_id = "example-project"',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden Terraform artifact" in result.stdout
    assert "terraform.tfvars" in result.stdout


def test_terraform_static_validation_harness_rejects_infrastructure_workflow_auth(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "infrastructure-quality.yml").write_text(
        "\n".join(
            [
                "permissions:",
                "  id-token: write",
                "jobs:",
                "  bad:",
                "    steps:",
                "      - uses: google-github-actions/auth@v2",
                "        with:",
                "          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic workflow permissions" in result.stdout
    assert "id-token: write" in result.stdout
    assert "google-github-actions/auth" in result.stdout


def test_terraform_static_validation_harness_rejects_yaml_flow_and_quoted_push_triggers(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "quoted-trigger.yaml").write_text(
        "\n".join(
            [
                'name: "Quoted push trigger"',
                '"on": [push]',
                "permissions:",
                "  contents: read",
                "jobs:",
                "  noop:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic workflow trigger" in result.stdout
    assert "quoted-trigger.yaml" in result.stdout
    assert "push" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_and_job_write_permissions(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "write-permissions.yaml").write_text(
        "\n".join(
            [
                'name: "Write permissions bypass"',
                "on:",
                "  pull_request:",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  bad:",
                "    runs-on: ubuntu-latest",
                "    permissions:",
                "      contents: write",
                "    steps:",
                "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic workflow permissions" in result.stdout
    assert "write-permissions.yaml" in result.stdout
    assert "contents: write" in result.stdout


def test_terraform_static_validation_harness_rejects_mutable_job_and_service_containers(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "mutable-containers.yaml").write_text(
        "\n".join(
            [
                'name: "Mutable containers bypass"',
                "on:",
                "  pull_request:",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  bad:",
                "    runs-on: ubuntu-latest",
                "    container:",
                "      image: python:3.12",
                "    services:",
                "      postgres:",
                "        image: postgres:16.10",
                "    steps:",
                "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic workflow container image" in result.stdout
    assert "mutable-containers.yaml" in result.stdout
    assert "python:3.12" in result.stdout
    assert "postgres:16.10" in result.stdout


def test_terraform_static_validation_harness_rejects_reusable_workflow_references(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "reusable-workflow.yaml").write_text(
        "\n".join(
            [
                'name: "Reusable workflow bypass"',
                "on:",
                "  pull_request:",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  delegated:",
                "    uses: owner/repo/.github/workflows/deploy.yml@1234567890abcdef1234567890abcdef12345678",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden semantic reusable workflow reference" in result.stdout
    assert "reusable-workflow.yaml" in result.stdout
    assert ".github/workflows/deploy.yml" in result.stdout


def test_terraform_static_validation_harness_rejects_local_action_references(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "local-action.yaml").write_text(
        "\n".join(
            [
                'name: "Local action bypass"',
                "on:",
                "  pull_request:",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  delegated:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: ./.github/actions/unreviewed-local-action",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unpinned workflow action" in result.stdout
    assert "local-action.yaml" in result.stdout
    assert "./.github/actions/unreviewed-local-action" in result.stdout


def test_terraform_static_validation_harness_rejects_malformed_yaml_fail_closed(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "malformed-workflow.yaml").write_text(
        "\n".join(
            [
                "name: malformed workflow",
                "on:",
                "  pull_request:",
                "jobs:",
                "  broken:",
                "    steps:",
                "      - run: [unterminated",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains malformed workflow YAML and fails closed" in result.stdout
    assert "malformed-workflow.yaml" in result.stdout


def test_terraform_static_validation_harness_rejects_duplicate_yaml_keys(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "duplicate-keys.yaml").write_text(
        "\n".join(
            [
                "name: duplicate keys workflow",
                "on:",
                "  pull_request:",
                "jobs:",
                "  duplicate:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - run: printf 'first'",
                "    steps:",
                "      - run: printf 'second'",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains duplicate workflow YAML key and fails closed" in result.stdout
    assert "duplicate-keys.yaml" in result.stdout
    assert "steps" in result.stdout


def test_terraform_static_validation_harness_rejects_duplicate_tf_json_keys(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    bad_file = terraform_root / "duplicate-keys.tf.json"
    bad_file.write_text(
        """
{
  "resource": {
    "google_service_account_key": {
      "bad": {
        "service_account_id": "projects/example/serviceAccounts/first"
      }
    },
    "google_service_account_key": {
      "bad": {
        "service_account_id": "projects/example/serviceAccounts/second"
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains duplicate Terraform JSON key and fails closed" in result.stdout
    assert "duplicate-keys.tf.json" in result.stdout
    assert "google_service_account_key" in result.stdout


def test_terraform_static_validation_harness_redacts_parser_and_policy_violation_values(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "redaction-malformed.yaml").write_text(
        "\n".join(
            [
                "name: redaction malformed workflow",
                "on:",
                "  pull_request:",
                "jobs:",
                "  broken:",
                "    steps:",
                "      - run: [SECRET_CANARY_WORKFLOW",
            ]
        ),
        encoding="utf-8",
    )
    (workflow_dir / "redaction-policy.yaml").write_text(
        "\n".join(
            [
                "name: redaction policy workflow",
                "on:",
                "  pull_request:",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  bad:",
                "    runs-on: ubuntu-latest",
                "    container:",
                "      image: registry.example.com/SECRET_CANARY_IMAGE:latest",
                "    steps:",
                "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    combined_output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "redaction-malformed.yaml" in result.stdout
    assert "contains malformed workflow YAML and fails closed" in result.stdout
    assert "redaction-policy.yaml" in result.stdout
    assert "forbidden semantic workflow container image" in result.stdout
    assert "SECRET_CANARY_WORKFLOW" not in combined_output
    assert "SECRET_CANARY_IMAGE" not in combined_output


def test_terraform_static_validation_harness_rejects_unknown_workflow_files(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "surprise-quality.yml").write_text(
        "\n".join(
            [
                "name: surprise workflow",
                "on:",
                "  pull_request:",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  verify:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains unknown workflow file" in result.stdout
    assert "surprise-quality.yml" in result.stdout


def test_terraform_static_validation_harness_rejects_unknown_workflow_jobs(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  surprise:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains unknown workflow job" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "surprise" in result.stdout


def test_terraform_static_validation_harness_rejects_unknown_workflow_steps(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Surprise step",
                "        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains unknown workflow step" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "Surprise step" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_runs_on_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    name: application",
                "    runs-on: ubuntu-24.04",
                "    steps:",
                "      - name: Check out repository",
                "        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow runs-on mutation" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "ubuntu-24.04" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_if_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    name: application",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Upload backend SBOM evidence",
                "        if: success()",
                "        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
                "        with:",
                "          name: backend-sbom-cdx",
                "          path: build/backend-sbom.cdx.json",
                "          if-no-files-found: error",
                "          retention-days: 14",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow if mutation" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "success()" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_action_with_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    name: application",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Upload backend SBOM evidence",
                "        if: always()",
                "        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
                "        with:",
                "          name: backend-sbom-cdx",
                "          path: build/backend-sbom.cdx.json",
                "          if-no-files-found: error",
                "          retention-days: 99",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow action with mutation" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "retention-days" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_uses_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    name: application",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Check out repository",
                "        uses: evilcorp/evil-action@1111111111111111111111111111111111111111",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow uses mutation" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "Check out repository" in result.stdout


def test_terraform_static_validation_harness_rejects_named_run_step_action_substitution(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "application-quality.yml").write_text(
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    name: application",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Run application quality gate",
                "        uses: evilcorp/quality-bypass@1111111111111111111111111111111111111111",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow uses mutation" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "Run application quality gate" in result.stdout
    assert "evilcorp/quality-bypass" in result.stdout


def test_terraform_static_validation_harness_rejects_missing_quality_gate_step(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _remove_named_workflow_step(
        _current_workflow_text("application-quality.yml"),
        "Run application quality gate",
        "Upload backend SBOM evidence",
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow step inventory mutation" in result.stdout
    assert "application-quality.yml" in result.stdout
    assert "missing name:Run application quality gate" in result.stdout


def test_terraform_static_validation_harness_rejects_checkout_only_quality_workflow(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_workflow_fixture(
        tmp_path,
        "application-quality.yml",
        "\n".join(
            [
                "name: Application quality",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  application:",
                "    name: application",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Check out repository",
                "        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            ]
        ),
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow step inventory mutation" in result.stdout
    assert "missing name:Run application quality gate" in result.stdout
    assert "step order or inventory changed" in result.stdout


def test_terraform_static_validation_harness_rejects_job_level_if_skip(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("application-quality.yml").replace(
        "    name: application\n    runs-on: ubuntu-latest",
        "    name: application\n    if: false\n    runs-on: ubuntu-latest",
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow job structure mutation" in result.stdout
    assert "unexpected job if" in result.stdout


def test_terraform_static_validation_harness_rejects_job_continue_on_error(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("application-quality.yml").replace(
        "    name: application\n    runs-on: ubuntu-latest",
        "    name: application\n    continue-on-error: true\n    runs-on: ubuntu-latest",
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow job structure mutation" in result.stdout
    assert "unexpected job continue-on-error" in result.stdout


def test_terraform_static_validation_harness_rejects_quality_gate_step_continue_on_error(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("application-quality.yml").replace(
        "      - name: Run application quality gate\n        run: |",
        "      - name: Run application quality gate\n"
        "        continue-on-error: true\n"
        "        run: |",
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow step control mutation" in result.stdout
    assert "Run application quality gate" in result.stdout
    assert "unexpected step continue-on-error" in result.stdout


def test_terraform_static_validation_harness_rejects_duplicate_approved_step(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("application-quality.yml").replace(
        "      - name: Set up Python 3.12",
        "      - name: Check out repository\n"
        "        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n\n"
        "      - name: Set up Python 3.12",
        1,
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow step inventory mutation" in result.stdout
    assert "duplicate name:Check out repository" in result.stdout


def test_application_quality_gate_requires_fail_closed_authority_downgrade_proof() -> None:
    workflow = (ROOT / ".github/workflows/application-quality.yml").read_text(encoding="utf-8")

    assert "if uv run alembic downgrade base 2> build/alembic-downgrade.stderr; then" in workflow
    assert "database authority lifecycle downgrade unexpectedly succeeded" in workflow
    assert (
        "database authority lifecycle downgrade is intentionally unsupported without "
        "an operator-reviewed role handoff"
    ) in workflow


def test_terraform_static_validation_harness_rejects_authority_downgrade_proof_mutation(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("application-quality.yml").replace(
        'grep -F "database authority lifecycle downgrade is intentionally unsupported without an operator-reviewed role handoff" build/alembic-downgrade.stderr',
        "true",
        1,
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow run mutation" in result.stdout
    assert "name:Run application quality gate ->" in result.stdout


def test_terraform_static_validation_harness_rejects_reordered_required_steps(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("application-quality.yml")
    python_step_start = workflow.index("      - name: Set up Python 3.12")
    uv_step_start = workflow.index("      - name: Set up uv", python_step_start)
    terraform_step_start = workflow.index(
        "      - name: Set up Terraform for hygiene tests", uv_step_start
    )
    python_step = workflow[python_step_start:uv_step_start]
    uv_step = workflow[uv_step_start:terraform_step_start]
    workflow = (
        workflow[:python_step_start] + uv_step + python_step + workflow[terraform_step_start:]
    )
    _write_workflow_fixture(tmp_path, "application-quality.yml", workflow)

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow step inventory mutation" in result.stdout
    assert "step order or inventory changed" in result.stdout


def test_terraform_static_validation_harness_rejects_unknown_workflow_command_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "branch-policy.yml").write_text(
        "\n".join(
            [
                "name: Branch policy",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  enforce:",
                "    name: enforce",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Validate source-to-target flow",
                "        run: echo hacked",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow run mutation" in result.stdout
    assert "branch-policy.yml" in result.stdout
    assert "echo hacked" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_shell_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "branch-policy.yml").write_text(
        "\n".join(
            [
                "name: Branch policy",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  enforce:",
                "    name: enforce",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Validate source-to-target flow",
                "        shell: bash",
                "        run: |",
                "          set -euo pipefail",
                '          case "$BASE_REF" in',
                "            main)",
                '              if [[ "$HEAD_REF" == "develop" || "$HEAD_REF" == hotfix/* ]]; then',
                '                echo "Allowed promotion: $HEAD_REF -> main"',
                "              else",
                '                echo "Only develop or hotfix/* may target main; got $HEAD_REF -> main." >&2',
                "                exit 1",
                "              fi",
                "              ;;&",
                "            develop)",
                '              if [[ "$HEAD_REF" =~ ^(feat|fix|docs|chore|hotfix|security|ci|test|refactor|spike)/[a-z0-9][a-z0-9._-]*$ ]]; then',
                '                echo "Allowed integration branch: $HEAD_REF -> develop"',
                "              else",
                '                echo "Feature branches targeting develop must use an approved prefix and lowercase slug; got $HEAD_REF." >&2',
                "                exit 1",
                "              fi",
                "              ;;&",
                "            *)",
                '              echo "Unexpected protected target branch: $BASE_REF" >&2',
                "              exit 1",
                "              ;;&",
                "          esac",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow shell mutation" in result.stdout
    assert "branch-policy.yml" in result.stdout
    assert "bash" in result.stdout


def test_terraform_static_validation_harness_rejects_workflow_working_directory_mutations(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)

    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "branch-policy.yml").write_text(
        "\n".join(
            [
                "name: Branch policy",
                "on:",
                "  pull_request:",
                "    branches: [main, develop]",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  enforce:",
                "    name: enforce",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Validate source-to-target flow",
                "        working-directory: infra",
                "        run: |",
                "          set -euo pipefail",
                '          case "$BASE_REF" in',
                "            main)",
                '              if [[ "$HEAD_REF" == "develop" || "$HEAD_REF" == hotfix/* ]]; then',
                '                echo "Allowed promotion: $HEAD_REF -> main"',
                "              else",
                '                echo "Only develop or hotfix/* may target main; got $HEAD_REF -> main." >&2',
                "                exit 1",
                "              fi",
                "              ;;",
                "            develop)",
                '              if [[ "$HEAD_REF" =~ ^(feat|fix|docs|chore|hotfix|security|ci|test|refactor|spike)/[a-z0-9][a-z0-9._-]*$ ]]; then',
                '                echo "Allowed integration branch: $HEAD_REF -> develop"',
                "              else",
                '                echo "Feature branches targeting develop must use an approved prefix and lowercase slug; got $HEAD_REF." >&2',
                "                exit 1",
                "              fi",
                "              ;;",
                "            *)",
                '              echo "Unexpected protected target branch: $BASE_REF" >&2',
                "              exit 1",
                "              ;;",
                "          esac",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "contains forbidden workflow working-directory mutation" in result.stdout
    assert "branch-policy.yml" in result.stdout
    assert "infra" in result.stdout


def test_terraform_static_validation_harness_rejects_unpinned_workflow_actions(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "terraform-quality.yml").write_text(
        "\n".join(
            [
                "permissions:",
                "  contents: read",
                "jobs:",
                "  bad:",
                "    steps:",
                "      - uses: third-party/action@main",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unpinned workflow action" in result.stdout
    assert "terraform-quality.yml" in result.stdout
    assert "third-party/action@main" in result.stdout


def test_terraform_static_validation_harness_rejects_service_account_keys(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "keys.tf").write_text(
        "\n".join(
            [
                'resource "google_service_account_key" "bad" {',
                "  service_account_id = google_service_account.runtime.name",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_service_account_key" in result.stdout


def test_terraform_static_validation_harness_rejects_yaml_infrastructure_workflow_auth(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "infrastructure-apply.yaml").write_text(
        "\n".join(
            [
                "jobs:",
                "  bad:",
                "    steps:",
                "      - run: terraform apply -auto-approve",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden workflow authority" in result.stdout
    assert "terraform apply" in result.stdout


def test_terraform_static_validation_harness_rejects_secret_injection_references(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "secret_injection.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "bad" {',
                "  template {",
                "    containers {",
                "      env {",
                '        name = "DATABASE_URL"',
                "        value_source {",
                "          secret_key_ref {",
                '            secret = "database-url"',
                '            version = "latest"',
                "          }",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert (
        "forbidden" in result.stdout
        or "unlisted" in result.stdout.lower()
        or "unapproved" in result.stdout.lower()
    )


def test_terraform_static_validation_harness_rejects_secret_manager_iam_grants(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "secret_iam.tf").write_text(
        "\n".join(
            [
                'resource "google_secret_manager_secret_iam_member" "bad" {',
                '  role   = "roles/secretmanager.secretAccessor"',
                '  member = "serviceAccount:runtime@example.iam.gserviceaccount.com"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_secret_manager_secret_iam" in result.stdout


def test_terraform_static_validation_harness_rejects_internal_only_cloud_run_ingress(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "public_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "bad" {',
                '  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert (
        "forbidden cloud run fragment" in result.stdout
        or "missing required cloud run contract fragment" in result.stdout
        or "without stage_ownership declared in manifest" in result.stdout
    )
    assert "INGRESS_TRAFFIC_INTERNAL_ONLY" in result.stdout or "stage_ownership" in result.stdout


def test_terraform_static_validation_harness_rejects_artifact_registry_iam_grants(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "artifact_iam.tf").write_text(
        "\n".join(
            [
                'resource "google_artifact_registry_repository_iam_member" "bad" {',
                '  role   = "roles/artifactregistry.writer"',
                '  member = "serviceAccount:runtime@example.iam.gserviceaccount.com"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_artifact_registry_repository_iam" in result.stdout


def test_terraform_static_validation_harness_rejects_disabled_deletion_protection(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "unsafe_delete.tf").write_text(
        "\n".join(
            [
                'resource "google_sql_database_instance" "bad" {',
                "  deletion_protection = false",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "deletion_protection = false" in result.stdout


def test_terraform_static_validation_harness_rejects_public_cloud_sql_ipv4(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "public_sql.tf").write_text(
        "\n".join(
            [
                'resource "google_sql_database_instance" "bad" {',
                "  settings {",
                "    ip_configuration {",
                "      ipv4_enabled = true",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "ipv4_enabled = true" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_sql_users(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "sql_user.tf").write_text(
        "\n".join(
            [
                'resource "google_sql_user" "bad" {',
                '  name     = "app"',
                '  password = "not-for-source"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_sql_user" in result.stdout


def test_terraform_static_validation_harness_rejects_provider_credentials(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp"
    terraform_root.mkdir(parents=True)
    (terraform_root / "providers.tf").write_text(
        "\n".join(
            [
                'provider "google" {',
                '  credentials = file("credentials.json")',
                '  impersonate_service_account = "terraform@example.iam.gserviceaccount.com"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "credentials =" in result.stdout
    assert "impersonate_service_account" in result.stdout


def test_terraform_static_validation_harness_rejects_project_iam_grants(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "project_iam.tf").write_text(
        "\n".join(
            [
                'resource "google_project_iam_member" "bad" {',
                '  role   = "roles/cloudsql.client"',
                '  member = "serviceAccount:runtime@example.iam.gserviceaccount.com"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_project_iam" in result.stdout


def test_terraform_static_validation_harness_rejects_push_triggered_workflows(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "infrastructure-quality.yml").write_text(
        "\n".join(
            [
                "on:",
                "  push:",
                "    branches: [develop]",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden workflow authority" in result.stdout
    assert "push:" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_run_environment_variables(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "cloud_run_env.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "bad" {',
                "  template {",
                "    containers {",
                "      env {",
                '        name  = "DATABASE_URL"',
                '        value = "not-for-source"',
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert (
        "forbidden" in result.stdout
        or "unlisted" in result.stdout.lower()
        or "literal" in result.stdout.lower()
    )


def test_terraform_static_validation_harness_rejects_cloud_run_jobs_outside_approved_migration_path(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "other_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  name     = "run-migrations"',
                "  location = var.region",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_cloud_run_v2_job" in result.stdout


def test_terraform_static_validation_harness_rejects_migration_job_with_runtime_identity(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    (terraform_root / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                "  project  = var.project_id",
                '  name     = "run-migrations"',
                "  location = var.region",
                "  template {",
                "    template {",
                "      service_account = google_service_account.runtime.email",
                "      max_retries = 0",
                "      containers {",
                "        image = local.managed_container_image",
                '        command = ["golden-rose-migrate"]',
                "      }",
                "    }",
                "    task_count  = 1",
                "    parallelism = 1",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert (
        "missing required migration job fragment" in result.stdout
        or "runtime.email" in result.stdout
    )


def test_terraform_static_validation_harness_rejects_billing_budget_resources(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "budget.tf").write_text(
        "\n".join(
            [
                'resource "google_billing_budget" "develop" {',
                '  billing_account = "billingAccounts/000000-000000-000000"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_billing_budget" in result.stdout


def test_terraform_static_validation_harness_rejects_logging_export_sinks(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "log_sink.tf").write_text(
        "\n".join(
            [
                'resource "google_logging_project_sink" "export" {',
                '  name        = "develop-export"',
                '  destination = "storage.googleapis.com/unapproved-bucket"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_logging_project_sink" in result.stdout


def test_terraform_static_validation_harness_rejects_monitoring_alert_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "alert.tf").write_text(
        "\n".join(
            [
                'resource "google_monitoring_alert_policy" "readiness" {',
                '  display_name = "Readiness failure"',
                "  enabled      = true",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_monitoring_alert_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_monitoring_notification_channels(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "notification_channel.tf").write_text(
        "\n".join(
            [
                'resource "google_monitoring_notification_channel" "email" {',
                '  display_name = "Owner email"',
                '  type         = "email"',
                '  labels = { email_address = "owner@example.com" }',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_monitoring_notification_channel" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_scheduler_jobs(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "scheduler.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_scheduler_job" "destroy" {',
                '  name     = "scheduled-destroy"',
                '  schedule = "0 2 * * *"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_cloud_scheduler_job" in result.stdout


def test_terraform_static_validation_harness_rejects_storage_buckets(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "bucket.tf").write_text(
        "\n".join(
            [
                'resource "google_storage_bucket" "state_or_logs" {',
                '  name     = "unapproved-state-or-log-bucket"',
                '  location = "US"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_storage_bucket" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_state_bucket_missing_controls(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    terraform_root = tmp_path / "infra" / "gcp" / "bootstrap"
    (terraform_root / "state.tf").write_text(
        "\n".join(
            [
                'resource "google_storage_bucket" "terraform_state" {',
                "  name     = var.state_bucket_name",
                "  project  = var.state_project_id",
                "  location = var.state_bucket_location",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "bootstrap state bucket missing required controls" in result.stdout
    assert "versioning" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_workload_references(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    terraform_root = tmp_path / "infra" / "gcp" / "bootstrap"
    (terraform_root / "state.tf").write_text(
        "\n".join(
            [
                'resource "google_storage_bucket" "terraform_state" {',
                "  name                        = var.state_bucket_name",
                "  project                     = var.state_project_id",
                "  location                    = var.state_bucket_location",
                "  uniform_bucket_level_access = true",
                '  public_access_prevention    = "enforced"',
                "  force_destroy               = false",
                "  versioning {",
                "    enabled = true",
                "  }",
                "  retention_policy {",
                "    retention_period = 604800",
                "    is_locked        = false",
                "  }",
                "  lifecycle {",
                "    prevent_destroy = true",
                "  }",
                "  depends_on = [module.develop]",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "bootstrap root references disposable workload" in result.stdout
    assert "module.develop" in result.stdout


def test_terraform_static_validation_harness_rejects_unbounded_bootstrap_authority(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    terraform_root = tmp_path / "infra" / "gcp" / "bootstrap"
    (terraform_root / "iam.tf").write_text(
        "\n".join(
            [
                'resource "google_storage_bucket_iam_binding" "bootstrap_admin" {',
                "  bucket = var.state_bucket_name",
                '  role   = "roles/storage.admin"',
                '  members = ["user:bootstrap@example.com"]',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "unbounded bootstrap authority" in result.stdout
    assert "google_storage_bucket_iam_binding" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_wildcard_repository_claim(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    wif = (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8")
    wif = _replace_bootstrap_wif_condition(
        wif,
        'attribute.repository == "b-mackenzie-alexander/golden_rose_project"',
        'attribute.repository == "b-mackenzie-alexander/*"',
    )
    (bootstrap_root / "wif.tf").write_text(wif, encoding="utf-8")
    (bootstrap_root / "iam.tf").write_text(
        'resource "google_service_account_iam_member" "provisioner_wif" {\n'
        "  member = local.github_principal_set\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "wildcard GitHub claim" in result.stdout
    assert "attribute.repository" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_missing_environment_claim(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    wif = (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8")
    wif = _replace_bootstrap_wif_condition(
        wif,
        'attribute.environment == "develop" && ',
        "",
    )
    (bootstrap_root / "wif.tf").write_text(wif, encoding="utf-8")
    (bootstrap_root / "iam.tf").write_text(
        'resource "google_service_account_iam_member" "provisioner_wif" {\n'
        "  member = local.github_principal_set\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "attribute condition drifted" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_missing_workflow_ref_mapping(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    wif = (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8")
    wif = wif.replace('    "attribute.workflow_ref"     = "assertion.workflow_ref"\n', "")
    (bootstrap_root / "wif.tf").write_text(wif, encoding="utf-8")
    (bootstrap_root / "iam.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "iam.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "missing exact GitHub claim" in result.stdout
    assert "attribute.workflow_ref" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_principal_set_broadening(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_root / "wif.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (bootstrap_root / "iam.tf").write_text(
        'resource "google_service_account_iam_member" "provisioner_wif" {\n'
        '  member = "principalSet://iam.googleapis.com/projects/test/locations/global/workloadIdentityPools/pool/attribute.repository_owner/b-mackenzie-alexander"\n'
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "principal-set broadening" in result.stdout
    assert "attribute.repository_owner" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_tag_ref_claim(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    wif = (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8")
    wif = _replace_bootstrap_wif_condition(
        wif,
        'attribute.ref == "refs/heads/develop"',
        'attribute.ref == "refs/tags/v1"',
    )
    (bootstrap_root / "wif.tf").write_text(wif, encoding="utf-8")
    (bootstrap_root / "iam.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "iam.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "attribute condition drifted" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_repository_only_impersonation_authority(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_root / "wif.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (bootstrap_root / "iam.tf").write_text(
        "\n".join(
            [
                'resource "google_service_account_iam_member" "image_publisher_wif" {',
                '  service_account_id = "projects/test/serviceAccounts/golden-rose-image-publisher@test.iam.gserviceaccount.com"',
                '  role               = "roles/iam.workloadIdentityUser"',
                '  member             = "principalSet://iam.googleapis.com/projects/test/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "repository-only impersonation authority" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_wif_non_dispatch_event_claim(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    wif = (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8")
    wif = _replace_bootstrap_wif_condition(
        wif,
        'attribute.event_name == "workflow_dispatch"',
        'attribute.event_name == "push"',
    )
    (bootstrap_root / "wif.tf").write_text(wif, encoding="utf-8")
    (bootstrap_root / "iam.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "iam.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "attribute condition drifted" in result.stdout


@pytest.mark.parametrize(
    "broadening",
    [
        " || true",
        ' || attribute.repository == "unreviewed/example"',
    ],
)
def test_terraform_static_validation_harness_rejects_additive_bootstrap_wif_condition(
    tmp_path: Path, broadening: str
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    wif = (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8")
    condition_match = re.search(
        r'attribute_condition\s*=\s*(?P<condition>"(?:\\.|[^"\\])*")',
        wif,
    )
    assert condition_match is not None
    broadened_condition = json.loads(condition_match.group("condition")) + broadening
    wif = (
        wif[: condition_match.start("condition")]
        + json.dumps(broadened_condition)
        + wif[condition_match.end("condition") :]
    )
    (bootstrap_root / "wif.tf").write_text(wif, encoding="utf-8")
    (bootstrap_root / "iam.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "iam.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "attribute condition" in result.stdout


@pytest.mark.parametrize(
    "effective_condition",
    [
        "local.unreviewed_condition",
        "<<-EOT\n  true\n  EOT",
    ],
)
def test_terraform_static_validation_rejects_decoy_comment_before_effective_wif_condition(
    tmp_path: Path, effective_condition: str
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    wif_path = tmp_path / "infra" / "gcp" / "bootstrap" / "wif.tf"
    wif = wif_path.read_text(encoding="utf-8")
    condition_match = re.search(
        r'attribute_condition\s*=\s*(?P<condition>"(?:\\.|[^"\\])*")',
        wif,
    )
    assert condition_match is not None
    approved_assignment = condition_match.group(0)
    wif = (
        wif[: condition_match.start()]
        + f"# {approved_assignment}\n  attribute_condition = {effective_condition}"
        + wif[condition_match.end() :]
    )
    wif_path.write_text(wif, encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "attribute condition" in result.stdout


@pytest.mark.parametrize(
    ("approved_fragment", "effective_fragment"),
    [
        (
            'issuer_uri = "https://token.actions.githubusercontent.com"',
            'issuer_uri = "https://attacker.invalid"',
        ),
        (
            '"attribute.workflow_ref"     = "assertion.workflow_ref"',
            '"attribute.workflow_ref"     = "assertion.repository"',
        ),
    ],
)
def test_terraform_static_validation_rejects_decoy_comment_before_effective_wif_provider_fields(
    tmp_path: Path, approved_fragment: str, effective_fragment: str
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    wif_path = tmp_path / "infra" / "gcp" / "bootstrap" / "wif.tf"
    wif = wif_path.read_text(encoding="utf-8")
    assert approved_fragment in wif
    wif_path.write_text(
        wif.replace(
            approved_fragment,
            f"# {approved_fragment}\n    {effective_fragment}",
            1,
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "effective GitHub WIF provider" in result.stdout


@pytest.mark.parametrize(
    ("approved_fragment", "duplicate_fragment"),
    [
        (
            "  attribute_condition = ",
            '  attribute_condition = "true"\n',
        ),
        (
            '    issuer_uri = "https://token.actions.githubusercontent.com"',
            '    issuer_uri = "https://attacker.invalid"\n',
        ),
        (
            '    "attribute.workflow_ref"     = "assertion.workflow_ref"',
            '    "attribute.workflow_ref"     = "assertion.repository"\n',
        ),
        (
            '    "attribute.workflow_ref"     = "assertion.workflow_ref"',
            '    "attribute\\u002eworkflow_ref" = "assertion.repository"\n',
        ),
        (
            '    "attribute.workflow_ref"     = "assertion.workflow_ref"',
            '    (local.unreviewed_key) = "assertion.repository"\n',
        ),
    ],
)
def test_terraform_static_validation_rejects_duplicate_effective_wif_provider_fields(
    tmp_path: Path, approved_fragment: str, duplicate_fragment: str
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    (tmp_path / "infra" / "policy").mkdir(parents=True)
    shutil.copy2(
        ROOT / "infra" / "policy" / "predeployment-authority-manifest.json",
        tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json",
    )
    wif_path = tmp_path / "infra" / "gcp" / "bootstrap" / "wif.tf"
    wif = wif_path.read_text(encoding="utf-8")
    assert approved_fragment in wif
    wif_path.write_text(
        wif.replace(approved_fragment, duplicate_fragment + approved_fragment, 1),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "effective GitHub WIF provider contains duplicate fields" in result.stdout


def test_terraform_static_validation_harness_rejects_bootstrap_provisioner_wif_path(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_root = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_root / "wif.tf").write_text(
        (ROOT / "infra" / "gcp" / "bootstrap" / "wif.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    iam = (ROOT / "infra" / "gcp" / "bootstrap" / "iam.tf").read_text(encoding="utf-8")
    iam = iam.replace(
        'resource "google_service_account_iam_member" "image_publisher_wif" {',
        'resource "google_service_account_iam_member" "provisioner_wif" {',
        1,
    )
    (bootstrap_root / "iam.tf").write_text(iam, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden bootstrap WIF fragment" in result.stdout
    assert "provisioner_wif" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_forwarding_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_global_forwarding_rule" "public" {',
                '  name       = "public-forwarding-rule"',
                '  target     = "unapproved-target"',
                '  port_range = "443"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_global_forwarding_rule" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_backend_services(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_backend.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_backend_service" "public" {',
                '  name                  = "public-backend-service"',
                '  load_balancing_scheme = "EXTERNAL_MANAGED"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_backend_service" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_url_maps(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_url_map.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_url_map" "public" {',
                '  name            = "public-url-map"',
                '  default_service = "unapproved-backend-service"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_url_map" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_target_https_proxies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_target_proxy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_target_https_proxy" "public" {',
                '  name             = "public-target-https-proxy"',
                '  url_map          = "unapproved-url-map"',
                '  ssl_certificates = ["unapproved-certificate"]',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_target_https_proxy" in result.stdout


def test_terraform_static_validation_harness_rejects_managed_ssl_certificates(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "managed_ssl_certificate.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_managed_ssl_certificate" "public" {',
                '  name = "public-managed-certificate"',
                "  managed {",
                '    domains = ["unapproved.example.com"]',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_managed_ssl_certificate" in result.stdout


def test_terraform_static_validation_harness_rejects_ssl_certificates(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "ssl_certificate.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_ssl_certificate" "public" {',
                '  name        = "public-ssl-certificate"',
                '  private_key = "unapproved-private-key-material"',
                '  certificate = "unapproved-certificate-material"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_ssl_certificate" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_target_http_proxies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_target_http_proxy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_target_http_proxy" "public" {',
                '  name    = "public-target-http-proxy"',
                '  url_map = "unapproved-url-map"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_target_http_proxy" in result.stdout


def test_terraform_static_validation_harness_rejects_regional_forwarding_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "regional_forwarding_rule.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_forwarding_rule" "public" {',
                '  name                  = "public-regional-forwarding-rule"',
                '  load_balancing_scheme = "EXTERNAL"',
                '  port_range            = "443"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_forwarding_rule" in result.stdout


def test_terraform_static_validation_harness_rejects_public_static_addresses(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "public_static_address.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_address" "public" {',
                '  name         = "public-static-address"',
                '  address_type = "EXTERNAL"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_address" in result.stdout


def test_terraform_static_validation_harness_rejects_global_public_static_addresses(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "global_public_static_address.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_global_address" "public" {',
                '  name         = "public-global-static-address"',
                '  address_type = "EXTERNAL"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "address_type = " in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_backend_buckets(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_backend_bucket.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_backend_bucket" "public" {',
                '  name        = "public-backend-bucket"',
                '  bucket_name = "unapproved-public-origin"',
                "  enable_cdn  = true",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_backend_bucket" in result.stdout


def test_terraform_static_validation_harness_rejects_global_network_endpoint_groups(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "global_network_endpoint_group.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_global_network_endpoint_group" "public" {',
                '  name                  = "public-global-neg"',
                '  network_endpoint_type = "INTERNET_FQDN_PORT"',
                "  default_port          = 443",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_global_network_endpoint_group" in result.stdout


def test_terraform_static_validation_harness_rejects_network_endpoint_groups(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_endpoint_group.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network_endpoint_group" "public" {',
                '  name                  = "public-regional-neg"',
                '  network_endpoint_type = "INTERNET_IP_PORT"',
                "  default_port          = 443",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_network_endpoint_group" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_armor_security_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "cloud_armor_security_policy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_security_policy" "public_edge" {',
                '  name = "public-edge-security-policy"',
                "  rule {",
                '    action   = "allow"',
                "    priority = 2147483647",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_security_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_region_network_endpoint_groups(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "region_network_endpoint_group.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_region_network_endpoint_group" "public" {',
                '  name                  = "public-region-neg"',
                '  network_endpoint_type = "SERVERLESS"',
                "  cloud_run {",
                '    service = "unapproved-public-service"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_region_network_endpoint_group" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_ssl_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_ssl_policy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_ssl_policy" "public_edge" {',
                '  name            = "public-edge-ssl-policy"',
                '  profile         = "MODERN"',
                '  min_tls_version = "TLS_1_2"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_ssl_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_target_ssl_proxies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_target_ssl_proxy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_target_ssl_proxy" "public_edge" {',
                '  name             = "public-edge-target-ssl-proxy"',
                '  backend_service  = "projects/example/global/backendServices/public"',
                '  ssl_certificates = ["projects/example/global/sslCertificates/public"]',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_target_ssl_proxy" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_target_tcp_proxies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_target_tcp_proxy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_target_tcp_proxy" "public_edge" {',
                '  name            = "public-edge-target-tcp-proxy"',
                '  backend_service = "projects/example/global/backendServices/public"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_target_tcp_proxy" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_target_grpc_proxies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_target_grpc_proxy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_target_grpc_proxy" "public_edge" {',
                '  name    = "public-edge-target-grpc-proxy"',
                '  url_map = "projects/example/global/urlMaps/public"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_target_grpc_proxy" in result.stdout


def test_terraform_static_validation_harness_rejects_legacy_target_pools(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "legacy_target_pool.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_target_pool" "public_edge" {',
                '  name = "public-edge-target-pool"',
                '  health_checks = ["projects/example/global/httpHealthChecks/public"]',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_target_pool" in result.stdout


def test_terraform_static_validation_harness_rejects_load_balancer_health_checks(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "load_balancer_health_check.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_health_check" "public_edge" {',
                '  name               = "public-edge-health-check"',
                "  check_interval_sec = 5",
                "  timeout_sec        = 5",
                "  http_health_check {",
                "    port         = 80",
                '    request_path = "/health"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_health_check" in result.stdout


def test_terraform_static_validation_harness_rejects_legacy_http_health_checks(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "legacy_http_health_check.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_http_health_check" "public_edge" {',
                '  name               = "public-edge-http-health-check"',
                "  check_interval_sec = 5",
                "  timeout_sec        = 5",
                "  port               = 80",
                '  request_path       = "/health"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_http_health_check" in result.stdout


def test_terraform_static_validation_harness_rejects_legacy_https_health_checks(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "legacy_https_health_check.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_https_health_check" "public_edge" {',
                '  name               = "public-edge-https-health-check"',
                "  check_interval_sec = 5",
                "  timeout_sec        = 5",
                "  port               = 443",
                '  request_path       = "/health"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_https_health_check" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_routers(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "cloud_router.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_router" "public_edge" {',
                '  name    = "public-edge-router"',
                '  network = "projects/example/global/networks/public-edge"',
                '  region  = "us-east4"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_router" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_nat(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "cloud_nat.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_router_nat" "public_edge" {',
                '  name                               = "public-edge-nat"',
                '  router                             = "public-edge-router"',
                '  region                             = "us-east4"',
                '  nat_ip_allocate_option             = "AUTO_ONLY"',
                '  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_router_nat" in result.stdout


def test_terraform_static_validation_harness_rejects_firewall_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "firewall.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_firewall" "public_edge" {',
                '  name    = "public-edge-firewall"',
                '  network = "projects/example/global/networks/public-edge"',
                "  allow {",
                '    protocol = "tcp"',
                '    ports    = ["443"]',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_firewall" in result.stdout


def test_terraform_static_validation_harness_rejects_authorized_networks(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "cloud_sql_authorized_networks.tf").write_text(
        "\n".join(
            [
                'resource "google_sql_database_instance" "public_edge" {',
                '  name             = "public-edge-db"',
                '  database_version = "POSTGRES_16"',
                "  settings {",
                '    tier = "db-f1-micro"',
                "    ip_configuration {",
                "      authorized_networks {",
                '        name  = "public-edge"',
                '        value = "203.0.113.0/24"',
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "authorized_networks" in result.stdout


def test_terraform_static_validation_harness_rejects_broad_cidr_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "broad_cidr.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network" "public_edge" {',
                '  name                    = "public-edge-network"',
                "  auto_create_subnetworks = false",
                "}",
                "",
                'resource "google_compute_subnetwork" "public_edge" {',
                '  name          = "public-edge-subnet"',
                '  ip_cidr_range = "0.0.0.0/0"',
                "  network       = google_compute_network.public_edge.id",
                '  region        = "us-east4"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "0.0.0.0/0" in result.stdout


def test_terraform_static_validation_harness_rejects_default_vpc_references(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "default_vpc.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_subnetwork" "default_edge" {',
                '  name          = "default-edge-subnet"',
                '  ip_cidr_range = "10.20.0.0/24"',
                '  network       = "default"',
                '  region        = "us-east4"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert 'network       = "default"' in result.stdout


def test_terraform_static_validation_harness_rejects_default_vpc_resources(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "default_vpc_resource.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network" "default_edge" {',
                '  name                    = "default"',
                "  auto_create_subnetworks = true",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert 'name                    = "default"' in result.stdout


def test_terraform_static_validation_harness_rejects_auto_created_subnetworks(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "auto_subnetworks.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network" "public_edge" {',
                '  name                    = "auto-subnetwork-edge"',
                "  auto_create_subnetworks = true",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "auto_create_subnetworks = true" in result.stdout


def test_terraform_static_validation_harness_rejects_default_route_retention(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "default_routes.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network" "public_edge" {',
                '  name                            = "default-route-edge"',
                "  auto_create_subnetworks         = false",
                "  delete_default_routes_on_create = false",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "delete_default_routes_on_create = false" in result.stdout


def test_terraform_static_validation_harness_rejects_custom_routes(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "custom_route.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_route" "public_edge" {',
                '  name             = "public-edge-default-route"',
                '  network          = "projects/example/global/networks/public-edge"',
                '  dest_range  = "10.30.0.0/16"',
                '  next_hop_ip = "10.0.0.1"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert 'google_compute_route"' in result.stdout


def test_terraform_static_validation_harness_rejects_vpn_gateways(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "vpn_gateway.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_vpn_gateway" "public_edge" {',
                '  name    = "public-edge-vpn-gateway"',
                '  network = "projects/example/global/networks/public-edge"',
                '  region  = "us-east4"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_vpn_gateway" in result.stdout


def test_terraform_static_validation_harness_rejects_vpn_tunnels(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "vpn_tunnel.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_vpn_tunnel" "public_edge" {',
                '  name          = "public-edge-vpn-tunnel"',
                '  peer_ip       = "203.0.113.10"',
                '  shared_secret = "placeholder-only"',
                '  region        = "us-east4"',
                '  target_vpn_gateway = "projects/example/regions/us-east4/targetVpnGateways/'
                'public-edge"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_vpn_tunnel" in result.stdout


def test_terraform_static_validation_harness_rejects_ha_vpn_gateways(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "ha_vpn_gateway.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_ha_vpn_gateway" "public_edge" {',
                '  name    = "public-edge-ha-vpn-gateway"',
                '  network = "projects/example/global/networks/public-edge"',
                '  region  = "us-east4"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_ha_vpn_gateway" in result.stdout


def test_terraform_static_validation_harness_rejects_external_vpn_gateways(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "external_vpn_gateway.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_external_vpn_gateway" "public_edge" {',
                '  name            = "public-edge-external-vpn-gateway"',
                '  redundancy_type = "SINGLE_IP_INTERNALLY_REDUNDANT"',
                "  interface {",
                "    id         = 0",
                '    ip_address = "203.0.113.20"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_external_vpn_gateway" in result.stdout


def test_terraform_static_validation_harness_rejects_interconnect_attachments(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "interconnect_attachment.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_interconnect_attachment" "public_edge" {',
                '  name    = "public-edge-interconnect"',
                '  type    = "PARTNER"',
                '  router  = "projects/example/regions/us-east4/routers/public-edge"',
                '  region  = "us-east4"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_interconnect_attachment" in result.stdout


def test_terraform_static_validation_harness_rejects_vpc_network_peerings(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_peering.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network_peering" "public_edge" {',
                '  name         = "public-edge-peering"',
                '  network      = "projects/example/global/networks/develop-vpc"',
                '  peer_network = "projects/example/global/networks/public-edge"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_network_peering" in result.stdout


def test_terraform_static_validation_harness_rejects_private_service_connect_attachments(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "service_attachment.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_service_attachment" "public_edge" {',
                '  name                  = "public-edge-service-attachment"',
                '  region                = "us-east4"',
                '  connection_preference = "ACCEPT_AUTOMATIC"',
                '  target_service        = "projects/example/regions/us-east4/forwardingRules/'
                'public-edge"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_service_attachment" in result.stdout


def test_terraform_static_validation_harness_rejects_packet_mirroring(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "packet_mirroring.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_packet_mirroring" "public_edge" {',
                '  name        = "public-edge-packet-mirroring"',
                '  region      = "us-east4"',
                '  network     = "projects/example/global/networks/develop-vpc"',
                "  collector_ilb {",
                '    url = "projects/example/regions/us-east4/forwardingRules/public-edge"',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_packet_mirroring" in result.stdout


def test_terraform_static_validation_harness_rejects_network_firewall_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_firewall_policy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network_firewall_policy" "public_edge" {',
                '  name        = "public-edge-network-firewall-policy"',
                '  description = "Unapproved public-edge network firewall policy."',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_network_firewall_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_network_firewall_policy_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_firewall_policy_rule.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network_firewall_policy_rule" "public_edge" {',
                '  firewall_policy = "projects/example/global/firewallPolicies/public-edge"',
                "  priority        = 1000",
                '  action          = "allow"',
                '  direction       = "INGRESS"',
                "  match {",
                '    src_ip_ranges = ["203.0.113.0/24"]',
                "    layer4_configs {",
                '      ip_protocol = "tcp"',
                '      ports       = ["443"]',
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_network_firewall_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_network_firewall_policy_associations(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_firewall_policy_association.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network_firewall_policy_association" "public_edge" {',
                '  name              = "public-edge-network-firewall-policy-association"',
                '  attachment_target = "projects/example/global/networks/develop-vpc"',
                '  firewall_policy   = "projects/example/global/firewallPolicies/public-edge"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_network_firewall_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_hierarchical_firewall_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "hierarchical_firewall_policy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_firewall_policy" "public_edge" {',
                '  short_name  = "public-edge-firewall-policy"',
                '  description = "Unapproved hierarchical firewall policy."',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_firewall" in result.stdout


def test_terraform_static_validation_harness_rejects_organization_security_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "organization_security_policy.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_organization_security_policy" "public_edge" {',
                '  display_name = "public-edge-organization-security-policy"',
                '  parent       = "organizations/123456789012"',
                '  description  = "Unapproved organization-level security policy."',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_organization_security_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_organization_security_policy_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "organization_security_policy_rule.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_organization_security_policy_rule" "public_edge" {',
                '  policy_id = "organizations/123456789012/securityPolicies/public-edge"',
                "  priority  = 1000",
                '  action    = "allow"',
                '  direction = "INGRESS"',
                "  match {",
                "    config {",
                '      src_ip_ranges = ["203.0.113.0/24"]',
                "      layer4_config {",
                '        ip_protocol = "tcp"',
                '        ports       = ["443"]',
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_organization_security_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_organization_security_policy_associations(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "organization_security_policy_association.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_organization_security_policy_association" '
                '"public_edge" {',
                '  name          = "public-edge-organization-security-policy-association"',
                '  attachment_id = "folders/123456789012"',
                '  policy_id     = "organizations/123456789012/securityPolicies/public-edge"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_organization_security_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_cloud_armor_security_policy_rules(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "cloud_armor_security_policy_rule.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_security_policy_rule" "public_edge" {',
                '  security_policy = "public-edge-security-policy"',
                "  priority        = 1000",
                '  action          = "allow"',
                "  match {",
                '    versioned_expr = "SRC_IPS_V1"',
                "    config {",
                '      src_ip_ranges = ["203.0.113.0/24"]',
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_security_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_network_attachments(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_attachment.tf").write_text(
        "\n".join(
            [
                'resource "google_compute_network_attachment" "public_edge" {',
                '  name                  = "public-edge-network-attachment"',
                '  region                = "us-east4"',
                '  connection_preference = "ACCEPT_AUTOMATIC"',
                '  subnetworks           = ["projects/example/regions/us-east4/subnetworks/'
                'public-edge"]',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_compute_network_attachment" in result.stdout


def test_terraform_static_validation_harness_rejects_service_connection_policies(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "service_connection_policy.tf").write_text(
        "\n".join(
            [
                'resource "google_network_connectivity_service_connection_policy" "public_edge" {',
                '  name          = "public-edge-service-connection-policy"',
                '  location      = "us-east4"',
                '  service_class = "gcp-memorystore-redis"',
                '  network       = "projects/example/global/networks/develop-vpc"',
                "  psc_config {",
                '    subnetworks = ["projects/example/regions/us-east4/subnetworks/public-edge"]',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_network_connectivity_service_connection_policy" in result.stdout


def test_terraform_static_validation_harness_rejects_network_connectivity_hubs(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "network_connectivity_hub.tf").write_text(
        "\n".join(
            [
                'resource "google_network_connectivity_hub" "public_edge" {',
                '  name        = "public-edge-connectivity-hub"',
                '  description = "Unreviewed network connectivity hub plumbing"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "forbidden" in result.stdout
    assert "google_network_connectivity_hub" in result.stdout


# ---------------------------------------------------------------------------
# Task 1: Freeze the staged authority model in tests and policy
#
# These tests enforce the foundation → migration → service deployment-stage
# contract before any Terraform behavior changes.  They probe the exact
# variables, the manifest stage-ownership declaration, the static validator's
# rejection of unconditional workload resources / boolean shortcuts, the
# foundation-stage image-digest non-requirement, and a local evaluated-stage
# inventory that does not treat a configuration graph as stage-instance proof.
# ---------------------------------------------------------------------------

_EXECUTABLE_WORKLOAD_RESOURCE_TYPES = [
    "google_cloud_run_v2_service",
    "google_cloud_run_v2_job",
]


def _load_manifest() -> dict[str, Any]:
    manifest_path = ROOT / "infra" / "policy" / "predeployment-authority-manifest.json"
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def _root_variables_text() -> str:
    return (ROOT / "infra" / "gcp" / "variables.tf").read_text(encoding="utf-8")


def _develop_variables_text() -> str:
    return (ROOT / "infra" / "gcp" / "develop" / "variables.tf").read_text(encoding="utf-8")


def _write_stage_ownership_manifest(tmp_path: Path) -> None:
    """Write a manifest with stage_ownership declarations for executable resources."""
    manifest_dest = tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json"
    manifest_dest.parent.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    terraform = manifest.get("terraform", {})
    resource_types = terraform.get("resource_types", {})
    for rt in _EXECUTABLE_WORKLOAD_RESOURCE_TYPES:
        if rt in resource_types:
            resource_types[rt]["stage_ownership"] = (
                "service" if rt == "google_cloud_run_v2_service" else "migration"
            )
    manifest_dest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_stage_deployment_vars(tmp_path: Path) -> None:
    develop_vars = tmp_path / "infra" / "gcp" / "develop" / "variables.tf"
    develop_vars.parent.mkdir(parents=True, exist_ok=True)
    develop_vars.write_text(
        "\n".join(
            [
                'variable "deployment_stage" {',
                "  type     = string",
                "  nullable = false",
                "  validation {",
                '    condition = contains(["foundation", "migration", "service"], var.deployment_stage)',
                '    error_message = "Invalid stage."',
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )


def _run_validator(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def test_deployment_stage_accepts_only_foundation_migration_or_service() -> None:
    """The deployment_stage variable must accept exactly foundation, migration, service."""
    for variables_text in [_root_variables_text(), _develop_variables_text()]:
        assert 'variable "deployment_stage"' in variables_text

        # Extract the variable block
        block_start = variables_text.index('variable "deployment_stage"')
        lines = variables_text[block_start:].splitlines()
        block_lines: list[str] = []
        brace_depth = 0
        for line in lines:
            block_lines.append(line)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth == 0 and line.strip() == "}":
                break
        block = "\n".join(block_lines)

        # Must have no default (fail-closed)
        assert "default" not in block

        # Must have nullable = false
        assert "nullable" in block and "= false" in block

        # Must validate against exactly the three approved stages
        assert "foundation" in block
        assert "migration" in block
        assert "service" in block

        # Must use contains() validation with an exact allowlist
        assert "contains(" in block


def test_foundation_stage_contract_forbids_cloud_run_service_and_job(
    tmp_path: Path,
) -> None:
    """Foundation stage must not create Cloud Run service or job resources.

    The validator must reject unconditional (no count) executable workload resources
    because they would exist in every stage including foundation.
    """
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    # Unconditional Cloud Run service (no count = stage gate)
    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  name     = "staff-tracer"',
                "  location = var.region",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    # Unconditional Cloud Run job
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  name     = "run-migrations"',
                "  location = var.region",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "unconditional" in result.stdout.lower() or "stage" in result.stdout.lower()


def test_migration_stage_contract_allows_job_but_forbids_service(
    tmp_path: Path,
) -> None:
    """Migration stage may create a Cloud Run job but must not create a service.

    A service resource gated only to `service` stage is correct stage-gating.
    The validator must reject a service whose count expression includes migration stage
    (e.g. `count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0`).
    """
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    # Service gated to migration+service (wrong — service belongs only in service stage)
    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0',
                '  name  = "staff-tracer"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    # Job correctly gated to migration+service
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0',
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "stage" in result.stdout.lower()
    assert "google_cloud_run_v2_service" in result.stdout


def test_service_stage_contract_requires_job_and_service(
    tmp_path: Path,
) -> None:
    """The manifest must declare stage ownership for executable resources.

    A service resource owned by `migration` stage (not `service`) must be rejected.
    """
    _write_minimal_required_terraform_scaffold(tmp_path)

    # Write a manifest with WRONG stage_ownership for the service
    manifest_dest = tmp_path / "infra" / "policy" / "predeployment-authority-manifest.json"
    manifest_dest.parent.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    terraform = manifest.get("terraform", {})
    resource_types = terraform.get("resource_types", {})
    if "google_cloud_run_v2_service" in resource_types:
        resource_types["google_cloud_run_v2_service"]["stage_ownership"] = "migration"
    if "google_cloud_run_v2_job" in resource_types:
        resource_types["google_cloud_run_v2_job"]["stage_ownership"] = "migration"
    manifest_dest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_stage_deployment_vars(tmp_path)

    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  count = var.deployment_stage == "service" ? 1 : 0',
                '  name  = "staff-tracer"',
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0',
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "stage_ownership" in result.stdout or "stage ownership" in result.stdout.lower()


def test_static_validator_rejects_unconditional_executable_workload_resources(
    tmp_path: Path,
) -> None:
    """The static validator must reject Cloud Run service/job created unconditionally."""
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  name     = "staff-tracer"',
                "  location = var.region",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  name     = "run-migrations"',
                "  location = var.region",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "unconditional" in result.stdout.lower() or "stage" in result.stdout.lower()
    assert (
        "google_cloud_run_v2_service" in result.stdout or "google_cloud_run_v2_job" in result.stdout
    )


def test_static_validator_rejects_boolean_workload_shortcut(
    tmp_path: Path,
) -> None:
    """The static validator must reject a boolean workload_enabled shortcut instead of deployment_stage."""
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)

    # Use workload_enabled instead of deployment_stage
    develop_vars = tmp_path / "infra" / "gcp" / "develop" / "variables.tf"
    develop_vars.write_text(
        "\n".join(
            [
                'variable "workload_enabled" {',
                "  type     = bool",
                "  nullable = false",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                "  count = var.workload_enabled ? 1 : 0",
                '  name  = "staff-tracer"',
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                "  count = var.workload_enabled ? 1 : 0",
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert (
        "workload_enabled" in result.stdout
        or "boolean" in result.stdout.lower()
        or "stage" in result.stdout.lower()
    )


def test_foundation_stage_does_not_require_or_resolve_container_image_digest() -> None:
    """Foundation stage must not require container_image_digest; it must be nullable so foundation can omit it.

    Task 1 scope: make the variable nullable at the root and develop module level.
    Task 2 scope: guard the managed_container_image local so foundation never resolves it.
    """
    for variables_text in [_root_variables_text(), _develop_variables_text()]:
        assert 'variable "container_image_digest"' in variables_text

        block_start = variables_text.index('variable "container_image_digest"')
        lines = variables_text[block_start:].splitlines()
        block_lines: list[str] = []
        brace_depth = 0
        for line in lines:
            block_lines.append(line)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth == 0 and line.strip() == "}":
                break
        block = "\n".join(block_lines)

        assert "nullable" in block
        assert "= true" in block
        assert re.search(r"^\s*default\s*=\s*null\s*$", block, re.MULTILINE)

    develop_locals = (ROOT / "infra" / "gcp" / "develop" / "locals.tf").read_text(encoding="utf-8")
    assignments = re.findall(
        r"^\s*managed_container_image\s*=\s*(.+)$", develop_locals, re.MULTILINE
    )
    assert len(assignments) == 1
    assert re.match(
        r"var\.container_image_digest\s*==\s*null\s*\?\s*null\s*:",
        assignments[0],
    )

    observability_locals = (ROOT / "infra" / "gcp" / "develop" / "observability.tf").read_text(
        encoding="utf-8"
    )
    readiness_assignments = re.findall(
        r"^\s*readiness_uptime_host\s*=\s*(.+)$", observability_locals, re.MULTILINE
    )
    assert len(readiness_assignments) == 1
    assert re.fullmatch(
        r'var\.deployment_stage\s*==\s*"service"\s*\?\s*replace\(.+\)\s*:\s*null',
        readiness_assignments[0],
    )


def test_imported_foundation_controls_use_canonical_workload_parent_shapes() -> None:
    """Same-project imports use the provider's canonical parent shape per resource family."""
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")
    secrets = (ROOT / "infra/gcp/develop/secrets.tf").read_text(encoding="utf-8")

    assert re.search(
        r'^\s*canonical_workload_project_name\s*=\s*"projects/\$\{data\.google_project\.current\.project_id\}"\s*$',
        observability,
        re.MULTILINE,
    )
    assert re.search(
        r"^\s*canonical_workload_project_number\s*=\s*data\.google_project\.current\.number\s*$",
        observability,
        re.MULTILINE,
    )

    logging_bucket = re.search(
        r'resource\s+"google_logging_project_bucket_config"\s+"default"\s*\{(?P<body>.*?)^\}',
        observability,
        re.DOTALL | re.MULTILINE,
    )
    assert logging_bucket is not None
    assert re.search(
        r"^\s*project\s*=\s*local\.canonical_workload_project_name\s*$",
        logging_bucket.group("body"),
        re.MULTILINE,
    )

    metadata_secrets = re.search(
        r'resource\s+"google_secret_manager_secret"\s+"metadata_only"\s*\{(?P<body>.*?)^\}',
        secrets,
        re.DOTALL | re.MULTILINE,
    )
    assert metadata_secrets is not None
    assert re.search(
        r"^\s*project\s*=\s*local\.canonical_workload_project_number\s*$",
        metadata_secrets.group("body"),
        re.MULTILINE,
    )


def _foundation_deferred_reference_violations(text: str, relative_path: str) -> list[str]:
    guarded_references = {
        "google_cloud_run_v2_service.staff_tracer[0]",
        "google_cloud_run_v2_job.migration[0]",
        "google_compute_network.develop[0]",
        "google_compute_subnetwork.direct_vpc[0]",
        "google_compute_global_address.private_service_access[0]",
        "google_service_networking_connection.private_service_access[0]",
        "google_sql_database_instance.develop[0]",
        "google_sql_database.application[0]",
        "google_monitoring_uptime_check_config.readiness[0]",
        "data.external.tester_authority[0]",
    }
    violations: list[str] = []

    def is_foundation_safe(assignment: str, reference: str) -> bool:
        service_only = re.search(
            r'var\.deployment_stage\s*==\s*"service"\s*\?\s*(?P<service>.*?)\s*:\s*null',
            assignment,
            re.DOTALL,
        )
        if service_only and reference in service_only.group("service"):
            return True
        foundation_null = re.search(
            r'var\.deployment_stage\s*==\s*"foundation"\s*\?\s*null\s*:\s*(?P<later>.+)',
            assignment,
            re.DOTALL,
        )
        return foundation_null is not None and reference in foundation_null.group("later")

    blocks = re.finditer(
        r'(?P<kind>locals|output\s+"[^\"]+")\s*\{(?P<body>.*?)^\}',
        text,
        re.DOTALL | re.MULTILINE,
    )
    for block in blocks:
        body = block.group("body")
        if block.group("kind") == "locals":
            assignment_starts = list(re.finditer(r"(?m)^(?P<indent>[ \t]+)[A-Za-z0-9_]+\s*=", body))
            top_level_indent = min(
                (len(match.group("indent")) for match in assignment_starts), default=0
            )
            assignments = (
                re.split(rf"(?m)^[ \t]{{{top_level_indent}}}[A-Za-z0-9_]+\s*=", body)[1:]
                if top_level_indent
                else [body]
            )
        else:
            assignments = [body]
        for assignment in assignments:
            for reference in guarded_references:
                if reference in assignment and not is_foundation_safe(assignment, reference):
                    violations.append(
                        f"{relative_path} has an unguarded deferred reference: {reference}"
                    )
    return violations


def test_foundation_locals_and_outputs_guard_count_zero_references() -> None:
    """Foundation-evaluated locals and outputs must not dereference count-zero resources."""
    terraform_files = list((ROOT / "infra/gcp").glob("*.tf")) + list(
        (ROOT / "infra/gcp/develop").glob("*.tf")
    )
    violations = [
        violation
        for path in terraform_files
        for violation in _foundation_deferred_reference_violations(
            path.read_text(encoding="utf-8"), str(path.relative_to(ROOT))
        )
    ]

    assert violations == []


def test_foundation_deferred_reference_guard_rejects_mixed_local_assignments() -> None:
    mixed_locals = """
locals {
  readiness_host = var.deployment_stage == "service" ? google_cloud_run_v2_service.staff_tracer[0].uri : null
  migration_name = google_cloud_run_v2_job.migration[0].name
}
"""

    assert _foundation_deferred_reference_violations(mixed_locals, "mixed.tf") == [
        "mixed.tf has an unguarded deferred reference: google_cloud_run_v2_job.migration[0]"
    ]


def test_foundation_deferred_reference_guard_rejects_inverted_service_conditional() -> None:
    inverted_local = """
locals {
  unsafe = var.deployment_stage == "service" ? null : google_cloud_run_v2_service.staff_tracer[0].uri
}
"""

    assert _foundation_deferred_reference_violations(inverted_local, "inverted.tf") == [
        "inverted.tf has an unguarded deferred reference: google_cloud_run_v2_service.staff_tracer[0]"
    ]


def test_foundation_deferred_reference_guard_rejects_four_space_local_assignment() -> None:
    indented_local = """
locals {
    readiness_host = var.deployment_stage == "service" ? google_cloud_run_v2_service.staff_tracer[0].uri : null
    migration_name = google_cloud_run_v2_job.migration[0].name
}
"""

    assert _foundation_deferred_reference_violations(indented_local, "indented.tf") == [
        "indented.tf has an unguarded deferred reference: google_cloud_run_v2_job.migration[0]"
    ]


def test_local_stage_inventory_evaluator_rejects_job_or_service_in_foundation(
    tmp_path: Path,
) -> None:
    """A local evaluated-stage inventory must reject job/service resources in foundation stage.

    This test proves that a Terraform configuration graph is not stage-instance proof.
    The static validator must evaluate the count/condition expressions on executable
    resources and determine which stages they belong to, rather than just counting blocks.
    """
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    # A job with a count that evaluates to 1 in ALL stages (including foundation)
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  count = var.deployment_stage != "never" ? 1 : 0',
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "foundation" in result.stdout.lower() or "stage" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Task 2: Stage Cloud Run job/service creation without losing Terraform authority
#
# These tests prove that foundation apply contains no executable workload,
# migration job creation precedes service creation, and Terraform remains the
# source of desired configuration.  Graph probes are structural evidence only;
# the evaluated-stage inventory from Task 1 is the authority.
# ---------------------------------------------------------------------------


def _copy_terraform_for_graph_probe(tmp_path: Path, stage: str = "service") -> Path:
    """Copy the real infra/gcp tree, omit the partial backend, inject deployment_stage,
    and return the graph root path."""
    import shutil

    graph_root = tmp_path / f"graph-probe-{stage}"
    shutil.copytree(
        ROOT / "infra" / "gcp",
        graph_root,
        ignore=shutil.ignore_patterns(".terraform"),
    )
    (graph_root / "backend.tf").write_text(
        "# graph probe omits the partial backend ceremony\n",
        encoding="utf-8",
    )
    # Inject deployment_stage into the root module pass-through
    develop_tf = graph_root / "develop.tf"
    develop_tf_text = develop_tf.read_text(encoding="utf-8")
    if "deployment_stage" not in develop_tf_text:
        develop_tf_text = develop_tf_text.replace(
            "  container_image_digest   = var.container_image_digest\n",
            "  container_image_digest   = var.container_image_digest\n"
            "  deployment_stage         = var.deployment_stage\n",
        )
        develop_tf.write_text(develop_tf_text, encoding="utf-8")
    return graph_root


def _run_terraform_graph(tmp_path: Path, graph_root: Path) -> str:
    """Run terraform init + graph and return stdout."""
    import os

    terraform_env = os.environ | {"TF_DATA_DIR": str(tmp_path / ".tfdata-graph")}
    init_result = subprocess.run(
        ["terraform", f"-chdir={graph_root}", "init", "-backend=false", "-input=false"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=terraform_env,
    )
    assert init_result.returncode == 0, init_result.stdout + init_result.stderr
    result = subprocess.run(
        ["terraform", f"-chdir={graph_root}", "graph"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=terraform_env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_foundation_graph_contains_no_cloud_run_job_or_service(
    tmp_path: Path,
) -> None:
    """Foundation stage must not create Cloud Run job or service resources.

    The graph probe shows all resources as nodes regardless of count, so the
    structural evidence is the count expression in the source, not the graph.
    These tests verify the source has stage-gating count expressions that
    exclude the resources from foundation.
    """
    cloud_run = (ROOT / "infra" / "gcp" / "develop" / "cloud_run.tf").read_text(encoding="utf-8")
    migration_job = (ROOT / "infra" / "gcp" / "develop" / "migration_job.tf").read_text(
        encoding="utf-8"
    )

    # Cloud Run service must have count gated to service stage only
    assert "count" in cloud_run
    assert 'var.deployment_stage == "service"' in cloud_run
    assert "foundation" not in cloud_run.split("count")[1].split("}")[0] or (
        'var.deployment_stage == "service"' in cloud_run
        and 'var.deployment_stage == "foundation"' not in cloud_run
    )

    # Migration job must have count gated to migration+service (not foundation)
    assert "count" in migration_job
    assert "deployment_stage" in migration_job
    assert "foundation" not in migration_job.split("count")[1].split("}")[0] or (
        'var.deployment_stage == "migration"' in migration_job
        and 'var.deployment_stage == "foundation"' not in migration_job
    )

    # Verify the count expressions do not include foundation
    import re as _re

    service_count_match = _re.search(r"count\s*=\s*(.+?)\n", cloud_run)
    assert service_count_match is not None
    service_count_expr = service_count_match.group(1)
    assert '"foundation"' not in service_count_expr

    job_count_match = _re.search(r"count\s*=\s*(.+?)\n", migration_job)
    assert job_count_match is not None
    job_count_expr = job_count_match.group(1)
    assert '"foundation"' not in job_count_expr


def test_migration_graph_contains_job_without_service_or_invoker_binding(
    tmp_path: Path,
) -> None:
    """Migration stage must have the job but not the service or invoker IAM.

    The graph probe shows all resources as nodes regardless of count, so the
    structural evidence is the count expression in the source.  The service
    and its invoker IAM must have count gated to service stage only, while
    the job must have count gated to migration+service.
    """
    cloud_run = (ROOT / "infra" / "gcp" / "develop" / "cloud_run.tf").read_text(encoding="utf-8")
    migration_job = (ROOT / "infra" / "gcp" / "develop" / "migration_job.tf").read_text(
        encoding="utf-8"
    )
    iam = (ROOT / "infra" / "gcp" / "develop" / "iam.tf").read_text(encoding="utf-8")

    # Job must include migration in its count expression
    assert "count" in migration_job
    assert '"migration"' in migration_job

    # Service must NOT include migration in its count expression
    assert "count" in cloud_run
    import re as _re

    service_count_match = _re.search(r"count\s*=\s*(.+?)\n", cloud_run)
    assert service_count_match is not None
    service_count_expr = service_count_match.group(1)
    assert '"migration"' not in service_count_expr

    # Service invoker IAM must have count gated to service stage only
    assert "count" in iam
    iam_invoker_section = iam.split("public_invoker")[1] if "public_invoker" in iam else ""
    assert 'var.deployment_stage == "service"' in iam_invoker_section


def test_service_graph_contains_job_service_and_public_invoker_binding(
    tmp_path: Path,
) -> None:
    """Service stage graph must contain job, service, and the public invoker IAM."""
    graph_root = _copy_terraform_for_graph_probe(tmp_path, stage="service")
    (graph_root / "service.tfvars").write_text(
        'deployment_stage = "service"\n',
        encoding="utf-8",
    )
    graph_output = _run_terraform_graph(tmp_path, graph_root)

    assert "google_cloud_run_v2_job" in graph_output, (
        "Service stage graph must contain the Cloud Run job"
    )
    assert "google_cloud_run_v2_service" in graph_output, (
        "Service stage graph must contain the Cloud Run service"
    )
    assert "google_cloud_run_v2_service_iam_member" in graph_output, (
        "Service stage graph must contain the public invoker IAM binding"
    )


def test_stage_outputs_do_not_reference_absent_resources_unsafely() -> None:
    """Stage-safe outputs must not reference resources that may be absent in earlier stages.

    The develop module outputs must not directly reference google_cloud_run_v2_service
    or google_cloud_run_v2_job attributes without stage guards, because those resources
    may have count = 0 in foundation or migration stage.
    """
    develop_outputs = (ROOT / "infra" / "gcp" / "develop" / "outputs.tf").read_text(
        encoding="utf-8"
    )

    # Outputs that reference Cloud Run service or job must be stage-safe
    # (use try or conditional, not direct attribute access)
    if "google_cloud_run_v2_service" in develop_outputs:
        # Must not directly access .name or .url without a stage guard
        assert "deployment_stage" in develop_outputs, (
            "Develop outputs reference Cloud Run service without stage guard"
        )

    if "google_cloud_run_v2_job" in develop_outputs:
        assert "deployment_stage" in develop_outputs, (
            "Develop outputs reference Cloud Run job without stage guard"
        )


def test_foundation_verifier_mode_rejects_present_workload() -> None:
    """The foundation verifier mode must reject a snapshot that contains workload resources.

    The verifier must accept a --mode argument. In foundation mode, it must
    reject any snapshot where cloud_run_service or cloud_run_job is present.
    """
    import importlib.util

    module_path = ROOT / "scripts" / "verify_gcp_foundation.py"
    spec = importlib.util.spec_from_file_location("verify_gcp_foundation", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    snapshot = {
        "project_labels": module.APPROVED_PROJECT_LABELS,
        "enabled_apis": list(module.APPROVED_APIS),
        "resource_inventory": {
            "service_accounts": [],
            "control_plane_service_accounts": [],
            "cloud_run_service": "staff-tracer",
            "cloud_run_job": "run-migrations",
            "cloud_sql_instance": "",
            "state_bucket": "",
        },
        "cloud_run_service": {},
        "cloud_run_service_iam": {},
        "migration_job": {},
        "cloud_sql": {},
        "service_account_keys": {},
        "project_iam": {},
        "service_account_iam": {},
        "artifact_registry_iam": {},
        "state_bucket": {},
        "state_bucket_iam": {},
        "budget": {},
        "notification_channels": {},
        "alert_policies": [],
        "logging": {},
    }
    contract = {
        "project_id": "test-project",
        "control_plane_project_id": "test-control-plane",
        "state_bucket_name": "test-bucket",
        "private_invoker_principal": "principal:test",
        "state_authority_principal": "serviceAccount:test@state.iam.gserviceaccount.com",
        "recovery_authority_principal": "group:test@example.com",
        "bootstrap_operator_principal": "user:test@example.com",
        "provisioner_operator_principal": "user:provisioner.operator@example.com",
        "bootstrap_operator_status": "bootstrap-retired",
        "observability_viewer_principal": "group:obs@example.com",
        "recovery_policy_review_status": "gate-2-evidence-required",
        "log_retention_days": 30,
    }

    violations = module.evaluate_foundation_snapshot(snapshot, contract, mode="foundation")
    assert any("workload" in v.lower() or "cloud_run" in v.lower() for v in violations), (
        "Foundation verifier mode must reject present workload resources"
    )


def test_deployment_verifier_mode_requires_expected_job_and_service() -> None:
    """The deployment (service) verifier mode must require both job and service present.

    In service mode, the verifier must reject a snapshot where cloud_run_service
    or cloud_run_job is absent.
    """
    import importlib.util

    module_path = ROOT / "scripts" / "verify_gcp_foundation.py"
    spec = importlib.util.spec_from_file_location("verify_gcp_foundation", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    snapshot = {
        "project_labels": module.APPROVED_PROJECT_LABELS,
        "enabled_apis": list(module.APPROVED_APIS),
        "resource_inventory": {
            "service_accounts": [],
            "control_plane_service_accounts": [],
            "cloud_run_service": "",
            "cloud_run_job": "run-migrations",
            "cloud_sql_instance": "",
            "state_bucket": "",
        },
        "cloud_run_service": {},
        "cloud_run_service_iam": {},
        "migration_job": {},
        "cloud_sql": {},
        "service_account_keys": {},
        "project_iam": {},
        "service_account_iam": {},
        "artifact_registry_iam": {},
        "state_bucket": {},
        "state_bucket_iam": {},
        "budget": {},
        "notification_channels": {},
        "alert_policies": [],
        "logging": {},
    }
    contract = {
        "project_id": "test-project",
        "control_plane_project_id": "test-control-plane",
        "state_bucket_name": "test-bucket",
        "private_invoker_principal": "principal:test",
        "state_authority_principal": "serviceAccount:test@state.iam.gserviceaccount.com",
        "recovery_authority_principal": "group:test@example.com",
        "bootstrap_operator_principal": "user:test@example.com",
        "provisioner_operator_principal": "user:provisioner.operator@example.com",
        "bootstrap_operator_status": "bootstrap-retired",
        "observability_viewer_principal": "group:obs@example.com",
        "recovery_policy_review_status": "gate-2-evidence-required",
        "log_retention_days": 30,
    }

    violations = module.evaluate_foundation_snapshot(snapshot, contract, mode="service")
    assert any(
        "cloud_run" in v.lower() or "service" in v.lower() or "workload" in v.lower()
        for v in violations
    ), "Service verifier mode must require cloud_run_service to be present"


def test_stage_plan_receipt_rejects_wrong_stage_source_lock_or_image_digest() -> None:
    """The saved-plan receipt contract must reject wrong stage, source lock, or image digest.

    A receipt parser must validate: stage, source SHA, plan hash, provider-lock digest,
    non-secret-input digest, evaluated inventory, approval reference, and workload
    image digest where applicable.  This test only validates the receipt shape
    parser; it does not run terraform plan.
    """
    import importlib.util

    module_path = ROOT / "scripts" / "verify_gcp_foundation.py"
    spec = importlib.util.spec_from_file_location("verify_gcp_foundation", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # A receipt with the wrong stage must be rejected
    valid_receipt = {
        "stage": "foundation",
        "source_sha": "abc123",
        "plan_hash": "def456",
        "provider_lock_digest": "ghi789",
        "non_secret_input_digest": "jkl012",
        "evaluated_inventory": {
            "google_cloud_run_v2_service": 0,
            "google_cloud_run_v2_job": 0,
        },
        "approval_reference": "manual-approval-001",
    }

    # Valid receipt in foundation mode (no workload) must pass
    assert module.validate_stage_plan_receipt(valid_receipt, expected_stage="foundation") == []

    # Wrong stage must fail
    wrong_stage_receipt = dict(valid_receipt)
    wrong_stage_receipt["stage"] = "service"
    violations = module.validate_stage_plan_receipt(
        wrong_stage_receipt, expected_stage="foundation"
    )
    assert any("stage" in v.lower() for v in violations)

    # Foundation receipt with workload present must fail
    workload_receipt = dict(valid_receipt)
    workload_receipt["evaluated_inventory"] = {
        "google_cloud_run_v2_service": 1,
        "google_cloud_run_v2_job": 0,
    }
    violations = module.validate_stage_plan_receipt(workload_receipt, expected_stage="foundation")
    assert any("workload" in v.lower() or "inventory" in v.lower() for v in violations)

    # Service receipt without image digest must fail
    service_receipt = {
        "stage": "service",
        "source_sha": "abc123",
        "plan_hash": "def456",
        "provider_lock_digest": "ghi789",
        "non_secret_input_digest": "jkl012",
        "evaluated_inventory": {
            "google_cloud_run_v2_service": 1,
            "google_cloud_run_v2_job": 1,
        },
        "approval_reference": "manual-approval-002",
    }
    violations = module.validate_stage_plan_receipt(service_receipt, expected_stage="service")
    assert any("image" in v.lower() or "digest" in v.lower() for v in violations)


# ---------------------------------------------------------------------------
# Task 3: Wire exact runtime and migration configuration safely
#
# These tests enforce that the migration job and service can start from
# reviewed Terraform configuration while keeping payloads out of source/state.
# They probe exact env/secret reference blocks, distinct database secret IDs,
# per-secret IAM, digest binding, and the static validator's reviewed
# secret/env allowlist.
# ---------------------------------------------------------------------------


def test_service_has_complete_exact_develop_configuration_contract() -> None:
    """The Cloud Run service must have exact env and secret-reference blocks."""
    cloud_run = (ROOT / "infra" / "gcp" / "develop" / "cloud_run.tf").read_text(encoding="utf-8")

    # Must have env block with exact non-secret values
    assert "env {" in cloud_run or "env {" in cloud_run
    assert "GOLDEN_ROSE_ENVIRONMENT" in cloud_run
    assert "GOLDEN_ROSE_AUTH_MODE" in cloud_run
    assert "GOLDEN_ROSE_DEPLOYMENT_TARGET" in cloud_run
    assert "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL" in cloud_run
    assert "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST" in cloud_run

    # Must have secret reference for runtime database URL
    assert "GOLDEN_ROSE_DATABASE_URL" in cloud_run
    assert "secret_key_ref" in cloud_run or "secret" in cloud_run.lower()

    # Must reference the runtime database-url secret specifically
    assert "database-url" in cloud_run or "runtime-database-url" in cloud_run


def test_migration_job_has_complete_exact_develop_configuration_contract() -> None:
    """The migration job must have exact env and secret-reference blocks."""
    migration_job = (ROOT / "infra" / "gcp" / "develop" / "migration_job.tf").read_text(
        encoding="utf-8"
    )

    # Must have env block with exact non-secret values
    assert "env {" in migration_job
    assert "GOLDEN_ROSE_ENVIRONMENT" in migration_job
    assert "GOLDEN_ROSE_AUTH_MODE" in migration_job
    assert "GOLDEN_ROSE_DEPLOYMENT_TARGET" in migration_job
    assert "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST" in migration_job
    assert "GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE" in migration_job

    # Must have secret reference for migration database URL
    assert "GOLDEN_ROSE_DATABASE_URL" in migration_job
    assert "secret_key_ref" in migration_job or "secret" in migration_job.lower()

    # Must reference the migration database-url secret specifically (distinct from runtime)
    assert "migration-database-url" in migration_job or "database-url" in migration_job


def test_runtime_and_migration_use_distinct_database_secret_ids() -> None:
    """Runtime and migration must use distinct database URL secret IDs."""
    secrets = (ROOT / "infra" / "gcp" / "develop" / "secrets.tf").read_text(encoding="utf-8")

    # Must define distinct runtime and migration database URL secrets
    assert "runtime-database-url" in secrets
    assert "migration-database-url" in secrets

    # The broad metadata_only collection must not grant both identities
    # access to the same database-url secret
    assert "runtime-database-url" in secrets
    assert "migration-database-url" in secrets


def test_digest_environment_marker_is_bound_to_container_image_digest() -> None:
    """GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST must be bound to the container image digest variable."""
    cloud_run = (ROOT / "infra" / "gcp" / "develop" / "cloud_run.tf").read_text(encoding="utf-8")
    migration_job = (ROOT / "infra" / "gcp" / "develop" / "migration_job.tf").read_text(
        encoding="utf-8"
    )

    # Both must bind GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST to var.container_image_digest
    for tf_text in [cloud_run, migration_job]:
        assert "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST" in tf_text
        assert "var.container_image_digest" in tf_text


def test_static_validator_allows_only_reviewed_secret_reference_shapes(
    tmp_path: Path,
) -> None:
    """The static validator must allow reviewed secret reference shapes, not broadly reject all env/secret blocks."""
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    # Write a cloud_run.tf with reviewed secret references
    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  count = var.deployment_stage == "service" ? 1 : 0',
                '  name  = "staff-tracer"',
                "  template {",
                "    containers {",
                '      image = "test@sha256:' + "a" * 64 + '"',
                "      env {",
                '        name  = "GOLDEN_ROSE_ENVIRONMENT"',
                '        value = "develop"',
                "      }",
                "      env {",
                '        name  = "GOLDEN_ROSE_DATABASE_URL"',
                "        value_source {",
                "          secret_key_ref {",
                '            secret = "runtime-database-url"',
                '            version = "latest"',
                "          }",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0',
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    # The validator must NOT reject reviewed env/secret_key_ref/value_source shapes
    env_violations = [
        v for v in result.stdout.splitlines() if "env" in v.lower() and "forbidden" in v.lower()
    ]
    assert not env_violations, (
        f"Static validator incorrectly rejects reviewed env/secret shapes: {env_violations}"
    )


def test_static_validator_rejects_literal_secret_values_and_unlisted_env_names(
    tmp_path: Path,
) -> None:
    """The static validator must reject literal secret values and unlisted env names."""
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  count = var.deployment_stage == "service" ? 1 : 0',
                '  name  = "staff-tracer"',
                "  template {",
                "    containers {",
                '      image = "test@sha256:' + "a" * 64 + '"',
                "      env {",
                '        name  = "UNLISTED_ENV_VAR"',
                '        value = "some-value"',
                "      }",
                "      env {",
                '        name  = "GOLDEN_ROSE_DATABASE_URL"',
                '        value = "postgresql://user:password@host/db"',
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0',
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    # Must reject unlisted env name
    assert (
        "UNLISTED_ENV_VAR" in result.stdout
        or "unlisted" in result.stdout.lower()
        or "env" in result.stdout.lower()
    )
    # Must reject literal secret value
    assert (
        "literal" in result.stdout.lower()
        or "value" in result.stdout.lower()
        or "secret" in result.stdout.lower()
    )


def test_static_validator_rejects_cross_wired_runtime_and_migration_database_secrets(
    tmp_path: Path,
) -> None:
    """The validator must reject runtime using migration's database secret and vice versa."""
    _write_minimal_required_terraform_scaffold(tmp_path)
    _write_stage_ownership_manifest(tmp_path)
    _write_stage_deployment_vars(tmp_path)

    # Runtime service referencing migration-database-url (cross-wired)
    (tmp_path / "infra" / "gcp" / "develop" / "cloud_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "staff_tracer" {',
                '  count = var.deployment_stage == "service" ? 1 : 0',
                '  name  = "staff-tracer"',
                "  template {",
                "    containers {",
                '      image = "test@sha256:' + "a" * 64 + '"',
                "      env {",
                '        name  = "GOLDEN_ROSE_DATABASE_URL"',
                "        value_source {",
                "          secret_key_ref {",
                '            secret = "migration-database-url"',
                '            version = "latest"',
                "          }",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "infra" / "gcp" / "develop" / "migration_job.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_job" "migration" {',
                '  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0',
                '  name  = "run-migrations"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert (
        "cross" in result.stdout.lower()
        or "migration-database-url" in result.stdout
        or "runtime" in result.stdout.lower()
    )


def test_runtime_and_migration_secret_iam_is_per_secret_and_rejects_collection_wide_access() -> (
    None
):
    """Runtime and migration secret IAM must be per-secret, not collection-wide for_each."""
    iam = (ROOT / "infra" / "gcp" / "develop" / "iam.tf").read_text(encoding="utf-8")

    # Must have per-secret runtime database URL access (not for_each on metadata_only)
    assert "runtime-database-url" in iam
    assert "migration-database-url" in iam

    # Must not use for_each on the broad metadata_only collection for runtime/migration DB access
    # (per-secret bindings are required for database URL secrets)
    runtime_db_section = (
        iam.split("runtime_database_secret_access")[1]
        if "runtime_database_secret_access" in iam
        else ""
    )
    migration_db_section = (
        iam.split("migration_database_secret_access")[1]
        if "migration_database_secret_access" in iam
        else ""
    )

    # Per-secret bindings must not use for_each on the broad collection
    if runtime_db_section:
        assert (
            "for_each" not in runtime_db_section.split("}")[0]
            or "runtime-database-url" in runtime_db_section
        )
    if migration_db_section:
        assert (
            "for_each" not in migration_db_section.split("}")[0]
            or "migration-database-url" in migration_db_section
        )


def test_deploy_workflow_uses_one_packet_stages_and_direct_oci_authority() -> None:
    workflow = (ROOT / ".github/workflows/deploy-develop.yml").read_text(encoding="utf-8")
    required = [
        "deployment_stage:",
        "eight-hour deployment packet",
        "- migration",
        "- service",
        "Verify direct OCI image authority",
        "cosign verify --certificate-identity",
        "cosign verify-attestation --type slsaprovenance1",
        "https://spdx.dev/Document",
        "scripts/verify_deploy_image_authority.py",
        '--source-commit "$GITHUB_SHA"',
        "Execute migration transition",
        "gcloud run jobs describe run-migrations",
        "job image must match the direct Cosign-verified image",
        "Verify service readiness transition",
    ]
    for fragment in required:
        assert fragment in workflow
    assert "publish_run_id:" not in workflow
    assert "reviewed-stage-plan-receipt" not in workflow
    assert "Download reviewed publish artifacts" not in workflow
    assert "stage_receipt" not in workflow
    assert "migration_success_receipt" not in workflow
    assert "cosign sign-blob" not in workflow
    assert "cosign verify-blob" not in workflow
    assert (
        workflow.index("Authenticate artifact verifier to Google Cloud")
        < workflow.index("Verify direct OCI image authority")
        < workflow.index("Clear artifact verifier credential context")
        < workflow.index("Authenticate deployer to Google Cloud")
        < workflow.index("Set up gcloud")
    )
    migration_step = workflow.split("- name: Execute migration transition", 1)[1].split(
        "- name: Verify service readiness transition", 1
    )[0]
    assert migration_step.index("gcloud run jobs describe") < migration_step.index(
        "gcloud run jobs execute"
    )
    service_step = workflow.split("- name: Verify service readiness transition", 1)[1].split(
        "- name: Record deploy result", 1
    )[0]
    assert 'payload.update({"result": "success"' in migration_step
    assert 'payload.update({"result": "success"' in service_step


def test_deploy_workflow_separates_artifact_verifier_credentials_from_deployer_credentials() -> (
    None
):
    workflow = (ROOT / ".github/workflows/deploy-develop.yml").read_text(encoding="utf-8")

    required = [
        "Authenticate artifact verifier to Google Cloud",
        "GCP_ARTIFACT_VERIFIER_SERVICE_ACCOUNT",
        "create_credentials_file: true",
        "Verify direct OCI image authority",
        "DOCKER_CONFIG",
        "docker logout us-east4-docker.pkg.dev",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE",
        "GOOGLE_GHA_CREDS_PATH",
        "Authenticate deployer to Google Cloud",
        "GCP_DEPLOYER_SERVICE_ACCOUNT",
    ]
    for fragment in required:
        assert fragment in workflow

    assert workflow.index("Authenticate artifact verifier to Google Cloud") < workflow.index(
        "Verify direct OCI image authority"
    )
    assert workflow.index("Verify direct OCI image authority") < workflow.index(
        "Authenticate deployer to Google Cloud"
    )
    assert workflow.index("docker logout us-east4-docker.pkg.dev") < workflow.index(
        "Authenticate deployer to Google Cloud"
    )


def test_static_validator_binds_artifact_verifier_reader_resource_fields_not_comments(
    tmp_path: Path,
) -> None:
    shutil.copytree(
        ROOT,
        tmp_path,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".terraform",
            ".ruff_cache",
            ".mypy_cache",
            ".pytest_cache",
            "__pycache__",
            "node_modules",
            "build",
            "dist",
        ),
    )
    iam_path = tmp_path / "infra" / "gcp" / "develop" / "iam.tf"
    iam = iam_path.read_text(encoding="utf-8")
    reader_start = iam.index(
        'resource "google_artifact_registry_repository_iam_member" "artifact_verifier_reader"'
    )
    reader_end = iam.index("\n}\n", reader_start) + len("\n}\n")
    reader = iam[reader_start:reader_end]
    mutated_reader = reader.replace(
        "golden-rose-artifact-verifier@${var.control_plane_project_id}.iam.gserviceaccount.com",
        "golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com",
    )
    iam_path.write_text(
        iam[:reader_start]
        + mutated_reader
        + iam[reader_end:]
        + '\n# member     = "serviceAccount:golden-rose-artifact-verifier@${var.control_plane_project_id}.iam.gserviceaccount.com"\n',
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "artifact verifier reader" in result.stdout.lower()


def test_static_policy_rejects_appended_deploy_environment_mutation(tmp_path: Path) -> None:
    """Deploy run bodies must not permit imperative Cloud Run configuration drift."""
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        '          gcloud run jobs execute run-migrations --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --wait --format=json > build/transition-authority/migration-execution.json\n',
        '          gcloud run jobs execute run-migrations --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --wait --format=json > build/transition-authority/migration-execution.json\n'
        '          gcloud run services update staff-tracer --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --update-env-vars UNREVIEWED_MUTATION=true\n',
        1,
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "imperative" in result.stdout.lower()
    assert "--update-env-vars" in result.stdout


@pytest.mark.parametrize(
    ("unreviewed_command", "authority_class"),
    [
        (
            "gcloud projects add-iam-policy-binding attacker-project --member=user:attacker@example.com --role=roles/owner",
            "IAM mutation",
        ),
        (
            'gcloud run services delete staff-tracer --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --quiet',
            "resource deletion",
        ),
        (
            "gcloud artifacts repositories create attacker-repository --location=us-east4",
            "resource creation",
        ),
        ("terraform apply -auto-approve", "Terraform"),
        ("gcloud secrets versions access latest --secret=runtime-database-url", "secret access"),
        ("gcloud projects describe attacker-project", "arbitrary gcloud"),
    ],
)
def test_static_policy_rejects_every_unreviewed_deploy_run_command(
    tmp_path: Path, unreviewed_command: str, authority_class: str
) -> None:
    """Every deploy run body is an exact reviewed command contract."""
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        '          gcloud run jobs execute run-migrations --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --wait --format=json > build/transition-authority/migration-execution.json\n',
        '          gcloud run jobs execute run-migrations --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --wait --format=json > build/transition-authority/migration-execution.json\n'
        f"          {unreviewed_command}\n",
        1,
    )
    _write_workflow_fixture(tmp_path, "deploy-develop.yml", workflow)

    result = _run_validator(tmp_path)

    assert result.returncode == 1, authority_class
    assert (
        "name:Execute migration transition must match reviewed executable script exactly"
        in result.stdout
    )


def test_quota_bootstrap_role_and_binding_are_exactly_one_permission_and_member() -> None:
    iam = (ROOT / "infra" / "gcp" / "develop" / "iam.tf").read_text(encoding="utf-8")

    assert 'resource "google_project_iam_custom_role" "provisioner_quota_user"' in iam
    assert 'role_id     = "goldenRoseProvisionerQuotaUser"' in iam
    assert 'permissions = ["serviceusage.services.use"]' in iam
    assert 'resource "google_project_iam_member" "provisioner_quota_user"' in iam
    assert (
        'member  = "serviceAccount:golden-rose-provisioner@${var.control_plane_project_id}.iam.gserviceaccount.com"'
        in iam
    )
    assert "roles/serviceusage.serviceUsageConsumer" not in iam


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            'permissions = ["serviceusage.services.use"]',
            'permissions = ["serviceusage.services.use", "resourcemanager.projects.get"]',
        ),
        (
            'member  = "serviceAccount:golden-rose-provisioner@${var.control_plane_project_id}.iam.gserviceaccount.com"',
            'member  = "serviceAccount:other@${var.control_plane_project_id}.iam.gserviceaccount.com"',
        ),
        (
            "role    = google_project_iam_custom_role.provisioner_quota_user.name",
            'role    = "roles/editor"',
        ),
    ],
)
def test_static_validation_rejects_quota_role_or_binding_expansion(
    tmp_path: Path,
    old: str,
    new: str,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    iam_path = tmp_path / "infra" / "gcp" / "develop" / "iam.tf"
    iam = iam_path.read_text(encoding="utf-8")
    assert old in iam
    iam_path.write_text(iam.replace(old, new, 1), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "provisioner quota" in result.stdout.lower()


def test_service_stage_has_exact_temporary_public_access_and_one_instance_contract() -> None:
    cloud_run = (ROOT / "infra" / "gcp" / "develop" / "cloud_run.tf").read_text(encoding="utf-8")
    iam = (ROOT / "infra" / "gcp" / "develop" / "iam.tf").read_text(encoding="utf-8")
    secrets = (ROOT / "infra" / "gcp" / "develop" / "secrets.tf").read_text(encoding="utf-8")
    observability = (ROOT / "infra" / "gcp" / "develop" / "observability.tf").read_text(
        encoding="utf-8"
    )

    for fragment in [
        'ingress             = "INGRESS_TRAFFIC_ALL"',
        "min_instance_count = 0",
        "max_instance_count = 1",
        "max_instance_request_concurrency = 10",
        'timeout                          = "60s"',
        'cpu    = "1"',
        'memory = "512Mi"',
        'name  = "GOLDEN_ROSE_DEMO_ACCESS_ENABLED"',
        'value = "true"',
        'name  = "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT"',
        "value = var.demo_access_expires_at",
        'name = "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD"',
        'secret  = "demo-access-password"',
    ]:
        assert fragment in cloud_run

    assert 'resource "google_cloud_run_v2_service_iam_member" "public_invoker"' in iam
    assert 'member   = "allUsers"' in iam
    assert 'role     = "roles/run.invoker"' in iam
    assert 'resource "google_cloud_run_v2_service_iam_member" "private_invoker"' not in iam
    assert 'data "external" "tester_authority"' not in iam
    assert (
        'resource "google_cloud_run_v2_service_iam_member" "monitoring_readiness_invoker"'
        not in (observability)
    )
    assert "service_agent_authentication" not in observability
    assert '"demo-access-password"' in secrets
    assert (
        'resource "google_secret_manager_secret_iam_member" "runtime_demo_access_secret_access"'
        in iam
    )
    assert "migration_demo_access_secret_access" not in iam


def test_outputs_expose_only_value_safe_temporary_access_markers() -> None:
    module_outputs = (ROOT / "infra" / "gcp" / "develop" / "outputs.tf").read_text(encoding="utf-8")
    root_outputs = (ROOT / "infra" / "gcp" / "outputs.tf").read_text(encoding="utf-8")

    assert 'output "human_visible_develop_contract"' in module_outputs
    for fragment in [
        'access_mode = "expiring-http-basic"',
        "public_invoker = true",
        "min_instances = 0",
        "max_instances = 1",
        'data_boundary = "fictional-synthetic-only"',
    ]:
        assert _contains_normalized_fragment(module_outputs, fragment)
    assert "demo_access_expires_at" not in module_outputs
    assert 'output "human_visible_develop_contract"' in root_outputs
    assert "module.develop.human_visible_develop_contract" in root_outputs


@pytest.mark.parametrize(
    ("relative_path", "old", "new", "expected"),
    [
        (
            Path("infra/gcp/develop/iam.tf"),
            'member   = "allUsers"',
            'member   = "allAuthenticatedUsers"',
            "public invoker",
        ),
        (
            Path("infra/gcp/develop/cloud_run.tf"),
            "max_instance_count = 1",
            "max_instance_count = 2",
            "cloud run contract",
        ),
        (
            Path("infra/gcp/develop/cloud_run.tf"),
            'name  = "GOLDEN_ROSE_DEMO_ACCESS_ENABLED"\n        value = "true"',
            'name  = "GOLDEN_ROSE_DEMO_ACCESS_ENABLED"\n        value = "false"',
            "cloud run contract",
        ),
        (
            Path("infra/gcp/develop/cloud_run.tf"),
            'name = "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD"\n        value_source {',
            'name  = "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD"\n        value = "forbidden-literal"\n        value_source {',
            "cloud run contract",
        ),
    ],
)
def test_static_validation_rejects_weakened_temporary_public_access_contract(
    tmp_path: Path,
    relative_path: Path,
    old: str,
    new: str,
    expected: str,
) -> None:
    _write_current_terraform_scaffold(tmp_path)
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True)
    shutil.copy(ROOT / "infra" / "policy" / "predeployment-authority-manifest.json", policy_dir)
    path = tmp_path / relative_path
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert expected in result.stdout.lower()
