from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import hcl2
import yaml

ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_ROOT = ROOT / "infra" / "gcp"


class DuplicateWorkflowYamlKeyError(yaml.YAMLError):
    pass


class DuplicateTerraformJsonKeyError(ValueError):
    pass


def _strip_block_scalar(text: str) -> str:
    return text.strip()


FORBIDDEN_SUBSTRINGS = [
    'backend "',
    '"backend"',
    "credentials =",
    '"credentials"',
    "impersonate_service_account",
    "allUsers",
    "allAuthenticatedUsers",
    "auto_create_subnetworks = true",
    "roles/owner",
    "roles/editor",
    "roles/run.invoker",
    "google_billing_budget",
    "google_cloud_scheduler_job",
    "google_cloud_run_v2_job",
    "google_artifact_registry_repository_iam",
    "google_compute_ha_vpn_gateway",
    "google_logging_project_sink",
    "google_monitoring_alert_policy",
    "google_monitoring_notification_channel",
    "google_project_iam",
    "google_service_account_key",
    "google_secret_manager_secret_version",
    "google_secret_manager_secret_iam",
    "google_storage_bucket",
    "env {",
    '"env"',
    '"value_source"',
    "secret_key_ref",
    '"secret_key_ref"',
    "secret_data",
    "delete_default_routes_on_create = false",
    "INGRESS_TRAFFIC_ALL",
    "deletion_protection = false",
    "ipv4_enabled = true",
    "authorized_networks",
    "google_sql_user",
    "0.0.0.0/0",
    'address_type = "EXTERNAL"',
    'name                    = "default"',
    'network       = "default"',
    "google_compute_address",
    "google_compute_backend_bucket",
    "google_compute_external_vpn_gateway",
    "google_compute_firewall",
    "google_compute_backend_service",
    "google_compute_forwarding_rule",
    "google_compute_global_forwarding_rule",
    "google_compute_global_network_endpoint_group",
    "google_compute_health_check",
    "google_compute_http_health_check",
    "google_compute_https_health_check",
    "google_compute_interconnect_attachment",
    "google_compute_managed_ssl_certificate",
    "google_compute_network_attachment",
    "google_compute_network_firewall_policy",
    "google_compute_network_peering",
    "google_compute_network_endpoint_group",
    "google_compute_organization_security_policy",
    "google_compute_packet_mirroring",
    "google_compute_region_network_endpoint_group",
    'google_compute_route"',
    "google_compute_router",
    "google_compute_router_nat",
    "google_compute_security_policy",
    "google_compute_service_attachment",
    "google_compute_ssl_certificate",
    "google_compute_ssl_policy",
    "google_compute_target_grpc_proxy",
    "google_compute_target_http_proxy",
    "google_compute_target_https_proxy",
    "google_compute_target_pool",
    "google_compute_target_ssl_proxy",
    "google_compute_target_tcp_proxy",
    "google_compute_url_map",
    "google_compute_vpn_gateway",
    "google_compute_vpn_tunnel",
    "google_network_connectivity_hub",
    "google_network_connectivity_service_connection_policy",
    ":latest",
]

FORBIDDEN_ARTIFACT_PATTERNS = [
    "*.tfplan",
    "*.tfstate",
    "*.tfstate.*",
    "*.tfvars",
    "*.tfvars.json",
    "*.auto.tfvars",
    "*.auto.tfvars.json",
]

FORBIDDEN_WORKFLOW_SUBSTRINGS = [
    "push:",
    "id-token: write",
    "google-github-actions/auth",
    "workload_identity_provider",
    "terraform plan",
    "terraform apply",
    "gcloud auth",
]

WORKFLOW_USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
PINNED_ACTION_PATTERN = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
FORBIDDEN_WORKFLOW_SECRET_PATTERN = re.compile(r"secrets\.(?!GITHUB_TOKEN\b)[A-Za-z0-9_]+")
SENSITIVE_VALUE_PATTERN = re.compile(r"secret|token|password|canary", re.IGNORECASE)

JSON_SEMANTIC_FORBIDDEN_SUBSTRINGS = [
    "backend",
    "credentials",
    "impersonate_service_account",
    "allUsers",
    "allAuthenticatedUsers",
    "roles/owner",
    "roles/editor",
    "roles/run.invoker",
    "google_billing_budget",
    "google_cloud_scheduler_job",
    "google_cloud_run_v2_job",
    "google_artifact_registry_repository_iam",
    "google_compute_ha_vpn_gateway",
    "google_logging_project_sink",
    "google_monitoring_alert_policy",
    "google_monitoring_notification_channel",
    "google_project_iam",
    "google_service_account_key",
    "google_secret_manager_secret_version",
    "google_secret_manager_secret_iam",
    "google_storage_bucket",
    "env",
    "value_source",
    "secret_key_ref",
    "secret_data",
    "INGRESS_TRAFFIC_ALL",
    "authorized_networks",
    "google_sql_user",
    "0.0.0.0/0",
    "google_compute_address",
    "google_compute_backend_bucket",
    "google_compute_external_vpn_gateway",
    "google_compute_firewall",
    "google_compute_backend_service",
    "google_compute_forwarding_rule",
    "google_compute_global_forwarding_rule",
    "google_compute_global_network_endpoint_group",
    "google_compute_health_check",
    "google_compute_http_health_check",
    "google_compute_https_health_check",
    "google_compute_interconnect_attachment",
    "google_compute_managed_ssl_certificate",
    "google_compute_network_attachment",
    "google_compute_network_firewall_policy",
    "google_compute_network_peering",
    "google_compute_network_endpoint_group",
    "google_compute_organization_security_policy",
    "google_compute_packet_mirroring",
    "google_compute_region_network_endpoint_group",
    "google_compute_route",
    "google_compute_router",
    "google_compute_router_nat",
    "google_compute_security_policy",
    "google_compute_service_attachment",
    "google_compute_ssl_certificate",
    "google_compute_ssl_policy",
    "google_compute_target_grpc_proxy",
    "google_compute_target_http_proxy",
    "google_compute_target_https_proxy",
    "google_compute_target_pool",
    "google_compute_target_ssl_proxy",
    "google_compute_target_tcp_proxy",
    "google_compute_url_map",
    "google_compute_vpn_gateway",
    "google_compute_vpn_tunnel",
    "google_network_connectivity_hub",
    "google_network_connectivity_service_connection_policy",
    ":latest",
]

EXACT_SEMANTIC_FORBIDDEN_CONSTRUCTS = {
    "backend",
    "credentials",
    "env",
    "value_source",
    "secret_key_ref",
    "secret_data",
}

REQUIRED_FILES = [
    TERRAFORM_ROOT / "versions.tf",
    TERRAFORM_ROOT / "providers.tf",
    TERRAFORM_ROOT / "variables.tf",
    TERRAFORM_ROOT / "locals.tf",
    TERRAFORM_ROOT / "outputs.tf",
    TERRAFORM_ROOT / "develop" / "apis.tf",
    TERRAFORM_ROOT / "develop" / "artifact_registry.tf",
    TERRAFORM_ROOT / "develop" / "secrets.tf",
    TERRAFORM_ROOT / "develop" / "network.tf",
    TERRAFORM_ROOT / "develop" / "cloud_sql.tf",
    TERRAFORM_ROOT / "develop" / "cloud_run.tf",
    TERRAFORM_ROOT / "develop" / "identities.tf",
]

ALLOWED_WORKFLOW_FILENAMES = {
    "application-quality.yml",
    "branch-policy.yml",
    "infrastructure-quality.yml",
    "repository-hygiene.yml",
}

ALLOWED_WORKFLOW_JOB_NAMES = {
    "application-quality.yml": {"application"},
    "branch-policy.yml": {"enforce"},
    "infrastructure-quality.yml": {"static-validation"},
    "repository-hygiene.yml": {"check"},
}

ALLOWED_WORKFLOW_STEP_IDENTIFIERS = {
    ("application-quality.yml", "application"): {
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Set up Terraform for hygiene tests",
        "name:Set up Node.js 22.22.3",
        "name:Wait for PostgreSQL health",
        "name:Initialize Terraform providers for hygiene tests",
        "name:Run application quality gate",
        "name:Upload backend SBOM evidence",
        "name:Upload frontend SBOM evidence",
    },
    ("branch-policy.yml", "enforce"): {
        "name:Validate source-to-target flow",
    },
    ("infrastructure-quality.yml", "static-validation"): {
        "name:Check out repository",
        "name:Set up Python",
        "name:Set up uv",
        "name:Set up Terraform",
        "name:Run Terraform local validation",
        "name:Run Terraform static validation",
        "name:Run Terraform hygiene tests",
    },
    ("repository-hygiene.yml", "check"): {
        "uses:actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "name:Check whitespace and confidential-path guardrails",
        "name:Scan for secrets",
    },
}

REQUIRED_WORKFLOW_STEP_ORDER = {
    ("application-quality.yml", "application"): [
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Set up Terraform for hygiene tests",
        "name:Set up Node.js 22.22.3",
        "name:Wait for PostgreSQL health",
        "name:Initialize Terraform providers for hygiene tests",
        "name:Run application quality gate",
        "name:Upload backend SBOM evidence",
        "name:Upload frontend SBOM evidence",
    ],
    ("branch-policy.yml", "enforce"): [
        "name:Validate source-to-target flow",
    ],
    ("infrastructure-quality.yml", "static-validation"): [
        "name:Check out repository",
        "name:Set up Python",
        "name:Set up uv",
        "name:Set up Terraform",
        "name:Run Terraform local validation",
        "name:Run Terraform static validation",
        "name:Run Terraform hygiene tests",
    ],
    ("repository-hygiene.yml", "check"): [
        "uses:actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "name:Check whitespace and confidential-path guardrails",
        "name:Scan for secrets",
    ],
}

ALLOWED_WORKFLOW_JOB_RUNS_ON = {
    ("application-quality.yml", "application"): "ubuntu-latest",
    ("branch-policy.yml", "enforce"): "ubuntu-latest",
    ("infrastructure-quality.yml", "static-validation"): "ubuntu-latest",
    ("repository-hygiene.yml", "check"): "ubuntu-latest",
}

ALLOWED_WORKFLOW_JOB_NAME = {
    ("application-quality.yml", "application"): "application",
    ("branch-policy.yml", "enforce"): "enforce",
    ("infrastructure-quality.yml", "static-validation"): "Terraform static validation",
    ("repository-hygiene.yml", "check"): "check",
}

ALLOWED_WORKFLOW_JOB_TIMEOUT_MINUTES = {
    ("application-quality.yml", "application"): 30,
}

ALLOWED_WORKFLOW_JOB_SERVICES = {
    ("application-quality.yml", "application"): {
        "postgres": {
            "image": "postgres:16.10@sha256:21f6013073bc6b92830a2129570e2f5ec42a6c734b5a985a41e83aa58f54c3c1",
            "env": {
                "POSTGRES_USER": "golden_rose_test",
                "POSTGRES_PASSWORD": "golden_rose_test_ci_password",
                "POSTGRES_DB": "golden_rose_test",
            },
            "ports": ["55432:5432"],
            "options": (
                '--health-cmd "pg_isready -U golden_rose_test -d golden_rose_test" '
                "--health-interval 5s --health-timeout 5s --health-retries 12 "
                "--health-start-period 5s"
            ),
        },
    },
}

ALLOWED_WORKFLOW_JOB_ENV = {
    ("application-quality.yml", "application"): {
        "GOLDEN_ROSE_ENVIRONMENT": "test",
        "GOLDEN_ROSE_AUTH_MODE": "synthetic",
        "GOLDEN_ROSE_SYNTHETIC_STAFF_ID": "22222222-2222-4222-8222-222222222222",
        "GOLDEN_ROSE_DATABASE_URL": (
            "postgresql+psycopg://golden_rose_test:golden_rose_test_ci_password"
            "@127.0.0.1:55432/golden_rose_test"
        ),
    },
}

ALLOWED_WORKFLOW_STEP_IF = {
    ("application-quality.yml", "application", "name:Upload backend SBOM evidence"): "always()",
    ("application-quality.yml", "application", "name:Upload frontend SBOM evidence"): "always()",
}

ALLOWED_WORKFLOW_STEP_WITH = {
    (
        "application-quality.yml",
        "application",
        "name:Set up Python 3.12",
    ): {"python-version": "3.12"},
    (
        "application-quality.yml",
        "application",
        "name:Set up uv",
    ): {
        "version": "0.12.5",
        "checksum": "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2",
        "enable-cache": True,
    },
    (
        "application-quality.yml",
        "application",
        "name:Set up Terraform for hygiene tests",
    ): {"terraform_version": "1.15.8"},
    (
        "application-quality.yml",
        "application",
        "name:Set up Node.js 22.22.3",
    ): {
        "node-version": "22.22.3",
        "cache": "npm",
        "cache-dependency-path": "apps/web/package-lock.json",
    },
    (
        "application-quality.yml",
        "application",
        "name:Upload backend SBOM evidence",
    ): {
        "name": "backend-sbom-cdx",
        "path": "build/backend-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "application-quality.yml",
        "application",
        "name:Upload frontend SBOM evidence",
    ): {
        "name": "frontend-sbom-cdx",
        "path": "build/frontend-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Set up Python",
    ): {"python-version": "3.12"},
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Set up uv",
    ): {
        "version": "0.12.5",
        "checksum": "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2",
    },
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Set up Terraform",
    ): {"terraform_version": "1.15.8"},
    (
        "repository-hygiene.yml",
        "check",
        "uses:actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    ): {"fetch-depth": 0},
}

ALLOWED_WORKFLOW_STEP_USES = {
    (
        "application-quality.yml",
        "application",
        "name:Check out repository",
    ): "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    (
        "application-quality.yml",
        "application",
        "name:Set up Python 3.12",
    ): "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    (
        "application-quality.yml",
        "application",
        "name:Set up uv",
    ): "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
    (
        "application-quality.yml",
        "application",
        "name:Set up Terraform for hygiene tests",
    ): "hashicorp/setup-terraform@b9cd54a3c349d3f38e8881555d616ced269862dd",
    (
        "application-quality.yml",
        "application",
        "name:Set up Node.js 22.22.3",
    ): "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
    (
        "application-quality.yml",
        "application",
        "name:Upload backend SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "application-quality.yml",
        "application",
        "name:Upload frontend SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Check out repository",
    ): "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Set up Python",
    ): "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Set up uv",
    ): "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Set up Terraform",
    ): "hashicorp/setup-terraform@b9cd54a3c349d3f38e8881555d616ced269862dd",
    (
        "repository-hygiene.yml",
        "check",
        "uses:actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    ): "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    (
        "repository-hygiene.yml",
        "check",
        "name:Scan for secrets",
    ): "gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7",
}

ALLOWED_WORKFLOW_STEP_RUN = {
    (
        "application-quality.yml",
        "application",
        "name:Wait for PostgreSQL health",
    ): _strip_block_scalar(
        """
set -euo pipefail
for _ in $(seq 1 30); do
  if pg_isready -h 127.0.0.1 -p 55432 -U golden_rose_test -d golden_rose_test; then
    exit 0
  fi
  sleep 2
done
echo "PostgreSQL did not become ready in time" >&2
exit 1
"""
    ),
    (
        "application-quality.yml",
        "application",
        "name:Initialize Terraform providers for hygiene tests",
    ): "terraform -chdir=infra/gcp init -backend=false -input=false",
    (
        "application-quality.yml",
        "application",
        "name:Run application quality gate",
    ): _strip_block_scalar(
        """
set -euo pipefail
uv --version
test "$(node --version)" = "v22.22.3"
test "$(npm --version)" = "10.9.8"
test "$(npm --userconfig apps/web/.npmrc config get registry)" = "https://registry.npmjs.org/"
test "$(npm --userconfig apps/web/.npmrc config get ignore-scripts)" = "true"
node --test apps/web/scripts/validate-lockfile.test.mjs
node apps/web/scripts/validate-lockfile.mjs apps/web/package-lock.json
uv lock --check
uv sync --locked --all-groups
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
npm --prefix apps/web run verify
npm --prefix apps/web ls --all
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run bandit -q -r src
uv run alembic upgrade head
uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95
uv run alembic downgrade base
uv run alembic upgrade head
uv run pip-audit --skip-editable
mkdir -p build
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
"""
    ),
    (
        "branch-policy.yml",
        "enforce",
        "name:Validate source-to-target flow",
    ): _strip_block_scalar(
        """
set -euo pipefail
case "$BASE_REF" in
  main)
    if [[ "$HEAD_REF" == "develop" || "$HEAD_REF" == hotfix/* ]]; then
      echo "Allowed promotion: $HEAD_REF -> main"
    else
      echo "Only develop or hotfix/* may target main; got $HEAD_REF -> main." >&2
      exit 1
    fi
    ;;
  develop)
    if [[ "$HEAD_REF" =~ ^(feat|fix|docs|chore|hotfix|security|ci|test|refactor|spike)/[a-z0-9][a-z0-9._-]*$ ]]; then
      echo "Allowed integration branch: $HEAD_REF -> develop"
    else
      echo "Feature branches targeting develop must use an approved prefix and lowercase slug; got $HEAD_REF." >&2
      exit 1
    fi
    ;;
  *)
    echo "Unexpected protected target branch: $BASE_REF" >&2
    exit 1
    ;;
esac
"""
    ),
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Run Terraform local validation",
    ): _strip_block_scalar(
        """
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false
terraform -chdir=infra/gcp validate
"""
    ),
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Run Terraform static validation",
    ): "uv run --locked python scripts/validate_terraform_static.py",
    (
        "infrastructure-quality.yml",
        "static-validation",
        "name:Run Terraform hygiene tests",
    ): _strip_block_scalar(
        """
uv --version
uv run pytest tests/unit/test_terraform_hygiene.py
"""
    ),
    (
        "repository-hygiene.yml",
        "check",
        "name:Check whitespace and confidential-path guardrails",
    ): _strip_block_scalar(
        """
set -euo pipefail
git diff --check "$BASE_SHA"...HEAD
test -f .gitignore
! git ls-files --error-unmatch 'artifacts/**' >/dev/null 2>&1
! git ls-files --error-unmatch 'docs/client-deliverables/**' >/dev/null 2>&1
! git ls-files --error-unmatch '.DS_Store' '**/.DS_Store' >/dev/null 2>&1
"""
    ),
}

ALLOWED_WORKFLOW_STEP_SHELL = {}

ALLOWED_WORKFLOW_STEP_WORKING_DIRECTORY = {}

ALLOWED_WORKFLOW_STEP_CONTINUE_ON_ERROR = {}

ALLOWED_WORKFLOW_STEP_TIMEOUT_MINUTES = {}

ALLOWED_WORKFLOW_STEP_ID = {}

ALLOWED_WORKFLOW_STEP_ENV = {
    (
        "branch-policy.yml",
        "enforce",
        "name:Validate source-to-target flow",
    ): {
        "BASE_REF": "${{ github.event.pull_request.base.ref }}",
        "HEAD_REF": "${{ github.event.pull_request.head.ref }}",
    },
    (
        "repository-hygiene.yml",
        "check",
        "name:Check whitespace and confidential-path guardrails",
    ): {"BASE_SHA": "${{ github.event.pull_request.base.sha }}"},
    (
        "repository-hygiene.yml",
        "check",
        "name:Scan for secrets",
    ): {"GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"},
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Terraform scaffold static boundaries.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to scan.")
    return parser.parse_args()


def _json_contains_forbidden_semantic_construct(node: object, forbidden: str) -> bool:
    if isinstance(node, dict):
        return any(
            (
                key == forbidden
                if forbidden in EXACT_SEMANTIC_FORBIDDEN_CONSTRUCTS
                else forbidden in key
            )
            or _json_contains_forbidden_semantic_construct(value, forbidden)
            for key, value in node.items()
        )
    if isinstance(node, list):
        return any(_json_contains_forbidden_semantic_construct(item, forbidden) for item in node)
    if isinstance(node, str):
        return (
            node == forbidden
            if forbidden in EXACT_SEMANTIC_FORBIDDEN_CONSTRUCTS
            else forbidden in node
        )
    return False


def _normalize_hcl_scalar(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        try:
            return str(json.loads(stripped))
        except json.JSONDecodeError:
            return stripped
    return stripped


def _hcl_contains_forbidden_semantic_construct(node: object, forbidden: str) -> bool:
    if isinstance(node, dict):
        return any(
            (
                _normalize_hcl_scalar(str(key)) == forbidden
                if forbidden in EXACT_SEMANTIC_FORBIDDEN_CONSTRUCTS
                else forbidden in _normalize_hcl_scalar(str(key))
            )
            or _hcl_contains_forbidden_semantic_construct(value, forbidden)
            for key, value in node.items()
        )
    if isinstance(node, list):
        return any(_hcl_contains_forbidden_semantic_construct(item, forbidden) for item in node)
    if isinstance(node, str):
        normalized = _normalize_hcl_scalar(node)
        return (
            normalized == forbidden
            if forbidden in EXACT_SEMANTIC_FORBIDDEN_CONSTRUCTS
            else forbidden in normalized
        )
    return False


def _workflow_contains_forbidden_push_trigger(node: object) -> bool:
    if isinstance(node, dict):
        return any(_workflow_contains_forbidden_push_trigger(value) for value in node.values())
    if isinstance(node, list):
        return any(_workflow_contains_forbidden_push_trigger(item) for item in node)
    return node == "push"


def _collect_forbidden_workflow_permissions(node: object) -> list[str]:
    violations: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "permissions":
                if isinstance(value, str) and value == "write-all":
                    violations.append("permissions: write-all")
                if isinstance(value, dict):
                    for permission_name, permission_value in value.items():
                        if permission_value == "write":
                            violations.append(f"{permission_name}: write")
            violations.extend(_collect_forbidden_workflow_permissions(value))
    elif isinstance(node, list):
        for item in node:
            violations.extend(_collect_forbidden_workflow_permissions(item))
    return violations


def _collect_mutable_workflow_container_images(node: object) -> list[str]:
    violations: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "container":
                if isinstance(value, str) and "@sha256:" not in value:
                    violations.append(value)
                if isinstance(value, dict):
                    image = value.get("image")
                    if isinstance(image, str) and "@sha256:" not in image:
                        violations.append(image)
            if key == "services" and isinstance(value, dict):
                for service in value.values():
                    if isinstance(service, dict):
                        image = service.get("image")
                        if isinstance(image, str) and "@sha256:" not in image:
                            violations.append(image)
            violations.extend(_collect_mutable_workflow_container_images(value))
    elif isinstance(node, list):
        for item in node:
            violations.extend(_collect_mutable_workflow_container_images(item))
    return violations


def _collect_reusable_workflow_references(node: object) -> list[str]:
    violations: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses" and isinstance(value, str) and ".github/workflows/" in value:
                violations.append(value)
            violations.extend(_collect_reusable_workflow_references(value))
    elif isinstance(node, list):
        for item in node:
            violations.extend(_collect_reusable_workflow_references(item))
    return violations


def _redact_sensitive_value(value: str) -> str:
    if SENSITIVE_VALUE_PATTERN.search(value):
        return "[REDACTED]"
    return value


def _collect_unknown_workflow_jobs(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    allowed_jobs = ALLOWED_WORKFLOW_JOB_NAMES.get(path.name, set())
    violations: list[str] = []
    for job_name in jobs:
        if job_name not in allowed_jobs:
            violations.append(str(job_name))
    return violations


def _workflow_step_identifier(step: object) -> str | None:
    if not isinstance(step, dict):
        return None
    name = step.get("name")
    if isinstance(name, str):
        return f"name:{name}"
    uses = step.get("uses")
    if isinstance(uses, str):
        return f"uses:{uses}"
    run = step.get("run")
    if isinstance(run, str):
        return f"run:{run.strip()}"
    return None


def _collect_unknown_workflow_steps(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        allowed_steps = ALLOWED_WORKFLOW_STEP_IDENTIFIERS.get((path.name, str(job_name)), set())
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None:
                continue
            if identifier not in allowed_steps:
                violations.append(identifier)
    return violations


def _collect_workflow_step_inventory_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        expected_steps = REQUIRED_WORKFLOW_STEP_ORDER.get((path.name, str(job_name)))
        if expected_steps is None:
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            violations.append(f"{job_name}: missing steps")
            continue
        actual_steps = [_workflow_step_identifier(step) for step in steps]
        if any(identifier is None for identifier in actual_steps):
            violations.append(f"{job_name}: step without reviewed identifier")
            continue
        actual_identifiers = [identifier for identifier in actual_steps if identifier is not None]
        duplicate_identifiers = sorted(
            {
                identifier
                for identifier in actual_identifiers
                if actual_identifiers.count(identifier) > 1
            }
        )
        for identifier in duplicate_identifiers:
            violations.append(f"{job_name}: duplicate {identifier}")
        missing_identifiers = [
            identifier for identifier in expected_steps if identifier not in actual_identifiers
        ]
        for identifier in missing_identifiers:
            violations.append(f"{job_name}: missing {identifier}")
        if actual_identifiers != expected_steps:
            violations.append(f"{job_name}: step order or inventory changed")
    return violations


def _collect_workflow_job_structure_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    guarded_fields = {
        "if": {},
        "continue-on-error": {},
        "needs": {},
        "permissions": {},
        "environment": {},
        "defaults": {},
        "container": {},
        "strategy": {},
        "concurrency": {},
        "uses": {},
        "services": ALLOWED_WORKFLOW_JOB_SERVICES,
        "env": ALLOWED_WORKFLOW_JOB_ENV,
        "timeout-minutes": ALLOWED_WORKFLOW_JOB_TIMEOUT_MINUTES,
        "name": ALLOWED_WORKFLOW_JOB_NAME,
    }
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        key = (path.name, str(job_name))
        for field, allowlist in guarded_fields.items():
            actual_value = job.get(field)
            expected_value = allowlist.get(key)
            if expected_value is None:
                if actual_value is not None:
                    violations.append(f"{job_name}: unexpected job {field}")
            elif actual_value != expected_value:
                violations.append(f"{job_name}: changed job {field}")
    return violations


def _collect_workflow_runs_on_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        runs_on = job.get("runs-on")
        allowed_runs_on = ALLOWED_WORKFLOW_JOB_RUNS_ON.get((path.name, str(job_name)))
        if isinstance(runs_on, str) and allowed_runs_on is not None and runs_on != allowed_runs_on:
            violations.append(runs_on)
    return violations


def _collect_workflow_if_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_if = step.get("if")
            expected_if = ALLOWED_WORKFLOW_STEP_IF.get((path.name, str(job_name), identifier))
            if expected_if is None:
                if actual_if is not None:
                    violations.append(str(actual_if))
            elif actual_if != expected_if:
                violations.append(str(actual_if))
    return violations


def _collect_workflow_with_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_with = step.get("with")
            expected_with = ALLOWED_WORKFLOW_STEP_WITH.get((path.name, str(job_name), identifier))
            if expected_with is None:
                if actual_with is not None:
                    violations.append(identifier)
            elif actual_with != expected_with:
                changed_keys: list[str] = []
                if isinstance(actual_with, dict):
                    changed_keys = sorted(
                        {
                            *expected_with.keys(),
                            *actual_with.keys(),
                        }
                        - {
                            key
                            for key in expected_with.keys() & actual_with.keys()
                            if actual_with.get(key) == expected_with.get(key)
                        }
                    )
                violations.append(f"{identifier} ({', '.join(changed_keys)})")
    return violations


def _collect_workflow_uses_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_uses = step.get("uses")
            expected_uses = ALLOWED_WORKFLOW_STEP_USES.get((path.name, str(job_name), identifier))
            if expected_uses is None:
                if actual_uses is not None:
                    violations.append(f"{identifier} -> {actual_uses}")
                continue
            if actual_uses != expected_uses:
                violations.append(f"{identifier} -> {actual_uses}")
    return violations


def _collect_workflow_run_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_run = step.get("run")
            expected_run = ALLOWED_WORKFLOW_STEP_RUN.get((path.name, str(job_name), identifier))
            if expected_run is None:
                if actual_run is not None:
                    violations.append(f"{identifier} -> {str(actual_run).strip()}")
            elif not isinstance(actual_run, str) or actual_run.strip() != expected_run.strip():
                violations.append(f"{identifier} -> {str(actual_run).strip()}")
    return violations


def _collect_workflow_shell_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_shell = step.get("shell")
            expected_shell = ALLOWED_WORKFLOW_STEP_SHELL.get((path.name, str(job_name), identifier))
            if expected_shell is None:
                if actual_shell is not None:
                    violations.append(str(actual_shell))
            elif actual_shell != expected_shell:
                violations.append(str(actual_shell))
    return violations


def _collect_workflow_working_directory_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_working_directory = step.get("working-directory")
            expected_working_directory = ALLOWED_WORKFLOW_STEP_WORKING_DIRECTORY.get(
                (path.name, str(job_name), identifier)
            )
            if expected_working_directory is None:
                if actual_working_directory is not None:
                    violations.append(str(actual_working_directory))
            elif actual_working_directory != expected_working_directory:
                violations.append(str(actual_working_directory))
    return violations


def _collect_workflow_env_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            actual_env = step.get("env")
            expected_env = ALLOWED_WORKFLOW_STEP_ENV.get((path.name, str(job_name), identifier))
            if expected_env is None:
                if actual_env is not None:
                    violations.append(identifier)
            elif actual_env != expected_env:
                violations.append(identifier)
    return violations


def _collect_workflow_step_control_mutations(path: Path, node: object) -> list[str]:
    if not isinstance(node, dict):
        return []
    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return []
    violations: list[str] = []
    guarded_fields = {
        "continue-on-error": ALLOWED_WORKFLOW_STEP_CONTINUE_ON_ERROR,
        "timeout-minutes": ALLOWED_WORKFLOW_STEP_TIMEOUT_MINUTES,
        "id": ALLOWED_WORKFLOW_STEP_ID,
    }
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            identifier = _workflow_step_identifier(step)
            if identifier is None or not isinstance(step, dict):
                continue
            key = (path.name, str(job_name), identifier)
            for field, allowlist in guarded_fields.items():
                actual_value = step.get(field)
                expected_value = allowlist.get(key)
                if expected_value is None:
                    if actual_value is not None:
                        violations.append(f"{identifier}: unexpected step {field}")
                elif actual_value != expected_value:
                    violations.append(f"{identifier}: changed step {field}")
    return violations


class DuplicateKeySafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping_with_duplicate_key_rejection(
    loader: DuplicateKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DuplicateWorkflowYamlKeyError(f"duplicate key {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


DuplicateKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_with_duplicate_key_rejection,
)


def _json_object_pairs_with_duplicate_key_rejection(
    pairs: list[tuple[object, object]],
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key, value in pairs:
        if key in mapping:
            raise DuplicateTerraformJsonKeyError(f"duplicate key {key!r}")
        mapping[key] = value
    return mapping


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()
    terraform_root = root / "infra" / "gcp"
    required_files = [root / path.relative_to(ROOT) for path in REQUIRED_FILES]

    violations: list[str] = []
    for pattern in FORBIDDEN_ARTIFACT_PATTERNS:
        for path in sorted(terraform_root.rglob(pattern)):
            violations.append(f"{path.relative_to(root)} is a forbidden Terraform artifact")

    terraform_config_paths = [
        *terraform_root.rglob("*.tf"),
        *terraform_root.rglob("*.tf.json"),
    ]
    for path in sorted(terraform_config_paths):
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SUBSTRINGS:
            if forbidden in text:
                violations.append(f"{path.relative_to(root)} contains forbidden {forbidden!r}")
        if path.name.endswith(".tf.json"):
            try:
                parsed = json.loads(
                    text,
                    object_pairs_hook=_json_object_pairs_with_duplicate_key_rejection,
                )
            except DuplicateTerraformJsonKeyError as exc:
                violations.append(
                    f"{path.relative_to(root)} contains duplicate Terraform JSON key and fails closed: {exc}"
                )
                continue
            except json.JSONDecodeError as exc:
                violations.append(
                    f"{path.relative_to(root)} contains malformed Terraform JSON and fails closed: {exc.msg}"
                )
                continue
            for forbidden in JSON_SEMANTIC_FORBIDDEN_SUBSTRINGS:
                if _json_contains_forbidden_semantic_construct(parsed, forbidden):
                    violations.append(
                        f"{path.relative_to(root)} contains forbidden semantic Terraform construct {forbidden!r}"
                    )
        elif path.suffix == ".tf":
            try:
                parsed_hcl = hcl2.loads(text)
            except Exception as exc:
                violations.append(
                    f"{path.relative_to(root)} contains malformed Terraform HCL and fails closed: {exc.__class__.__name__}"
                )
                continue
            for forbidden in JSON_SEMANTIC_FORBIDDEN_SUBSTRINGS:
                if _hcl_contains_forbidden_semantic_construct(parsed_hcl, forbidden):
                    violations.append(
                        f"{path.relative_to(root)} contains forbidden semantic Terraform construct {forbidden!r}"
                    )

    workflow_paths = [
        *(root / ".github" / "workflows").glob("*.yml"),
        *(root / ".github" / "workflows").glob("*.yaml"),
    ]
    for path in sorted(workflow_paths):
        text = path.read_text(encoding="utf-8")
        if path.name not in ALLOWED_WORKFLOW_FILENAMES:
            violations.append(f"{path.relative_to(root)} contains unknown workflow file")
        for forbidden in FORBIDDEN_WORKFLOW_SUBSTRINGS:
            if forbidden in text:
                violations.append(
                    f"{path.relative_to(root)} contains forbidden workflow authority {forbidden!r}"
                )
        for match in FORBIDDEN_WORKFLOW_SECRET_PATTERN.finditer(text):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow secret reference "
                f"{match.group(0)!r}"
            )
        for match in WORKFLOW_USES_PATTERN.finditer(text):
            uses_ref = match.group(1)
            if not PINNED_ACTION_PATTERN.fullmatch(uses_ref):
                violations.append(
                    f"{path.relative_to(root)} contains unpinned workflow action {uses_ref!r}"
                )
        try:
            parsed_workflow = yaml.load(text, Loader=DuplicateKeySafeLoader)
        except yaml.YAMLError as exc:
            if isinstance(exc, DuplicateWorkflowYamlKeyError):
                violations.append(
                    f"{path.relative_to(root)} contains duplicate workflow YAML key and fails closed: {exc}"
                )
                continue
            violations.append(
                f"{path.relative_to(root)} contains malformed workflow YAML and fails closed: {exc.__class__.__name__}"
            )
            continue
        triggers = {}
        if isinstance(parsed_workflow, dict):
            triggers = parsed_workflow.get("on", parsed_workflow.get(True, {}))
        if _workflow_contains_forbidden_push_trigger(triggers):
            violations.append(
                f"{path.relative_to(root)} contains forbidden semantic workflow trigger 'push'"
            )
        for forbidden_permission in _collect_forbidden_workflow_permissions(parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden semantic workflow permissions "
                f"{forbidden_permission!r}"
            )
        for mutable_image in _collect_mutable_workflow_container_images(parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden semantic workflow container image "
                f"{_redact_sensitive_value(mutable_image)!r}"
            )
        for reusable_ref in _collect_reusable_workflow_references(parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden semantic reusable workflow reference "
                f"{_redact_sensitive_value(reusable_ref)!r}"
            )
        for job_name in _collect_unknown_workflow_jobs(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains unknown workflow job {job_name!r}"
            )
        for step_identifier in _collect_unknown_workflow_steps(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains unknown workflow step {step_identifier!r}"
            )
        for step_inventory in _collect_workflow_step_inventory_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow step inventory mutation {step_inventory!r}"
            )
        for job_structure in _collect_workflow_job_structure_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow job structure mutation {job_structure!r}"
            )
        for runs_on in _collect_workflow_runs_on_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow runs-on mutation {runs_on!r}"
            )
        for if_expr in _collect_workflow_if_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow if mutation {if_expr!r}"
            )
        for step_identifier in _collect_workflow_with_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow action with mutation {step_identifier!r}"
            )
        for step_identifier in _collect_workflow_uses_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow uses mutation {step_identifier!r}"
            )
        for run_text in _collect_workflow_run_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow run mutation {run_text!r}"
            )
        for shell_name in _collect_workflow_shell_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow shell mutation {shell_name!r}"
            )
        for working_directory in _collect_workflow_working_directory_mutations(
            path, parsed_workflow
        ):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow working-directory mutation {working_directory!r}"
            )
        for step_identifier in _collect_workflow_env_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow env mutation {step_identifier!r}"
            )
        for step_control in _collect_workflow_step_control_mutations(path, parsed_workflow):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow step control mutation {step_control!r}"
            )

    if violations:
        for violation in violations:
            print(violation)
        return 1

    missing = [path for path in required_files if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing required Terraform scaffold file: {path.relative_to(root)}")
        return 1

    print("Terraform static validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
