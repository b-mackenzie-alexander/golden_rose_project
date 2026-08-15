import ast
import ipaddress
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TERRAFORM_RELATIVE_FILES = [
    Path("infra/gcp/versions.tf"),
    Path("infra/gcp/providers.tf"),
    Path("infra/gcp/variables.tf"),
    Path("infra/gcp/locals.tf"),
    Path("infra/gcp/outputs.tf"),
    Path("infra/gcp/develop/apis.tf"),
    Path("infra/gcp/develop/artifact_registry.tf"),
    Path("infra/gcp/develop/secrets.tf"),
    Path("infra/gcp/develop/network.tf"),
    Path("infra/gcp/develop/cloud_sql.tf"),
    Path("infra/gcp/develop/cloud_run.tf"),
    Path("infra/gcp/develop/identities.tf"),
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


def test_gcp_terraform_variables_require_private_sql_subnet_input_without_committed_default() -> None:
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
    assert "direct_vpc_subnet_cidr = var.direct_vpc_subnet_cidr" in root_module


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
    assert (
        'google_project_service.approved["artifactregistry.googleapis.com"]'
        in artifact_registry
    )
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
    assert "enabled = true" in cloud_sql
    assert "point_in_time_recovery_enabled" not in cloud_sql
    assert "transaction_log_retention_days" not in cloud_sql
    assert "start_time" not in cloud_sql
    assert "0.0.0.0/0" not in cloud_sql
    assert "authorized_networks" not in cloud_sql
    assert "public" not in cloud_sql.lower()
    assert "password" not in cloud_sql.lower()
    assert "google_sql_user" not in cloud_sql
    assert 'name = "root"' not in cloud_sql.lower()
    assert "root" not in cloud_sql.lower()
    assert "@" not in cloud_sql
    assert 'google_project_service.approved["sqladmin.googleapis.com"]' in cloud_sql
    assert "depends_on" in cloud_sql
    assert "provisioner" not in cloud_sql.lower()
    assert "local-exec" not in cloud_sql.lower()


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
    assert 'PRIVATE_RANGES_ONLY' in cloud_run
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
    assert 'staff-tracer@${var.container_image_digest}' in develop_locals
    assert "google_artifact_registry_repository.application_images.repository_id" in develop_locals
    assert '${var.region}-docker.pkg.dev/${var.project_id}' in develop_locals


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


def test_gcp_terraform_root_loads_develop_resource_module() -> None:
    module = (ROOT / "infra/gcp/develop.tf").read_text(encoding="utf-8")

    assert 'module "develop"' in module
    assert 'source = "./develop"' in module
    assert "project_id" in module
    assert "region" in module
    assert "container_image_digest" in module


def test_gcp_container_image_digest_is_digest_only_and_not_arbitrary_reference() -> None:
    root_variables = (ROOT / "infra/gcp/variables.tf").read_text(encoding="utf-8")
    develop_variables = (ROOT / "infra/gcp/develop/variables.tf").read_text(encoding="utf-8")

    for variables in (root_variables, develop_variables):
        assert 'sha256:[0-9a-f]{64}$' in variables
        assert '@sha256:' not in variables
        assert "docker.pkg.dev" not in variables
        assert "latest" not in variables.lower()

    result = subprocess.run(
        ["terraform", "-chdir=infra/gcp", "graph"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
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
        (
            'checksum: '
            '"68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2"'
        ),
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
    assert "forbidden" in result.stdout
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
    assert "forbidden" in result.stdout
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
    assert "forbidden workflow authority" in result.stdout
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
        workflow[:python_step_start]
        + uv_step
        + python_step
        + workflow[terraform_step_start:]
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
                "          case \"$BASE_REF\" in",
                "            main)",
                "              if [[ \"$HEAD_REF\" == \"develop\" || \"$HEAD_REF\" == hotfix/* ]]; then",
                "                echo \"Allowed promotion: $HEAD_REF -> main\"",
                "              else",
                "                echo \"Only develop or hotfix/* may target main; got $HEAD_REF -> main.\" >&2",
                "                exit 1",
                "              fi",
                "              ;;&",
                "            develop)",
                "              if [[ \"$HEAD_REF\" =~ ^(feat|fix|docs|chore|hotfix|security|ci|test|refactor|spike)/[a-z0-9][a-z0-9._-]*$ ]]; then",
                "                echo \"Allowed integration branch: $HEAD_REF -> develop\"",
                "              else",
                "                echo \"Feature branches targeting develop must use an approved prefix and lowercase slug; got $HEAD_REF.\" >&2",
                "                exit 1",
                "              fi",
                "              ;;&",
                "            *)",
                "              echo \"Unexpected protected target branch: $BASE_REF\" >&2",
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
                "          case \"$BASE_REF\" in",
                "            main)",
                "              if [[ \"$HEAD_REF\" == \"develop\" || \"$HEAD_REF\" == hotfix/* ]]; then",
                "                echo \"Allowed promotion: $HEAD_REF -> main\"",
                "              else",
                "                echo \"Only develop or hotfix/* may target main; got $HEAD_REF -> main.\" >&2",
                "                exit 1",
                "              fi",
                "              ;;",
                "            develop)",
                "              if [[ \"$HEAD_REF\" =~ ^(feat|fix|docs|chore|hotfix|security|ci|test|refactor|spike)/[a-z0-9][a-z0-9._-]*$ ]]; then",
                "                echo \"Allowed integration branch: $HEAD_REF -> develop\"",
                "              else",
                "                echo \"Feature branches targeting develop must use an approved prefix and lowercase slug; got $HEAD_REF.\" >&2",
                "                exit 1",
                "              fi",
                "              ;;",
                "            *)",
                "              echo \"Unexpected protected target branch: $BASE_REF\" >&2",
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


def test_terraform_static_validation_harness_rejects_cloud_run_jobs(
    tmp_path: Path,
) -> None:
    terraform_root = tmp_path / "infra" / "gcp" / "develop"
    terraform_root.mkdir(parents=True)
    (terraform_root / "migration_job.tf").write_text(
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
