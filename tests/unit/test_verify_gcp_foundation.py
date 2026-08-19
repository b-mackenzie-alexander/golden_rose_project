import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

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
        "control_plane_project_id": "state-project",
        "region": "us-east4",
        "state_bucket_name": "example-terraform-state",
        "private_invoker_principal": "principal://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/example/subject/private-tester",
        "deployer_principal": "serviceAccount:golden-rose-deployer@example-project.iam.gserviceaccount.com",
        "state_authority_principal": "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com",
        "recovery_authority_principal": "group:recovery@example.com",
        "bootstrap_operator_principal": "user:bootstrap@example.com",
        "bootstrap_operator_status": "bootstrap-retired",
        "observability_viewer_principal": "group:observability@example.com",
        "recovery_policy_review_status": "gate-2-evidence-required",
        "log_retention_days": 30,
    }


def valid_snapshot() -> dict[str, Any]:
    contract = expected_contract()
    return {
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
                "staff-tracer-migration@example-project.iam.gserviceaccount.com",
                "staff-tracer-runtime@example-project.iam.gserviceaccount.com",
            ],
            "control_plane_service_accounts": [
                "golden-rose-deployer@state-project.iam.gserviceaccount.com",
                "golden-rose-image-publisher@state-project.iam.gserviceaccount.com",
                "golden-rose-provisioner@state-project.iam.gserviceaccount.com",
            ],
            "cloud_run_service": "staff-tracer",
            "cloud_run_job": "run-migrations",
            "cloud_sql_instance": "develop-postgres",
            "state_bucket": contract["state_bucket_name"],
        },
        "cloud_run_service": {
            "labels": {
                "environment": "develop",
                "data_boundary": "fictional-synthetic-only",
                "managed_by": "terraform",
                "service": "staff-tracer",
                "cost_center": "develop",
                "owner": "technical-owner",
                "teardown": "intentional-runbook-only",
            },
            "ingress": "INGRESS_TRAFFIC_INTERNAL_ONLY",
            "service_account": "staff-tracer-runtime@example-project.iam.gserviceaccount.com",
        },
        "cloud_run_service_iam": {
            "roles/run.invoker": [contract["private_invoker_principal"]],
        },
        "migration_job": {
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
            "parallelism": 1,
            "task_count": 1,
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
            "golden-rose-deployer@state-project.iam.gserviceaccount.com": [],
            "golden-rose-image-publisher@state-project.iam.gserviceaccount.com": [],
            "golden-rose-provisioner@state-project.iam.gserviceaccount.com": [],
            "staff-tracer-migration@example-project.iam.gserviceaccount.com": [],
            "staff-tracer-runtime@example-project.iam.gserviceaccount.com": [],
        },
        "project_iam": {
            "roles/cloudsql.client": [
                "serviceAccount:staff-tracer-runtime@example-project.iam.gserviceaccount.com",
                "serviceAccount:staff-tracer-migration@example-project.iam.gserviceaccount.com",
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
        },
        "service_account_iam": {
            "staff-tracer-runtime@example-project.iam.gserviceaccount.com": {
                "roles/iam.serviceAccountUser": [contract["deployer_principal"]]
            },
            "staff-tracer-migration@example-project.iam.gserviceaccount.com": {
                "roles/iam.serviceAccountUser": [contract["deployer_principal"]]
            },
            "golden-rose-provisioner@state-project.iam.gserviceaccount.com": {
                "roles/iam.workloadIdentityUser": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"
                ],
                "roles/iam.serviceAccountTokenCreator": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"
                ],
            },
            "golden-rose-image-publisher@state-project.iam.gserviceaccount.com": {
                "roles/iam.workloadIdentityUser": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"
                ],
                "roles/iam.serviceAccountTokenCreator": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"
                ],
            },
            "golden-rose-deployer@state-project.iam.gserviceaccount.com": {
                "roles/iam.workloadIdentityUser": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"
                ],
                "roles/iam.serviceAccountTokenCreator": [
                    "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/golden-rose-github/attribute.repository/b-mackenzie-alexander/golden_rose_project"
                ],
            },
        },
        "artifact_registry_iam": {
            "roles/artifactregistry.writer": [
                "serviceAccount:golden-rose-image-publisher@state-project.iam.gserviceaccount.com"
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
            "notification_channels": ["Develop private synthetic alert route"],
        },
        "notification_channels": ["Develop private synthetic alert route"],
        "alert_policies": [
            "Develop private synthetic health failures",
            "Develop private synthetic readiness failures",
            "Develop private synthetic service error events",
        ],
        "logging": {
            "default_bucket_retention_days": contract["log_retention_days"],
            "sinks": [],
        },
    }


def test_verify_gcp_foundation_script_exists_and_template_is_value_safe() -> None:
    assert MODULE_PATH.exists()
    assert EVIDENCE_TEMPLATE_PATH.exists()
    template = EVIDENCE_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "[REDACTED]" in template
    assert "read-only" in template.lower()


def test_manifest_lists_verify_gcp_foundation_script_entrypoint() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "scripts/verify_gcp_foundation.py" in manifest["scripts"]["entrypoints"]


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
        ("cloud-run-service",): valid_snapshot()["cloud_run_service"],
        ("cloud-run-service-iam",): valid_snapshot()["cloud_run_service_iam"],
        ("migration-job",): valid_snapshot()["migration_job"],
        ("cloud-sql",): valid_snapshot()["cloud_sql"],
        ("service-account-keys",): valid_snapshot()["service_account_keys"],
        ("project-iam",): valid_snapshot()["project_iam"],
        ("service-account-iam",): valid_snapshot()["service_account_iam"],
        ("artifact-registry-iam",): valid_snapshot()["artifact_registry_iam"],
        ("state-bucket",): valid_snapshot()["state_bucket"],
        ("state-bucket-iam",): valid_snapshot()["state_bucket_iam"],
        ("budget",): valid_snapshot()["budget"],
        ("notification-channels",): valid_snapshot()["notification_channels"],
        ("alert-policies",): valid_snapshot()["alert_policies"],
        ("logging",): valid_snapshot()["logging"],
    }

    snapshot = module.collect_foundation_snapshot(lambda command: commands[tuple(command)])

    assert snapshot["resource_inventory"]["cloud_run_service"] == "staff-tracer"
    assert snapshot["cloud_run_service"]["ingress"] == "INGRESS_TRAFFIC_INTERNAL_ONLY"
    assert snapshot["state_bucket"]["versioning_enabled"] is True


def test_collect_foundation_snapshot_rejects_duplicate_enabled_apis() -> None:
    module = load_module()
    commands = {
        ("project-labels",): {"environment": "develop"},
        ("enabled-apis",): ["run.googleapis.com", "run.googleapis.com"],
        ("service-accounts",): [],
        ("cloud-run-service",): {},
        ("cloud-run-service-iam",): {},
        ("migration-job",): {},
        ("cloud-sql",): {},
        ("service-account-keys",): {},
        ("project-iam",): {},
        ("service-account-iam",): {},
        ("artifact-registry-iam",): {},
        ("state-bucket",): {},
        ("state-bucket-iam",): {},
        ("budget",): {},
        ("notification-channels",): [],
        ("alert-policies",): [],
        ("logging",): {},
    }

    with pytest.raises(ValueError, match="duplicate enabled API"):
        module.collect_foundation_snapshot(lambda command: commands[tuple(command)])


def test_evaluate_foundation_snapshot_accepts_expected_snapshot() -> None:
    module = load_module()

    assert module.evaluate_foundation_snapshot(valid_snapshot(), expected_contract()) == []


def test_evaluate_foundation_snapshot_fails_closed_on_public_invoker_and_basic_role() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["cloud_run_service_iam"]["roles/run.invoker"] = ["allUsers"]
    snapshot["project_iam"]["roles/editor"] = ["user:admin@example.com"]

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract())

    assert any("public Cloud Run invoker" in violation for violation in violations)
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
