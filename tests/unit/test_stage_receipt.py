import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "verify_stage_receipt.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_stage_receipt", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def receipt(stage: str = "migration") -> dict[str, object]:
    return {
        "stage": stage,
        "source_sha": "a" * 40,
        "plan_hash": "b" * 64,
        "provider_lock_digest": "c" * 64,
        "non_secret_input_digest": "d" * 64,
        "approval_reference": "operator-held",
        "evaluated_inventory": {
            "google_cloud_run_v2_job": 1,
            "google_cloud_run_v2_service": 0 if stage == "migration" else 1,
        },
        "workload_image_digest": "sha256:" + "e" * 64,
        "configuration_projection": configuration_projection(stage),
    }


def configuration_projection(stage: str = "migration") -> dict[str, object]:
    projection: dict[str, object] = {
        "resource_type": (
            "google_cloud_run_v2_job" if stage == "migration" else "google_cloud_run_v2_service"
        ),
        "name": "run-migrations" if stage == "migration" else "staff-tracer",
        "location": "us-east4",
        "service_account": (
            "golden-rose-migration@example.iam.gserviceaccount.com"
            if stage == "migration"
            else "golden-rose-runtime@example.iam.gserviceaccount.com"
        ),
        "image_digest": "sha256:" + "e" * 64,
        "environment": [
            {"name": "GOLDEN_ROSE_ENVIRONMENT", "value": "develop"},
            {
                "name": "GOLDEN_ROSE_DATABASE_URL",
                "secret": "migration-database-url"
                if stage == "migration"
                else "runtime-database-url",
                "version": "latest",
            },
        ],
        "vpc_access": {
            "egress": "PRIVATE_RANGES_ONLY",
            "network": "projects/example/global/networks/develop",
            "subnetwork": "projects/example/regions/us-east4/subnetworks/direct-vpc",
        },
    }
    if stage == "migration":
        projection.update(
            {
                "command": ["golden-rose-migrate"],
                "max_retries": 0,
                "timeout": "1800s",
                "task_count": 1,
                "parallelism": 1,
            }
        )
    else:
        projection.update(
            {
                "ingress": "INGRESS_TRAFFIC_ALL",
                "iam": {
                    "roles/run.invoker": [
                        "serviceAccount:service-123@gcp-sa-monitoring-notification.iam.gserviceaccount.com",
                        "user:private.tester@example.com",
                    ],
                    "roles/run.viewer": [
                        "serviceAccount:golden-rose-deployer@control-plane.iam.gserviceaccount.com"
                    ],
                },
            }
        )
    return projection


def test_migration_receipt_accepts_only_its_exact_stage_and_inventory() -> None:
    module = load_module()
    module.validate_stage_receipt(
        receipt(),
        expected_stage="migration",
        expected_source_sha="a" * 40,
        expected_digest="sha256:" + "e" * 64,
    )
    bad = receipt()
    bad["evaluated_inventory"] = {"google_cloud_run_v2_job": 1, "google_cloud_run_v2_service": 1}
    with pytest.raises(module.ReceiptError, match="must not contain"):
        module.validate_stage_receipt(
            bad,
            expected_stage="migration",
            expected_source_sha="a" * 40,
            expected_digest="sha256:" + "e" * 64,
        )


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (
            lambda candidate: candidate.update({"stage": "service"}),
            "stage does not match",
        ),
        (
            lambda candidate: candidate.update({"source_sha": "f" * 40}),
            "source SHA does not match",
        ),
        (
            lambda candidate: candidate.update(
                {
                    "evaluated_inventory": {
                        "google_cloud_run_v2_job": 1,
                        "google_cloud_run_v2_service": 1,
                    }
                }
            ),
            "must not contain",
        ),
        (
            lambda candidate: candidate.update(
                {"configuration_projection": configuration_projection("service")}
            ),
            "configuration projection does not match",
        ),
        (
            lambda candidate: candidate.update({"workload_image_digest": "sha256:" + "f" * 64}),
            "image digest does not match",
        ),
    ],
)
def test_service_rejects_migration_receipts_outside_the_current_transition_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: Any, error: str
) -> None:
    module = load_module()
    migration_receipt = receipt()
    mutation(migration_receipt)
    migration_path = tmp_path / "migration.json"
    migration_path.write_text(json.dumps(migration_receipt))
    migration_sha256 = hashlib.sha256(migration_path.read_bytes()).hexdigest()

    service_path = tmp_path / "service.json"
    service_path.write_text(json.dumps(receipt("service")))
    success_path = tmp_path / "migration-success.json"
    success_path.write_text(
        json.dumps(
            {
                "stage": "migration",
                "result": "success",
                "migration_receipt_sha256": migration_sha256,
                "workload_image_digest": "sha256:" + "e" * 64,
            }
        )
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "verify_stage_receipt.py",
            "--receipt",
            str(service_path),
            "--stage",
            "service",
            "--source-sha",
            "a" * 40,
            "--image-digest",
            "sha256:" + "e" * 64,
            "--migration-receipt",
            str(migration_path),
            "--migration-success-receipt",
            str(success_path),
        ],
    )

    with pytest.raises(module.ReceiptError, match=error):
        module.main()


def test_service_requires_separate_migration_success_receipt_bound_to_its_receipt_hash() -> None:
    module = load_module()
    migration = {
        "stage": "migration",
        "result": "success",
        "migration_receipt_sha256": "f" * 64,
        "workload_image_digest": "sha256:" + "e" * 64,
    }
    module.validate_migration_success_receipt(
        migration, migration_receipt_sha256="f" * 64, expected_digest="sha256:" + "e" * 64
    )
    migration["migration_receipt_sha256"] = "0" * 64
    with pytest.raises(module.ReceiptError, match="not bound"):
        module.validate_migration_success_receipt(
            migration, migration_receipt_sha256="f" * 64, expected_digest="sha256:" + "e" * 64
        )


def test_stage_receipt_requires_exact_normalized_configuration_projection_schema() -> None:
    module = load_module()
    valid = receipt()
    module.validate_stage_receipt(
        valid,
        expected_stage="migration",
        expected_source_sha="a" * 40,
        expected_digest="sha256:" + "e" * 64,
    )

    malformed = receipt()
    malformed["configuration_projection"] = {"name": "run-migrations"}
    with pytest.raises(module.ReceiptError, match="configuration projection"):
        module.validate_stage_receipt(
            malformed,
            expected_stage="migration",
            expected_source_sha="a" * 40,
            expected_digest="sha256:" + "e" * 64,
        )


def test_configuration_projection_comparison_rejects_live_drift_and_normalizes_env_order() -> None:
    module = load_module()
    expected = configuration_projection()
    live = configuration_projection()
    environment = live["environment"]
    assert isinstance(environment, list)
    live["environment"] = list(reversed(environment))

    module.compare_configuration_projections(expected, live)

    live["max_retries"] = 1
    with pytest.raises(module.ReceiptError, match="configuration projection does not match"):
        module.compare_configuration_projections(expected, live)


def test_live_job_resource_extraction_returns_the_normalized_projection() -> None:
    module = load_module()
    expected = configuration_projection()
    live_resource = {
        "name": expected["name"],
        "location": expected["location"],
        "template": {
            "template": {
                "serviceAccount": expected["service_account"],
                "maxRetries": expected["max_retries"],
                "timeout": expected["timeout"],
                "taskCount": expected["task_count"],
                "parallelism": expected["parallelism"],
                "vpcAccess": {
                    "egress": "PRIVATE_RANGES_ONLY",
                    "networkInterfaces": [
                        {
                            "network": "projects/example/global/networks/develop",
                            "subnetwork": (
                                "projects/example/regions/us-east4/subnetworks/direct-vpc"
                            ),
                        }
                    ],
                },
                "containers": [
                    {
                        "image": "example/image@" + "sha256:" + "e" * 64,
                        "command": ["golden-rose-migrate"],
                        "env": [
                            {"name": "GOLDEN_ROSE_ENVIRONMENT", "value": "develop"},
                            {
                                "name": "GOLDEN_ROSE_DATABASE_URL",
                                "valueSource": {
                                    "secretKeyRef": {
                                        "secret": "migration-database-url",
                                        "version": "latest",
                                    }
                                },
                            },
                        ],
                    }
                ],
            }
        },
    }

    assert module.extract_live_configuration_projection(
        live_resource, stage="migration"
    ) == module.normalize_configuration_projection(expected)


def test_live_service_projection_requires_reviewed_ingress_and_complete_iam_policy() -> None:
    module = load_module()
    expected = configuration_projection("service")
    live_resource = {
        "name": expected["name"],
        "location": expected["location"],
        "ingress": expected["ingress"],
        "template": {
            "serviceAccount": expected["service_account"],
            "vpcAccess": {
                "egress": "PRIVATE_RANGES_ONLY",
                "networkInterfaces": [
                    {
                        "network": "projects/example/global/networks/develop",
                        "subnetwork": "projects/example/regions/us-east4/subnetworks/direct-vpc",
                    }
                ],
            },
            "containers": [
                {
                    "image": "example/image@" + "sha256:" + "e" * 64,
                    "env": [
                        {"name": "GOLDEN_ROSE_ENVIRONMENT", "value": "develop"},
                        {
                            "name": "GOLDEN_ROSE_DATABASE_URL",
                            "valueSource": {
                                "secretKeyRef": {
                                    "secret": "runtime-database-url",
                                    "version": "latest",
                                }
                            },
                        },
                    ],
                }
            ],
        },
    }
    service_iam = cast(dict[str, list[str]], expected["iam"])
    iam_policy: dict[str, Any] = {
        "bindings": [
            {
                "role": "roles/run.invoker",
                "members": list(service_iam["roles/run.invoker"]),
            },
            {
                "role": "roles/run.viewer",
                "members": list(service_iam["roles/run.viewer"]),
            },
        ]
    }

    assert module.extract_live_configuration_projection(
        live_resource, stage="service", iam_policy=iam_policy
    ) == module.normalize_configuration_projection(expected)

    live_resource["ingress"] = "INGRESS_TRAFFIC_INTERNAL_ONLY"
    with pytest.raises(module.ReceiptError, match="configuration projection does not match"):
        module.compare_configuration_projections(
            expected,
            module.extract_live_configuration_projection(
                live_resource, stage="service", iam_policy=iam_policy
            ),
        )

    live_resource["ingress"] = expected["ingress"]
    iam_policy["bindings"][0]["members"].append("allUsers")
    with pytest.raises(module.ReceiptError, match="configuration projection does not match"):
        module.compare_configuration_projections(
            expected,
            module.extract_live_configuration_projection(
                live_resource, stage="service", iam_policy=iam_policy
            ),
        )
