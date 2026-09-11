import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "verify_gcp_foundation.py"
EVIDENCE_TEMPLATE_PATH = ROOT / "deploy" / "gcp" / "evidence-template.md"
MANIFEST_PATH = ROOT / "infra" / "policy" / "predeployment-authority-manifest.json"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_gcp_foundation", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_contract() -> dict[str, Any]:
    return {
        "project_id": "example-project",
        "project_number": "123456789",
        "control_plane_project_id": "state-project",
        "region": "us-east4",
        "expected_image_digest": "sha256:" + "1" * 64,
        "state_bucket_name": "example-terraform-state",
        "state_authority_principal": "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com",
        "recovery_authority_principal": "group:recovery@example.com",
        "bootstrap_operator_principal": "user:bootstrap@example.com",
        "provisioner_operator_principal": "user:provisioner.operator@example.com",
        "provider_operator_principal": "user:provider.operator@example.com",
        "bootstrap_operator_status": "bootstrap-retired",
        "observability_viewer_principal": "group:observability@example.com",
        "recovery_policy_review_status": "gate-2-evidence-required",
        "log_retention_days": 30,
    }


def verifier_common_args(*, mode: str | None = None) -> list[str]:
    args = [
        "--project-id",
        "example-project",
        "--control-plane-project-id",
        "state-project",
        "--expected-image-digest",
        "sha256:" + "1" * 64,
        "--state-bucket-name",
        "example-terraform-state",
        "--state-authority-principal",
        "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com",
        "--recovery-authority-principal",
        "group:recovery@example.com",
        "--bootstrap-operator-principal",
        "user:bootstrap@example.com",
        "--provisioner-operator-principal",
        "user:provisioner.operator@example.com",
        "--provider-operator-principal",
        "user:provider.operator@example.com",
        "--bootstrap-operator-status",
        "bootstrap-retired",
        "--observability-viewer-principal",
        "group:observability@example.com",
        "--recovery-policy-review-status",
        "gate-2-evidence-required",
        "--log-retention-days",
        "30",
    ]
    if mode is not None:
        args.extend(["--mode", mode])
    return args


def valid_snapshot() -> dict[str, Any]:
    contract = expected_contract()
    now = datetime.now(UTC).replace(microsecond=0)
    return {
        "project_number": "123456789",
        "project_labels": {
            "environment": "develop",
            "data_boundary": "fictional-synthetic-only",
            "managed_by": "terraform",
            "service": "staff-tracer",
            "cost_center": "develop",
            "owner": "technical-owner",
            "teardown": "intentional-runbook-only",
        },
        "enabled_apis": [
            "artifactregistry.googleapis.com",
            "billingbudgets.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "compute.googleapis.com",
            "iam.googleapis.com",
            "logging.googleapis.com",
            "monitoring.googleapis.com",
            "run.googleapis.com",
            "secretmanager.googleapis.com",
            "serviceusage.googleapis.com",
            "servicenetworking.googleapis.com",
            "sqladmin.googleapis.com",
        ],
        "resource_inventory": {
            "service_accounts": [
                "staff-tracer-database-verifier@example-project.iam.gserviceaccount.com",
                "staff-tracer-migration@example-project.iam.gserviceaccount.com",
                "staff-tracer-runtime@example-project.iam.gserviceaccount.com",
            ],
            "control_plane_service_accounts": [
                "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com",
                "golden-rose-deployer@state-project.iam.gserviceaccount.com",
                "golden-rose-image-publisher@state-project.iam.gserviceaccount.com",
                "golden-rose-provisioner@state-project.iam.gserviceaccount.com",
            ],
            "cloud_run_service": "staff-tracer",
            "cloud_run_job": "run-migrations",
            "database_authority_job": "verify-database-authority",
            "cloud_run_jobs": ["run-migrations", "verify-database-authority"],
            "cloud_sql_instance": "develop-postgres",
            "state_bucket": contract["state_bucket_name"],
        },
        "cloud_run_service": {
            "name": "staff-tracer",
            "uri": "https://staff-tracer-example-uc.a.run.app",
            "labels": {
                "environment": "develop",
                "data_boundary": "fictional-synthetic-only",
                "managed_by": "terraform",
                "service": "staff-tracer",
                "cost_center": "develop",
                "owner": "technical-owner",
                "teardown": "intentional-runbook-only",
            },
            "ingress": "INGRESS_TRAFFIC_ALL",
            "service_account": "staff-tracer-runtime@example-project.iam.gserviceaccount.com",
            "image": "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer@sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "create_time": (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "min_instance_count": 0,
            "max_instance_count": 1,
            "max_instance_request_concurrency": 10,
            "timeout": "60s",
            "cpu": "1",
            "memory": "512Mi",
            "environment": {
                "GOLDEN_ROSE_ENVIRONMENT": {"value": "develop"},
                "GOLDEN_ROSE_AUTH_MODE": {"value": "synthetic"},
                "GOLDEN_ROSE_DEPLOYMENT_TARGET": {"value": "gcp-develop-private-synthetic"},
                "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL": {
                    "value": "non-production fictional synthetic develop"
                },
                "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST": {"value": "sha256:" + "1" * 64},
                "GOLDEN_ROSE_DEMO_ACCESS_ENABLED": {"value": "true"},
                "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT": {
                    "value": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD": {
                    "secret": "demo-access-password",
                    "version": "latest",
                },
                "GOLDEN_ROSE_DATABASE_URL": {
                    "secret": "runtime-database-url",
                    "version": "latest",
                },
                "GOLDEN_ROSE_SYNTHETIC_STAFF_ID": {
                    "secret": "synthetic-staff-id",
                    "version": "latest",
                },
            },
        },
        "cloud_run_service_iam": {
            "roles/run.invoker": ["allUsers"],
            "roles/run.viewer": [
                "serviceAccount:golden-rose-deployer@state-project.iam.gserviceaccount.com"
            ],
        },
        "migration_job_iam": {
            "roles/run.jobsExecutor": [
                "serviceAccount:golden-rose-deployer@state-project.iam.gserviceaccount.com"
            ],
            "roles/run.viewer": [
                "serviceAccount:golden-rose-deployer@state-project.iam.gserviceaccount.com"
            ],
        },
        "database_authority_job_iam": {
            "roles/run.jobsExecutor": [
                "serviceAccount:golden-rose-deployer@state-project.iam.gserviceaccount.com"
            ],
            "roles/run.viewer": [
                "serviceAccount:golden-rose-deployer@state-project.iam.gserviceaccount.com"
            ],
        },
        "migration_job": {
            "name": "run-migrations",
            "labels": {
                "environment": "develop",
                "data_boundary": "fictional-synthetic-only",
                "managed_by": "terraform",
                "service": "staff-tracer",
                "cost_center": "develop",
                "owner": "technical-owner",
                "teardown": "intentional-runbook-only",
            },
            "service_account": "staff-tracer-migration@example-project.iam.gserviceaccount.com",
            "container_count": 1,
            "parallelism": 1,
            "task_count": 1,
            "max_retries": 0,
            "timeout": "1800s",
            "vpc_egress": "PRIVATE_RANGES_ONLY",
            "vpc_network": "projects/example-project/global/networks/develop-vpc",
            "vpc_subnetwork": "projects/example-project/regions/us-east4/subnetworks/develop-direct-vpc",
            "image": "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer@sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "command": ["golden-rose-migrate"],
            "args": None,
            "environment": {
                "GOLDEN_ROSE_ENVIRONMENT": {"value": "develop"},
                "GOLDEN_ROSE_AUTH_MODE": {"value": "synthetic"},
                "GOLDEN_ROSE_DEPLOYMENT_TARGET": {"value": "gcp-develop-private-synthetic"},
                "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL": {
                    "value": "Non-production fictional synthetic develop"
                },
                "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST": {"value": "sha256:" + "1" * 64},
                "GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE": {"value": "golden_rose_schema_owner"},
                "GOLDEN_ROSE_DATABASE_URL": {
                    "secret": "migration-database-url",
                    "version": "latest",
                },
                "GOLDEN_ROSE_SYNTHETIC_STAFF_ID": {
                    "secret": "synthetic-staff-id",
                    "version": "latest",
                },
            },
        },
        "database_authority_job": {
            "name": "verify-database-authority",
            "labels": {
                "environment": "develop",
                "data_boundary": "fictional-synthetic-only",
                "managed_by": "terraform",
                "service": "staff-tracer",
                "cost_center": "develop",
                "owner": "technical-owner",
                "teardown": "intentional-runbook-only",
            },
            "service_account": "staff-tracer-database-verifier@example-project.iam.gserviceaccount.com",
            "container_count": 1,
            "parallelism": 1,
            "task_count": 1,
            "max_retries": 0,
            "timeout": "600s",
            "vpc_egress": "PRIVATE_RANGES_ONLY",
            "vpc_network": "projects/example-project/global/networks/develop-vpc",
            "vpc_subnetwork": "projects/example-project/regions/us-east4/subnetworks/develop-direct-vpc",
            "image": "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer@sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "command": ["python", "/app/scripts/verify_database_authority.py"],
            "args": None,
            "environment": {
                "GOLDEN_ROSE_DATABASE_URL": {
                    "secret": "migration-database-url",
                    "version": "latest",
                },
                "GOLDEN_ROSE_MIGRATION_DATABASE_URL": {
                    "secret": "migration-database-url",
                    "version": "latest",
                },
                "GOLDEN_ROSE_RUNTIME_DATABASE_URL": {
                    "secret": "runtime-database-url",
                    "version": "latest",
                },
            },
        },
        "database_authority_secret_iam": {
            "migration-database-url": {
                "roles/secretmanager.secretAccessor": [
                    "serviceAccount:staff-tracer-migration@example-project.iam.gserviceaccount.com",
                    "serviceAccount:staff-tracer-database-verifier@example-project.iam.gserviceaccount.com",
                ]
            },
            "runtime-database-url": {
                "roles/secretmanager.secretAccessor": [
                    "serviceAccount:staff-tracer-runtime@example-project.iam.gserviceaccount.com",
                    "serviceAccount:staff-tracer-database-verifier@example-project.iam.gserviceaccount.com",
                ]
            },
        },
        "cloud_sql": {
            "name": "develop-postgres",
            "database_version": "POSTGRES_16",
            "deletion_protection": True,
            "ipv4_enabled": False,
            "private_network": "projects/example-project/global/networks/develop",
            "labels": {
                "environment": "develop",
                "data_boundary": "fictional-synthetic-only",
                "managed_by": "terraform",
                "service": "staff-tracer",
                "cost_center": "develop",
                "owner": "technical-owner",
                "teardown": "intentional-runbook-only",
                "recovery_policy_review_status": contract["recovery_policy_review_status"],
            },
        },
        "service_account_keys": {
            "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com": [],
            "golden-rose-deployer@state-project.iam.gserviceaccount.com": [],
            "golden-rose-image-publisher@state-project.iam.gserviceaccount.com": [],
            "golden-rose-provisioner@state-project.iam.gserviceaccount.com": [],
            "staff-tracer-database-verifier@example-project.iam.gserviceaccount.com": [],
            "staff-tracer-migration@example-project.iam.gserviceaccount.com": [],
            "staff-tracer-runtime@example-project.iam.gserviceaccount.com": [],
        },
        "project_iam": {
            "roles/cloudsql.client": [
                "serviceAccount:staff-tracer-runtime@example-project.iam.gserviceaccount.com",
                "serviceAccount:staff-tracer-migration@example-project.iam.gserviceaccount.com",
                "serviceAccount:staff-tracer-database-verifier@example-project.iam.gserviceaccount.com",
            ],
            "roles/logging.logWriter": [
                "serviceAccount:staff-tracer-runtime@example-project.iam.gserviceaccount.com",
                "serviceAccount:staff-tracer-migration@example-project.iam.gserviceaccount.com",
            ],
            "roles/monitoring.metricWriter": [
                "serviceAccount:staff-tracer-runtime@example-project.iam.gserviceaccount.com",
                "serviceAccount:staff-tracer-migration@example-project.iam.gserviceaccount.com",
            ],
            "roles/logging.viewer": [contract["observability_viewer_principal"]],
            "roles/monitoring.viewer": [contract["observability_viewer_principal"]],
            "projects/example-project/roles/goldenRoseProvisionerQuotaUser": [
                "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com"
            ],
        },
        "provisioner_quota_role": {
            "name": "projects/example-project/roles/goldenRoseProvisionerQuotaUser",
            "title": "Golden Rose Provisioner Quota User",
            "description": "Permits only workload-project quota attribution for the provisioner.",
            "stage": "GA",
            "included_permissions": ["serviceusage.services.use"],
        },
        "provisioner_ancestor_iam": {
            "folders/123456789": {},
            "organizations/987654321": {},
        },
        "control_plane_project_iam": {},
        "service_account_iam": {
            "staff-tracer-runtime@example-project.iam.gserviceaccount.com": {},
            "staff-tracer-migration@example-project.iam.gserviceaccount.com": {},
            "golden-rose-provisioner@state-project.iam.gserviceaccount.com": {
                "roles/iam.serviceAccountTokenCreator": [contract["provisioner_operator_principal"]]
            },
            "golden-rose-image-publisher@state-project.iam.gserviceaccount.com": {
                "roles/iam.workloadIdentityUser": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.workflow_ref/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop"
                ],
            },
            "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com": {
                "roles/iam.workloadIdentityUser": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.workflow_ref/b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop"
                ],
            },
            "golden-rose-deployer@state-project.iam.gserviceaccount.com": {
                "roles/iam.workloadIdentityUser": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.workflow_ref/b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop"
                ],
            },
        },
        "artifact_registry_iam": {
            "roles/artifactregistry.writer": [
                "serviceAccount:golden-rose-image-publisher@state-project.iam.gserviceaccount.com"
            ],
            "roles/artifactregistry.reader": [
                "serviceAccount:golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com"
            ],
        },
        "state_bucket": {
            "name": contract["state_bucket_name"],
            "versioning_enabled": True,
            "uniform_bucket_level_access": True,
            "public_access_prevention": "enforced",
            "retention_period": 604800,
        },
        "state_bucket_iam": {
            "roles/storage.objectAdmin": [
                contract["state_authority_principal"],
                contract["recovery_authority_principal"],
            ]
        },
        "budget": {
            "display_name": "Develop private synthetic workload monthly cost guardrail",
            "threshold_percents": [0.5, 0.75, 1.0],
            "notification_channel_resource_names": [
                "projects/example-project/notificationChannels/123"
            ],
        },
        "notification_channels": {
            "projects/example-project/notificationChannels/123": "Develop private synthetic alert route"
        },
        "alert_policies": [
            "Develop private synthetic health failures",
            "Develop private synthetic readiness failures",
            "Develop private synthetic service error events",
        ],
        "logging": {
            "default_bucket_retention_days": contract["log_retention_days"],
            "sinks": [
                {
                    "name": "reviewed-sink-a",
                    "destination": "logging.googleapis.com/projects/example-project/locations/global/buckets/_Default",
                },
                {
                    "name": "reviewed-sink-b",
                    "destination": "logging.googleapis.com/projects/example-project/locations/global/buckets/_Required",
                },
            ],
            "exclusions": {
                "develop-exclude-uuid-bearing-staff-paths": 'resource.type="cloud_run_revision" AND httpRequest.requestUrl=~"/api/staff/v1/employers/[0-9a-fA-F-]{36}(/contacts(/[0-9a-fA-F-]{36})?)?$"'
            },
        },
        "uptime_checks": [
            {
                "display_name": "Develop private synthetic public readiness",
                "period": "300s",
                "timeout": "10s",
                "selected_regions": ["USA"],
                "monitored_resource": {
                    "type": "uptime_url",
                    "labels": {
                        "host": "staff-tracer-example-uc.a.run.app",
                        "project_id": "example-project",
                    },
                },
                "http_check": {
                    "request_method": "GET",
                    "path": "/readiness",
                    "port": 443,
                    "use_ssl": True,
                    "validate_ssl": True,
                },
            }
        ],
        "workload_identity_provider": {
            "pool_id": "golden-rose-github",
            "provider_id": "golden-rose-github-provider",
            "attribute_mapping": {
                "google.subject": "assertion.sub",
                "attribute.repository": "assertion.repository",
                "attribute.repository_owner": "assertion.repository_owner",
                "attribute.ref": "assertion.ref",
                "attribute.environment": "assertion.environment",
                "attribute.event_name": "assertion.event_name",
                "attribute.workflow_ref": "assertion.workflow_ref",
            },
            "attribute_condition": 'attribute.repository == "b-mackenzie-alexander/golden_rose_project" && attribute.repository_owner == "b-mackenzie-alexander" && attribute.ref == "refs/heads/develop" && attribute.environment == "develop" && attribute.event_name == "workflow_dispatch" && ( attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop" || attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop" )',
        },
    }


def foundation_snapshot() -> dict[str, Any]:
    snapshot = valid_snapshot()
    project_id = expected_contract()["project_id"]
    database_verifier = f"staff-tracer-database-verifier@{project_id}.iam.gserviceaccount.com"
    database_verifier_member = f"serviceAccount:{database_verifier}"

    snapshot["resource_inventory"].update(
        {
            "service_accounts": [
                f"staff-tracer-migration@{project_id}.iam.gserviceaccount.com",
                f"staff-tracer-runtime@{project_id}.iam.gserviceaccount.com",
            ],
            "cloud_run_jobs": [],
            "cloud_run_job": "",
            "database_authority_job": "",
            "cloud_run_service": "",
            "cloud_sql_instance": "",
        }
    )
    snapshot["cloud_run_service"] = {}
    snapshot["cloud_run_service_iam"] = {}
    snapshot["migration_job"] = {}
    snapshot["migration_job_iam"] = {}
    snapshot["cloud_run_job"] = {}
    snapshot["cloud_run_job_iam"] = {}
    snapshot["database_authority_job"] = {}
    snapshot["database_authority_job_iam"] = {}
    snapshot["cloud_sql"] = {}
    snapshot["uptime_checks"] = []
    snapshot["alert_policies"] = [
        "Develop private synthetic health failures",
        "Develop private synthetic service error events",
    ]
    snapshot["service_account_keys"].pop(database_verifier)
    snapshot["service_account_iam"].pop(database_verifier, None)
    snapshot["project_iam"]["roles/cloudsql.client"].remove(database_verifier_member)
    for policy in snapshot["database_authority_secret_iam"].values():
        policy["roles/secretmanager.secretAccessor"].remove(database_verifier_member)
    return snapshot


def test_foundation_mode_accepts_database_verifier_absence_and_existing_secret_consumers() -> None:
    module = load_module()

    assert (
        module.evaluate_foundation_snapshot(
            foundation_snapshot(),
            expected_contract(),
            mode="foundation",
        )
        == []
    )


def test_foundation_mode_key_inventory_omits_deferred_database_verifier() -> None:
    module = load_module()
    snapshot = foundation_snapshot()

    assert (
        "staff-tracer-database-verifier@example-project.iam.gserviceaccount.com"
        not in snapshot["service_account_keys"]
    )
    assert (
        module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="foundation") == []
    )


@pytest.mark.parametrize("mutation", ["missing_policy", "extra_member", "premature_verifier"])
def test_foundation_mode_rejects_database_secret_iam_drift(mutation: str) -> None:
    module = load_module()
    snapshot = foundation_snapshot()
    policies = snapshot["database_authority_secret_iam"]
    accessor = "roles/secretmanager.secretAccessor"
    if mutation == "missing_policy":
        policies.pop("runtime-database-url")
    elif mutation == "extra_member":
        policies["runtime-database-url"][accessor].append("user:unexpected@example.com")
    else:
        policies["migration-database-url"][accessor].append(
            "serviceAccount:staff-tracer-database-verifier@example-project.iam.gserviceaccount.com"
        )

    violations = module.evaluate_foundation_snapshot(
        snapshot,
        expected_contract(),
        mode="foundation",
    )

    assert any("foundation database secret IAM" in violation for violation in violations)


def test_foundation_mode_accepts_exact_named_human_provider_owner() -> None:
    module = load_module()
    contract = expected_contract()
    snapshot = foundation_snapshot()
    snapshot["project_iam"]["roles/owner"] = [contract["provider_operator_principal"]]

    assert module.evaluate_foundation_snapshot(snapshot, contract, mode="foundation") == []


@pytest.mark.parametrize(
    ("provider_principal", "role", "members"),
    [
        ("user:provider.operator@example.com", "roles/owner", ["user:other@example.com"]),
        (
            "user:provider.operator@example.com",
            "roles/owner",
            ["user:provider.operator@example.com", "user:other@example.com"],
        ),
        (
            "user:provider.operator@example.com",
            "roles/editor",
            ["user:provider.operator@example.com"],
        ),
        (
            "serviceAccount:provider@example-project.iam.gserviceaccount.com",
            "roles/owner",
            ["serviceAccount:provider@example-project.iam.gserviceaccount.com"],
        ),
    ],
)
def test_foundation_mode_rejects_broadened_or_nonhuman_provider_authority(
    provider_principal: str,
    role: str,
    members: list[str],
) -> None:
    module = load_module()
    contract = expected_contract() | {"provider_operator_principal": provider_principal}
    snapshot = foundation_snapshot()
    snapshot["project_iam"][role] = members

    assert module.evaluate_foundation_snapshot(snapshot, contract, mode="foundation")


def test_service_verifier_accepts_only_exact_expiring_public_basic_boundary() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    now = datetime.now(UTC).replace(microsecond=0)
    snapshot["cloud_run_service"].update(
        {
            "create_time": (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "min_instance_count": 0,
            "max_instance_count": 1,
            "max_instance_request_concurrency": 10,
            "timeout": "60s",
            "cpu": "1",
            "memory": "512Mi",
            "environment": {
                "GOLDEN_ROSE_ENVIRONMENT": {"value": "develop"},
                "GOLDEN_ROSE_AUTH_MODE": {"value": "synthetic"},
                "GOLDEN_ROSE_DEPLOYMENT_TARGET": {"value": "gcp-develop-private-synthetic"},
                "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL": {
                    "value": "non-production fictional synthetic develop"
                },
                "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST": {"value": "sha256:" + "1" * 64},
                "GOLDEN_ROSE_DEMO_ACCESS_ENABLED": {"value": "true"},
                "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT": {
                    "value": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD": {
                    "secret": "demo-access-password",
                    "version": "latest",
                },
                "GOLDEN_ROSE_DATABASE_URL": {
                    "secret": "runtime-database-url",
                    "version": "latest",
                },
                "GOLDEN_ROSE_SYNTHETIC_STAFF_ID": {
                    "secret": "synthetic-staff-id",
                    "version": "latest",
                },
            },
        }
    )
    snapshot["cloud_run_service_iam"]["roles/run.invoker"] = ["allUsers"]
    snapshot["project_iam"]["projects/example-project/roles/goldenRoseProvisionerQuotaUser"] = [
        "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com"
    ]
    snapshot["provisioner_quota_role"] = {
        "name": "projects/example-project/roles/goldenRoseProvisionerQuotaUser",
        "title": "Golden Rose Provisioner Quota User",
        "description": "Permits only workload-project quota attribution for the provisioner.",
        "stage": "GA",
        "included_permissions": ["serviceusage.services.use"],
    }
    snapshot["uptime_checks"][0]["display_name"] = "Develop private synthetic public readiness"
    snapshot["uptime_checks"][0]["http_check"].pop("service_agent_authentication", None)

    assert module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service") == []


def test_live_verifier_requires_exact_database_authority_job_and_secret_iam() -> None:
    module = load_module()

    missing_job = valid_snapshot()
    missing_job.pop("database_authority_job")
    extra_job_member = valid_snapshot()
    extra_job_member["database_authority_job_iam"]["roles/run.viewer"].append(
        "user:unexpected@example.com"
    )
    wrong_network = valid_snapshot()
    wrong_network["database_authority_job"]["vpc_network"] = (
        "projects/other-project/global/networks/develop-vpc"
    )
    unexpected_args = valid_snapshot()
    unexpected_args["database_authority_job"]["args"] = ["--unsafe"]
    extra_job = valid_snapshot()
    extra_job["resource_inventory"]["cloud_run_jobs"].append("unexpected-job")
    missing_secret_policy = valid_snapshot()
    missing_secret_policy["database_authority_secret_iam"].pop("runtime-database-url")
    extra_secret_member = valid_snapshot()
    extra_secret_member["database_authority_secret_iam"]["migration-database-url"][
        "roles/secretmanager.secretAccessor"
    ].append("user:unexpected@example.com")

    for snapshot in [
        missing_job,
        extra_job_member,
        wrong_network,
        unexpected_args,
        extra_job,
        missing_secret_policy,
        extra_secret_member,
    ]:
        violations = module.evaluate_foundation_snapshot(
            snapshot,
            expected_contract(),
            mode="service",
        )
        assert any("database authority" in violation.lower() for violation in violations)


def test_service_verifier_rejects_quota_role_binding_and_inherited_authority_expansion() -> None:
    module = load_module()

    extra_permission = valid_snapshot()
    extra_permission["provisioner_quota_role"]["included_permissions"].append(
        "resourcemanager.projects.get"
    )
    wrong_description = valid_snapshot()
    wrong_description["provisioner_quota_role"]["description"] = "Different description"
    extra_member = valid_snapshot()
    extra_member["project_iam"][
        "projects/example-project/roles/goldenRoseProvisionerQuotaUser"
    ].append("user:unexpected@example.com")
    direct_broad_role = valid_snapshot()
    direct_broad_role["project_iam"]["roles/serviceusage.serviceUsageConsumer"] = [
        "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com"
    ]
    inherited_role = valid_snapshot()
    inherited_role["provisioner_ancestor_iam"]["organizations/987654321"] = {
        "roles/owner": [
            "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com"
        ]
    }
    unresolved_group_role = valid_snapshot()
    unresolved_group_role["provisioner_ancestor_iam"]["folders/123456789"] = {
        "roles/serviceusage.serviceUsageConsumer": ["group:platform@example.com"]
    }
    malformed_members = valid_snapshot()
    malformed_members["provisioner_ancestor_iam"]["folders/123456789"] = {
        "roles/owner": {"unexpected": "object"}
    }
    missing_ancestry = valid_snapshot()
    missing_ancestry.pop("provisioner_ancestor_iam")

    for snapshot in [
        extra_permission,
        wrong_description,
        extra_member,
        direct_broad_role,
        inherited_role,
        unresolved_group_role,
        malformed_members,
        missing_ancestry,
    ]:
        violations = module.evaluate_foundation_snapshot(
            snapshot, expected_contract(), mode="service"
        )
        assert any(
            "quota" in violation.lower() or "project iam" in violation.lower()
            for violation in violations
        )


def test_service_verifier_rejects_database_verifier_ancestor_authority() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["provisioner_ancestor_iam"]["organizations/987654321"] = {
        "roles/secretmanager.secretAccessor": [
            "serviceAccount:staff-tracer-database-verifier@example-project.iam.gserviceaccount.com"
        ]
    }

    violations = module.evaluate_foundation_snapshot(
        snapshot,
        expected_contract(),
        mode="service",
    )

    assert any("database verifier inherited authority" in violation for violation in violations)


def test_service_verifier_rejects_weakened_basic_expiry_scale_or_secret_reference() -> None:
    module = load_module()
    now = datetime.now(UTC).replace(microsecond=0)
    mutations = [
        ("max_instance_count", 2),
        ("max_instance_request_concurrency", 80),
        ("timeout", "300s"),
    ]
    for field, value in mutations:
        snapshot = valid_snapshot()
        snapshot["cloud_run_service"][field] = value
        assert module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    for name, value in [
        ("GOLDEN_ROSE_DEMO_ACCESS_ENABLED", {"value": "false"}),
        (
            "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD",
            {"secret": "wrong-secret", "version": "latest"},
        ),
        (
            "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT",
            {"value": (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")},
        ),
        (
            "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT",
            {"value": (now + timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")},
        ),
    ]:
        snapshot = valid_snapshot()
        snapshot["cloud_run_service"]["environment"][name] = value
        assert module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")


def test_migration_and_service_verifier_require_exact_packet_image_digest() -> None:
    module = load_module()
    stale_migration = valid_snapshot()
    stale_migration["migration_job"]["image"] = (
        "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer@sha256:"
        + "2" * 64
    )
    stale_service = valid_snapshot()
    stale_service["cloud_run_service"]["image"] = (
        "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer@sha256:"
        + "2" * 64
    )

    migration_violations = module.evaluate_foundation_snapshot(
        stale_migration,
        expected_contract(),
        mode="migration",
    )
    service_violations = module.evaluate_foundation_snapshot(
        stale_service,
        expected_contract(),
        mode="service",
    )

    assert any("expected image digest" in violation for violation in migration_violations)
    assert any("expected image digest" in violation for violation in service_violations)


def test_migration_live_verifier_rejects_arguments_and_foreign_project_vpc() -> None:
    module = load_module()
    unexpected_args = valid_snapshot()
    unexpected_args["migration_job"]["args"] = ["--unsafe"]
    foreign_network = valid_snapshot()
    foreign_network["migration_job"]["vpc_network"] = (
        "projects/other-project/global/networks/develop-vpc"
    )
    foreign_subnetwork = valid_snapshot()
    foreign_subnetwork["migration_job"]["vpc_subnetwork"] = (
        "projects/other-project/regions/us-east4/subnetworks/develop-direct-vpc"
    )

    for snapshot in [unexpected_args, foreign_network, foreign_subnetwork]:
        violations = module.evaluate_foundation_snapshot(
            snapshot,
            expected_contract(),
            mode="migration",
        )
        assert any("migration job" in violation.lower() for violation in violations)


def test_verify_gcp_foundation_script_exists_and_template_is_value_safe() -> None:
    assert MODULE_PATH.exists()
    assert EVIDENCE_TEMPLATE_PATH.exists()
    template = EVIDENCE_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "[REDACTED]" in template
    assert "read-only" in template.lower()


def test_manifest_lists_verify_gcp_foundation_script_entrypoint() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "scripts/verify_gcp_foundation.py" in manifest["scripts"]["entrypoints"]


@pytest.mark.parametrize(
    "retired_argument",
    [
        "--private-invoker-principal",
        "--tester-authority-receipt",
        "--tester-authority-bundle",
        "--tester-authority-certificate-identity",
    ],
)
def test_live_foundation_verifier_rejects_retired_named_tester_inputs(
    retired_argument: str,
) -> None:
    module = load_module()

    with pytest.raises(SystemExit):
        module._parse_args([*verifier_common_args(), retired_argument, "retired-value"])


def test_all_modes_use_the_fixed_temporary_public_invoker_contract() -> None:
    module = load_module()

    for mode in ["foundation", "migration", "service"]:
        parsed = module._parse_args(verifier_common_args(mode=mode))
        assert parsed.mode == mode
        assert not hasattr(parsed, "tester_authority_receipt")
        assert not hasattr(parsed, "private_invoker_principal")


def test_service_mode_evaluates_without_named_tester_derivation() -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    calls: dict[str, Any] = {}

    def fake_collect(_: Any, *, mode: str = "service") -> dict[str, Any]:
        calls["collect"] = mode
        return valid_snapshot()

    def fake_evaluate(
        snapshot: dict[str, Any], contract: dict[str, Any], *, mode: str
    ) -> list[str]:
        calls["evaluate"] = {"snapshot": snapshot, "contract": contract, "mode": mode}
        return []

    mutable_module.collect_foundation_snapshot = fake_collect
    mutable_module.evaluate_foundation_snapshot = fake_evaluate

    exit_code = module.main(verifier_common_args(mode="service"))

    assert exit_code == 0
    assert calls["collect"] == "service"
    assert calls["evaluate"]["mode"] == "service"
    assert "private_invoker_principal" not in calls["evaluate"]["contract"]


def test_foundation_mode_main_allows_absent_cloud_sql_during_collection() -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    calls: dict[str, Any] = {"cloud_sql_requested": False, "commands": []}

    def fake_build_live_command_runner(contract: dict[str, Any], *, mode: str = "service") -> Any:
        calls["contract"] = contract
        calls["runner_mode"] = mode

        def runner(command: Any) -> Any:
            key = tuple(command)
            calls["commands"].append(key)
            if key == ("cloud-sql",):
                calls["cloud_sql_requested"] = True
                raise module.VerificationError(
                    "cloud sql failed: ERROR: (gcloud.sql.instances.describe) HTTPError 404: "
                    "The Cloud SQL instance does not exist. This command is authenticated as "
                    "operator@example.com which is the active account specified by the "
                    "[core/account] property."
                )
            staged_values = {
                ("project-labels",): valid_snapshot()["project_labels"],
                ("enabled-apis",): valid_snapshot()["enabled_apis"],
                ("service-accounts",): {
                    "workload": valid_snapshot()["resource_inventory"]["service_accounts"],
                    "control_plane": valid_snapshot()["resource_inventory"][
                        "control_plane_service_accounts"
                    ],
                },
                ("project-number",): expected_contract()["project_number"],
                ("cloud-run-jobs",): [],
                ("cloud-run-service",): {},
                ("cloud-run-service-iam",): {},
                ("migration-job",): {},
                ("migration-job-iam",): {},
                ("database-authority-job",): {},
                ("database-authority-job-iam",): {},
                ("database-authority-secret-iam",): {
                    "migration-database-url": {},
                    "runtime-database-url": {},
                },
                ("service-account-keys",): valid_snapshot()["service_account_keys"],
                ("provisioner-quota-role",): valid_snapshot()["provisioner_quota_role"],
                ("provisioner-ancestor-iam",): valid_snapshot()["provisioner_ancestor_iam"],
                ("project-iam",): valid_snapshot()["project_iam"],
                ("control-plane-project-iam",): valid_snapshot()["control_plane_project_iam"],
                ("service-account-iam",): valid_snapshot()["service_account_iam"],
                ("artifact-registry-iam",): valid_snapshot()["artifact_registry_iam"],
                ("state-bucket",): valid_snapshot()["state_bucket"],
                ("state-bucket-iam",): valid_snapshot()["state_bucket_iam"],
                ("budget",): valid_snapshot()["budget"],
                ("notification-channels",): valid_snapshot()["notification_channels"],
                ("alert-policies",): valid_snapshot()["alert_policies"],
                ("logging",): valid_snapshot()["logging"],
                ("uptime-checks",): [],
                ("workload-identity-provider",): valid_snapshot()["workload_identity_provider"],
            }
            return staged_values[key]

        return runner

    def fake_render(snapshot: dict[str, Any], contract: dict[str, Any], *, mode: str) -> list[str]:
        calls["evaluate"] = {"snapshot": snapshot, "contract": contract, "mode": mode}
        return []

    mutable_module._build_live_command_runner = fake_build_live_command_runner
    mutable_module.evaluate_foundation_snapshot = fake_render

    exit_code = module.main(verifier_common_args(mode="foundation"))

    assert exit_code == 0
    assert calls["runner_mode"] == "foundation"
    assert calls["cloud_sql_requested"] is True
    assert calls["evaluate"]["mode"] == "foundation"
    assert calls["evaluate"]["snapshot"]["cloud_sql"] == {}
    assert calls["evaluate"]["snapshot"]["resource_inventory"]["cloud_sql_instance"] == ""


def test_foundation_collection_allows_gcloud_absent_cloud_sql_instance_message() -> None:
    module = load_module()
    commands: dict[tuple[str, ...], Any] = {
        ("project-labels",): valid_snapshot()["project_labels"],
        ("enabled-apis",): valid_snapshot()["enabled_apis"],
        ("service-accounts",): {
            "workload": valid_snapshot()["resource_inventory"]["service_accounts"],
            "control_plane": valid_snapshot()["resource_inventory"][
                "control_plane_service_accounts"
            ],
        },
        ("project-number",): expected_contract()["project_number"],
        ("cloud-run-jobs",): [],
        ("cloud-run-service",): {},
        ("cloud-run-service-iam",): {},
        ("migration-job",): {},
        ("migration-job-iam",): {},
        ("database-authority-job",): {},
        ("database-authority-job-iam",): {},
        ("database-authority-secret-iam",): {
            "migration-database-url": {},
            "runtime-database-url": {},
        },
        ("service-account-keys",): valid_snapshot()["service_account_keys"],
        ("provisioner-quota-role",): valid_snapshot()["provisioner_quota_role"],
        ("provisioner-ancestor-iam",): valid_snapshot()["provisioner_ancestor_iam"],
        ("project-iam",): valid_snapshot()["project_iam"],
        ("control-plane-project-iam",): valid_snapshot()["control_plane_project_iam"],
        ("service-account-iam",): valid_snapshot()["service_account_iam"],
        ("artifact-registry-iam",): valid_snapshot()["artifact_registry_iam"],
        ("state-bucket",): valid_snapshot()["state_bucket"],
        ("state-bucket-iam",): valid_snapshot()["state_bucket_iam"],
        ("budget",): valid_snapshot()["budget"],
        ("notification-channels",): valid_snapshot()["notification_channels"],
        ("alert-policies",): valid_snapshot()["alert_policies"],
        ("logging",): valid_snapshot()["logging"],
        ("uptime-checks",): [],
        ("workload-identity-provider",): valid_snapshot()["workload_identity_provider"],
    }

    def runner(command: tuple[str, ...]) -> Any:
        if command == ("cloud-sql",):
            raise module.VerificationError(
                "cloud sql failed: ERROR: (gcloud.sql.instances.describe) HTTPError 404: "
                "The Cloud SQL instance does not exist. This command is authenticated as "
                "operator@example.com which is the active account specified by the "
                "[core/account] property."
            )
        return commands[command]

    snapshot = module.collect_foundation_snapshot(runner, mode="foundation")

    assert snapshot["cloud_sql"] == {}
    assert snapshot["resource_inventory"]["cloud_sql_instance"] == ""


@pytest.mark.parametrize(
    "message",
    [
        "The Cloud SQL instance does not exist. retryable transport fault",
        "The unrelated instance does not exist.",
        "NOT_FOUND",
        "resource not found",
        "ERROR: (gcloud.sql.instances.describe) HTTPError 404: "
        "The Cloud SQL instance does not exist. This command is authenticated as "
        "foreign account which is the active account specified by the [core/account] property.",
        "ERROR: (gcloud.sql.instances.describe) HTTPError 404: "
        "The Cloud SQL instance does not exist. This command is authenticated as "
        "operator@EXAMPLE.com which is the active account specified by the [core/account] property.",
        "ERROR: (gcloud.sql.instances.describe) HTTPError 404: "
        "The Cloud SQL instance does not exist. This command is authenticated as "
        "operator@example.com which is the active account specified by the "
        "[core/account] property. retryable transport fault",
    ],
)
def test_cloud_sql_absence_matcher_rejects_near_matches(message: str) -> None:
    module = load_module()
    error = module.VerificationError(f"cloud sql failed: {message}")

    assert module._is_absent_cloud_sql_error(error) is False


def test_workload_absence_matcher_rejects_cloud_sql_specific_message() -> None:
    module = load_module()
    error = module.VerificationError("cloud sql failed: The Cloud SQL instance does not exist.")

    assert module._is_absent_workload_resource_error(error) is False


@pytest.mark.parametrize(
    "message",
    [
        "cloud sql failed: NOT_FOUND",
        "cloud sql failed: The Cloud SQL instance was not found",
    ],
)
def test_workload_absence_matcher_rejects_cloud_sql_not_found_forms(message: str) -> None:
    module = load_module()

    assert module._is_absent_workload_resource_error(module.VerificationError(message)) is False


def test_live_runner_collects_database_authority_job_inventory_and_exact_policies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_run_json_command(command: list[str], *, context: str) -> Any:
        calls.append((context, tuple(command)))
        if context == "cloud run jobs":
            return [
                {"name": "projects/example-project/locations/us-east4/jobs/run-migrations"},
                {
                    "name": "projects/example-project/locations/us-east4/jobs/verify-database-authority"
                },
            ]
        if context == "database authority job":
            return {
                "name": "verify-database-authority",
                "labels": valid_snapshot()["database_authority_job"]["labels"],
                "template": {
                    "parallelism": 1,
                    "taskCount": 1,
                    "template": {
                        "serviceAccount": "staff-tracer-database-verifier@example-project.iam.gserviceaccount.com",
                        "maxRetries": 0,
                        "timeout": "600s",
                        "vpcAccess": {
                            "egress": "PRIVATE_RANGES_ONLY",
                            "networkInterfaces": [
                                {
                                    "network": "projects/example-project/global/networks/develop-vpc",
                                    "subnetwork": "projects/example-project/regions/us-east4/subnetworks/develop-direct-vpc",
                                }
                            ],
                        },
                        "containers": [
                            {
                                "image": valid_snapshot()["database_authority_job"]["image"],
                                "command": [
                                    "python",
                                    "/app/scripts/verify_database_authority.py",
                                ],
                                "env": [
                                    {
                                        "name": name,
                                        "valueSource": {
                                            "secretKeyRef": {
                                                "secret": value["secret"],
                                                "version": value["version"],
                                            }
                                        },
                                    }
                                    for name, value in valid_snapshot()["database_authority_job"][
                                        "environment"
                                    ].items()
                                ],
                            }
                        ],
                    },
                },
            }
        if context == "database authority job iam":
            return {
                "bindings": [
                    {"role": role, "members": members}
                    for role, members in valid_snapshot()["database_authority_job_iam"].items()
                ]
            }
        if context.startswith("database authority secret iam for "):
            secret_name = context.rsplit(" ", maxsplit=1)[-1]
            return {
                "bindings": [
                    {"role": role, "members": members}
                    for role, members in valid_snapshot()["database_authority_secret_iam"][
                        secret_name
                    ].items()
                ]
            }
        raise AssertionError(f"unexpected context: {context}")

    monkeypatch.setattr(module, "_run_json_command", fake_run_json_command)
    runner = module._build_live_command_runner(expected_contract())

    assert runner(("cloud-run-jobs",)) == ["run-migrations", "verify-database-authority"]
    assert runner(("database-authority-job",)) == valid_snapshot()["database_authority_job"]
    assert runner(("database-authority-job-iam",)) == valid_snapshot()["database_authority_job_iam"]
    assert (
        runner(("database-authority-secret-iam",))
        == valid_snapshot()["database_authority_secret_iam"]
    )
    assert {context for context, _command in calls} == {
        "cloud run jobs",
        "database authority job",
        "database authority job iam",
        "database authority secret iam for migration-database-url",
        "database authority secret iam for runtime-database-url",
    }


def test_live_runner_treats_gcloud_cannot_find_service_as_absent() -> None:
    module = load_module()
    mutable_module = cast(Any, module)

    def fake_run_json_command(command: list[str], *, context: str) -> dict[str, Any]:
        assert context == "cloud run service"
        raise module.VerificationError(
            "cloud run service failed: ERROR: (gcloud.run.services.describe) "
            "Cannot find service [staff-tracer]"
        )

    mutable_module._run_json_command = fake_run_json_command

    runner = module._build_live_command_runner(expected_contract())

    assert runner(("cloud-run-service",)) == {}


def test_live_runner_reads_gcloud_storage_snake_case_bucket_posture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    def fake_run_json_command(command: list[str], *, context: str) -> dict[str, Any]:
        assert context == "state bucket"
        return {
            "name": "example-terraform-state",
            "versioning_enabled": True,
            "uniform_bucket_level_access": True,
            "public_access_prevention": "enforced",
            "retention_policy": {"retentionPeriod": 604800},
        }

    monkeypatch.setattr(module, "_run_json_command", fake_run_json_command)

    assert module._build_live_command_runner(expected_contract())(("state-bucket",)) == {
        "name": "example-terraform-state",
        "versioning_enabled": True,
        "uniform_bucket_level_access": True,
        "public_access_prevention": "enforced",
        "retention_period": 604800,
    }


def test_live_runner_reads_wif_ids_from_gcloud_resource_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    def fake_run_json_command(command: list[str], *, context: str) -> dict[str, Any]:
        if context == "workload identity pool":
            return {
                "name": "projects/example/locations/global/workloadIdentityPools/golden-rose-github"
            }
        assert context == "workload identity provider"
        return {
            "name": "projects/example/locations/global/workloadIdentityPools/golden-rose-github/providers/golden-rose-github-provider",
            "attributeMapping": {"google.subject": "assertion.sub"},
            "attributeCondition": "attribute.repository == 'example/repository'",
        }

    monkeypatch.setattr(module, "_run_json_command", fake_run_json_command)

    snapshot = module._build_live_command_runner(expected_contract())(
        ("workload-identity-provider",)
    )

    assert snapshot["pool_id"] == "golden-rose-github"
    assert snapshot["provider_id"] == "golden-rose-github-provider"


def test_live_runner_excludes_provider_managed_service_accounts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    def fake_run_json_command(command: list[str], *, context: str) -> list[dict[str, str]]:
        if context == "service accounts":
            return [
                {"email": "staff-tracer-migration@example-project.iam.gserviceaccount.com"},
                {"email": "staff-tracer-runtime@example-project.iam.gserviceaccount.com"},
                {"email": "123456789-compute@developer.gserviceaccount.com"},
            ]
        assert context == "control-plane service accounts"
        return [
            {"email": "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com"},
            {"email": "golden-rose-deployer@state-project.iam.gserviceaccount.com"},
            {"email": "golden-rose-image-publisher@state-project.iam.gserviceaccount.com"},
            {"email": "golden-rose-provisioner@state-project.iam.gserviceaccount.com"},
        ]

    monkeypatch.setattr(module, "_run_json_command", fake_run_json_command)

    snapshot = module._build_live_command_runner(expected_contract())(("service-accounts",))

    assert snapshot["workload"] == [
        "staff-tracer-migration@example-project.iam.gserviceaccount.com",
        "staff-tracer-runtime@example-project.iam.gserviceaccount.com",
    ]


def test_foundation_live_runner_omits_deferred_database_verifier_key_and_iam_queries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    contexts: list[str] = []

    def fake_run_json_command(command: list[str], *, context: str) -> Any:
        contexts.append(context)
        if context == "service accounts":
            return [
                {"email": "staff-tracer-migration@example-project.iam.gserviceaccount.com"},
                {"email": "staff-tracer-runtime@example-project.iam.gserviceaccount.com"},
            ]
        if context == "control-plane service accounts":
            return [
                {"email": "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com"},
                {"email": "golden-rose-deployer@state-project.iam.gserviceaccount.com"},
                {"email": "golden-rose-image-publisher@state-project.iam.gserviceaccount.com"},
                {"email": "golden-rose-provisioner@state-project.iam.gserviceaccount.com"},
            ]
        if context.startswith("service account keys "):
            return []
        if context.startswith("service account iam "):
            return {"bindings": []}
        raise AssertionError(f"unexpected context: {context}")

    monkeypatch.setattr(module, "_run_json_command", fake_run_json_command)
    runner = module._build_live_command_runner(expected_contract(), mode="foundation")

    runner(("service-accounts",))
    key_inventory = runner(("service-account-keys",))
    iam_inventory = runner(("service-account-iam",))

    deferred_email = "staff-tracer-database-verifier@example-project.iam.gserviceaccount.com"
    assert deferred_email not in key_inventory
    assert deferred_email not in iam_inventory
    assert all(deferred_email not in context for context in contexts)


@pytest.mark.parametrize(
    "message",
    [
        "Cannot find service account [unexpected]",
        "Cannot find jobber [unexpected]",
    ],
)
def test_live_runner_does_not_treat_near_match_as_absent(message: str) -> None:
    module = load_module()
    mutable_module = cast(Any, module)

    def fake_run_json_command(command: list[str], *, context: str) -> dict[str, Any]:
        assert context == "cloud run service"
        raise module.VerificationError(f"cloud run service failed: {message}")

    mutable_module._run_json_command = fake_run_json_command
    runner = module._build_live_command_runner(expected_contract())

    with pytest.raises(module.VerificationError, match="cloud run service failed"):
        runner(("cloud-run-service",))


def test_live_foundation_verifier_reads_exact_provisioner_quota_role() -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    commands: list[list[str]] = []

    def fake_run_json_command(command: list[str], *, context: str) -> dict[str, Any]:
        commands.append(command)
        assert context == "provisioner quota role"
        return {
            "name": "projects/example-project/roles/goldenRoseProvisionerQuotaUser",
            "title": "Golden Rose Provisioner Quota User",
            "description": "Permits only workload-project quota attribution for the provisioner.",
            "stage": "GA",
            "includedPermissions": ["serviceusage.services.use"],
        }

    mutable_module._run_json_command = fake_run_json_command
    runner = module._build_live_command_runner(expected_contract())

    assert runner(("provisioner-quota-role",)) == valid_snapshot()["provisioner_quota_role"]
    assert commands == [
        [
            "gcloud",
            "iam",
            "roles",
            "describe",
            "goldenRoseProvisionerQuotaUser",
            "--project",
            "example-project",
            "--format=json",
        ]
    ]


def test_live_foundation_verifier_reads_every_project_ancestor_iam_policy() -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    commands: list[list[str]] = []
    responses: list[Any] = [
        [
            {"type": "project", "id": "example-project"},
            {"type": "folder", "id": "123456789"},
            {"type": "organization", "id": "987654321"},
        ],
        {"bindings": []},
        {"bindings": []},
    ]

    def fake_run_json_command(command: list[str], *, context: str) -> Any:
        commands.append(command)
        return responses.pop(0)

    mutable_module._run_json_command = fake_run_json_command
    runner = module._build_live_command_runner(expected_contract())

    assert runner(("provisioner-ancestor-iam",)) == {
        "folders/123456789": {},
        "organizations/987654321": {},
    }
    assert commands == [
        [
            "gcloud",
            "projects",
            "get-ancestors",
            "example-project",
            "--format=json",
        ],
        [
            "gcloud",
            "resource-manager",
            "folders",
            "get-iam-policy",
            "123456789",
            "--format=json",
        ],
        [
            "gcloud",
            "organizations",
            "get-iam-policy",
            "987654321",
            "--format=json",
        ],
    ]


@pytest.mark.parametrize(
    "ancestors",
    [
        [],
        [{"type": "project", "id": "wrong-project"}],
        [{"type": "project"}],
        [
            {"type": "project", "id": "example-project"},
            {"type": "project", "id": "example-project"},
        ],
        [
            {"type": "project", "id": "example-project"},
            {"type": "folder", "id": "123456789"},
            {"type": "folder", "id": "123456789"},
        ],
    ],
)
def test_live_foundation_verifier_rejects_unanchored_or_duplicate_ancestry(
    ancestors: list[dict[str, str]],
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)

    def fake_run_json_command(command: list[str], *, context: str) -> Any:
        if context == "workload project ancestors":
            return ancestors
        return {"bindings": []}

    mutable_module._run_json_command = fake_run_json_command
    runner = module._build_live_command_runner(expected_contract())

    with pytest.raises(module.VerificationError, match="ancestor metadata is malformed"):
        runner(("provisioner-ancestor-iam",))


def test_collect_foundation_snapshot_accepts_reviewed_fixture() -> None:
    module = load_module()
    commands = {
        ("project-labels",): {
            "environment": "develop",
            "data_boundary": "fictional-synthetic-only",
            "managed_by": "terraform",
            "service": "staff-tracer",
            "cost_center": "develop",
            "owner": "technical-owner",
            "teardown": "intentional-runbook-only",
        },
        ("enabled-apis",): [
            "artifactregistry.googleapis.com",
            "billingbudgets.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "compute.googleapis.com",
            "iam.googleapis.com",
            "logging.googleapis.com",
            "monitoring.googleapis.com",
            "run.googleapis.com",
            "secretmanager.googleapis.com",
            "serviceusage.googleapis.com",
            "servicenetworking.googleapis.com",
            "sqladmin.googleapis.com",
        ],
        ("service-accounts",): {
            "workload": valid_snapshot()["resource_inventory"]["service_accounts"],
            "control_plane": valid_snapshot()["resource_inventory"][
                "control_plane_service_accounts"
            ],
        },
        ("project-number",): expected_contract()["project_number"],
        ("cloud-run-jobs",): ["run-migrations", "verify-database-authority"],
        ("cloud-run-service",): valid_snapshot()["cloud_run_service"],
        ("cloud-run-service-iam",): valid_snapshot()["cloud_run_service_iam"],
        ("migration-job",): valid_snapshot()["migration_job"],
        ("migration-job-iam",): valid_snapshot()["migration_job_iam"],
        ("database-authority-job",): valid_snapshot()["database_authority_job"],
        ("database-authority-job-iam",): valid_snapshot()["database_authority_job_iam"],
        ("database-authority-secret-iam",): valid_snapshot()["database_authority_secret_iam"],
        ("cloud-sql",): valid_snapshot()["cloud_sql"],
        ("service-account-keys",): valid_snapshot()["service_account_keys"],
        ("provisioner-quota-role",): valid_snapshot()["provisioner_quota_role"],
        ("provisioner-ancestor-iam",): valid_snapshot()["provisioner_ancestor_iam"],
        ("project-iam",): valid_snapshot()["project_iam"],
        ("control-plane-project-iam",): valid_snapshot()["control_plane_project_iam"],
        ("service-account-iam",): valid_snapshot()["service_account_iam"],
        ("artifact-registry-iam",): valid_snapshot()["artifact_registry_iam"],
        ("state-bucket",): valid_snapshot()["state_bucket"],
        ("state-bucket-iam",): valid_snapshot()["state_bucket_iam"],
        ("budget",): valid_snapshot()["budget"],
        ("notification-channels",): valid_snapshot()["notification_channels"],
        ("alert-policies",): valid_snapshot()["alert_policies"],
        ("logging",): valid_snapshot()["logging"],
        ("uptime-checks",): valid_snapshot()["uptime_checks"],
        ("workload-identity-provider",): valid_snapshot()["workload_identity_provider"],
    }

    snapshot = module.collect_foundation_snapshot(lambda command: commands[tuple(command)])

    assert snapshot["resource_inventory"]["cloud_run_service"] == "staff-tracer"
    assert snapshot["cloud_run_service"]["ingress"] == "INGRESS_TRAFFIC_ALL"
    assert snapshot["project_number"] == "123456789"
    assert snapshot["migration_job_iam"]["roles/run.jobsExecutor"]
    assert snapshot["uptime_checks"][0]["http_check"]["path"] == "/readiness"
    assert snapshot["state_bucket"]["versioning_enabled"] is True


def test_control_plane_inventory_and_live_collection_include_artifact_verifier() -> None:
    module = load_module()
    expected_email = "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com"

    assert expected_email in module._expected_control_plane_service_accounts("state-project")


def test_live_runner_skips_key_and_iam_queries_for_absent_future_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    contract = expected_contract()
    future_identity = "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com"
    calls: list[tuple[str, ...]] = []

    def fake_run_json_command(command: list[str], *, context: str) -> Any:
        calls.append(tuple(command))
        if context == "service accounts":
            return [
                {"email": email} for email in module._expected_service_accounts("example-project")
            ]
        if context == "control-plane service accounts":
            return [
                {"email": email}
                for email in module._expected_control_plane_service_accounts("state-project")
                if email != future_identity
            ]
        return [] if context.startswith("service account keys") else {"bindings": []}

    monkeypatch.setattr(mutable_module, "_run_json_command", fake_run_json_command)
    runner = module._build_live_command_runner(contract)

    runner(("service-accounts",))
    keys = runner(("service-account-keys",))
    iam = runner(("service-account-iam",))

    assert keys[future_identity] == []
    assert iam[future_identity] == {}
    assert all(future_identity not in " ".join(command) for command in calls[2:])


def test_live_runner_reads_control_plane_project_iam_from_control_plane_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    calls: list[tuple[list[str], str]] = []

    def fake_run_json_command(command: list[str], *, context: str) -> Any:
        calls.append((command, context))
        return {
            "bindings": [
                {
                    "role": "roles/iam.serviceAccountTokenCreator",
                    "members": ["user:unexpected@example.com"],
                }
            ]
        }

    monkeypatch.setattr(mutable_module, "_run_json_command", fake_run_json_command)

    result = module._build_live_command_runner(expected_contract())(("control-plane-project-iam",))

    assert result == {"roles/iam.serviceAccountTokenCreator": ["user:unexpected@example.com"]}
    assert calls == [
        (
            [
                "gcloud",
                "projects",
                "get-iam-policy",
                "state-project",
                "--format=json",
            ],
            "control-plane project iam",
        )
    ]


def test_list_logging_exclusions_uses_token_header_and_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    requests: list[Any] = []
    payloads: list[dict[str, Any]] = [
        {"exclusions": [{"name": "first"}], "nextPageToken": "next-token"},
        {"exclusions": [{"name": "second"}]},
    ]

    class FakeResponse:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

    def fake_urlopen(request: Any, *, timeout: int) -> FakeResponse:
        assert timeout == 30
        requests.append(request)
        return FakeResponse(payloads.pop(0))

    monkeypatch.setattr(
        mutable_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="short-lived-token\n"),
    )
    monkeypatch.setattr(mutable_module, "urlopen", fake_urlopen)

    exclusions = module._list_logging_exclusions("example-project")

    assert exclusions == [{"name": "first"}, {"name": "second"}]
    assert requests[0].get_header("Authorization") == "Bearer short-lived-token"
    assert requests[0].full_url.endswith("/projects/example-project/exclusions")
    assert requests[1].full_url.endswith("?pageToken=next-token")


def test_list_logging_exclusions_rejects_malformed_next_page_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"exclusions": [], "nextPageToken": 7}'

    monkeypatch.setattr(
        mutable_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="short-lived-token\n"),
    )
    monkeypatch.setattr(mutable_module, "urlopen", lambda *_args, **_kwargs: FakeResponse())

    with pytest.raises(
        module.VerificationError, match="logging exclusions returned malformed JSON"
    ):
        module._list_logging_exclusions("example-project")


def test_list_logging_exclusions_rejects_repeated_page_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    requests: list[Any] = []

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"exclusions": [], "nextPageToken": "repeat"}'

    monkeypatch.setattr(
        mutable_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="short-lived-token\n"),
    )

    def fake_urlopen(request: Any, **_kwargs: Any) -> FakeResponse:
        requests.append(request)
        if len(requests) > 2:
            raise RuntimeError("unexpected third page request")
        return FakeResponse()

    monkeypatch.setattr(mutable_module, "urlopen", fake_urlopen)

    with pytest.raises(
        module.VerificationError, match="logging exclusions returned malformed JSON"
    ):
        module._list_logging_exclusions("example-project")

    assert len(requests) == 2


def test_list_logging_exclusions_normalizes_non_utf8_response_to_safe_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    mutable_module = cast(Any, module)

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return b"\xff"

    monkeypatch.setattr(
        mutable_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="short-lived-token\n"),
    )
    monkeypatch.setattr(mutable_module, "urlopen", lambda *_args, **_kwargs: FakeResponse())

    with pytest.raises(module.VerificationError, match="logging exclusions read failed"):
        module._list_logging_exclusions("example-project")


def test_evaluate_foundation_snapshot_fails_closed_on_artifact_verifier_user_managed_key() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["service_account_keys"][
        "golden-rose-artifact-verifier@state-project.iam.gserviceaccount.com"
    ] = [{"name": "redacted-key-id"}]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("service account keys detected" in violation for violation in violations)


def test_collect_foundation_snapshot_rejects_duplicate_enabled_apis() -> None:
    module = load_module()
    commands = {
        ("project-labels",): {"environment": "develop"},
        ("enabled-apis",): ["run.googleapis.com", "run.googleapis.com"],
        ("service-accounts",): [],
        ("project-number",): "123456789",
        ("cloud-run-jobs",): [],
        ("cloud-run-service",): {},
        ("cloud-run-service-iam",): {},
        ("migration-job",): {},
        ("migration-job-iam",): {},
        ("database-authority-job",): {},
        ("database-authority-job-iam",): {},
        ("database-authority-secret-iam",): {
            "migration-database-url": {},
            "runtime-database-url": {},
        },
        ("cloud-sql",): {},
        ("service-account-keys",): {},
        ("project-iam",): {},
        ("control-plane-project-iam",): {},
        ("service-account-iam",): {},
        ("artifact-registry-iam",): {},
        ("state-bucket",): {},
        ("state-bucket-iam",): {},
        ("budget",): {},
        ("notification-channels",): [],
        ("alert-policies",): [],
        ("logging",): {},
        ("uptime-checks",): [],
        ("workload-identity-provider",): {},
    }

    with pytest.raises(ValueError, match="duplicate enabled API"):
        module.collect_foundation_snapshot(lambda command: commands[tuple(command)])


def test_evaluate_foundation_snapshot_accepts_expected_snapshot() -> None:
    module = load_module()

    assert module.evaluate_foundation_snapshot(valid_snapshot(), expected_contract()) == []


def test_evaluate_foundation_snapshot_requires_provisioner_state_bucket_authority() -> None:
    module = load_module()
    contract = expected_contract() | {
        "state_authority_principal": "user:state.authority@example.com"
    }
    snapshot = valid_snapshot()
    snapshot["state_bucket_iam"]["roles/storage.objectAdmin"] = [
        contract["state_authority_principal"],
        contract["recovery_authority_principal"],
        "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com",
    ]

    assert module.evaluate_foundation_snapshot(snapshot, contract) == []


def test_evaluate_foundation_snapshot_accepts_exact_provisioner_operator_token_creator() -> None:
    module = load_module()
    contract = expected_contract() | {
        "provisioner_operator_principal": "user:provisioner.operator@example.com"
    }
    snapshot = valid_snapshot()
    snapshot["service_account_iam"][
        "golden-rose-provisioner@state-project.iam.gserviceaccount.com"
    ] = {"roles/iam.serviceAccountTokenCreator": [contract["provisioner_operator_principal"]]}

    assert module.evaluate_foundation_snapshot(snapshot, contract) == []


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "wrong_user",
        "extra_role",
        "extra_member",
        "wif_substitution",
    ],
)
def test_evaluate_foundation_snapshot_rejects_provisioner_operator_authority_drift(
    mutation: str,
) -> None:
    module = load_module()
    contract = expected_contract()
    snapshot = valid_snapshot()
    email = "golden-rose-provisioner@state-project.iam.gserviceaccount.com"
    expected_principal = contract["provisioner_operator_principal"]
    authority = {"roles/iam.serviceAccountTokenCreator": [expected_principal]}
    if mutation == "missing":
        authority = {}
    elif mutation == "wrong_user":
        authority["roles/iam.serviceAccountTokenCreator"] = ["user:other@example.com"]
    elif mutation == "extra_role":
        authority["roles/iam.serviceAccountUser"] = [expected_principal]
    elif mutation == "extra_member":
        authority["roles/iam.serviceAccountTokenCreator"].append("user:other@example.com")
    else:
        authority["roles/iam.serviceAccountTokenCreator"] = [
            "principalSet://iam.googleapis.com/projects/123/locations/global/"
            "workloadIdentityPools/golden-rose-github/attribute.workflow_ref/example"
        ]
    snapshot["service_account_iam"][email] = authority

    violations = module.evaluate_foundation_snapshot(snapshot, contract)

    assert any("provisioner" in violation for violation in violations)


@pytest.mark.parametrize(
    "principal",
    [
        "group:operators@example.com",
        "serviceAccount:operator@example.iam.gserviceaccount.com",
        "user:not-an-email",
        "user:name@host",
    ],
)
def test_evaluate_foundation_snapshot_rejects_non_user_provisioner_operator_contract(
    principal: str,
) -> None:
    module = load_module()
    contract = expected_contract() | {"provisioner_operator_principal": principal}
    snapshot = valid_snapshot()
    snapshot["service_account_iam"][
        "golden-rose-provisioner@state-project.iam.gserviceaccount.com"
    ] = {"roles/iam.serviceAccountTokenCreator": [principal]}

    violations = module.evaluate_foundation_snapshot(snapshot, contract)

    assert any("provisioner operator binding drifted" in violation for violation in violations)


@pytest.mark.parametrize(
    "role",
    [
        "roles/iam.serviceAccountTokenCreator",
        "roles/iam.workloadIdentityUser",
    ],
)
def test_evaluate_foundation_snapshot_rejects_control_plane_project_wide_impersonation_role(
    role: str,
) -> None:
    module = load_module()
    contract = expected_contract()
    snapshot = valid_snapshot()
    snapshot["control_plane_project_iam"][role] = [contract["provisioner_operator_principal"]]

    violations = module.evaluate_foundation_snapshot(snapshot, contract)

    assert any(
        f"control-plane project-wide impersonation authority detected: {role}" in violation
        for violation in violations
    )


@pytest.mark.parametrize(
    "role",
    [
        "roles/storage.objectAdmin",
        "roles/storage.admin",
        "roles/storage.objectViewer",
        "roles/owner",
        "projects/state-project/roles/customProvisioner",
    ],
)
def test_evaluate_foundation_snapshot_rejects_any_project_wide_provisioner_role(
    role: str,
) -> None:
    module = load_module()
    contract = expected_contract()
    snapshot = valid_snapshot()
    provisioner = (
        "serviceAccount:golden-rose-provisioner@"
        f"{contract['control_plane_project_id']}.iam.gserviceaccount.com"
    )
    snapshot["control_plane_project_iam"][role] = [provisioner]

    violations = module.evaluate_foundation_snapshot(snapshot, contract)

    assert any(
        f"control-plane project-wide provisioner authority detected: {role}" in violation
        for violation in violations
    )


def test_evaluate_foundation_snapshot_rejects_missing_control_plane_project_iam() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot.pop("control_plane_project_iam")

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert "control-plane project IAM inventory missing" in violations


def test_evaluate_foundation_snapshot_allows_only_two_logging_to_logging_sinks() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["logging"]["sinks"] = [
        {
            "name": "reviewed-sink-a",
            "destination": "logging.googleapis.com/projects/example-project/locations/global/buckets/_Default",
        },
        {
            "name": "reviewed-sink-b",
            "destination": "logging.googleapis.com/projects/example-project/locations/global/buckets/_Required",
        },
    ]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert not any("logging sink" in violation for violation in violations)


@pytest.mark.parametrize(
    ("name", "destination"),
    [
        (
            "reviewed-sink",
            "logging.googleapis.com/projects/foreign-project/locations/global/buckets/export",
        ),
        ("reviewed-sink", "logging.googleapis.com/"),
        ("", "logging.googleapis.com/projects/example-project/locations/global/buckets/_Default"),
        ("reviewed-sink", "storage.googleapis.com/projects/example-project/buckets/export"),
    ],
)
def test_evaluate_foundation_snapshot_rejects_unreviewed_logging_sink_destination(
    name: str, destination: str
) -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["logging"]["sinks"][0] = {"name": name, "destination": destination}

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("logging sink" in violation for violation in violations)


def test_evaluate_foundation_snapshot_rejects_duplicate_logging_sink_id() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["logging"]["sinks"][1] = dict(snapshot["logging"]["sinks"][0])

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("logging sink" in violation for violation in violations)


def test_evaluate_foundation_snapshot_allows_exact_active_bootstrap_owner_exception() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    contract = expected_contract()
    contract["bootstrap_operator_status"] = "bootstrap-active"
    snapshot["project_iam"] = {
        **snapshot["project_iam"],
        "roles/owner": [contract["bootstrap_operator_principal"]],
        "roles/artifactregistry.admin": [contract["bootstrap_operator_principal"]],
        "roles/iam.serviceAccountCreator": [contract["bootstrap_operator_principal"]],
        "roles/resourcemanager.projectIamAdmin": [contract["bootstrap_operator_principal"]],
        "roles/containerregistry.ServiceAgent": [
            "serviceAccount:service-123456789@containerregistry.iam.gserviceaccount.com"
        ],
    }

    violations = module.evaluate_foundation_snapshot(snapshot, contract)

    assert not any(
        "project IAM" in violation or "basic role" in violation for violation in violations
    )


def test_active_bootstrap_rejects_service_agent_role_for_provisioner() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    contract = expected_contract()
    contract["bootstrap_operator_status"] = "bootstrap-active"
    snapshot["project_iam"] = {
        **snapshot["project_iam"],
        "roles/owner": [contract["bootstrap_operator_principal"]],
        "roles/run.serviceAgent": [
            "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com"
        ],
    }

    violations = module.evaluate_foundation_snapshot(snapshot, contract)

    assert any("project IAM" in violation for violation in violations)


def test_evaluate_foundation_snapshot_rejects_nonexact_public_invoker_and_basic_role() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["cloud_run_service_iam"]["roles/run.invoker"] = ["allAuthenticatedUsers"]
    snapshot["project_iam"]["roles/editor"] = ["user:admin@example.com"]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("IAM drifted for roles/run.invoker" in violation for violation in violations)
    assert any("basic role" in violation for violation in violations)


def test_evaluate_foundation_snapshot_fails_closed_on_unexpected_project_role() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["project_iam"]["roles/artifactregistry.admin"] = ["user:unexpected@example.com"]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("project IAM role inventory drifted" in violation for violation in violations)


def test_evaluate_foundation_snapshot_fails_closed_on_artifact_registry_writer_drift() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["artifact_registry_iam"]["roles/artifactregistry.writer"] = ["allUsers"]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("public Artifact Registry writer" in violation for violation in violations)


def test_evaluate_foundation_snapshot_fails_closed_on_artifact_registry_extra_privileged_role() -> (
    None
):
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["artifact_registry_iam"]["roles/artifactregistry.repoAdmin"] = [
        "serviceAccount:golden-rose-image-publisher@state-project.iam.gserviceaccount.com"
    ]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("Artifact Registry IAM roles drifted" in violation for violation in violations)


def test_evaluate_foundation_snapshot_fails_closed_on_control_plane_user_managed_key() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["service_account_keys"][
        "golden-rose-provisioner@state-project.iam.gserviceaccount.com"
    ] = [{"name": "redacted-key-id"}]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("service account keys detected" in violation for violation in violations)


def test_evaluate_foundation_snapshot_rejects_substituted_wif_pool_or_provider() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["workload_identity_provider"]["pool_id"] = "unexpected-pool"
    snapshot["workload_identity_provider"]["provider_id"] = "unexpected-provider"

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("workload identity pool drifted" in violation for violation in violations)
    assert any("workload identity provider drifted" in violation for violation in violations)


def test_evaluate_foundation_snapshot_requires_exact_authority_specific_workflow_claims() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["service_account_iam"][
        "golden-rose-image-publisher@state-project.iam.gserviceaccount.com"
    ] = {
        "roles/iam.workloadIdentityUser": [
            "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.workflow_ref/b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop"
        ]
    }

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("WIF principal binding drifted" in violation for violation in violations)


def test_evaluate_foundation_snapshot_requires_exact_artifact_verifier_reader_binding() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["artifact_registry_iam"]["roles/artifactregistry.reader"] = [
        "serviceAccount:golden-rose-deployer@state-project.iam.gserviceaccount.com"
    ]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("Artifact Registry reader bindings drifted" in violation for violation in violations)


def test_evaluate_foundation_snapshot_requires_workflow_dispatch_event_claim() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["workload_identity_provider"]["attribute_condition"] = snapshot[
        "workload_identity_provider"
    ]["attribute_condition"].replace(
        'attribute.event_name == "workflow_dispatch"',
        'attribute.event_name == "push"',
    )

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("attribute condition drifted" in violation for violation in violations)


@pytest.mark.parametrize(
    "broadening",
    [
        " || true",
        ' || attribute.repository == "unreviewed/example"',
    ],
)
def test_evaluate_foundation_snapshot_rejects_additive_wif_condition_broadening(
    broadening: str,
) -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["workload_identity_provider"]["attribute_condition"] += broadening

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("attribute condition drifted" in violation for violation in violations)


def test_budget_channel_resource_name_is_resolved_to_expected_channel_identity() -> None:
    module = load_module()

    assert module.evaluate_foundation_snapshot(valid_snapshot(), expected_contract()) == []


def test_display_name_cannot_substitute_for_budget_channel_resource_name() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["budget"]["notification_channel_resource_names"] = [
        "Develop private synthetic alert route"
    ]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("channel identity" in violation for violation in violations)


def test_foundation_mode_rejects_job_or_service_inventory() -> None:
    module = load_module()
    snapshot = valid_snapshot()

    violations = module.evaluate_foundation_snapshot(
        snapshot, expected_contract(), mode="foundation"
    )

    assert any(
        "foundation verifier mode rejects present cloud_run_service" in violation
        for violation in violations
    )
    assert any(
        "foundation verifier mode rejects present cloud_run_job" in violation
        for violation in violations
    )


def test_foundation_mode_treats_cloud_sql_as_deferred_but_later_modes_still_require_it() -> None:
    module = load_module()

    snapshot_missing_sql = valid_snapshot()
    snapshot_missing_sql["resource_inventory"]["cloud_run_service"] = ""
    snapshot_missing_sql["cloud_run_service"] = {}
    snapshot_missing_sql["cloud_run_service_iam"] = {}
    snapshot_missing_sql["resource_inventory"]["cloud_run_job"] = ""
    snapshot_missing_sql["migration_job"] = {}
    snapshot_missing_sql["migration_job_iam"] = {}
    snapshot_missing_sql["resource_inventory"]["cloud_sql_instance"] = ""
    snapshot_missing_sql["cloud_sql"] = {}

    missing_sql_violations = module.evaluate_foundation_snapshot(
        snapshot_missing_sql,
        expected_contract(),
        mode="foundation",
    )

    assert all(
        "cloud sql inventory drifted from develop-postgres" not in violation
        for violation in missing_sql_violations
    )
    assert all(
        "cloud sql version drifted from POSTGRES_16" not in violation
        for violation in missing_sql_violations
    )
    assert all(
        "public Cloud SQL path detected" not in violation for violation in missing_sql_violations
    )

    snapshot_public_sql = valid_snapshot()
    snapshot_public_sql["resource_inventory"]["cloud_run_service"] = ""
    snapshot_public_sql["cloud_run_service"] = {}
    snapshot_public_sql["cloud_run_service_iam"] = {}
    snapshot_public_sql["resource_inventory"]["cloud_run_job"] = ""
    snapshot_public_sql["migration_job"] = {}
    snapshot_public_sql["migration_job_iam"] = {}
    snapshot_public_sql["cloud_sql"]["database_version"] = "POSTGRES_15"
    snapshot_public_sql["cloud_sql"]["ipv4_enabled"] = True
    snapshot_public_sql["cloud_sql"]["private_network"] = ""

    public_sql_violations = module.evaluate_foundation_snapshot(
        snapshot_public_sql,
        expected_contract(),
        mode="foundation",
    )

    assert any(
        "unexpected cloud sql inventory present in foundation mode" in violation
        for violation in public_sql_violations
    )
    assert all(
        "cloud sql version drifted from POSTGRES_16" not in violation
        for violation in public_sql_violations
    )
    assert all(
        "public Cloud SQL path detected" not in violation for violation in public_sql_violations
    )

    migration_missing_sql_violations = module.evaluate_foundation_snapshot(
        snapshot_missing_sql,
        expected_contract(),
        mode="migration",
    )
    assert any(
        "cloud sql inventory drifted from develop-postgres" in violation
        for violation in migration_missing_sql_violations
    )

    service_missing_sql_violations = module.evaluate_foundation_snapshot(
        snapshot_missing_sql,
        expected_contract(),
        mode="service",
    )
    assert any(
        "cloud sql inventory drifted from develop-postgres" in violation
        for violation in service_missing_sql_violations
    )

    snapshot_with_workloads = valid_snapshot()
    workload_violations = module.evaluate_foundation_snapshot(
        snapshot_with_workloads,
        expected_contract(),
        mode="foundation",
    )

    assert any(
        "foundation verifier mode rejects present cloud_run_service workload" in violation
        for violation in workload_violations
    )
    assert any(
        "foundation verifier mode rejects present cloud_run_job workload" in violation
        for violation in workload_violations
    )


def test_migration_mode_requires_configured_job_and_no_service() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["resource_inventory"]["cloud_run_service"] = ""
    snapshot["cloud_run_service"] = {}
    snapshot["cloud_run_service_iam"] = {}
    snapshot["uptime_checks"] = []
    snapshot["alert_policies"] = [
        "Develop private synthetic health failures",
        "Develop private synthetic service error events",
    ]

    assert (
        module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="migration") == []
    )

    snapshot_missing_job = valid_snapshot()
    snapshot_missing_job["resource_inventory"]["cloud_run_job"] = ""
    snapshot_missing_job["migration_job"] = {}
    violations = module.evaluate_foundation_snapshot(
        snapshot_missing_job, expected_contract(), mode="migration"
    )

    assert any("requires cloud_run_job to be present" in violation for violation in violations)


def test_service_mode_requires_reviewed_revision_digest_configuration_and_iam() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["cloud_run_service"]["image"] = (
        "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer:latest"
    )
    snapshot["cloud_run_service_iam"]["roles/run.invoker"] = []

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("digest-bound cloud run service image" in violation for violation in violations)
    assert any("IAM drifted for roles/run.invoker" in violation for violation in violations)


def test_foundation_verifier_distinguishes_network_reachability_from_iam_privacy() -> None:
    module = load_module()

    assert (
        module.evaluate_foundation_snapshot(valid_snapshot(), expected_contract(), mode="service")
        == []
    )


def test_foundation_verifier_requires_public_minimized_readiness_uptime_check() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["uptime_checks"] = []

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("public minimized readiness uptime check" in violation for violation in violations)


def test_live_uptime_collector_omits_absent_service_agent_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    contract = expected_contract()
    payload = {
        "displayName": "Develop private synthetic public readiness",
        "period": "300s",
        "timeout": "10s",
        "selectedRegions": ["USA"],
        "monitoredResource": {
            "type": "uptime_url",
            "labels": {
                "host": "staff-tracer-example-uc.a.run.app",
                "project_id": "example-project",
            },
        },
        "httpCheck": {
            "requestMethod": "GET",
            "path": "/readiness",
            "port": 443,
            "useSsl": True,
            "validateSsl": True,
        },
    }

    monkeypatch.setattr(module, "_run_json_command", lambda *args, **kwargs: [payload])

    uptime_checks = module._build_live_command_runner(contract)(("uptime-checks",))
    snapshot = valid_snapshot()
    snapshot["uptime_checks"] = uptime_checks

    assert uptime_checks == valid_snapshot()["uptime_checks"]
    assert module.evaluate_foundation_snapshot(snapshot, contract, mode="service") == []


def test_uptime_check_and_monitoring_invoker_are_absent_before_service_stage() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["resource_inventory"]["cloud_run_service"] = ""
    snapshot["cloud_run_service"] = {}
    snapshot["cloud_run_service_iam"] = {}
    snapshot["uptime_checks"] = []
    snapshot["alert_policies"] = [
        "Develop private synthetic health failures",
        "Develop private synthetic service error events",
    ]

    assert (
        module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="migration") == []
    )


def test_service_stage_has_exactly_one_public_readiness_uptime_check() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["uptime_checks"].append({"display_name": "unexpected-second-check"})

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any(
        "exactly one public minimized readiness uptime check" in violation
        for violation in violations
    )


def test_service_stage_rejects_extra_invoker_and_migration_job_iam_drift() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["cloud_run_service_iam"]["roles/run.invoker"].append(
        "serviceAccount:unexpected@example-project.iam.gserviceaccount.com"
    )
    snapshot["migration_job_iam"]["roles/run.jobsExecutor"] = []

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("IAM drifted for roles/run.invoker" in violation for violation in violations)
    assert any("migration job IAM" in violation for violation in violations)


def test_service_stage_requires_full_public_readiness_uptime_configuration() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["uptime_checks"][0]["monitored_resource"]["labels"]["host"] = "wrong.example"
    snapshot["uptime_checks"][0]["http_check"] = {
        "request_method": "POST",
        "path": "/health",
        "port": 80,
        "use_ssl": False,
        "validate_ssl": False,
        "service_agent_authentication": {"type": "NONE"},
    }

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("uptime check configuration drifted" in violation for violation in violations)


def test_public_invoker_rejects_substituted_extra_empty_group_domain_and_principal_set() -> None:
    module = load_module()
    for invokers in [
        [],
        ["user:other@example.com", "user:second@example.com"],
        ["group:testers@example.com"],
        ["domain:example.com"],
        [
            "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/example/subject/tester"
        ],
        ["allAuthenticatedUsers"],
    ]:
        snapshot = valid_snapshot()
        snapshot["cloud_run_service_iam"]["roles/run.invoker"] = invokers
        violations = module.evaluate_foundation_snapshot(
            snapshot, expected_contract(), mode="service"
        )
        assert any(
            "invoker" in violation.lower() or "public" in violation.lower()
            for violation in violations
        )


def test_verifier_rejects_missing_required_api_even_when_extra_apis_are_observed() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["enabled_apis"].remove("billingbudgets.googleapis.com")
    snapshot["enabled_apis"].append("cloudbuild.googleapis.com")

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("required APIs missing" in violation for violation in violations)


def test_verifier_allows_observed_extra_apis_when_every_required_api_is_enabled() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["enabled_apis"].append("cloudbuild.googleapis.com")

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert not any("approved APIs drifted" in violation for violation in violations)


def test_verifier_rejects_arbitrary_deployer_principal_not_derived_from_control_plane_project() -> (
    None
):
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["migration_job_iam"]["roles/run.jobsExecutor"] = [
        "serviceAccount:arbitrary-deployer@other-project.iam.gserviceaccount.com"
    ]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any(
        "migration job IAM drifted for roles/run.jobsExecutor" in violation
        for violation in violations
    )


def test_bindings_to_role_map_aggregates_duplicate_roles_and_rejects_conditional_bindings() -> None:
    module = load_module()

    role_map = module._bindings_to_role_map(
        {
            "bindings": [
                {"role": "roles/artifactregistry.writer", "members": ["allUsers"]},
                {
                    "role": "roles/artifactregistry.writer",
                    "members": [
                        "serviceAccount:golden-rose-image-publisher@state-project.iam.gserviceaccount.com"
                    ],
                },
            ]
        }
    )

    assert role_map["roles/artifactregistry.writer"] == [
        "allUsers",
        "serviceAccount:golden-rose-image-publisher@state-project.iam.gserviceaccount.com",
    ]
    with pytest.raises(module.VerificationError, match="conditional IAM binding"):
        module._bindings_to_role_map(
            {
                "bindings": [
                    {
                        "role": "roles/artifactregistry.writer",
                        "members": ["allUsers"],
                        "condition": {"title": "temporary"},
                    }
                ]
            }
        )


def test_render_violations_redacts_sensitive_values() -> None:
    module = load_module()
    rendered = module.render_violations(
        [
            "serviceAccount:staff-tracer-runtime@example-project.iam.gserviceaccount.com has unexpected role in example-project",
            "group:observability@example.com missing logging.viewer",
        ]
    )

    assert "example-project" not in rendered
    assert "observability@example.com" not in rendered
    assert "staff-tracer-runtime@example-project.iam.gserviceaccount.com" not in rendered
    assert "[REDACTED]" in rendered


def test_validated_evidence_output_path_rejects_symlink_ancestor_and_non_markdown(
    tmp_path: Path,
) -> None:
    module = load_module()
    target_root = tmp_path / "real"
    target_root.mkdir()
    symlink_root = tmp_path / "link"
    symlink_root.symlink_to(target_root, target_is_directory=True)

    with pytest.raises(module.VerificationError, match="symlink components"):
        module._validated_evidence_output_path(str(symlink_root), "foundation.md")

    with pytest.raises(module.VerificationError, match="simple markdown basename"):
        module._validated_evidence_output_path(str(tmp_path), "foundation.txt")


def test_atomic_write_text_replaces_existing_content(tmp_path: Path) -> None:
    module = load_module()
    destination = tmp_path / "evidence" / "foundation.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("old", encoding="utf-8")

    module._atomic_write_text(destination, "new evidence")

    assert destination.read_text(encoding="utf-8") == "new evidence"


def test_atomic_write_text_rejects_renamed_parent_replaced_with_symlink(tmp_path: Path) -> None:
    module = load_module()
    destination = tmp_path / "evidence" / "foundation.md"
    destination.parent.mkdir(parents=True)
    escaped = tmp_path / "escaped"
    escaped.mkdir()
    displaced_parent = tmp_path / "displaced-evidence"

    def swap_parent_to_symlink() -> None:
        destination.parent.rename(displaced_parent)
        destination.parent.symlink_to(escaped, target_is_directory=True)

    with pytest.raises(module.VerificationError, match="reviewed directory"):
        module._atomic_write_text(
            destination, "new evidence", before_replace=swap_parent_to_symlink
        )

    assert not (escaped / "foundation.md").exists()
    assert not (displaced_parent / "foundation.md").exists()
