import ast
import ipaddress
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TERRAFORM_RELATIVE_FILES = [
    Path("infra/gcp/backend.tf"),
    Path("infra/gcp/versions.tf"),
    Path("infra/gcp/providers.tf"),
    Path("infra/gcp/variables.tf"),
    Path("infra/gcp/locals.tf"),
    Path("infra/gcp/outputs.tf"),
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


def test_gcp_terraform_readme_preserves_validate_without_apply_boundary() -> None:
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
        "local state only",
        "remote state must be approved before shared apply",
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
        "WIF handoff",
        "bootstrap authority retirement",
        "emergency recovery",
        "client handoff",
        "teardown exclusions",
    ]

    for phrase in required_phrases:
        assert phrase in runbook


def test_gcp_first_deployment_runbook_documents_recovery_and_secret_boundaries() -> None:
    runbook = (ROOT / "deploy/gcp/first-deployment-runbook.md").read_text(encoding="utf-8")

    required_phrases = [
        "out-of-band secret payload custody and injection",
        "rollback-versus-forward-recovery decision",
        "Database passwords must be generated without terminal display",
        "Stop immediately",
        "Revoke and replace every affected secret value",
        "teardown/rebuild",
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


def test_gcp_terraform_backend_uses_partial_gcs_configuration_without_committed_values() -> None:
    backend = (ROOT / "infra/gcp/backend.tf").read_text(encoding="utf-8")

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
        'attribute.repository == "b-mackenzie-alexander/golden_rose_project"',
        'attribute.ref == "refs/heads/develop"',
        'attribute.environment == "develop"',
        'attribute.event_name != "pull_request"',
        'attribute.repository_owner == "b-mackenzie-alexander"',
    ]

    for fragment in required_fragments:
        assert fragment in wif

    assert "principalSet://iam.googleapis.com" in wif
    assert "*" not in wif


def test_gcp_bootstrap_iam_separates_provisioner_image_publisher_and_deployer() -> None:
    iam = (ROOT / "infra/gcp/bootstrap/iam.tf").read_text(encoding="utf-8")

    required_fragments = [
        'resource "google_service_account" "provisioner"',
        'resource "google_service_account" "image_publisher"',
        'resource "google_service_account" "deployer"',
        'resource "google_service_account_iam_member" "provisioner_wif"',
        'resource "google_service_account_iam_member" "provisioner_token_creator"',
        'resource "google_service_account_iam_member" "image_publisher_wif"',
        'resource "google_service_account_iam_member" "image_publisher_token_creator"',
        'resource "google_service_account_iam_member" "deployer_wif"',
        'resource "google_service_account_iam_member" "deployer_token_creator"',
        'role               = "roles/iam.workloadIdentityUser"',
        'role               = "roles/iam.serviceAccountTokenCreator"',
        "member             = local.github_principal_set",
    ]

    for fragment in required_fragments:
        assert fragment in iam

    assert "google_service_account_key" not in iam
    assert "roles/owner" not in iam
    assert "roles/editor" not in iam


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
    assert "default =" not in variables
    assert "nullable" in variables
    assert "= false" in variables
    assert 'contains(["us-east4"], var.region)' in variables
    assert "client" not in variables.lower()
    assert "golden" not in variables.lower()


def test_gcp_terraform_variables_require_private_sql_subnet_input_without_committed_default() -> (
    None
):
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    root_module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    expected_validation_fragments = [
        'variable "direct_vpc_subnet_cidr"',
        "type        = string",
        "nullable    = false",
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

    assert "default =" not in root_variables
    assert "default =" not in develop_variables
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
        "billingbudgets.googleapis.com",
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
    assert "billing" not in apis.lower()


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
        "database-url",
        "synthetic-staff-id",
        "deployment-posture",
    ]

    assert "google_secret_manager_secret" in secrets
    assert "google_secret_manager_secret_version" not in secrets
    assert "secret_data" not in secrets
    assert "payload" not in secrets.lower()
    assert "password" not in secrets.lower()
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
    assert "network       = google_compute_network.develop.id" in network
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
    assert "google_compute_network.develop.id" in cloud_sql
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

    cloud_sql_backup_enabled_section = develop_variables.split(
        'variable "cloud_sql_backup_enabled"', 1
    )[1]
    cloud_sql_database_name_section = develop_variables.split(
        'variable "cloud_sql_database_name"', 1
    )[1]
    assert (
        "default ="
        not in cloud_sql_backup_enabled_section.split('variable "cloud_sql_backup_start_time"', 1)[
            0
        ]
    )
    assert (
        "default ="
        not in cloud_sql_database_name_section.split('variable "cloud_sql_schema_owner_role"', 1)[0]
    )


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
    assert "@" not in outputs


def test_gcp_develop_observability_models_private_alerting_bounded_retention_and_startup_dependencies() -> (
    None
):
    observability = (ROOT / "infra/gcp/develop/observability.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    root_module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")
    outputs = (ROOT / "infra/gcp/outputs.tf").read_text(encoding="utf-8")
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
        'resource "google_monitoring_alert_policy" "health_failures"',
        'resource "google_monitoring_alert_policy" "readiness_failures"',
        'resource "google_monitoring_alert_policy" "service_error_events"',
        'resource "google_logging_project_bucket_config" "default"',
        'resource "google_logging_metric" "health_failure_count"',
        'resource "google_logging_metric" "readiness_failure_count"',
        'resource "google_logging_metric" "service_error_count"',
        'role    = "roles/logging.viewer"',
        'role    = "roles/monitoring.viewer"',
        "member  = var.observability_viewer_principal",
        "retention_days = var.log_retention_days",
        "var.cloud_run_request_log_posture",
        'google_project_service.approved["logging.googleapis.com"]',
        'google_project_service.approved["monitoring.googleapis.com"]',
    ]
    for fragment in required_fragments:
        assert _contains_normalized_fragment(observability, fragment)

    forbidden_fragments = [
        'resource "google_logging_project_sink"',
        "request.body",
        "requestBody",
        "jsonPayload",
        "textPayload",
        "allUsers",
        "allAuthenticatedUsers",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in observability

    assert "google_billing_budget.develop" in cloud_run
    assert "google_monitoring_alert_policy.health_failures" in cloud_run
    assert "google_billing_budget.develop" in migration_job
    assert "google_monitoring_alert_policy.health_failures" in migration_job

    assert 'output "observability_contract"' in outputs
    assert "module.develop.observability_contract" in outputs
    assert "@" not in outputs


def test_gcp_develop_cloud_run_is_private_and_digest_only_without_invoker_iam() -> None:
    cloud_run = (ROOT / "infra/gcp/develop/cloud_run.tf").read_text(encoding="utf-8")
    develop_locals = (ROOT / "infra/gcp/develop/locals.tf").read_text(encoding="utf-8")

    assert "google_cloud_run_v2_service" in cloud_run
    assert "ingress" in cloud_run
    assert "INGRESS_TRAFFIC_INTERNAL_ONLY" in cloud_run
    assert "deletion_protection" in cloud_run
    assert "labels" in cloud_run
    assert "local.standard_labels" in cloud_run
    assert "vpc_access" in cloud_run
    assert "network_interfaces" in cloud_run
    assert "google_compute_subnetwork.direct_vpc.id" in cloud_run
    assert "PRIVATE_RANGES_ONLY" in cloud_run
    assert "image" in cloud_run
    assert "local.managed_container_image" in cloud_run
    assert "latest" not in cloud_run.lower()
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
        "deployer_principal",
        "private_invoker_principal",
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
        'resource "google_secret_manager_secret_iam_member" "runtime_secret_access"',
        'resource "google_secret_manager_secret_iam_member" "migration_secret_access"',
        'resource "google_artifact_registry_repository_iam_member" "image_publisher_writer"',
        'resource "google_cloud_run_v2_service_iam_member" "private_invoker"',
        'resource "google_service_account_iam_member" "deployer_runtime_user"',
        'resource "google_service_account_iam_member" "deployer_migration_user"',
        "roles/cloudsql.client",
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter",
        "roles/secretmanager.secretAccessor",
        "roles/artifactregistry.writer",
        "roles/run.invoker",
        "roles/iam.serviceAccountUser",
        "serviceAccount:${google_service_account.runtime.email}",
        "serviceAccount:${google_service_account.migration.email}",
        "golden-rose-image-publisher@${var.control_plane_project_id}.iam.gserviceaccount.com",
        "var.private_invoker_principal",
        "var.deployer_principal",
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
        "google_service_account_key",
        "allUsers",
        "allAuthenticatedUsers",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in iam


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
        "google_compute_subnetwork.direct_vpc.id",
        "PRIVATE_RANGES_ONLY",
    ]
    for fragment in required_fragments:
        assert _contains_normalized_fragment(migration_job, fragment)

    forbidden_fragments = [
        "google_service_account.runtime.email",
        "INGRESS_TRAFFIC_ALL",
        "env {",
        "value_source",
        "secret_key_ref",
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
    shutil.copytree(ROOT / "infra" / "gcp", graph_root)
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
    assert "terraform -chdir=infra/gcp init -backend=false -input=false" in workflow
    assert "terraform -chdir=infra/gcp validate" in workflow
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
    assert "docker buildx build" in workflow
    assert "--push" in workflow
    assert "--metadata-file build/image-metadata.json" in workflow
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
    assert "build/published-image.txt" in workflow
    assert "backend-sbom-cdx" in workflow
    assert "frontend-sbom-cdx" in workflow
    assert "image-metadata" in workflow
    assert "published-image" in workflow
    assert "never deploy by tag" in workflow
    assert "oauth2accesstoken" in workflow
    assert "docker.pkg.dev" in workflow


def test_deploy_develop_workflow_binds_reviewed_publish_artifacts_and_serializes_migration_before_rollout() -> (
    None
):
    workflow = (ROOT / ".github/workflows/deploy-develop.yml").read_text(encoding="utf-8")

    expected_pinned_actions = [
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
        "google-github-actions/auth@ba79af03959ebeac9769e648f473a284504d9193",
        "google-github-actions/setup-gcloud@77e7a554d41e2ee56fc945c52dfd3f33d12def9a",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ]

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "publish_run_id:" in workflow
    assert "actions: read" in workflow
    assert "environment: develop" in workflow
    assert "id-token: write" in workflow
    assert "concurrency:" in workflow
    assert "group: deploy-develop" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "if: github.event_name == 'workflow_dispatch'" in workflow
    assert "google-github-actions/auth" in workflow
    assert "google-github-actions/setup-gcloud" in workflow
    assert "actions/runs/{run_id}/artifacts" in workflow
    assert "scripts/verify_image_provenance.py --mode publish" in workflow
    assert "gcloud run jobs execute" in workflow
    assert "gcloud run jobs update" in workflow
    assert "run-migrations" in workflow
    assert "gcloud run services update" in workflow
    assert "published-image.txt" in workflow
    assert "backend-sbom.cdx.json" in workflow
    assert "frontend-sbom.cdx.json" in workflow
    assert workflow.index("gcloud run jobs execute") < workflow.index("gcloud run services update")
    assert workflow.index("gcloud run jobs update") < workflow.index("gcloud run jobs execute")
    assert "${{ inputs.image_digest }}" not in workflow
    assert ":latest" not in workflow
    for pinned_action in expected_pinned_actions:
        assert pinned_action in workflow


def test_deploy_develop_workflow_records_forward_only_readiness_and_qualification_distinction() -> (
    None
):
    workflow = (ROOT / ".github/workflows/deploy-develop.yml").read_text(encoding="utf-8")

    assert "build/deploy-compatibility.json" in workflow
    assert "build/deploy-result.json" in workflow
    assert "qualification_executed" in workflow
    assert "false" in workflow
    assert "forward recovery" in workflow
    assert "rollback_without_proven_compatibility_window" in workflow
    assert "publish_run_id" in workflow
    assert (
        "published-image artifact plus backend/frontend SBOM and metadata evidence from the reviewed publish run"
        in workflow
    )
    assert "upload-artifact" in workflow


def test_terraform_static_validation_harness_rejects_deploy_workflow_without_migration_step(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _remove_named_workflow_step(
        _current_workflow_text("deploy-develop.yml"),
        "Execute migration job",
        "Deploy reviewed service",
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
    assert "contains forbidden workflow step inventory mutation" in result.stdout
    assert "missing name:Execute migration job" in result.stdout


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


def test_terraform_static_validation_harness_rejects_deploy_workflow_reordered_migration_and_rollout(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml")
    migration_step_start = workflow.index("      - name: Execute migration job")
    deploy_step_start = workflow.index(
        "      - name: Deploy reviewed service", migration_step_start
    )
    readiness_step_start = workflow.index(
        "      - name: Verify readiness gate and record deploy result", deploy_step_start
    )
    migration_step = workflow[migration_step_start:deploy_step_start]
    deploy_step = workflow[deploy_step_start:readiness_step_start]
    workflow = (
        workflow[:migration_step_start]
        + deploy_step
        + migration_step
        + workflow[readiness_step_start:]
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
    assert "contains forbidden workflow step inventory mutation" in result.stdout
    assert "step order or inventory changed" in result.stdout


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


def test_terraform_static_validation_harness_rejects_deploy_workflow_without_publish_sha_match(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        '          if head_sha != deploy_commit_sha:\n              raise SystemExit("publish run head sha must match the deploy commit sha")\n',
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
    assert "must match reviewed executable script" in result.stdout


def test_terraform_static_validation_harness_rejects_deploy_workflow_without_image_equality_guard(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        '          test "$VERIFIED_IMAGE_REF" = "$PUBLISHED_IMAGE_REF"\n',
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
    assert "must match reviewed executable script" in result.stdout


def test_terraform_static_validation_rejects_image_guard_replaced_by_comment(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    workflow = _current_workflow_text("deploy-develop.yml").replace(
        '          test "$VERIFIED_IMAGE_REF" = "$PUBLISHED_IMAGE_REF"',
        '          # test "$VERIFIED_IMAGE_REF" = "$PUBLISHED_IMAGE_REF"',
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
    assert "must match reviewed executable script" in result.stdout


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


def test_terraform_static_validation_harness_rejects_manifest_deploy_order_drift(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    manifest = (ROOT / "infra/policy/predeployment-authority-manifest.json").read_text(
        encoding="utf-8"
    )
    manifest = manifest.replace(
        '              "name:Enforce protected develop source",\n              "name:Authenticate to Google Cloud",',
        '              "name:Authenticate to Google Cloud",\n              "name:Enforce protected develop source",',
    )
    policy_dir = tmp_path / "infra" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "predeployment-authority-manifest.json").write_text(manifest, encoding="utf-8")
    _write_workflow_fixture(
        tmp_path, "deploy-develop.yml", _current_workflow_text("deploy-develop.yml")
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate_terraform_static.py", "--root", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "workflow step order drifted for deploy-develop.yml:deploy" in result.stdout


@pytest.mark.parametrize(
    "old_fragment, new_fragment, expected_fragment",
    [
        (
            'role   = "roles/storage.objectAdmin"',
            'role   = "roles/storage.admin"',
            "roles/storage.admin",
        ),
        (
            "member = var.recovery_authority_principal",
            'member = "user:unexpected@example.com"',
            "recovery_authority_principal",
        ),
        (
            'count  = var.bootstrap_operator_status == "bootstrap-active" ? 1 : 0\n',
            "",
            "bootstrap-active",
        ),
    ],
)
def test_terraform_static_validation_harness_rejects_state_bucket_iam_drift(
    tmp_path: Path, old_fragment: str, new_fragment: str, expected_fragment: str
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "state.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/state.tf").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
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


def test_terraform_static_validation_binds_each_state_iam_resource_to_its_principal(
    tmp_path: Path,
) -> None:
    _write_minimal_required_terraform_scaffold(tmp_path)
    bootstrap_dir = tmp_path / "infra" / "gcp" / "bootstrap"
    (bootstrap_dir / "state.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/state.tf").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (bootstrap_dir / "iam.tf").write_text(
        (ROOT / "infra/gcp/bootstrap/iam.tf")
        .read_text(encoding="utf-8")
        .replace("member = var.state_authority_principal", "member = var.placeholder", 1)
        .replace(
            "member = var.recovery_authority_principal", "member = var.state_authority_principal", 1
        )
        .replace("member = var.placeholder", "member = var.recovery_authority_principal", 1),
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
    assert "state_authority_object_admin" in result.stdout


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
    assert "forbidden" in result.stdout
    assert "env_injection.tf.json" in result.stdout
    assert "env" in result.stdout


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
    assert "forbidden" in result.stdout
    assert "secret_key_ref" in result.stdout


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


def test_terraform_static_validation_harness_rejects_public_cloud_run_ingress(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "public_run.tf").write_text(
        "\n".join(
            [
                'resource "google_cloud_run_v2_service" "bad" {',
                '  ingress = "INGRESS_TRAFFIC_ALL"',
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
    assert "INGRESS_TRAFFIC_ALL" in result.stdout


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
    assert "forbidden" in result.stdout
    assert "env {" in result.stdout


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
    wif = wif.replace(
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
    wif = wif.replace('  attribute.environment == "develop" &&\n', "")
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
    assert "missing exact GitHub claim" in result.stdout
    assert "attribute.environment" in result.stdout


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
    wif = wif.replace('attribute.ref == "refs/heads/develop"', 'attribute.ref == "refs/tags/v1"')
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
    assert 'attribute.ref == "refs/heads/develop"' in result.stdout


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
