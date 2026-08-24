from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import hcl2
import yaml

ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_ROOT = ROOT / "infra" / "gcp"
MANIFEST_RELATIVE_PATH = Path("infra/policy/predeployment-authority-manifest.json")


class DuplicateWorkflowYamlKeyError(yaml.YAMLError):
    pass


class DuplicateTerraformJsonKeyError(ValueError):
    pass


def _strip_block_scalar(text: str) -> str:
    return text.strip()


FORBIDDEN_SUBSTRINGS = [
    "credentials =",
    '"credentials"',
    "impersonate_service_account",
    "allUsers",
    "allAuthenticatedUsers",
    "auto_create_subnetworks = true",
    "roles/owner",
    "roles/editor",
    "google_cloud_scheduler_job",
    "google_compute_ha_vpn_gateway",
    "google_logging_project_sink",
    "google_service_account_key",
    "google_secret_manager_secret_version",
    "secret_data",
    "delete_default_routes_on_create = false",
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
    "terraform plan",
    "terraform apply",
    "gcloud auth",
]

WORKFLOW_USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
PINNED_ACTION_PATTERN = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
FORBIDDEN_WORKFLOW_SECRET_PATTERN = re.compile(r"secrets\.(?!GITHUB_TOKEN\b)[A-Za-z0-9_]+")
SENSITIVE_VALUE_PATTERN = re.compile(r"secret|token|password|canary", re.IGNORECASE)
RESOURCE_BLOCK_PATTERN = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"')
RESOURCE_BLOCK_WITH_BODY_PATTERN = re.compile(
    r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{(?P<body>.*?)^\}',
    re.MULTILINE | re.DOTALL,
)
WORKFLOW_SCRIPT_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_./-])((?:scripts|apps/web/scripts)/[A-Za-z0-9_./-]+\.(?:py|sh|bash|mjs))"
)

JSON_SEMANTIC_FORBIDDEN_SUBSTRINGS = [
    "credentials",
    "impersonate_service_account",
    "allUsers",
    "allAuthenticatedUsers",
    "roles/owner",
    "roles/editor",
    "google_cloud_scheduler_job",
    "google_compute_ha_vpn_gateway",
    "google_logging_project_sink",
    "google_service_account_key",
    "google_secret_manager_secret_version",
    "secret_data",
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
    "credentials",
    "secret_data",
}

# Task 1: Staged authority model — approved deployment stage values.
APPROVED_STAGE_VALUES = ["foundation", "migration", "service"]

# Task 3: Reviewed env names allowed in Cloud Run service/job containers.
APPROVED_ENV_NAMES = {
    "GOLDEN_ROSE_ENVIRONMENT",
    "GOLDEN_ROSE_AUTH_MODE",
    "GOLDEN_ROSE_DEPLOYMENT_TARGET",
    "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL",
    "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST",
    "GOLDEN_ROSE_DATABASE_URL",
    "GOLDEN_ROSE_SYNTHETIC_STAFF_ID",
    "GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE",
}

# Env names that must use value_source/secret_ref (not literal value).
SECRET_ENV_NAMES = {
    "GOLDEN_ROSE_DATABASE_URL",
    "GOLDEN_ROSE_SYNTHETIC_STAFF_ID",
}

# Env names exclusive to migration (not allowed in service containers).
MIGRATION_ONLY_ENV_NAMES = {
    "GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE",
}

# Approved secret reference names for each env name.
APPROVED_SECRET_REFS: dict[str, set[str]] = {
    "GOLDEN_ROSE_DATABASE_URL": {
        "runtime-database-url",  # service only
        "migration-database-url",  # migration only
    },
    "GOLDEN_ROSE_SYNTHETIC_STAFF_ID": {
        "synthetic-staff-id",
    },
}

# Mapping of resource type to which secret is allowed for GOLDEN_ROSE_DATABASE_URL.
RESOURCE_DB_SECRET_MAP: dict[str, str] = {
    "google_cloud_run_v2_service": "runtime-database-url",
    "google_cloud_run_v2_job": "migration-database-url",
}

REQUIRED_FILES = [
    TERRAFORM_ROOT / "backend.tf",
    TERRAFORM_ROOT / "versions.tf",
    TERRAFORM_ROOT / "providers.tf",
    TERRAFORM_ROOT / "variables.tf",
    TERRAFORM_ROOT / "locals.tf",
    TERRAFORM_ROOT / "outputs.tf",
    TERRAFORM_ROOT / "bootstrap" / "versions.tf",
    TERRAFORM_ROOT / "bootstrap" / "providers.tf",
    TERRAFORM_ROOT / "bootstrap" / "variables.tf",
    TERRAFORM_ROOT / "bootstrap" / "state.tf",
    TERRAFORM_ROOT / "bootstrap" / "iam.tf",
    TERRAFORM_ROOT / "bootstrap" / "wif.tf",
    TERRAFORM_ROOT / "bootstrap" / "outputs.tf",
    TERRAFORM_ROOT / "develop" / "apis.tf",
    TERRAFORM_ROOT / "develop" / "artifact_registry.tf",
    TERRAFORM_ROOT / "develop" / "secrets.tf",
    TERRAFORM_ROOT / "develop" / "network.tf",
    TERRAFORM_ROOT / "develop" / "cloud_sql.tf",
    TERRAFORM_ROOT / "develop" / "cloud_run.tf",
    TERRAFORM_ROOT / "develop" / "identities.tf",
    TERRAFORM_ROOT / "develop" / "iam.tf",
    TERRAFORM_ROOT / "develop" / "migration_job.tf",
    TERRAFORM_ROOT / "develop" / "budgets.tf",
    TERRAFORM_ROOT / "develop" / "observability.tf",
]

ALLOWED_WORKFLOW_FILENAMES = {
    "application-quality.yml",
    "build-image.yml",
    "deploy-develop.yml",
    "branch-policy.yml",
    "infrastructure-quality.yml",
    "repository-hygiene.yml",
}

ALLOWED_WORKFLOW_JOB_NAMES = {
    "application-quality.yml": {"application"},
    "build-image.yml": {"build-validate", "publish-image"},
    "deploy-develop.yml": {"deploy"},
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
    ("build-image.yml", "build-validate"): {
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Set up Node.js 22.22.3",
        "name:Set up Docker Buildx",
        "name:Build validation image and evidence",
        "name:Upload backend SBOM evidence",
        "name:Upload frontend SBOM evidence",
        "name:Upload image metadata evidence",
    },
    ("build-image.yml", "publish-image"): {
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Set up Node.js 22.22.3",
        "name:Set up Docker Buildx",
        "name:Install Cosign",
        "name:Enforce protected develop source",
        "name:Authenticate to Google Cloud",
        "name:Log in to Artifact Registry",
        "name:Build publish image and evidence",
        "name:Sign and verify published image attestation set",
        "name:Upload backend SBOM evidence",
        "name:Upload frontend SBOM evidence",
        "name:Upload image metadata evidence",
        "name:Upload image SBOM evidence",
        "name:Upload signature verification evidence",
        "name:Upload provenance verification evidence",
        "name:Upload application SBOM attestation evidence",
        "name:Upload published image reference",
    },
    ("deploy-develop.yml", "deploy"): {
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Enforce protected develop source",
        "name:Install Cosign",
        "name:Verify signed stage receipt before cloud authentication",
        "name:Authenticate to Google Cloud",
        "name:Set up gcloud",
        "name:Initialize failed deploy result",
        "name:Download reviewed publish artifacts",
        "name:Bind reviewed published image evidence",
        "name:Record schema compatibility posture",
        "name:Validate reviewed stage plan receipt",
        "name:Verify migration job already matches reviewed image",
        "name:Execute migration job",
        "name:Verify service already matches reviewed image",
        "name:Verify readiness gate and record deploy result",
        "name:Upload deploy compatibility evidence",
        "name:Upload deploy result evidence",
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
    ("build-image.yml", "build-validate"): [
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Set up Node.js 22.22.3",
        "name:Set up Docker Buildx",
        "name:Build validation image and evidence",
        "name:Upload backend SBOM evidence",
        "name:Upload frontend SBOM evidence",
        "name:Upload image metadata evidence",
    ],
    ("build-image.yml", "publish-image"): [
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Set up Node.js 22.22.3",
        "name:Set up Docker Buildx",
        "name:Install Cosign",
        "name:Enforce protected develop source",
        "name:Authenticate to Google Cloud",
        "name:Log in to Artifact Registry",
        "name:Build publish image and evidence",
        "name:Sign and verify published image attestation set",
        "name:Upload backend SBOM evidence",
        "name:Upload frontend SBOM evidence",
        "name:Upload image metadata evidence",
        "name:Upload image SBOM evidence",
        "name:Upload signature verification evidence",
        "name:Upload provenance verification evidence",
        "name:Upload application SBOM attestation evidence",
        "name:Upload published image reference",
    ],
    ("deploy-develop.yml", "deploy"): [
        "name:Check out repository",
        "name:Set up Python 3.12",
        "name:Set up uv",
        "name:Enforce protected develop source",
        "name:Install Cosign",
        "name:Verify signed stage receipt before cloud authentication",
        "name:Authenticate to Google Cloud",
        "name:Set up gcloud",
        "name:Initialize failed deploy result",
        "name:Download reviewed publish artifacts",
        "name:Bind reviewed published image evidence",
        "name:Record schema compatibility posture",
        "name:Validate reviewed stage plan receipt",
        "name:Verify migration job already matches reviewed image",
        "name:Execute migration job",
        "name:Verify service already matches reviewed image",
        "name:Verify readiness gate and record deploy result",
        "name:Upload deploy compatibility evidence",
        "name:Upload deploy result evidence",
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
    ("build-image.yml", "build-validate"): "ubuntu-latest",
    ("build-image.yml", "publish-image"): "ubuntu-latest",
    ("deploy-develop.yml", "deploy"): "ubuntu-latest",
    ("branch-policy.yml", "enforce"): "ubuntu-latest",
    ("infrastructure-quality.yml", "static-validation"): "ubuntu-latest",
    ("repository-hygiene.yml", "check"): "ubuntu-latest",
}

ALLOWED_WORKFLOW_JOB_NAME = {
    ("application-quality.yml", "application"): "application",
    ("build-image.yml", "build-validate"): "build-validate",
    ("build-image.yml", "publish-image"): "publish-image",
    ("deploy-develop.yml", "deploy"): "deploy",
    ("branch-policy.yml", "enforce"): "enforce",
    ("infrastructure-quality.yml", "static-validation"): "Terraform static validation",
    ("repository-hygiene.yml", "check"): "check",
}

ALLOWED_WORKFLOW_JOB_TIMEOUT_MINUTES = {
    ("application-quality.yml", "application"): 30,
    ("deploy-develop.yml", "deploy"): 30,
}

ALLOWED_WORKFLOW_JOB_IF = {
    ("build-image.yml", "build-validate"): "github.event_name == 'pull_request'",
    ("build-image.yml", "publish-image"): "github.event_name == 'workflow_dispatch'",
    ("deploy-develop.yml", "deploy"): "github.event_name == 'workflow_dispatch'",
}

ALLOWED_WORKFLOW_JOB_PERMISSIONS = {
    ("build-image.yml", "publish-image"): {
        "contents": "read",
        "id-token": "write",
    },
    ("deploy-develop.yml", "deploy"): {
        "actions": "read",
        "contents": "read",
        "id-token": "write",
    },
}

ALLOWED_WORKFLOW_JOB_ENVIRONMENT = {
    ("build-image.yml", "publish-image"): "develop",
    ("deploy-develop.yml", "deploy"): "develop",
}

ALLOWED_WORKFLOW_JOB_CONCURRENCY = {
    ("deploy-develop.yml", "deploy"): {
        "group": "deploy-develop",
        "cancel-in-progress": False,
    },
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
    ("build-image.yml", "build-validate", "name:Upload backend SBOM evidence"): "always()",
    ("build-image.yml", "build-validate", "name:Upload frontend SBOM evidence"): "always()",
    ("build-image.yml", "build-validate", "name:Upload image metadata evidence"): "always()",
    ("build-image.yml", "publish-image", "name:Upload backend SBOM evidence"): "always()",
    ("build-image.yml", "publish-image", "name:Upload frontend SBOM evidence"): "always()",
    ("build-image.yml", "publish-image", "name:Upload image metadata evidence"): "always()",
    ("build-image.yml", "publish-image", "name:Upload image SBOM evidence"): "always()",
    ("build-image.yml", "publish-image", "name:Upload signature verification evidence"): "always()",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload provenance verification evidence",
    ): "always()",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload application SBOM attestation evidence",
    ): "always()",
    ("build-image.yml", "publish-image", "name:Upload published image reference"): "always()",
    ("deploy-develop.yml", "deploy", "name:Upload deploy compatibility evidence"): "always()",
    ("deploy-develop.yml", "deploy", "name:Upload deploy result evidence"): "always()",
}

ALLOWED_WORKFLOW_STEP_WITH = {
    (
        "deploy-develop.yml",
        "deploy",
        "name:Install Cosign",
    ): {"cosign-release": "v3.0.6"},
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
        "build-image.yml",
        "build-validate",
        "name:Set up Python 3.12",
    ): {"python-version": "3.12"},
    (
        "build-image.yml",
        "build-validate",
        "name:Set up uv",
    ): {
        "version": "0.12.5",
        "checksum": "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2",
        "enable-cache": True,
    },
    (
        "build-image.yml",
        "build-validate",
        "name:Set up Node.js 22.22.3",
    ): {
        "node-version": "22.22.3",
        "cache": "npm",
        "cache-dependency-path": "apps/web/package-lock.json",
    },
    (
        "build-image.yml",
        "build-validate",
        "name:Upload backend SBOM evidence",
    ): {
        "name": "backend-sbom-cdx",
        "path": "build/backend-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "build-validate",
        "name:Upload frontend SBOM evidence",
    ): {
        "name": "frontend-sbom-cdx",
        "path": "build/frontend-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "build-validate",
        "name:Upload image metadata evidence",
    ): {
        "name": "image-metadata",
        "path": "build/image-metadata.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Set up Python 3.12",
    ): {"python-version": "3.12"},
    (
        "build-image.yml",
        "publish-image",
        "name:Set up uv",
    ): {
        "version": "0.12.5",
        "checksum": "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2",
        "enable-cache": True,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Set up Node.js 22.22.3",
    ): {
        "node-version": "22.22.3",
        "cache": "npm",
        "cache-dependency-path": "apps/web/package-lock.json",
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Install Cosign",
    ): {
        "cosign-release": "v3.0.6",
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Authenticate to Google Cloud",
    ): {
        "workload_identity_provider": "${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}",
        "service_account": "${{ vars.GCP_IMAGE_PUBLISHER_SERVICE_ACCOUNT }}",
        "token_format": "access_token",
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Log in to Artifact Registry",
    ): {
        "registry": "us-east4-docker.pkg.dev",
        "username": "oauth2accesstoken",
        "password": "${{ steps.auth.outputs.access_token }}",
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload backend SBOM evidence",
    ): {
        "name": "backend-sbom-cdx",
        "path": "build/backend-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload frontend SBOM evidence",
    ): {
        "name": "frontend-sbom-cdx",
        "path": "build/frontend-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload image metadata evidence",
    ): {
        "name": "image-metadata",
        "path": "build/image-metadata.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload image SBOM evidence",
    ): {
        "name": "image-sbom-cdx",
        "path": "build/image-sbom.cdx.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload signature verification evidence",
    ): {
        "name": "publish-signature-verification",
        "path": "build/publish-signature-verification.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload provenance verification evidence",
    ): {
        "name": "publish-provenance-verification",
        "path": "build/publish-provenance-verification.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload application SBOM attestation evidence",
    ): {
        "name": "publish-application-sbom-verification",
        "path": "build/publish-application-sbom-verification.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Upload published image reference",
    ): {
        "name": "published-image",
        "path": "build/published-image.txt",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Set up Python 3.12",
    ): {"python-version": "3.12"},
    (
        "deploy-develop.yml",
        "deploy",
        "name:Set up uv",
    ): {
        "version": "0.12.5",
        "checksum": "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2",
        "enable-cache": True,
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Authenticate to Google Cloud",
    ): {
        "workload_identity_provider": "${{ vars.GCP_WORKLOAD_IDENTITY_PROVIDER }}",
        "service_account": "${{ vars.GCP_DEPLOYER_SERVICE_ACCOUNT }}",
        "token_format": "access_token",
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Upload deploy compatibility evidence",
    ): {
        "name": "deploy-compatibility",
        "path": "build/deploy-compatibility.json",
        "if-no-files-found": "error",
        "retention-days": 14,
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Upload deploy result evidence",
    ): {
        "name": "deploy-result",
        "path": "build/deploy-result.json",
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
        "build-image.yml",
        "build-validate",
        "name:Check out repository",
    ): "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    (
        "build-image.yml",
        "build-validate",
        "name:Set up Python 3.12",
    ): "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    (
        "build-image.yml",
        "build-validate",
        "name:Set up uv",
    ): "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
    (
        "build-image.yml",
        "build-validate",
        "name:Set up Node.js 22.22.3",
    ): "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
    (
        "build-image.yml",
        "build-validate",
        "name:Set up Docker Buildx",
    ): "docker/setup-buildx-action@e468171a9de216ec08956ac3ada2f0791b6bd435",
    (
        "build-image.yml",
        "build-validate",
        "name:Upload backend SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "build-validate",
        "name:Upload frontend SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "build-validate",
        "name:Upload image metadata evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Check out repository",
    ): "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    (
        "build-image.yml",
        "publish-image",
        "name:Set up Python 3.12",
    ): "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    (
        "build-image.yml",
        "publish-image",
        "name:Set up uv",
    ): "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
    (
        "build-image.yml",
        "publish-image",
        "name:Set up Node.js 22.22.3",
    ): "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
    (
        "build-image.yml",
        "publish-image",
        "name:Set up Docker Buildx",
    ): "docker/setup-buildx-action@e468171a9de216ec08956ac3ada2f0791b6bd435",
    (
        "build-image.yml",
        "publish-image",
        "name:Install Cosign",
    ): "sigstore/cosign-installer@ba7bc0a3fef59531c69a25acd34668d6d3fe6f22",
    (
        "build-image.yml",
        "publish-image",
        "name:Authenticate to Google Cloud",
    ): "google-github-actions/auth@ba79af03959ebeac9769e648f473a284504d9193",
    (
        "build-image.yml",
        "publish-image",
        "name:Log in to Artifact Registry",
    ): "docker/login-action@184bdaa0721073962dff0199f1fb9940f07167d1",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload backend SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload frontend SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload image metadata evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload image SBOM evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload signature verification evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload provenance verification evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload application SBOM attestation evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "build-image.yml",
        "publish-image",
        "name:Upload published image reference",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Check out repository",
    ): "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Set up Python 3.12",
    ): "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Set up uv",
    ): "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Authenticate to Google Cloud",
    ): "google-github-actions/auth@ba79af03959ebeac9769e648f473a284504d9193",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Set up gcloud",
    ): "google-github-actions/setup-gcloud@77e7a554d41e2ee56fc945c52dfd3f33d12def9a",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Upload deploy compatibility evidence",
    ): "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    (
        "deploy-develop.yml",
        "deploy",
        "name:Upload deploy result evidence",
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
        "deploy-develop.yml",
        "deploy",
        "name:Install Cosign",
    ): "sigstore/cosign-installer@ba7bc0a3fef59531c69a25acd34668d6d3fe6f22",
    (
        "repository-hygiene.yml",
        "check",
        "name:Scan for secrets",
    ): "gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7",
}

ALLOWED_WORKFLOW_STEP_RUN = {
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify signed stage receipt before cloud authentication",
    ): _strip_block_scalar(
        """
set -euo pipefail
mkdir -p build/transition-authority
printf '%s' "$STAGE_RECEIPT_BASE64" | base64 --decode > build/transition-authority/stage-receipt.json
printf '%s' "$STAGE_RECEIPT_BUNDLE_BASE64" | base64 --decode > build/transition-authority/stage-receipt.sigstore.json
cosign verify-blob build/transition-authority/stage-receipt.json --bundle build/transition-authority/stage-receipt.sigstore.json --certificate-identity "$STAGE_RECEIPT_CERTIFICATE_IDENTITY" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
"""
    ),
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
if uv run alembic downgrade base 2> build/alembic-downgrade.stderr; then
  echo "database authority lifecycle downgrade unexpectedly succeeded" >&2
  exit 1
fi
grep -F "database authority lifecycle downgrade is intentionally unsupported without an operator-reviewed role handoff" build/alembic-downgrade.stderr
uv run alembic upgrade head
uv run pip-audit --skip-editable
mkdir -p build
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
"""
    ),
    (
        "build-image.yml",
        "build-validate",
        "name:Build validation image and evidence",
    ): _strip_block_scalar(
        """
set -euo pipefail
uv --version
test "$(node --version)" = "v22.22.3"
test "$(npm --version)" = "10.9.8"
test "$(npm --userconfig apps/web/.npmrc config get registry)" = "https://registry.npmjs.org/"
test "$(npm --userconfig apps/web/.npmrc config get ignore-scripts)" = "true"
uv lock --check
uv sync --locked --all-groups
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
docker buildx build --load --platform linux/amd64 --metadata-file build/image-metadata.json --tag golden-rose:workflow-pr .
uv run python scripts/verify_image_provenance.py --mode pr --dockerfile Dockerfile --metadata-path build/image-metadata.json --backend-sbom-path build/backend-sbom.cdx.json --frontend-sbom-path build/frontend-sbom.cdx.json
"""
    ),
    (
        "build-image.yml",
        "publish-image",
        "name:Enforce protected develop source",
    ): _strip_block_scalar(
        """
set -euo pipefail
test "$GITHUB_REF" = "refs/heads/develop"
"""
    ),
    (
        "build-image.yml",
        "publish-image",
        "name:Build publish image and evidence",
    ): _strip_block_scalar(
        """
set -euo pipefail
uv --version
test "$(node --version)" = "v22.22.3"
test "$(npm --version)" = "10.9.8"
test "$(npm --userconfig apps/web/.npmrc config get registry)" = "https://registry.npmjs.org/"
test "$(npm --userconfig apps/web/.npmrc config get ignore-scripts)" = "true"
uv lock --check
uv sync --locked --all-groups
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
docker buildx build --push --platform linux/amd64 --provenance=mode=max --sbom=true --metadata-file build/image-metadata.json --tag us-east4-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/staff-tracer-images/staff-tracer:${{ github.sha }} .
"""
    ),
    (
        "build-image.yml",
        "publish-image",
        "name:Sign and verify published image attestation set",
    ): _strip_block_scalar(
        """
set -euo pipefail
IMAGE_DIGEST="$(python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('build/image-metadata.json').read_text(encoding='utf-8'))
print(payload['containerimage.digest'])
PY
)"
MANAGED_IMAGE="${MANAGED_REPOSITORY}@${IMAGE_DIGEST}"
export IMAGE_DIGEST MANAGED_IMAGE
python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

payload = {
    "backend_sbom_sha256": hashlib.sha256(Path("build/backend-sbom.cdx.json").read_bytes()).hexdigest(),
    "frontend_sbom_sha256": hashlib.sha256(Path("build/frontend-sbom.cdx.json").read_bytes()).hexdigest(),
    "image_digest": os.environ["IMAGE_DIGEST"],
}
Path("build/application-sbom-checksums-predicate.json").write_text(
    json.dumps(payload, indent=2) + "\n",
    encoding="utf-8",
)
PY
cosign sign --yes "$MANAGED_IMAGE"
cosign attest --yes --type slsaprovenance --predicate build/image-metadata.json "$MANAGED_IMAGE"
cosign attest --yes --type https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1 --predicate build/application-sbom-checksums-predicate.json "$MANAGED_IMAGE"
cosign verify --certificate-identity "https://github.com/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop" --certificate-oidc-issuer "https://token.actions.githubusercontent.com" --output json "$MANAGED_IMAGE" >/dev/null
cosign verify-attestation --type slsaprovenance --certificate-identity "https://github.com/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop" --certificate-oidc-issuer "https://token.actions.githubusercontent.com" --output json "$MANAGED_IMAGE" >/dev/null
cosign verify-attestation --type https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1 --certificate-identity "https://github.com/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop" --certificate-oidc-issuer "https://token.actions.githubusercontent.com" --output json "$MANAGED_IMAGE" >/dev/null
python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

managed_image = os.environ["MANAGED_IMAGE"]
image_digest = os.environ["IMAGE_DIGEST"]
trust = {
    "subject": managed_image,
    "digest": image_digest,
    "certificate_identity": "https://github.com/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop",
    "certificate_oidc_issuer": "https://token.actions.githubusercontent.com",
    "transparency_log_included": True,
}
Path("build/published-image.txt").write_text(managed_image + "\n", encoding="utf-8")
Path("build/publish-signature-verification.json").write_text(
    json.dumps(trust, indent=2) + "\n", encoding="utf-8"
)
Path("build/publish-provenance-verification.json").write_text(
    json.dumps(
        {
            **trust,
            "predicate_type": "https://slsa.dev/provenance/v1",
            "source_commit": os.environ["SOURCE_COMMIT"],
            "builder_id": "https://github.com/actions/runner",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
Path("build/publish-application-sbom-verification.json").write_text(
    json.dumps(
        {
            **trust,
            "predicate_type": "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1",
            "backend_sbom_sha256": hashlib.sha256(Path("build/backend-sbom.cdx.json").read_bytes()).hexdigest(),
            "frontend_sbom_sha256": hashlib.sha256(Path("build/frontend-sbom.cdx.json").read_bytes()).hexdigest(),
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
Path("build/image-sbom.cdx.json").write_text(
    json.dumps(
        {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "metadata": {
                "component": {
                    "name": "staff-tracer",
                    "purl": f"pkg:oci/staff-tracer@{image_digest}?repository_url={os.environ['MANAGED_REPOSITORY']}",
                    "properties": [
                        {
                            "name": "syft:source:image:platform",
                            "value": "linux/amd64",
                        }
                    ],
                }
            },
            "components": [
                {
                    "name": "staff-tracer-runtime",
                    "version": image_digest,
                }
            ],
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY
# never deploy by tag; capture and verify the immutable digest and trust evidence emitted by the publish build
uv run python scripts/verify_image_provenance.py --mode publish --dockerfile Dockerfile --metadata-path build/image-metadata.json --backend-sbom-path build/backend-sbom.cdx.json --frontend-sbom-path build/frontend-sbom.cdx.json --published-image-repository "$MANAGED_REPOSITORY" --signature-verification-path build/publish-signature-verification.json --provenance-verification-path build/publish-provenance-verification.json --image-sbom-path build/image-sbom.cdx.json --application-sbom-verification-path build/publish-application-sbom-verification.json > build/published-image.txt
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Enforce protected develop source",
    ): _strip_block_scalar(
        """
set -euo pipefail
test "$GITHUB_REF" = "refs/heads/develop"
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Initialize failed deploy result",
    ): _strip_block_scalar(
        """
set -euo pipefail
mkdir -p build/reviewed-artifacts build
python - <<'PY'
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Download reviewed publish artifacts",
    ): _strip_block_scalar(
        """
set -euo pipefail
mkdir -p build/reviewed-artifacts
python - <<'PY'
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Bind reviewed published image evidence",
    ): _strip_block_scalar(
        """
set -euo pipefail
PUBLISHED_IMAGE_REF="$(tr -d '\r\n' < build/reviewed-artifacts/published-image.txt)"
VERIFIED_IMAGE_REF="$(uv run python scripts/verify_image_provenance.py --mode publish --dockerfile Dockerfile --metadata-path build/reviewed-artifacts/image-metadata.json --backend-sbom-path build/reviewed-artifacts/backend-sbom.cdx.json --frontend-sbom-path build/reviewed-artifacts/frontend-sbom.cdx.json --published-image-repository "$MANAGED_REPOSITORY")"
test "$VERIFIED_IMAGE_REF" = "$PUBLISHED_IMAGE_REF"
case "$VERIFIED_IMAGE_REF" in
  "$MANAGED_REPOSITORY"@sha256:*) ;;
  *)
    echo "reviewed image reference is not bound to the managed repository" >&2
    exit 1
    ;;
esac
IMAGE_DIGEST="${VERIFIED_IMAGE_REF##*@}"
printf 'MANAGED_IMAGE=%s\n' "$VERIFIED_IMAGE_REF" >> "$GITHUB_ENV"
printf 'IMAGE_DIGEST=%s\n' "$IMAGE_DIGEST" >> "$GITHUB_ENV"
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Record schema compatibility posture",
    ): _strip_block_scalar(
        """
set -euo pipefail
mkdir -p build
python - <<'PY'
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Validate reviewed stage plan receipt",
    ): _strip_block_scalar(
        """
set -euo pipefail
python - <<'PY'
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify migration job already matches reviewed image",
    ): _strip_block_scalar(
        """
set -euo pipefail
CURRENT_JOB_IMAGE=$(gcloud run jobs describe run-migrations --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --format='value(template.template.containers[0].image)')
test "$CURRENT_JOB_IMAGE" = "$MANAGED_IMAGE"
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Execute migration job",
    ): _strip_block_scalar(
        """
set -euo pipefail
gcloud run jobs execute run-migrations --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --wait >/dev/null
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify service already matches reviewed image",
    ): _strip_block_scalar(
        """
set -euo pipefail
CURRENT_SERVICE_IMAGE=$(gcloud run services describe staff-tracer --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --format='value(spec.template.spec.containers[0].image)')
test "$CURRENT_SERVICE_IMAGE" = "$MANAGED_IMAGE"
"""
    ),
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify readiness gate and record deploy result",
    ): _strip_block_scalar(
        """
set -euo pipefail
if ! SERVICE_JSON=$(gcloud run services describe staff-tracer --project "${{ vars.GCP_PROJECT_ID }}" --region us-east4 --format=json); then
  python - <<'PY'
  exit 1
fi
mkdir -p build
python - <<'PY'
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
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
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

EXACT_WORKFLOW_RUN_SHA256 = {
    ("build-image.yml", "publish-image", "name:Sign and verify published image attestation set"): (
        "a72505d2304a88160a61d70a3489980f93b83d33fc198c8465c770f9c615ff81"
    ),
    ("deploy-develop.yml", "deploy", "name:Initialize failed deploy result"): (
        "931d39097ca97bc9a49f5227f4287d19f0709adfff40ca6f540f673703622b40"
    ),
    ("deploy-develop.yml", "deploy", "name:Download reviewed publish artifacts"): (
        "2705003a7b1816fd2d8d969fb2a5e3a028975afd789d0580f62024fe46f237fa"
    ),
    ("deploy-develop.yml", "deploy", "name:Bind reviewed published image evidence"): (
        "fae1871d1f66f845993ef7f8be42342854a45f9d259523b35bb716c116939aaf"
    ),
    ("deploy-develop.yml", "deploy", "name:Record schema compatibility posture"): (
        "35ce29e8fb471b0ecefca7694a7754e4be52a5a359dafebac4ce4307ab889d86"
    ),
    ("deploy-develop.yml", "deploy", "name:Validate reviewed stage plan receipt"): (
        "230ecddb58ac80a56dc0bb9ded0b99edd6f903c92dac3cf9336c9a9e8460b18c"
    ),
    ("deploy-develop.yml", "deploy", "name:Execute migration job"): (
        "ed74538566a1fdfdc6d4cb29462eca6e391d357c13963c6b0118fdf3f5d9d3ed"
    ),
    ("deploy-develop.yml", "deploy", "name:Verify readiness gate and record deploy result"): (
        "45273accf9e443a2297206af6c0e578dd3624b791a65759f0c45258dff827c00"
    ),
}

ALLOWED_WORKFLOW_STEP_RUN_SUBSTRINGS = {
    (
        "build-image.yml",
        "publish-image",
        "name:Sign and verify published image attestation set",
    ): [
        "cosign sign --yes",
        "cosign attest --yes --type slsaprovenance",
        "cosign verify --certificate-identity",
        "cosign verify-attestation --type slsaprovenance",
        '"predicate_type": "https://slsa.dev/provenance/v1"',
        '"predicate_type": "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1"',
        '"value": "linux/amd64"',
        "scripts/verify_image_provenance.py --mode publish",
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Initialize failed deploy result",
    ): [
        '"result": "failed"',
        '"current_stage": "pre_deploy_validation"',
        '"qualification_executed": False',
        '"recovery_disposition": "forward recovery or teardown/rebuild required"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Download reviewed publish artifacts",
    ): [
        "PUBLISH_RUN_ID",
        "DEPLOY_COMMIT_SHA",
        'repository = os.environ["GITHUB_REPOSITORY"]',
        'f"{api_base}/actions/runs/{run_id}"',
        '"path": ".github/workflows/build-image.yml"',
        '"head_branch": "develop"',
        '"conclusion": "success"',
        'deploy_commit_sha = os.environ["DEPLOY_COMMIT_SHA"]',
        "if head_sha != deploy_commit_sha:",
        '"deploy_commit_sha": deploy_commit_sha',
        '"publish_job_name": publish_job["name"]',
        'f"{api_base}/actions/runs/{run_id}/artifacts"',
        '"published-image": "published-image.txt"',
        '"image-sbom-cdx": "image-sbom.cdx.json"',
        '"backend-sbom-cdx": "backend-sbom.cdx.json"',
        '"frontend-sbom-cdx": "frontend-sbom.cdx.json"',
        '"publish-signature-verification": "publish-signature-verification.json"',
        '"publish-provenance-verification": "publish-provenance-verification.json"',
        '"publish-application-sbom-verification": "publish-application-sbom-verification.json"',
        '"reviewed-stage-plan-receipt": "reviewed-stage-plan-receipt.json"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Bind reviewed published image evidence",
    ): [
        "PUBLISHED_IMAGE_REF",
        "VERIFIED_IMAGE_REF",
        "scripts/verify_image_provenance.py --mode publish",
        "--signature-verification-path build/reviewed-artifacts/publish-signature-verification.json",
        "--provenance-verification-path build/reviewed-artifacts/publish-provenance-verification.json",
        "--image-sbom-path build/reviewed-artifacts/image-sbom.cdx.json",
        "--application-sbom-verification-path build/reviewed-artifacts/publish-application-sbom-verification.json",
        'test "$VERIFIED_IMAGE_REF" = "$PUBLISHED_IMAGE_REF"',
        'case "$VERIFIED_IMAGE_REF" in',
        '"$MANAGED_REPOSITORY"@sha256:*) ;;',
        'IMAGE_DIGEST="${VERIFIED_IMAGE_REF##*@}"',
        'printf \'MANAGED_IMAGE=%s\\n\' "$VERIFIED_IMAGE_REF" >> "$GITHUB_ENV"',
        'printf \'IMAGE_DIGEST=%s\\n\' "$IMAGE_DIGEST" >> "$GITHUB_ENV"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Validate reviewed stage plan receipt",
    ): [
        "reviewed-stage-plan-receipt.json",
        'receipt["stage"] != "service"',
        'receipt["source_sha"] != os.environ["DEPLOY_COMMIT_SHA"]',
        'receipt["workload_image_digest"] != os.environ["IMAGE_DIGEST"]',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Record schema compatibility posture",
    ): [
        "build/deploy-compatibility.json",
        '"publish_run_id": os.environ["PUBLISH_RUN_ID"]',
        '"rollback_without_proven_compatibility_window": False',
        '"recovery_posture": "forward recovery"',
        '"qualification_executed": False',
        '"compatibility_evidence": "published-image artifact plus backend/frontend SBOM, image SBOM, signature/provenance verification, and metadata evidence from the reviewed publish run"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify migration job already matches reviewed image",
    ): [
        "CURRENT_JOB_IMAGE=$(gcloud run jobs describe run-migrations --project",
        'test "$CURRENT_JOB_IMAGE" = "$MANAGED_IMAGE"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Execute migration job",
    ): [
        "gcloud run jobs execute run-migrations --project",
        'payload["current_stage"] = "migration_execution"',
        'payload["recovery_disposition"] = "forward recovery or teardown/rebuild required"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify service already matches reviewed image",
    ): [
        "CURRENT_SERVICE_IMAGE=$(gcloud run services describe staff-tracer --project",
        'test "$CURRENT_SERVICE_IMAGE" = "$MANAGED_IMAGE"',
    ],
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify readiness gate and record deploy result",
    ): [
        'if condition.get("type") == "Ready"',
        'ready_image.split("@", 1)[1] != os.environ["IMAGE_DIGEST"]',
        "gcloud run services describe staff-tracer --project",
        "build/deploy-result.json",
        '"ready_revision": ready_revision',
        '"ready_image": ready_image',
        '"deploy_executed": False',
        '"publish_run_id": os.environ["PUBLISH_RUN_ID"]',
        '"qualification_executed": False',
        '"result": "success"',
    ],
}

ALLOWED_WORKFLOW_STEP_SHELL = {}

ALLOWED_WORKFLOW_STEP_WORKING_DIRECTORY = {}

ALLOWED_WORKFLOW_STEP_CONTINUE_ON_ERROR = {}

ALLOWED_WORKFLOW_STEP_TIMEOUT_MINUTES = {}

ALLOWED_WORKFLOW_STEP_ID = {
    ("build-image.yml", "publish-image", "name:Authenticate to Google Cloud"): "auth",
    ("deploy-develop.yml", "deploy", "name:Authenticate to Google Cloud"): "auth",
}

ALLOWED_WORKFLOW_STEP_ENV = {
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify signed stage receipt before cloud authentication",
    ): {
        "STAGE_RECEIPT_BASE64": "${{ inputs.stage_receipt_base64 }}",
        "STAGE_RECEIPT_BUNDLE_BASE64": "${{ inputs.stage_receipt_bundle_base64 }}",
        "STAGE_RECEIPT_CERTIFICATE_IDENTITY": "${{ vars.STAGE_RECEIPT_CERTIFICATE_IDENTITY }}",
    },
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
    (
        "deploy-develop.yml",
        "deploy",
        "name:Initialize failed deploy result",
    ): {"PUBLISH_RUN_ID": "${{ inputs.publish_run_id }}"},
    (
        "deploy-develop.yml",
        "deploy",
        "name:Download reviewed publish artifacts",
    ): {
        "GITHUB_TOKEN": "${{ github.token }}",
        "PUBLISH_RUN_ID": "${{ inputs.publish_run_id }}",
        "DEPLOY_COMMIT_SHA": "${{ github.sha }}",
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Bind reviewed published image evidence",
    ): {
        "MANAGED_REPOSITORY": "us-east4-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/staff-tracer-images/staff-tracer"
    },
    (
        "build-image.yml",
        "publish-image",
        "name:Sign and verify published image attestation set",
    ): {
        "MANAGED_REPOSITORY": "us-east4-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/staff-tracer-images/staff-tracer",
        "SOURCE_COMMIT": "${{ github.sha }}",
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Record schema compatibility posture",
    ): {"PUBLISH_RUN_ID": "${{ inputs.publish_run_id }}"},
    (
        "deploy-develop.yml",
        "deploy",
        "name:Validate reviewed stage plan receipt",
    ): {
        "PUBLISH_RUN_ID": "${{ inputs.publish_run_id }}",
        "DEPLOY_COMMIT_SHA": "${{ github.sha }}",
    },
    (
        "deploy-develop.yml",
        "deploy",
        "name:Verify readiness gate and record deploy result",
    ): {"PUBLISH_RUN_ID": "${{ inputs.publish_run_id }}"},
}


DEPLOY_WORKFLOW_STEPS = [
    "name:Check out repository",
    "name:Set up Python 3.12",
    "name:Set up uv",
    "name:Enforce protected develop source",
    "name:Install Cosign",
    "name:Verify signed stage receipt before cloud authentication",
    "name:Initialize failed deploy result",
    "name:Verify direct OCI image authority",
    "name:Validate signed stage receipt after image digest",
    "name:Authenticate to Google Cloud",
    "name:Set up gcloud",
    "name:Extract and validate selected live configuration projection",
    "name:Execute migration transition",
    "name:Verify service readiness transition",
    "name:Record deploy result",
    "name:Upload deploy result evidence",
]
_DEPLOY_KEY = ("deploy-develop.yml", "deploy")
ALLOWED_WORKFLOW_STEP_IDENTIFIERS[_DEPLOY_KEY] = set(DEPLOY_WORKFLOW_STEPS)
REQUIRED_WORKFLOW_STEP_ORDER[_DEPLOY_KEY] = DEPLOY_WORKFLOW_STEPS
ALLOWED_WORKFLOW_JOB_PERMISSIONS[_DEPLOY_KEY] = {"contents": "read", "id-token": "write"}
for _identifier in DEPLOY_WORKFLOW_STEPS:
    ALLOWED_WORKFLOW_STEP_RUN.pop(("deploy-develop.yml", "deploy", _identifier), None)
    EXACT_WORKFLOW_RUN_SHA256.pop(("deploy-develop.yml", "deploy", _identifier), None)
    ALLOWED_WORKFLOW_STEP_RUN_SUBSTRINGS.pop(("deploy-develop.yml", "deploy", _identifier), None)
ALLOWED_WORKFLOW_STEP_IF[("deploy-develop.yml", "deploy", "name:Execute migration transition")] = (
    "inputs.deployment_stage == 'migration'"
)
ALLOWED_WORKFLOW_STEP_IF[
    ("deploy-develop.yml", "deploy", "name:Verify service readiness transition")
] = "inputs.deployment_stage == 'service'"
ALLOWED_WORKFLOW_STEP_IF[("deploy-develop.yml", "deploy", "name:Record deploy result")] = "always()"
ALLOWED_WORKFLOW_STEP_ENV[
    ("deploy-develop.yml", "deploy", "name:Verify signed stage receipt before cloud authentication")
] = {
    "STAGE_RECEIPT_BASE64": "${{ inputs.stage_receipt_base64 }}",
    "STAGE_RECEIPT_BUNDLE_BASE64": "${{ inputs.stage_receipt_bundle_base64 }}",
    "STAGE_RECEIPT_CERTIFICATE_IDENTITY": "${{ vars.STAGE_RECEIPT_CERTIFICATE_IDENTITY }}",
    "MIGRATION_SUCCESS_RECEIPT_BASE64": "${{ inputs.migration_success_receipt_base64 }}",
    "MIGRATION_SUCCESS_RECEIPT_BUNDLE_BASE64": "${{ inputs.migration_success_receipt_bundle_base64 }}",
    "MIGRATION_SUCCESS_RECEIPT_CERTIFICATE_IDENTITY": "${{ vars.MIGRATION_SUCCESS_RECEIPT_CERTIFICATE_IDENTITY }}",
    "MIGRATION_RECEIPT_BASE64": "${{ inputs.migration_receipt_base64 }}",
    "MIGRATION_RECEIPT_BUNDLE_BASE64": "${{ inputs.migration_receipt_bundle_base64 }}",
    "DEPLOYMENT_STAGE": "${{ inputs.deployment_stage }}",
}
ALLOWED_WORKFLOW_STEP_ENV.pop(
    ("deploy-develop.yml", "deploy", "name:Initialize failed deploy result"), None
)
ALLOWED_WORKFLOW_STEP_ENV[
    ("deploy-develop.yml", "deploy", "name:Verify direct OCI image authority")
] = {
    "MANAGED_REPOSITORY": "us-east4-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/staff-tracer-images/staff-tracer",
    "BUILD_CERTIFICATE_IDENTITY": "${{ vars.BUILD_CERTIFICATE_IDENTITY }}",
}
ALLOWED_WORKFLOW_STEP_ENV[
    ("deploy-develop.yml", "deploy", "name:Validate signed stage receipt after image digest")
] = {
    "DEPLOYMENT_STAGE": "${{ inputs.deployment_stage }}",
}
ALLOWED_WORKFLOW_STEP_ENV[
    (
        "deploy-develop.yml",
        "deploy",
        "name:Extract and validate selected live configuration projection",
    )
] = {
    "DEPLOYMENT_STAGE": "${{ inputs.deployment_stage }}",
}
ALLOWED_WORKFLOW_STEP_ENV[("deploy-develop.yml", "deploy", "name:Record deploy result")] = {
    "DEPLOYMENT_STAGE": "${{ inputs.deployment_stage }}",
}

# Deploy is the only workflow that can obtain the deployer identity. Every
# executable body is pinned, rather than merely checked for a few dangerous
# substrings. This rejects both known authority expansions and syntactically
# valid but unreviewed commands (including new gcloud groups).
EXACT_WORKFLOW_RUN_SHA256.update(
    {
        (
            "deploy-develop.yml",
            "deploy",
            "name:Enforce protected develop source",
        ): "4cc323975c42ce2d900b90afc6ce6efc272462d00b51a490915b8c23093ad963",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Verify signed stage receipt before cloud authentication",
        ): "4c6808f0dadffdd9928015544da4a5f01ee29276a86d3ccb561ff04997f79b2e",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Initialize failed deploy result",
        ): "81dbf3a69fd1821aee92b7b44894027865d07dd73fe7dc501e8e955b8ce1792f",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Verify direct OCI image authority",
        ): "24555e0c0dca73edfd117741cd9be7a92d6a463406b57751e6209ea806629799",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Validate signed stage receipt after image digest",
        ): "2a15ed6518a39525d3d35862441af994a168958ef2f6acc7039fc3b010c05594",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Extract and validate selected live configuration projection",
        ): "8698695ce9400ffa409aeba425d4566a396fc3f8fe27955982272563c78506fc",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Execute migration transition",
        ): "a3dcc21f6e4fdcd0fe7552e1c0a402a34c4c538a916e914872e5998d314ba336",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Verify service readiness transition",
        ): "6911e08b248ee22bea937040a0976407ac38bbe6cc407e1d8bff0f1fab992b92",
        (
            "deploy-develop.yml",
            "deploy",
            "name:Record deploy result",
        ): "491e2d8b8fb26c206faeeec288d25f5340bc9528fc0dc1147ce4129aab3b82c9",
    }
)


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


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _contains_normalized_fragment(text: str, fragment: str) -> bool:
    return _normalize_whitespace(fragment) in _normalize_whitespace(text)


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


def _collect_forbidden_workflow_permissions(path: Path, node: object) -> list[str]:
    violations: list[str] = []
    if not isinstance(node, dict):
        return violations

    workflow_permissions = node.get("permissions")
    if isinstance(workflow_permissions, str) and workflow_permissions == "write-all":
        violations.append("permissions: write-all")
    if isinstance(workflow_permissions, dict):
        for permission_name, permission_value in workflow_permissions.items():
            if permission_value == "write":
                violations.append(f"{permission_name}: write")

    jobs = node.get("jobs")
    if not isinstance(jobs, dict):
        return violations
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        permissions = job.get("permissions")
        allowed_permissions = ALLOWED_WORKFLOW_JOB_PERMISSIONS.get((path.name, str(job_name)))
        if allowed_permissions is not None:
            continue
        if isinstance(permissions, str) and permissions == "write-all":
            violations.append("permissions: write-all")
        if isinstance(permissions, dict):
            for permission_name, permission_value in permissions.items():
                if permission_value == "write":
                    violations.append(f"{permission_name}: write")
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
        "if": ALLOWED_WORKFLOW_JOB_IF,
        "continue-on-error": {},
        "needs": {},
        "permissions": ALLOWED_WORKFLOW_JOB_PERMISSIONS,
        "environment": ALLOWED_WORKFLOW_JOB_ENVIRONMENT,
        "defaults": {},
        "container": {},
        "strategy": {},
        "concurrency": ALLOWED_WORKFLOW_JOB_CONCURRENCY,
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
            workflow_step_key = (path.name, str(job_name), identifier)
            if workflow_step_key[:2] == ("deploy-develop.yml", "deploy"):
                if isinstance(actual_run, str):
                    for forbidden in (
                        "gcloud run services update",
                        "gcloud run jobs update",
                        "--update-env-vars",
                        "--set-env-vars",
                        "--set-secrets",
                        "--update-secrets",
                        "--add-cloudsql-instances",
                    ):
                        if forbidden in actual_run:
                            violations.append(
                                f"{identifier} contains forbidden imperative deployment mutation {forbidden!r}"
                            )
                if actual_run is None:
                    continue
                expected_digest = EXACT_WORKFLOW_RUN_SHA256.get(workflow_step_key)
                if (
                    not isinstance(actual_run, str)
                    or expected_digest is None
                    or hashlib.sha256(actual_run.strip().encode()).hexdigest() != expected_digest
                ):
                    violations.append(f"{identifier} must match reviewed executable script exactly")
                continue
            expected_run = ALLOWED_WORKFLOW_STEP_RUN.get(workflow_step_key)
            if expected_run is None:
                if actual_run is not None:
                    violations.append(f"{identifier} -> {str(actual_run).strip()}")
            elif not isinstance(actual_run, str) or actual_run.strip() != expected_run.strip():
                expected_digest = EXACT_WORKFLOW_RUN_SHA256.get(workflow_step_key)
                if expected_digest is not None and isinstance(actual_run, str):
                    observed_digest = hashlib.sha256(actual_run.strip().encode()).hexdigest()
                    if observed_digest == expected_digest:
                        continue
                    violations.append(f"{identifier} must match reviewed executable script exactly")
                    continue
                if workflow_step_key in ALLOWED_WORKFLOW_STEP_RUN_SUBSTRINGS:
                    violations.append(f"{identifier} must match reviewed executable script exactly")
                    continue
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


def _load_predeployment_authority_manifest(root: Path) -> dict[object, object] | None:
    manifest_path = root / MANIFEST_RELATIVE_PATH
    if not manifest_path.exists():
        return None

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_json_object_pairs_with_duplicate_key_rejection,
        )
    except DuplicateTerraformJsonKeyError as exc:
        raise ValueError(
            f"{manifest_path.relative_to(root)} contains duplicate manifest key and fails closed: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{manifest_path.relative_to(root)} contains malformed manifest JSON and fails closed: {exc.msg}"
        ) from exc

    if not isinstance(manifest, dict):
        raise ValueError(
            f"{manifest_path.relative_to(root)} must be a JSON object with terraform resource contracts"
        )

    terraform = manifest.get("terraform")
    if not isinstance(terraform, dict):
        raise ValueError(f"{manifest_path.relative_to(root)} must define an object at 'terraform'")

    resource_types = terraform.get("resource_types")
    if not isinstance(resource_types, dict):
        raise ValueError(
            f"{manifest_path.relative_to(root)} must define an object at 'terraform.resource_types'"
        )

    for resource_type, contract in resource_types.items():
        if not isinstance(resource_type, str):
            raise ValueError(
                f"{manifest_path.relative_to(root)} contains a non-string Terraform resource type key"
            )
        if not isinstance(contract, dict):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define an object contract for {resource_type!r}"
            )
        max_count = contract.get("max_count")
        if not isinstance(max_count, int) or max_count < 1:
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define a positive integer max_count for {resource_type!r}"
            )
        max_count_by_stage = contract.get("max_count_by_stage")
        if max_count_by_stage is not None:
            if not isinstance(max_count_by_stage, dict):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} must define an object max_count_by_stage for {resource_type!r}"
                )
            for stage_name, stage_count in max_count_by_stage.items():
                if stage_name not in APPROVED_STAGE_VALUES:
                    raise ValueError(
                        f"{manifest_path.relative_to(root)} contains unsupported max_count_by_stage key {stage_name!r} for {resource_type!r}"
                    )
                if not isinstance(stage_count, int) or stage_count < 0:
                    raise ValueError(
                        f"{manifest_path.relative_to(root)} must define a non-negative integer stage max for {resource_type!r}:{stage_name!r}"
                    )
        stage_ownership = contract.get("stage_ownership")
        if stage_ownership is not None:
            if not isinstance(stage_ownership, str):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} must define a string stage_ownership for {resource_type!r}"
                )
            if stage_ownership not in APPROVED_STAGE_VALUES:
                raise ValueError(
                    f"{manifest_path.relative_to(root)} stage_ownership for {resource_type!r} "
                    f"must be one of {APPROVED_STAGE_VALUES}, got {stage_ownership!r}"
                )

    workflows = manifest.get("workflows")
    if workflows is not None:
        if not isinstance(workflows, dict):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define an object at 'workflows'"
            )
        workflow_files = workflows.get("files")
        if workflow_files is None or not isinstance(workflow_files, dict):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define an object at 'workflows.files'"
            )
        for workflow_name in workflow_files:
            if not isinstance(workflow_name, str):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} contains a non-string workflow file key"
                )
            workflow_contract = workflow_files[workflow_name]
            if not isinstance(workflow_contract, dict):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} must define an object contract for workflow file {workflow_name!r}"
                )
            jobs = workflow_contract.get("jobs")
            if jobs is not None:
                if not isinstance(jobs, dict):
                    raise ValueError(
                        f"{manifest_path.relative_to(root)} must define an object at 'workflows.files.{workflow_name}.jobs'"
                    )
                for job_name, job_contract in jobs.items():
                    if not isinstance(job_name, str):
                        raise ValueError(
                            f"{manifest_path.relative_to(root)} contains a non-string workflow job key"
                        )
                    if not isinstance(job_contract, dict):
                        raise ValueError(
                            f"{manifest_path.relative_to(root)} must define an object contract for workflow job {job_name!r}"
                        )
                    steps = job_contract.get("steps")
                    if steps is not None:
                        if not isinstance(steps, list):
                            raise ValueError(
                                f"{manifest_path.relative_to(root)} must define a list at 'workflows.files.{workflow_name}.jobs.{job_name}.steps'"
                            )
                        for step_identifier in steps:
                            if not isinstance(step_identifier, str):
                                raise ValueError(
                                    f"{manifest_path.relative_to(root)} contains a non-string workflow step identifier"
                                )

    scripts = manifest.get("scripts")
    if scripts is not None:
        if not isinstance(scripts, dict):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define an object at 'scripts'"
            )
        entrypoints = scripts.get("entrypoints")
        if entrypoints is None or not isinstance(entrypoints, list):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define a list at 'scripts.entrypoints'"
            )
        for entrypoint in entrypoints:
            if not isinstance(entrypoint, str):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} contains a non-string script entrypoint"
                )

    protected_deployment_paths = manifest.get("protected_deployment_paths")
    if protected_deployment_paths is not None:
        if not isinstance(protected_deployment_paths, list):
            raise ValueError(
                f"{manifest_path.relative_to(root)} must define a list at 'protected_deployment_paths'"
            )
        for protected_path in protected_deployment_paths:
            if not isinstance(protected_path, str):
                raise ValueError(
                    f"{manifest_path.relative_to(root)} contains a non-string protected deployment path"
                )

    return manifest


def _collect_manifest_workflow_contract_violations(
    root: Path, manifest: dict[object, object]
) -> list[str]:
    violations: list[str] = []
    workflows = manifest.get("workflows")
    workflow_files = workflows.get("files") if isinstance(workflows, dict) else None
    if not isinstance(workflow_files, dict):
        return violations
    for (workflow_name, job_name), expected_steps in REQUIRED_WORKFLOW_STEP_ORDER.items():
        workflow_contract = workflow_files.get(workflow_name)
        if not isinstance(workflow_contract, dict):
            continue
        jobs = workflow_contract.get("jobs")
        if not isinstance(jobs, dict):
            continue
        job_contract = jobs.get(job_name)
        if not isinstance(job_contract, dict):
            continue
        manifest_steps = job_contract.get("steps")
        if manifest_steps != expected_steps:
            violations.append(
                f"{MANIFEST_RELATIVE_PATH} workflow step order drifted for {workflow_name}:{job_name}"
            )
    return violations


def _collect_declared_terraform_resource_types(
    terraform_config_paths: list[Path],
) -> tuple[list[tuple[Path, str]], dict[str, int]]:
    occurrences: list[tuple[Path, str]] = []
    counts: dict[str, int] = {}

    for path in sorted(terraform_config_paths):
        text = path.read_text(encoding="utf-8")
        if path.name.endswith(".tf.json"):
            try:
                parsed = json.loads(
                    text,
                    object_pairs_hook=_json_object_pairs_with_duplicate_key_rejection,
                )
            except (DuplicateTerraformJsonKeyError, json.JSONDecodeError):
                continue
            resources = parsed.get("resource") if isinstance(parsed, dict) else None
            if not isinstance(resources, dict):
                continue
            for resource_type, instances in resources.items():
                if not isinstance(resource_type, str) or not isinstance(instances, dict):
                    continue
                instance_count = len(instances)
                if instance_count < 1:
                    continue
                occurrences.append((path, resource_type))
                counts[resource_type] = counts.get(resource_type, 0) + instance_count
            continue

        if path.suffix != ".tf":
            continue
        for match in RESOURCE_BLOCK_PATTERN.finditer(text):
            resource_type = match.group(1)
            occurrences.append((path, resource_type))
            counts[resource_type] = counts.get(resource_type, 0) + 1

    return occurrences, counts


def _extract_local_toset_length(text: str, local_name: str) -> int | None:
    match = re.search(
        rf"{re.escape(local_name)}\s*=\s*toset\(\[(?P<body>.*?)\]\)",
        text,
        re.DOTALL,
    )
    if match is None:
        return None
    body = match.group("body")
    return len(re.findall(r'"[^"]+"', body))


def _approved_count_max(count_expr: str) -> int | None:
    normalized = " ".join(count_expr.split())
    if re.fullmatch(r"[0-9]+", normalized):
        return int(normalized)
    approved_patterns = [
        r'var\.deployment_stage == "service" \? 1 : 0',
        r'var\.deployment_stage == "migration" \|\| var\.deployment_stage == "service" \? 1 : 0',
        r'var\.bootstrap_operator_status == "bootstrap-active" \? 1 : 0',
    ]
    for pattern in approved_patterns:
        if re.fullmatch(pattern, normalized):
            return 1
    return None


def _approved_for_each_max(for_each_expr: str, text: str) -> int | None:
    normalized = " ".join(for_each_expr.split())
    match = re.fullmatch(r"local\.([A-Za-z0-9_]+)", normalized)
    if match is None:
        return None
    return _extract_local_toset_length(text, match.group(1))


def _collect_declared_terraform_resource_expansions(
    terraform_config_paths: list[Path],
) -> tuple[list[tuple[Path, str]], dict[str, int], list[tuple[Path, str, str, str]]]:
    occurrences: list[tuple[Path, str]] = []
    counts: dict[str, int] = {}
    unresolved: list[tuple[Path, str, str, str]] = []

    for path in sorted(terraform_config_paths):
        text = path.read_text(encoding="utf-8")
        if path.name.endswith(".tf.json"):
            try:
                parsed = json.loads(
                    text,
                    object_pairs_hook=_json_object_pairs_with_duplicate_key_rejection,
                )
            except (DuplicateTerraformJsonKeyError, json.JSONDecodeError):
                continue
            resources = parsed.get("resource") if isinstance(parsed, dict) else None
            if not isinstance(resources, dict):
                continue
            for resource_type, instances in resources.items():
                if not isinstance(resource_type, str) or not isinstance(instances, dict):
                    continue
                instance_count = len(instances)
                if instance_count < 1:
                    continue
                occurrences.append((path, resource_type))
                counts[resource_type] = counts.get(resource_type, 0) + instance_count
            continue

        if path.suffix != ".tf":
            continue
        for match in RESOURCE_BLOCK_WITH_BODY_PATTERN.finditer(text):
            resource_type = match.group(1)
            body = match.group("body")
            occurrences.append((path, resource_type))
            count_match = re.search(r"^\s*count\s*=\s*(.+?)$", body, re.MULTILINE)
            for_each_match = re.search(r"^\s*for_each\s*=\s*(.+?)$", body, re.MULTILINE)
            if count_match and for_each_match:
                unresolved.append(
                    (path, resource_type, "count+for_each", "count and for_each both set")
                )
                continue
            if count_match:
                expr = count_match.group(1).strip()
                max_instances = _approved_count_max(expr)
                if max_instances is None:
                    unresolved.append((path, resource_type, "count", expr))
                    continue
                counts[resource_type] = counts.get(resource_type, 0) + max_instances
                continue
            if for_each_match:
                expr = for_each_match.group(1).strip()
                max_instances = _approved_for_each_max(expr, text)
                if max_instances is None:
                    unresolved.append((path, resource_type, "for_each", expr))
                    continue
                counts[resource_type] = counts.get(resource_type, 0) + max_instances
                continue
            counts[resource_type] = counts.get(resource_type, 0) + 1

    return occurrences, counts, unresolved


def _collect_backend_configuration_violations(
    root: Path, terraform_config_paths: list[Path]
) -> list[str]:
    violations: list[str] = []
    allowed_backend_path = Path("infra/gcp/backend.tf")
    forbidden_backend_value_tokens = [
        "bucket",
        "prefix",
        "project",
        "credentials",
        "access_token",
        "impersonate_service_account",
    ]

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        if 'backend "gcs"' in text:
            if relative_path != allowed_backend_path:
                violations.append(
                    f"{relative_path} contains backend configuration outside the approved partial backend path"
                )
                continue
            for token in forbidden_backend_value_tokens:
                if re.search(rf"\b{re.escape(token)}\s*=", text):
                    violations.append(f"{relative_path} contains committed backend value {token!r}")

        if path.name.endswith(".tf.json"):
            try:
                parsed = json.loads(
                    text,
                    object_pairs_hook=_json_object_pairs_with_duplicate_key_rejection,
                )
            except (DuplicateTerraformJsonKeyError, json.JSONDecodeError):
                continue
            terraform_blocks = parsed.get("terraform") if isinstance(parsed, dict) else None
            if not isinstance(terraform_blocks, list):
                continue
            for terraform_block in terraform_blocks:
                if not isinstance(terraform_block, dict) or "backend" not in terraform_block:
                    continue
                violations.append(
                    f"{relative_path} contains backend configuration outside the approved partial backend path"
                )
                backend_blocks = terraform_block.get("backend")
                if not isinstance(backend_blocks, list):
                    continue
                for backend_block in backend_blocks:
                    if not isinstance(backend_block, dict):
                        continue
                    for backend_type, backend_values in backend_block.items():
                        if backend_type != "gcs" or not isinstance(backend_values, dict):
                            continue
                        for token in forbidden_backend_value_tokens:
                            if token in backend_values:
                                violations.append(
                                    f"{relative_path} contains committed backend value {token!r}"
                                )

    return violations


def _collect_bootstrap_state_bucket_violations(
    root: Path, terraform_config_paths: list[Path]
) -> list[str]:
    violations: list[str] = []
    allowed_state_bucket_path = Path("infra/gcp/bootstrap/state.tf")
    required_control_patterns = [
        (r"uniform_bucket_level_access\s*=\s*true", "uniform_bucket_level_access = true"),
        (r'public_access_prevention\s*=\s*"enforced"', 'public_access_prevention = "enforced"'),
        (r"versioning\s*\{", "versioning {"),
        (r"enabled\s*=\s*true", "enabled = true"),
        (r"force_destroy\s*=\s*false", "force_destroy = false"),
        (r"retention_policy\s*\{", "retention_policy {"),
        (r"prevent_destroy\s*=\s*true", "prevent_destroy = true"),
    ]

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        resource_occurrences, _ = _collect_declared_terraform_resource_types([path])
        resource_types = [
            resource_type
            for candidate_path, resource_type in resource_occurrences
            if candidate_path == path
        ]
        if "google_storage_bucket" not in resource_types:
            continue

        if relative_path != allowed_state_bucket_path:
            violations.append(
                f"{relative_path} contains forbidden google_storage_bucket outside the approved bootstrap state root"
            )
            continue

        text = path.read_text(encoding="utf-8")
        missing_controls = [
            label
            for pattern, label in required_control_patterns
            if re.search(pattern, text) is None
        ]
        if missing_controls:
            violations.append(
                f"{relative_path} contains bootstrap state bucket missing required controls: {', '.join(missing_controls)}"
            )

    return violations


def _collect_bootstrap_boundary_violations(
    root: Path, terraform_config_paths: list[Path]
) -> list[str]:
    violations: list[str] = []
    bootstrap_root = Path("infra/gcp/bootstrap")
    bootstrap_state_bucket_declared = any(
        path.relative_to(root) == bootstrap_root / "state.tf"
        and "google_storage_bucket" in path.read_text(encoding="utf-8")
        for path in terraform_config_paths
    )

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        if bootstrap_root not in relative_path.parents:
            continue

        text = path.read_text(encoding="utf-8")
        if "module.develop" in text or "../develop" in text:
            violations.append(
                f"{relative_path} contains bootstrap root references disposable workload 'module.develop'"
            )

        resource_occurrences, _ = _collect_declared_terraform_resource_types([path])
        resource_types = [
            resource_type
            for candidate_path, resource_type in resource_occurrences
            if candidate_path == path
        ]
        for forbidden_type in [
            "google_storage_bucket_iam_binding",
            "google_storage_bucket_iam_policy",
            "google_project_iam_binding",
            "google_project_iam_member",
            "google_project_iam_policy",
        ]:
            if forbidden_type in resource_types:
                violations.append(
                    f"{relative_path} contains unbounded bootstrap authority {forbidden_type!r}"
                )

        if relative_path == bootstrap_root / "iam.tf" and bootstrap_state_bucket_declared:
            required_fragments = [
                'resource "google_storage_bucket_iam_member" "state_authority_object_admin"',
                'resource "google_storage_bucket_iam_member" "recovery_authority_object_admin"',
                'resource "google_storage_bucket_iam_member" "bootstrap_operator_object_admin"',
                'count  = var.bootstrap_operator_status == "bootstrap-active" ? 1 : 0',
                'role   = "roles/storage.objectAdmin"',
                "member = var.state_authority_principal",
                "member = var.recovery_authority_principal",
                "member = var.bootstrap_operator_principal",
            ]
            for fragment in required_fragments:
                if fragment not in text:
                    violations.append(
                        f"{relative_path} missing reviewed state-bucket IAM fragment {fragment!r}"
                    )
            state_iam_contracts = {
                "state_authority_object_admin": {
                    "bucket": "google_storage_bucket.terraform_state.name",
                    "role": "roles/storage.objectAdmin",
                    "member": "var.state_authority_principal",
                    "count": None,
                },
                "recovery_authority_object_admin": {
                    "bucket": "google_storage_bucket.terraform_state.name",
                    "role": "roles/storage.objectAdmin",
                    "member": "var.recovery_authority_principal",
                    "count": None,
                },
                "bootstrap_operator_object_admin": {
                    "bucket": "google_storage_bucket.terraform_state.name",
                    "role": "roles/storage.objectAdmin",
                    "member": "var.bootstrap_operator_principal",
                    "count": 'var.bootstrap_operator_status == "bootstrap-active" ? 1 : 0',
                },
            }
            resource_pattern = re.compile(
                r'resource\s+"google_storage_bucket_iam_member"\s+"(?P<name>[^"]+)"\s*\{(?P<body>.*?)^\}',
                re.MULTILINE | re.DOTALL,
            )
            observed_resource_names: set[str] = set()
            for match in resource_pattern.finditer(text):
                resource_name = match.group("name")
                body = match.group("body")
                observed_resource_names.add(resource_name)
                expected = state_iam_contracts.get(resource_name)
                if expected is None:
                    violations.append(
                        f"{relative_path} contains unreviewed state-bucket IAM resource {resource_name!r}"
                    )
                    continue
                for attribute in ("bucket", "role", "member"):
                    expected_value = expected[attribute]
                    if not re.search(
                        rf"^\s*{attribute}\s*=\s*(?:\"{re.escape(str(expected_value))}\"|{re.escape(str(expected_value))})\s*$",
                        body,
                        re.MULTILINE,
                    ):
                        violations.append(
                            f"{relative_path} state-bucket IAM resource {resource_name!r} "
                            f"must bind {attribute} to {expected_value!r}"
                        )
                expected_count = expected["count"]
                if expected_count is None:
                    if re.search(r"^\s*count\s*=", body, re.MULTILINE):
                        violations.append(
                            f"{relative_path} state-bucket IAM resource {resource_name!r} must not have count"
                        )
                elif not re.search(
                    rf"^\s*count\s*=\s*{re.escape(str(expected_count))}\s*$",
                    body,
                    re.MULTILINE,
                ):
                    violations.append(
                        f"{relative_path} state-bucket IAM resource {resource_name!r} "
                        "must retain its reviewed active-only count"
                    )
            if observed_resource_names != set(state_iam_contracts):
                violations.append(
                    f"{relative_path} state-bucket IAM resource inventory drifted from reviewed authority boundary"
                )

            forbidden_fragments = [
                'role   = "roles/storage.admin"',
                'role   = "roles/storage.objectCreator"',
                'role   = "roles/storage.objectViewer"',
                "allUsers",
                "allAuthenticatedUsers",
            ]
            for fragment in forbidden_fragments:
                if fragment in text:
                    violations.append(
                        f"{relative_path} contains forbidden state-bucket IAM fragment {fragment!r}"
                    )

    return violations


def _collect_bootstrap_wif_violations(root: Path) -> list[str]:
    violations: list[str] = []
    wif_path = root / "infra" / "gcp" / "bootstrap" / "wif.tf"
    iam_path = root / "infra" / "gcp" / "bootstrap" / "iam.tf"

    if wif_path.exists():
        wif_text = wif_path.read_text(encoding="utf-8")
        required_claims = [
            'attribute.repository == "b-mackenzie-alexander/golden_rose_project"',
            'attribute.repository_owner == "b-mackenzie-alexander"',
            'attribute.ref == "refs/heads/develop"',
            'attribute.environment == "develop"',
            'attribute.event_name == "workflow_dispatch"',
            '"attribute.workflow_ref"     = "assertion.workflow_ref"',
            'attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop"',
            'attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop"',
        ]
        for claim in required_claims:
            if claim not in wif_text:
                violations.append(
                    f"{wif_path.relative_to(root)} missing exact GitHub claim {claim!r}"
                )

        wildcard_claim_patterns = [
            (r'attribute\.repository\s*==\s*"[^"]*\*[^"]*"', "attribute.repository"),
            (r'attribute\.repository_owner\s*==\s*"[^"]*\*[^"]*"', "attribute.repository_owner"),
            (r'attribute\.ref\s*==\s*"[^"]*\*[^"]*"', "attribute.ref"),
            (r'attribute\.environment\s*==\s*"[^"]*\*[^"]*"', "attribute.environment"),
            (r'attribute\.workflow_ref\s*==\s*"[^"]*\*[^"]*"', "attribute.workflow_ref"),
        ]
        for pattern, attribute_name in wildcard_claim_patterns:
            if re.search(pattern, wif_text):
                violations.append(
                    f"{wif_path.relative_to(root)} contains wildcard GitHub claim {attribute_name}"
                )
        if 'attribute.event_name != "pull_request"' in wif_text:
            violations.append(
                f"{wif_path.relative_to(root)} must require workflow_dispatch rather than only rejecting pull_request"
            )

    if iam_path.exists():
        iam_text = iam_path.read_text(encoding="utf-8")
        if "attribute.repository_owner/" in iam_text:
            violations.append(
                f"{iam_path.relative_to(root)} contains principal-set broadening via attribute.repository_owner"
            )
        if "/attribute.repository/" in iam_text:
            violations.append(
                f"{iam_path.relative_to(root)} contains repository-only impersonation authority instead of exact workflow_ref trust"
            )
        broad_principal_patterns = [
            r'principalSet://[^"]*/attribute\.repository/[^"\n]*\*',
            r'principalSet://[^"]*/attribute\.ref/[^"\n]*\*',
            r'principalSet://[^"]*/attribute\.environment/[^"\n]*\*',
        ]
        for pattern in broad_principal_patterns:
            if re.search(pattern, iam_text):
                violations.append(f"{iam_path.relative_to(root)} contains principal-set broadening")
        required_fragments = [
            'resource "google_service_account_iam_member" "image_publisher_wif"',
            'resource "google_service_account_iam_member" "deployer_wif"',
            "member             = local.build_image_workflow_principal_set",
            "member             = local.deploy_develop_workflow_principal_set",
        ]
        for fragment in required_fragments:
            if fragment not in iam_text:
                violations.append(
                    f"{iam_path.relative_to(root)} missing exact bootstrap WIF authority fragment {fragment!r}"
                )
        forbidden_fragments = [
            'resource "google_service_account_iam_member" "provisioner_wif"',
            'resource "google_service_account_iam_member" "provisioner_token_creator"',
            'resource "google_service_account_iam_member" "image_publisher_token_creator"',
            'resource "google_service_account_iam_member" "deployer_token_creator"',
            "roles/iam.serviceAccountTokenCreator",
            "local.github_principal_set",
        ]
        for fragment in forbidden_fragments:
            if fragment in iam_text:
                violations.append(
                    f"{iam_path.relative_to(root)} contains forbidden bootstrap WIF fragment {fragment!r}"
                )

    return violations


def _collect_develop_iam_violations(root: Path, terraform_config_paths: list[Path]) -> list[str]:
    violations: list[str] = []
    allowed_iam_path = Path("infra/gcp/develop/iam.tf")
    allowed_bootstrap_iam_path = Path("infra/gcp/bootstrap/iam.tf")
    allowed_observability_path = Path("infra/gcp/develop/observability.tf")
    managed_iam_resource_prefixes = [
        "google_project_iam_",
        "google_secret_manager_secret_iam_",
        "google_artifact_registry_repository_iam_",
        "google_cloud_run_v2_service_iam_",
        "google_service_account_iam_",
        "google_storage_bucket_iam_",
    ]

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        resource_occurrences, _ = _collect_declared_terraform_resource_types([path])
        resource_types = [
            resource_type
            for candidate_path, resource_type in resource_occurrences
            if candidate_path == path
        ]

        for resource_type in resource_types:
            if not any(
                resource_type.startswith(prefix) for prefix in managed_iam_resource_prefixes
            ):
                continue
            if relative_path not in {
                allowed_iam_path,
                allowed_bootstrap_iam_path,
                allowed_observability_path,
            }:
                violations.append(
                    f"{relative_path} contains forbidden {resource_type!r} outside the approved develop IAM path"
                )
                if "roles/run.invoker" in text:
                    violations.append(f"{relative_path} contains forbidden 'roles/run.invoker'")

        if relative_path != allowed_iam_path:
            continue

        forbidden_broad_types = [
            "google_project_iam_binding",
            "google_project_iam_policy",
            "google_secret_manager_secret_iam_binding",
            "google_secret_manager_secret_iam_policy",
            "google_artifact_registry_repository_iam_binding",
            "google_artifact_registry_repository_iam_policy",
            "google_cloud_run_v2_service_iam_binding",
            "google_cloud_run_v2_service_iam_policy",
            "google_service_account_iam_binding",
            "google_service_account_iam_policy",
        ]
        for forbidden_type in forbidden_broad_types:
            if forbidden_type in resource_types:
                violations.append(
                    f"{relative_path} contains forbidden broad IAM construct {forbidden_type!r}"
                )

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
            'resource "google_artifact_registry_repository_iam_member" "image_publisher_writer"',
            'resource "google_cloud_run_v2_service_iam_member" "private_invoker"',
            'role    = "roles/cloudsql.client"',
            'role    = "roles/logging.logWriter"',
            'role    = "roles/monitoring.metricWriter"',
            'role     = "roles/run.jobsExecutor"',
            'role     = "roles/run.viewer"',
            'role      = "roles/secretmanager.secretAccessor"',
            'role       = "roles/artifactregistry.writer"',
            'role     = "roles/run.invoker"',
            'member  = "serviceAccount:${google_service_account.runtime.email}"',
            'member  = "serviceAccount:${google_service_account.migration.email}"',
            'member     = "serviceAccount:golden-rose-image-publisher@${var.control_plane_project_id}.iam.gserviceaccount.com"',
            'member   = "serviceAccount:golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com"',
            'data "external" "tester_authority"',
            "verify_tester_authority_receipt.py",
            "data.external.tester_authority[0].result.private_invoker_principal",
            "data.external.tester_authority[0].result.tester_authority_receipt_sha256",
        ]
        for fragment in required_fragments:
            if fragment not in text:
                violations.append(
                    f"{relative_path} missing required least-privilege IAM fragment {fragment!r}"
                )

        migration_job_iam_count = 'count    = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0'
        for resource_name in ["deployer_jobs_executor", "deployer_migration_job_viewer"]:
            resource_marker = f'resource "google_cloud_run_v2_job_iam_member" "{resource_name}"'
            if resource_marker not in text:
                violations.append(
                    f"{relative_path} missing required migration job IAM member {resource_name!r}"
                )
                continue
            resource_text = text.split(resource_marker, 1)[1].split("\n}\n", 1)[0]
            if not _contains_normalized_fragment(resource_text, migration_job_iam_count):
                violations.append(
                    f"{relative_path} missing migration/service count on job IAM member {resource_name!r}"
                )
            if "google_cloud_run_v2_job.migration[0].name" not in resource_text:
                violations.append(
                    f"{relative_path} missing migration job target on IAM member {resource_name!r}"
                )

        forbidden_fragments = [
            "roles/viewer",
            "roles/secretmanager.admin",
            "roles/artifactregistry.admin",
            "roles/run.admin",
            "roles/run.developer",
            "roles/run.jobsExecutorWithOverrides",
            "roles/iam.serviceAccountUser",
            "roles/iam.serviceAccountTokenCreator",
            'resource "google_service_account_iam_member" "deployer_runtime_user"',
            'resource "google_service_account_iam_member" "deployer_migration_user"',
            'resource "google_project_iam_member" "deployer_jobs_executor"',
            'resource "google_project_iam_member" "deployer_run_viewer"',
            "var.deployer_principal",
        ]
        for fragment in forbidden_fragments:
            if fragment in text:
                violations.append(f"{relative_path} contains forbidden broad IAM role {fragment!r}")

    return violations


def _collect_migration_job_violations(root: Path, terraform_config_paths: list[Path]) -> list[str]:
    violations: list[str] = []
    allowed_job_path = Path("infra/gcp/develop/migration_job.tf")

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        resource_occurrences, _ = _collect_declared_terraform_resource_types([path])
        resource_types = [
            resource_type
            for candidate_path, resource_type in resource_occurrences
            if candidate_path == path
        ]

        if "google_cloud_run_v2_job" not in resource_types:
            continue

        if relative_path != allowed_job_path:
            violations.append(
                f"{relative_path} contains forbidden 'google_cloud_run_v2_job' outside the approved migration job path"
            )
            continue

        required_fragments = [
            'resource "google_cloud_run_v2_job" "migration"',
            'name     = "run-migrations"',
            "service_account = google_service_account.migration.email",
            "image = local.managed_container_image",
            'command = ["golden-rose-migrate"]',
            "max_retries = 0",
            "task_count  = 1",
            "parallelism = 1",
            "subnetwork = google_compute_subnetwork.direct_vpc.id",
            'egress = "PRIVATE_RANGES_ONLY"',
        ]
        for fragment in required_fragments:
            if not _contains_normalized_fragment(text, fragment):
                violations.append(
                    f"{relative_path} missing required migration job fragment {fragment!r}"
                )

        forbidden_fragments = [
            "google_service_account.runtime.email",
            "INGRESS_TRAFFIC_ALL",
            ":latest",
        ]
        for fragment in forbidden_fragments:
            if fragment in text:
                violations.append(
                    f"{relative_path} contains forbidden migration job fragment {fragment!r}"
                )

    return violations


def _collect_budget_observability_violations(
    root: Path, terraform_config_paths: list[Path]
) -> list[str]:
    violations: list[str] = []
    allowed_budget_path = Path("infra/gcp/develop/budgets.tf")
    allowed_observability_path = Path("infra/gcp/develop/observability.tf")
    budget_resource_types = {"google_billing_budget"}
    observability_resource_types = {
        "google_logging_metric",
        "google_logging_project_exclusion",
        "google_logging_project_bucket_config",
        "google_monitoring_alert_policy",
        "google_monitoring_notification_channel",
        "google_monitoring_uptime_check_config",
    }

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        resource_occurrences, _ = _collect_declared_terraform_resource_types([path])
        resource_types = {
            resource_type
            for candidate_path, resource_type in resource_occurrences
            if candidate_path == path
        }

        if budget_resource_types & resource_types and relative_path != allowed_budget_path:
            violations.append(
                f"{relative_path} contains forbidden 'google_billing_budget' outside the approved budgets path"
            )

        if (
            observability_resource_types & resource_types
            and relative_path != allowed_observability_path
        ):
            observed = sorted(observability_resource_types & resource_types)[0]
            violations.append(
                f"{relative_path} contains forbidden {observed!r} outside the approved observability path"
            )

        if relative_path == allowed_budget_path:
            required_fragments = [
                'resource "google_billing_budget" "develop"',
                "billing_account = var.billing_account_id",
                'projects = ["projects/${var.project_id}"]',
                "google_monitoring_notification_channel.alerts.name",
                "disable_default_iam_recipients = true",
                "threshold_percent = 0.5",
                "threshold_percent = 0.75",
                "threshold_percent = 1.0",
            ]
            for fragment in required_fragments:
                if not _contains_normalized_fragment(text, fragment):
                    violations.append(
                        f"{relative_path} missing required budget contract fragment {fragment!r}"
                    )

            for forbidden_fragment in ["pubsub_topic", "pubsubTopic"]:
                if forbidden_fragment in text:
                    violations.append(
                        f"{relative_path} contains forbidden budget routing fragment {forbidden_fragment!r}"
                    )

        if relative_path == allowed_observability_path:
            required_fragments = [
                'resource "google_monitoring_notification_channel" "alerts"',
                'resource "google_logging_project_exclusion" "uuid_bearing_staff_paths"',
                'resource "google_cloud_run_v2_service_iam_member" "monitoring_readiness_invoker"',
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
                "service-${data.google_project.current.number}@gcp-sa-monitoring-notification.iam.gserviceaccount.com",
                'path         = "/readiness"',
                'type = "OIDC_TOKEN"',
                "google_monitoring_uptime_check_config.readiness[0].uptime_check_id",
            ]
            for fragment in required_fragments:
                if not _contains_normalized_fragment(text, fragment):
                    violations.append(
                        f"{relative_path} missing required observability contract fragment {fragment!r}"
                    )

            for forbidden_fragment in [
                'resource "google_logging_project_sink"',
                "request.body",
                "requestBody",
                "jsonPayload",
                "textPayload",
                "allUsers",
                "allAuthenticatedUsers",
                "untested RTO",
                "untested RPO",
                "approved SLO",
                'resource "google_logging_metric" "readiness_failure_count"',
            ]:
                if forbidden_fragment in text:
                    violations.append(
                        f"{relative_path} contains forbidden observability fragment {forbidden_fragment!r}"
                    )

    return violations


def _collect_api_contract_violations(root: Path) -> list[str]:
    violations: list[str] = []
    apis_path = root / "infra" / "gcp" / "develop" / "apis.tf"
    budgets_path = root / "infra" / "gcp" / "develop" / "budgets.tf"

    if apis_path.exists():
        apis_text = apis_path.read_text(encoding="utf-8")
        required_services = [
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
        for service in required_services:
            if service not in apis_text:
                violations.append(f"{apis_path.relative_to(root)} missing approved API {service!r}")

    if budgets_path.exists():
        budgets_text = budgets_path.read_text(encoding="utf-8")
        dependency_fragment = 'google_project_service.approved["billingbudgets.googleapis.com"]'
        if dependency_fragment not in budgets_text:
            violations.append(
                f"{budgets_path.relative_to(root)} missing explicit Budget API dependency {dependency_fragment!r}"
            )

    return violations


def _collect_evidence_template_violations(root: Path) -> list[str]:
    violations: list[str] = []
    template_path = root / "deploy" / "gcp" / "evidence-template.md"
    if not template_path.exists():
        return violations

    template = template_path.read_text(encoding="utf-8")
    required_fragments = [
        "foundation, migration, or service",
        "notification-channel resource names",
        "display names",
        "signature, provenance, image SBOM, and application SBOM attestation",
        "Do not claim publication or attestation verification occurred",
        "provisional develop review triggers",
        "not SLOs or client commitments",
    ]
    for fragment in required_fragments:
        if fragment not in template:
            violations.append(
                f"{template_path.relative_to(root)} missing required Task 6 evidence fragment {fragment!r}"
            )

    return violations


def _collect_cloud_run_contract_violations(root: Path) -> list[str]:
    violations: list[str] = []
    cloud_run_path = root / "infra" / "gcp" / "develop" / "cloud_run.tf"
    if not cloud_run_path.exists():
        return violations

    cloud_run = cloud_run_path.read_text(encoding="utf-8")
    required_fragments = [
        'resource "google_cloud_run_v2_service" "staff_tracer"',
        'ingress             = "INGRESS_TRAFFIC_ALL"',
        'value = "gcp-develop-private-synthetic"',
    ]
    for fragment in required_fragments:
        if fragment not in cloud_run:
            violations.append(
                f"{cloud_run_path.relative_to(root)} missing required cloud run contract fragment {fragment!r}"
            )

    forbidden_fragments = [
        "INGRESS_TRAFFIC_INTERNAL_ONLY",
        "allUsers",
        "allAuthenticatedUsers",
    ]
    for fragment in forbidden_fragments:
        if fragment in cloud_run:
            violations.append(
                f"{cloud_run_path.relative_to(root)} contains forbidden cloud run fragment {fragment!r}"
            )

    return violations


# ---------------------------------------------------------------------------
# Task 1: Staged authority model — stage-contract enforcement
# ---------------------------------------------------------------------------

# Resource types that are executable workloads and must be stage-gated.
STAGE_OWNERSHIP_RESOURCE_TYPES = {
    "google_cloud_run_v2_service",
    "google_cloud_run_v2_job",
}

# Expected stage ownership for each executable workload resource type.
# The manifest must declare exactly this ownership; a wrong value is rejected.
EXPECTED_STAGE_OWNERSHIP: dict[str, str] = {
    "google_cloud_run_v2_service": "service",
    "google_cloud_run_v2_job": "migration",
}

# Approved count-expression patterns for stage-gated executable resources.
# Each entry maps a resource type to a list of regex patterns that match
# approved count expressions referencing var.deployment_stage.
APPROVED_STAGE_COUNT_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "google_cloud_run_v2_service": [
        re.compile(r'count\s*=\s*var\.deployment_stage\s*==\s*"service"\s*\?\s*1\s*:\s*0'),
    ],
    "google_cloud_run_v2_job": [
        re.compile(
            r'count\s*=\s*var\.deployment_stage\s*==\s*"migration"\s*\|\|\s*var\.deployment_stage\s*==\s*"service"\s*\?\s*1\s*:\s*0'
        ),
        re.compile(r'count\s*=\s*var\.deployment_stage\s*==\s*"migration"\s*\?\s*1\s*:\s*0'),
        re.compile(r'count\s*=\s*var\.deployment_stage\s*!=\s*"foundation"\s*\?\s*1\s*:\s*0'),
    ],
}

# Regex to extract the count expression from a resource block.
_COUNT_PATTERN = re.compile(
    r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{(?P<body>.*?)^\}',
    re.MULTILINE | re.DOTALL,
)


def _extract_resource_count_expressions(
    text: str,
) -> list[tuple[str, str, str | None]]:
    """Extract (resource_type, resource_name, count_expression) from HCL text.

    Returns None for count_expression if the resource has no count meta-argument.
    """
    results: list[tuple[str, str, str | None]] = []
    for match in _COUNT_PATTERN.finditer(text):
        resource_type = match.group(1)
        resource_name = match.group(2)
        body = match.group("body")
        count_match = re.search(r"^\s*count\s*=\s*(.+?)$", body, re.MULTILINE)
        count_expr = count_match.group(1).strip() if count_match else None
        results.append((resource_type, resource_name, count_expr))
    return results


def _evaluate_count_stages(count_expr: str) -> set[str]:
    """Evaluate which deployment stages a count expression includes.

    Returns the set of stages where the resource would have count > 0.
    Handles the approved patterns:
      - var.deployment_stage == "X" ? 1 : 0  → includes X
      - var.deployment_stage == "X" || var.deployment_stage == "Y" ? 1 : 0  → includes X, Y
      - var.deployment_stage != "X" ? 1 : 0  → includes all stages except X
      - var.deployment_stage != "foundation" ? 1 : 0  → includes migration, service
    """
    stages: set[str] = set()

    # Match: var.deployment_stage == "X" (positive equality)
    for m in re.finditer(r'var\.deployment_stage\s*==\s*"([^"]+)"', count_expr):
        stages.add(m.group(1))

    # Match: var.deployment_stage != "X" (negative equality — includes all except X)
    negative_matches = re.findall(r'var\.deployment_stage\s*!=\s*"([^"]+)"', count_expr)
    if negative_matches:
        excluded = set(negative_matches)
        stages.update(stage for stage in APPROVED_STAGE_VALUES if stage not in excluded)

    # If no stages matched but the expression doesn't reference deployment_stage,
    # the resource is unconditional (exists in all stages)
    if not stages and "deployment_stage" not in count_expr:
        stages.update(APPROVED_STAGE_VALUES)

    return stages


def _collect_stage_contract_violations(
    root: Path,
    terraform_config_paths: list[Path],
    manifest: dict[object, object] | None,
) -> list[str]:
    """Collect stage-contract violations for executable workload resources.

    Checks:
    1. Executable resources must have stage_ownership in the manifest.
    2. Executable resources must be stage-gated (have a count referencing var.deployment_stage).
    3. The count expression must not include foundation stage for any executable resource.
    4. The count expression must not include a stage outside the resource's stage_ownership.
    5. Boolean workload_enabled shortcuts must be rejected.
    """
    violations: list[str] = []

    # Extract stage_ownership from manifest
    stage_ownership: dict[str, str] = {}
    if manifest is not None:
        terraform_contract = manifest.get("terraform")
        resource_contracts = (
            terraform_contract.get("resource_types")
            if isinstance(terraform_contract, dict)
            else None
        )
        if isinstance(resource_contracts, dict):
            for rt, contract in resource_contracts.items():
                if not isinstance(contract, dict):
                    continue
                ownership = contract.get("stage_ownership")
                if isinstance(ownership, str):
                    stage_ownership[str(rt)] = ownership

    develop_vars_path = root / "infra" / "gcp" / "develop" / "variables.tf"

    # Check for workload_enabled boolean shortcut
    if develop_vars_path.exists():
        develop_vars_text = develop_vars_path.read_text(encoding="utf-8")
        if 'variable "workload_enabled"' in develop_vars_text:
            violations.append(
                "infra/gcp/develop/variables.tf contains forbidden boolean "
                "'workload_enabled' shortcut; use deployment_stage instead"
            )

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")

        # Extract count expressions for all resources
        resource_counts = _extract_resource_count_expressions(text)

        for resource_type, resource_name, count_expr in resource_counts:
            if resource_type not in STAGE_OWNERSHIP_RESOURCE_TYPES:
                continue

            # Check 1: stage_ownership must be declared in manifest
            if resource_type not in stage_ownership:
                violations.append(
                    f"{relative_path} contains executable workload resource "
                    f"{resource_type!r} without stage_ownership declared in manifest"
                )
                continue

            expected_stage = stage_ownership[resource_type]

            # Check 1b: stage_ownership must match the expected value for this resource type
            expected_manifest_stage = EXPECTED_STAGE_OWNERSHIP.get(resource_type)
            if expected_manifest_stage is not None and expected_stage != expected_manifest_stage:
                violations.append(
                    f"{relative_path} executable workload resource {resource_type!r} "
                    f"stage_ownership is {expected_stage!r} but must be "
                    f"{expected_manifest_stage!r}"
                )

            # Check 2: must be stage-gated (have count referencing deployment_stage)
            if count_expr is None:
                violations.append(
                    f"{relative_path} contains unconditional executable workload resource "
                    f"{resource_type} {resource_name!r}; must use count = var.deployment_stage ..."
                )
                continue

            if "deployment_stage" not in count_expr:
                # Check for boolean workload_enabled shortcut
                if "workload_enabled" in count_expr:
                    violations.append(
                        f"{relative_path} contains forbidden boolean workload shortcut "
                        f"for {resource_type} {resource_name!r}; use deployment_stage instead"
                    )
                else:
                    violations.append(
                        f"{relative_path} contains unconditional executable workload resource "
                        f"{resource_type} {resource_name!r}; count must reference var.deployment_stage"
                    )
                continue

            # Check 3: evaluate which stages the count expression includes
            evaluated_stages = _evaluate_count_stages(count_expr)

            if "foundation" in evaluated_stages:
                violations.append(
                    f"{relative_path} executable workload resource {resource_type} "
                    f"{resource_name!r} count expression includes foundation stage; "
                    f"foundation must not create any executable workload"
                )

            # Check 4: count must not include stages outside the resource's stage_ownership
            # For service-owned resources, migration stage must not be included
            # For migration-owned resources, service stage inclusion is allowed (migration+service)
            if expected_stage == "service" and "migration" in evaluated_stages:
                violations.append(
                    f"{relative_path} executable workload resource {resource_type} "
                    f"{resource_name!r} stage_ownership is 'service' but count expression "
                    f"includes migration stage"
                )

    return violations


def _collect_env_secret_violations(root: Path, terraform_config_paths: list[Path]) -> list[str]:
    """Collect env/secret-reference violations in Cloud Run service/job containers.

    Checks:
    1. All env names must be in the approved allowlist.
    2. Secret env names must use value_source/secret_ref, not literal value.
    3. Secret reference names must be in the approved set.
    4. Runtime service must use runtime-database-url, not migration-database-url.
    5. Migration job must use migration-database-url, not runtime-database-url.
    6. Migration-only env names must not appear in service containers.
    7. Literal secret values are forbidden.
    """
    violations: list[str] = []

    # Regex to extract env blocks from HCL resource containers
    env_block_pattern = re.compile(
        r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{(?P<body>.*?)^\}',
        re.MULTILINE | re.DOTALL,
    )

    for path in sorted(terraform_config_paths):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")

        for match in env_block_pattern.finditer(text):
            resource_type = match.group(1)
            resource_name = match.group(2)
            body = match.group("body")

            if resource_type not in STAGE_OWNERSHIP_RESOURCE_TYPES:
                continue

            # Find all env blocks: env { name = "..." ... }
            env_blocks = re.findall(
                r"env\s*\{(.*?)(?=^\s*env\s*\{|^\s*\}\s*$|\Z)",
                body,
                re.MULTILINE | re.DOTALL,
            )

            for env_block in env_blocks:
                name_match = re.search(r'name\s*=\s*"([^"]+)"', env_block)
                if name_match is None:
                    continue
                env_name = name_match.group(1)

                # Check 1: env name must be in the approved allowlist
                if env_name not in APPROVED_ENV_NAMES:
                    violations.append(
                        f"{relative_path} contains unlisted env name {env_name!r} "
                        f"in {resource_type} {resource_name!r}"
                    )
                    continue

                # Check 6: migration-only env must not appear in service
                if (
                    resource_type == "google_cloud_run_v2_service"
                    and env_name in MIGRATION_ONLY_ENV_NAMES
                ):
                    violations.append(
                        f"{relative_path} contains migration-only env {env_name!r} "
                        f"in service {resource_name!r}"
                    )

                # Check 2: secret env names must use value_source/secret_key_ref
                has_value = re.search(r'value\s*=\s*"', env_block)
                has_secret_ref = "secret_key_ref" in env_block or "value_source" in env_block

                if env_name in SECRET_ENV_NAMES:
                    if has_value and not has_secret_ref:
                        violations.append(
                            f"{relative_path} env {env_name!r} in {resource_type} "
                            f"{resource_name!r} uses literal value instead of secret_key_ref; "
                            f"literal secret values are forbidden"
                        )
                        continue

                    if has_secret_ref:
                        secret_name_match = re.search(
                            r'secret_key_ref\s*\{\s*secret\s*=\s*"([^"]+)"', env_block
                        )
                        if secret_name_match is None:
                            continue
                        secret_name = secret_name_match.group(1)

                        # Check 3: secret reference must be in approved set
                        approved_refs = APPROVED_SECRET_REFS.get(env_name, set())
                        if secret_name not in approved_refs:
                            violations.append(
                                f"{relative_path} env {env_name!r} references "
                                f"unapproved secret {secret_name!r}"
                            )

                        # Check 4 & 5: cross-wiring check for DATABASE_URL
                        if env_name == "GOLDEN_ROSE_DATABASE_URL":
                            expected_secret = RESOURCE_DB_SECRET_MAP.get(resource_type)
                            if expected_secret and secret_name != expected_secret:
                                violations.append(
                                    f"{relative_path} env {env_name!r} in "
                                    f"{resource_type} {resource_name!r} is cross-wired "
                                    f"to secret {secret_name!r}; expected "
                                    f"{expected_secret!r}"
                                )
                else:
                    # Non-secret env: value is allowed but check for literal
                    # secret values in non-secret env names
                    if has_value:
                        value_match = re.search(r'value\s*=\s*"([^"]*)"', env_block)
                        if value_match:
                            value = value_match.group(1)
                            if any(
                                keyword in value.lower()
                                for keyword in ["password", "secret", "token", "postgresql://"]
                            ):
                                violations.append(
                                    f"{relative_path} env {env_name!r} in "
                                    f"{resource_type} {resource_name!r} contains "
                                    f"literal secret value"
                                )

    return violations


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()
    terraform_root = root / "infra" / "gcp"
    required_files = [root / path.relative_to(ROOT) for path in REQUIRED_FILES]
    terraform_config_paths = [
        *terraform_root.rglob("*.tf"),
        *terraform_root.rglob("*.tf.json"),
    ]

    violations: list[str] = []
    try:
        manifest = _load_predeployment_authority_manifest(root)
    except ValueError as exc:
        violations.append(str(exc))
        manifest = None

    if manifest is not None:
        violations.extend(_collect_manifest_workflow_contract_violations(root, manifest))
        terraform_contract = manifest.get("terraform")
        resource_contracts = (
            terraform_contract.get("resource_types")
            if isinstance(terraform_contract, dict)
            else None
        )
        if isinstance(resource_contracts, dict):
            resource_occurrences, resource_counts, unresolved_expansions = (
                _collect_declared_terraform_resource_expansions(terraform_config_paths)
            )
            for path, resource_type in resource_occurrences:
                if resource_type not in resource_contracts:
                    violations.append(
                        f"{path.relative_to(root)} contains unlisted Terraform resource type {resource_type!r}"
                    )
            for path, resource_type, expansion_kind, expansion_expr in unresolved_expansions:
                if resource_type not in resource_contracts:
                    continue
                if expansion_kind == "count":
                    violations.append(
                        f"{path.relative_to(root)} contains unbounded or unreviewed count expression for allowed resource type {resource_type!r}: {expansion_expr}"
                    )
                elif expansion_kind == "for_each":
                    violations.append(
                        f"{path.relative_to(root)} contains unbounded or unreviewed for_each expression for allowed resource type {resource_type!r}: {expansion_expr}"
                    )
                else:
                    violations.append(
                        f"{path.relative_to(root)} contains invalid combined count/for_each expansion for allowed resource type {resource_type!r}"
                    )
            for resource_type, count in sorted(resource_counts.items()):
                if resource_type not in resource_contracts:
                    continue
                contract = resource_contracts.get(resource_type)
                max_count = contract.get("max_count") if isinstance(contract, dict) else None
                max_count_by_stage = (
                    contract.get("max_count_by_stage") if isinstance(contract, dict) else None
                )
                if isinstance(max_count_by_stage, dict) and max_count_by_stage:
                    stage_max = max(max_count_by_stage.values())
                    if isinstance(stage_max, int):
                        max_count = stage_max
                if isinstance(max_count, int) and count > max_count:
                    violations.append(
                        "predeployment authority manifest exceeded Terraform resource type "
                        f"cardinality {resource_type!r}: {count} > {max_count}"
                    )

    for pattern in FORBIDDEN_ARTIFACT_PATTERNS:
        for path in sorted(terraform_root.rglob(pattern)):
            violations.append(f"{path.relative_to(root)} is a forbidden Terraform artifact")

    violations.extend(_collect_backend_configuration_violations(root, terraform_config_paths))
    violations.extend(_collect_bootstrap_state_bucket_violations(root, terraform_config_paths))
    violations.extend(_collect_bootstrap_boundary_violations(root, terraform_config_paths))
    violations.extend(_collect_bootstrap_wif_violations(root))
    violations.extend(_collect_develop_iam_violations(root, terraform_config_paths))
    violations.extend(_collect_migration_job_violations(root, terraform_config_paths))
    violations.extend(_collect_budget_observability_violations(root, terraform_config_paths))
    violations.extend(_collect_api_contract_violations(root))
    violations.extend(_collect_cloud_run_contract_violations(root))
    violations.extend(_collect_evidence_template_violations(root))
    violations.extend(_collect_stage_contract_violations(root, terraform_config_paths, manifest))
    violations.extend(_collect_env_secret_violations(root, terraform_config_paths))

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
    workflow_files_contract: dict[object, object] | None = None
    if manifest is not None:
        workflows_contract = manifest.get("workflows")
        workflow_files_contract = (
            workflows_contract.get("files") if isinstance(workflows_contract, dict) else None
        )
        if isinstance(workflow_files_contract, dict):
            for path in sorted(workflow_paths):
                if path.name not in workflow_files_contract:
                    violations.append(
                        f"{path.relative_to(root)} is a workflow file not listed in manifest"
                    )
        scripts_contract = manifest.get("scripts")
        script_entrypoints = (
            scripts_contract.get("entrypoints") if isinstance(scripts_contract, dict) else None
        )
        if isinstance(script_entrypoints, list):
            allowed_script_entrypoints = {
                entrypoint for entrypoint in script_entrypoints if isinstance(entrypoint, str)
            }
            for path in sorted(workflow_paths):
                text = path.read_text(encoding="utf-8")
                for script_path in sorted(set(WORKFLOW_SCRIPT_PATH_PATTERN.findall(text))):
                    if script_path not in allowed_script_entrypoints:
                        violations.append(
                            f"{path.relative_to(root)} contains workflow script entrypoint not listed in manifest {script_path!r}"
                        )
        protected_paths = manifest.get("protected_deployment_paths")
        if isinstance(protected_paths, list):
            allowed_protected_paths = {
                protected_path
                for protected_path in protected_paths
                if isinstance(protected_path, str)
            }
            for path in sorted(workflow_paths):
                text = path.read_text(encoding="utf-8")
                for protected_path in ["infra/gcp", "deploy/gcp"]:
                    if protected_path in text and protected_path not in allowed_protected_paths:
                        violations.append(
                            f"{path.relative_to(root)} contains workflow deployment path not listed in manifest {protected_path!r}"
                        )
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
        if manifest is not None and isinstance(workflow_files_contract, dict):
            workflow_contract = workflow_files_contract.get(path.name)
            workflow_jobs = (
                workflow_contract.get("jobs") if isinstance(workflow_contract, dict) else None
            )
            actual_jobs = parsed_workflow.get("jobs") if isinstance(parsed_workflow, dict) else None
            if isinstance(workflow_jobs, dict) and isinstance(actual_jobs, dict):
                for job_name, job_payload in actual_jobs.items():
                    normalized_job_name = str(job_name)
                    if normalized_job_name not in workflow_jobs:
                        violations.append(
                            f"{path.relative_to(root)} contains workflow job not listed in manifest {normalized_job_name!r}"
                        )
                        continue
                    job_contract = workflow_jobs.get(normalized_job_name)
                    step_contract = (
                        job_contract.get("steps") if isinstance(job_contract, dict) else None
                    )
                    if not isinstance(step_contract, list) or not isinstance(job_payload, dict):
                        continue
                    allowed_steps = {
                        step_identifier
                        for step_identifier in step_contract
                        if isinstance(step_identifier, str)
                    }
                    for step in job_payload.get("steps", []):
                        identifier = _workflow_step_identifier(step)
                        if identifier is not None and identifier not in allowed_steps:
                            violations.append(
                                f"{path.relative_to(root)} contains workflow step not listed in manifest {identifier!r}"
                            )
        for forbidden_permission in _collect_forbidden_workflow_permissions(path, parsed_workflow):
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
