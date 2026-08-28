import importlib.util
import json
from pathlib import Path
from types import ModuleType
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
        "state_bucket_name": "example-terraform-state",
        "private_invoker_principal": "user:private.tester@example.com",
        "state_authority_principal": "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com",
        "recovery_authority_principal": "group:recovery@example.com",
        "bootstrap_operator_principal": "user:bootstrap@example.com",
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
        "--state-bucket-name",
        "example-terraform-state",
        "--state-authority-principal",
        "serviceAccount:golden-rose-provisioner@state-project.iam.gserviceaccount.com",
        "--recovery-authority-principal",
        "group:recovery@example.com",
        "--bootstrap-operator-principal",
        "user:bootstrap@example.com",
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
        },
        "cloud_run_service_iam": {
            "roles/run.invoker": [
                contract["private_invoker_principal"],
                "serviceAccount:service-123456789@gcp-sa-monitoring-notification.iam.gserviceaccount.com",
            ],
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
            "parallelism": 1,
            "task_count": 1,
            "image": "us-east4-docker.pkg.dev/example-project/staff-tracer-images/staff-tracer@sha256:2222222222222222222222222222222222222222222222222222222222222222",
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
            "staff-tracer-runtime@example-project.iam.gserviceaccount.com": {},
            "staff-tracer-migration@example-project.iam.gserviceaccount.com": {},
            "golden-rose-provisioner@state-project.iam.gserviceaccount.com": {},
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
            "sinks": [],
            "exclusions": {
                "develop-exclude-uuid-bearing-staff-paths": 'resource.type="cloud_run_revision" AND httpRequest.requestUrl=~"/api/staff/v1/employers/[0-9a-fA-F-]{36}(/contacts(/[0-9a-fA-F-]{36})?)?$"'
            },
        },
        "uptime_checks": [
            {
                "display_name": "Develop private synthetic authenticated readiness",
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
                    "service_agent_authentication": {"type": "OIDC_TOKEN"},
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


def test_verify_gcp_foundation_script_exists_and_template_is_value_safe() -> None:
    assert MODULE_PATH.exists()
    assert EVIDENCE_TEMPLATE_PATH.exists()
    template = EVIDENCE_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "[REDACTED]" in template
    assert "read-only" in template.lower()


def test_manifest_lists_verify_gcp_foundation_script_entrypoint() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "scripts/verify_gcp_foundation.py" in manifest["scripts"]["entrypoints"]


def test_live_foundation_verifier_derives_private_invoker_from_a_signed_receipt() -> None:
    module = load_module()
    parsed = module._parse_args(
        [
            *verifier_common_args(),
            "--tester-authority-receipt",
            "private/tester-receipt.json",
            "--tester-authority-bundle",
            "private/tester-receipt.sigstore.json",
            "--tester-authority-certificate-identity",
            "https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
        ]
    )

    assert parsed.tester_authority_receipt.name == "tester-receipt.json"
    assert parsed.tester_authority_bundle.name == "tester-receipt.sigstore.json"
    with pytest.raises(SystemExit):
        module._parse_args(
            [
                *verifier_common_args(),
                "--private-invoker-principal",
                "user:attacker@example.com",
            ]
        )


def test_foundation_and_migration_modes_accept_absent_tester_inputs() -> None:
    module = load_module()

    foundation = module._parse_args(verifier_common_args(mode="foundation"))
    migration = module._parse_args(verifier_common_args(mode="migration"))

    assert foundation.mode == "foundation"
    assert foundation.tester_authority_receipt is None
    assert foundation.tester_authority_bundle is None
    assert foundation.tester_authority_certificate_identity is None
    assert migration.mode == "migration"
    assert migration.tester_authority_receipt is None
    assert migration.tester_authority_bundle is None
    assert migration.tester_authority_certificate_identity is None


def test_service_mode_rejects_absent_tester_inputs_before_live_reads() -> None:
    module = load_module()
    mutable_module = cast(Any, module)

    def fail_derive(**_: Any) -> dict[str, str]:
        raise AssertionError(
            "service-mode missing-tester rejection should happen before derivation"
        )

    def fail_collect(_: Any) -> dict[str, Any]:
        raise AssertionError(
            "service-mode missing-tester rejection should happen before live reads"
        )

    def fail_evaluate(*_: Any, **__: Any) -> list[str]:
        raise AssertionError(
            "service-mode missing-tester rejection should happen before evaluation"
        )

    mutable_module.derive_tester_authority_contract = fail_derive
    mutable_module.collect_foundation_snapshot = fail_collect
    mutable_module.evaluate_foundation_snapshot = fail_evaluate

    with pytest.raises(module.VerificationError, match="tester authority"):
        module.main(verifier_common_args(mode="service"))


def test_service_mode_derives_tester_authority_contract_before_evaluation(tmp_path: Path) -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    receipt = tmp_path / "tester-receipt.json"
    bundle = tmp_path / "tester-receipt.sigstore.json"
    calls: dict[str, Any] = {}

    def fake_derive(**kwargs: Any) -> dict[str, str]:
        calls["derive"] = kwargs
        return {
            "private_invoker_principal": "user:private.tester@example.com",
            "tester_authority_receipt_sha256": "a" * 64,
        }

    def fake_collect(_: Any, *, mode: str = "service") -> dict[str, Any]:
        calls["collect"] = mode
        return valid_snapshot()

    def fake_evaluate(
        snapshot: dict[str, Any], contract: dict[str, Any], *, mode: str
    ) -> list[str]:
        calls["evaluate"] = {"snapshot": snapshot, "contract": contract, "mode": mode}
        return []

    mutable_module.derive_tester_authority_contract = fake_derive
    mutable_module.collect_foundation_snapshot = fake_collect
    mutable_module.evaluate_foundation_snapshot = fake_evaluate

    exit_code = module.main(
        [
            *verifier_common_args(mode="service"),
            "--tester-authority-receipt",
            str(receipt),
            "--tester-authority-bundle",
            str(bundle),
            "--tester-authority-certificate-identity",
            "https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
        ]
    )

    assert exit_code == 0
    assert calls["derive"]["receipt_path"] == receipt
    assert calls["derive"]["bundle_path"] == bundle
    assert calls["derive"]["certificate_identity"] == (
        "https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main"
    )
    assert calls["collect"] == "service"
    assert calls["evaluate"]["mode"] == "service"
    assert calls["evaluate"]["contract"]["private_invoker_principal"] == (
        "user:private.tester@example.com"
    )
    assert calls["evaluate"]["contract"]["tester_authority_receipt_sha256"] == "a" * 64


def test_foundation_mode_main_allows_absent_cloud_sql_during_collection() -> None:
    module = load_module()
    mutable_module = cast(Any, module)
    calls: dict[str, Any] = {"cloud_sql_requested": False, "commands": []}

    def fake_build_live_command_runner(contract: dict[str, Any]) -> Any:
        calls["contract"] = contract

        def runner(command: Any) -> Any:
            key = tuple(command)
            calls["commands"].append(key)
            if key == ("cloud-sql",):
                calls["cloud_sql_requested"] = True
                raise module.VerificationError("cloud sql failed: NOT_FOUND")
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
                ("cloud-run-service",): {},
                ("cloud-run-service-iam",): {},
                ("migration-job",): {},
                ("migration-job-iam",): {},
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
    assert calls["cloud_sql_requested"] is True
    assert calls["evaluate"]["mode"] == "foundation"
    assert calls["evaluate"]["snapshot"]["cloud_sql"] == {}
    assert calls["evaluate"]["snapshot"]["resource_inventory"]["cloud_sql_instance"] == ""


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


def test_live_foundation_verifier_uses_receipt_derived_principal_and_digest(tmp_path: Path) -> None:
    module = load_module()
    receipt = tmp_path / "tester-receipt.json"
    bundle = tmp_path / "tester-receipt.sigstore.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "golden-rose.tester-authority/v1",
                "principal": "user:private.tester@example.com",
                "scope": {
                    "project_id": "example-project",
                    "region": "us-east4",
                    "service": "staff-tracer",
                    "role": "roles/run.invoker",
                },
                "approval_reference": "operator-held",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    bundle.write_text("{}", encoding="utf-8")

    derived = module.derive_tester_authority_contract(
        receipt_path=receipt,
        bundle_path=bundle,
        certificate_identity="https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
        project_id="example-project",
        region="us-east4",
        verifier_runner=lambda command: None,
    )

    assert derived["private_invoker_principal"] == "user:private.tester@example.com"
    assert len(derived["tester_authority_receipt_sha256"]) == 64


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
        ("cloud-run-service",): valid_snapshot()["cloud_run_service"],
        ("cloud-run-service-iam",): valid_snapshot()["cloud_run_service_iam"],
        ("migration-job",): valid_snapshot()["migration_job"],
        ("migration-job-iam",): valid_snapshot()["migration_job_iam"],
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
        ("cloud-run-service",): {},
        ("cloud-run-service-iam",): {},
        ("migration-job",): {},
        ("migration-job-iam",): {},
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
        ("uptime-checks",): [],
        ("workload-identity-provider",): {},
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
        {
            **expected_contract(),
            "private_invoker_principal": "user:private.tester@example.com",
            "tester_authority_receipt_sha256": "a" * 64,
        },
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
    assert any("invoker bindings drifted" in violation for violation in violations)


def test_foundation_verifier_distinguishes_network_reachability_from_iam_privacy() -> None:
    module = load_module()

    assert (
        module.evaluate_foundation_snapshot(valid_snapshot(), expected_contract(), mode="service")
        == []
    )


def test_foundation_verifier_requires_authenticated_readiness_uptime_check() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["uptime_checks"] = []

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("authenticated readiness uptime check" in violation for violation in violations)


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


def test_service_stage_has_exactly_one_uptime_check_and_monitoring_invoker() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["uptime_checks"].append({"display_name": "unexpected-second-check"})

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any(
        "exactly one authenticated readiness uptime check" in violation for violation in violations
    )


def test_service_stage_requires_exact_resource_iam_and_project_number_monitoring_agent() -> None:
    module = load_module()
    snapshot = valid_snapshot()
    snapshot["cloud_run_service_iam"]["roles/run.invoker"][1] = (
        "serviceAccount:service-999999999@gcp-sa-monitoring-notification.iam.gserviceaccount.com"
    )
    snapshot["migration_job_iam"]["roles/run.jobsExecutor"] = []

    violations = module.evaluate_foundation_snapshot(snapshot, expected_contract(), mode="service")

    assert any("service-agent authority" in violation for violation in violations)
    assert any("migration job IAM" in violation for violation in violations)


def test_service_stage_requires_full_authenticated_readiness_uptime_configuration() -> None:
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


def test_tester_authority_rejects_substituted_extra_empty_group_domain_principal_set_and_public_invokers() -> (
    None
):
    module = load_module()
    for invokers in [
        [],
        ["user:other@example.com", "user:second@example.com"],
        ["group:testers@example.com"],
        ["domain:example.com"],
        [
            "principalSet://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/example/subject/tester"
        ],
        ["allUsers"],
    ]:
        snapshot = valid_snapshot()
        snapshot["cloud_run_service_iam"]["roles/run.invoker"] = invokers
        violations = module.evaluate_foundation_snapshot(
            snapshot, expected_contract(), mode="service"
        )
        assert any(
            "invoker" in violation.lower()
            or "named tester" in violation.lower()
            or "public" in violation.lower()
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
