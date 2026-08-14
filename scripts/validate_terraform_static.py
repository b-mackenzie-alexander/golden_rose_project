from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_ROOT = ROOT / "infra" / "gcp"

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Terraform scaffold static boundaries.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to scan.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = args.root.resolve()
    terraform_root = root / "infra" / "gcp"
    required_files = [
        root / path.relative_to(ROOT) for path in REQUIRED_FILES
    ]

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

    workflow_paths = [
        *(root / ".github" / "workflows").glob("*.yml"),
        *(root / ".github" / "workflows").glob("*.yaml"),
    ]
    for path in sorted(workflow_paths):
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_WORKFLOW_SUBSTRINGS:
            if forbidden in text:
                violations.append(
                    f"{path.relative_to(root)} contains forbidden workflow authority {forbidden!r}"
                )
        for match in FORBIDDEN_WORKFLOW_SECRET_PATTERN.finditer(text):
            violations.append(
                f"{path.relative_to(root)} contains forbidden workflow secret reference {match.group(0)!r}"
            )
        for match in WORKFLOW_USES_PATTERN.finditer(text):
            uses_ref = match.group(1)
            if not PINNED_ACTION_PATTERN.fullmatch(uses_ref):
                violations.append(
                    f"{path.relative_to(root)} contains unpinned workflow action {uses_ref!r}"
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
