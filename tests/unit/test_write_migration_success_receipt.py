import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "write_migration_success_receipt.py"
MANIFEST_PATH = ROOT / "infra" / "policy" / "predeployment-authority-manifest.json"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("write_migration_success_receipt", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def migration_receipt() -> dict[str, object]:
    return {
        "stage": "migration",
        "source_sha": "a" * 40,
        "plan_hash": "b" * 64,
        "provider_lock_digest": "c" * 64,
        "non_secret_input_digest": "d" * 64,
        "approval_reference": "operator-held",
        "evaluated_inventory": {
            "google_cloud_run_v2_job": 1,
            "google_cloud_run_v2_service": 0,
        },
        "workload_image_digest": "sha256:" + "e" * 64,
        "configuration_projection": {
            "resource_type": "google_cloud_run_v2_job",
            "name": "run-migrations",
            "location": "us-east4",
            "service_account": "golden-rose-migration@example.iam.gserviceaccount.com",
            "image_digest": "sha256:" + "e" * 64,
            "environment": [{"name": "GOLDEN_ROSE_ENVIRONMENT", "value": "develop"}],
            "vpc_access": {
                "egress": "PRIVATE_RANGES_ONLY",
                "network": "projects/example/global/networks/develop",
                "subnetwork": "projects/example/regions/us-east4/subnetworks/direct-vpc",
            },
            "command": ["golden-rose-migrate"],
            "max_retries": 0,
            "timeout": "1800s",
            "task_count": 1,
            "parallelism": 1,
        },
    }


def deploy_result() -> dict[str, object]:
    return {
        "result": "success",
        "current_stage": "migration_execution",
        "image_digest": "sha256:" + "e" * 64,
        "qualification_executed": False,
        "recovery_disposition": "forward recovery or teardown/rebuild required",
    }


def migration_execution() -> dict[str, object]:
    return {
        "name": (
            "projects/example-project/locations/us-east4/jobs/run-migrations/executions/exec-123"
        )
    }


def test_write_migration_success_receipt_emits_minimized_receipt_on_success(
    tmp_path: Path,
) -> None:
    module = load_module()
    migration_receipt_path = tmp_path / "migration-receipt.json"
    deploy_result_path = tmp_path / "deploy-result.json"
    execution_path = tmp_path / "migration-execution.json"
    output_path = tmp_path / "migration-success-receipt.json"
    migration_receipt_path.write_text(json.dumps(migration_receipt()), encoding="utf-8")
    deploy_result_path.write_text(json.dumps(deploy_result()), encoding="utf-8")
    execution_path.write_text(json.dumps(migration_execution()), encoding="utf-8")

    receipt = module.write_migration_success_receipt(
        migration_receipt_path=migration_receipt_path,
        deploy_result_path=deploy_result_path,
        execution_path=execution_path,
        output_path=output_path,
    )

    assert receipt == json.loads(output_path.read_text(encoding="utf-8"))
    assert receipt == {
        "stage": "migration",
        "result": "success",
        "migration_receipt_sha256": module.sha256_file(migration_receipt_path),
        "source_sha": "a" * 40,
        "workload_image_digest": "sha256:" + "e" * 64,
        "execution_reference": (
            "projects/example-project/locations/us-east4/jobs/run-migrations/executions/exec-123"
        ),
    }


def test_write_migration_success_receipt_rejects_failed_or_non_migration_results(
    tmp_path: Path,
) -> None:
    module = load_module()
    migration_receipt_path = tmp_path / "migration-receipt.json"
    deploy_result_path = tmp_path / "deploy-result.json"
    execution_path = tmp_path / "migration-execution.json"
    output_path = tmp_path / "migration-success-receipt.json"
    bad_result = deploy_result()
    bad_result["result"] = "failed"
    migration_receipt_path.write_text(json.dumps(migration_receipt()), encoding="utf-8")
    deploy_result_path.write_text(json.dumps(bad_result), encoding="utf-8")
    execution_path.write_text(json.dumps(migration_execution()), encoding="utf-8")

    with pytest.raises(module.MigrationSuccessReceiptError, match="successful waited migration"):
        module.write_migration_success_receipt(
            migration_receipt_path=migration_receipt_path,
            deploy_result_path=deploy_result_path,
            execution_path=execution_path,
            output_path=output_path,
        )


def test_write_migration_success_receipt_rejects_mismatched_source_or_digest(
    tmp_path: Path,
) -> None:
    module = load_module()
    migration_receipt_path = tmp_path / "migration-receipt.json"
    deploy_result_path = tmp_path / "deploy-result.json"
    execution_path = tmp_path / "migration-execution.json"
    output_path = tmp_path / "migration-success-receipt.json"
    mismatched_result = deploy_result()
    mismatched_result["image_digest"] = "sha256:" + "f" * 64
    migration_receipt_path.write_text(json.dumps(migration_receipt()), encoding="utf-8")
    deploy_result_path.write_text(json.dumps(mismatched_result), encoding="utf-8")
    execution_path.write_text(json.dumps(migration_execution()), encoding="utf-8")

    with pytest.raises(module.MigrationSuccessReceiptError, match="image digest"):
        module.write_migration_success_receipt(
            migration_receipt_path=migration_receipt_path,
            deploy_result_path=deploy_result_path,
            execution_path=execution_path,
            output_path=output_path,
        )


def test_workflow_sequence_binds_digest_before_writing_migration_success_receipt(
    tmp_path: Path,
) -> None:
    """The waited-execution update must bind the already-verified digest before writing."""
    module = load_module()
    migration_receipt_path = tmp_path / "migration-receipt.json"
    deploy_result_path = tmp_path / "deploy-result.json"
    execution_path = tmp_path / "migration-execution.json"
    output_path = tmp_path / "migration-success-receipt.json"
    initial_result = {
        "result": "failed",
        "current_stage": "pre_deploy_validation",
        "qualification_executed": False,
        "recovery_disposition": "forward recovery or teardown/rebuild required",
    }
    migration_receipt_path.write_text(json.dumps(migration_receipt()), encoding="utf-8")
    deploy_result_path.write_text(json.dumps(initial_result), encoding="utf-8")
    execution_path.write_text(json.dumps(migration_execution()), encoding="utf-8")

    with pytest.raises(module.MigrationSuccessReceiptError, match="successful waited migration"):
        module.write_migration_success_receipt(
            migration_receipt_path=migration_receipt_path,
            deploy_result_path=deploy_result_path,
            execution_path=execution_path,
            output_path=output_path,
        )

    initial_result.update(
        {
            "result": "success",
            "current_stage": "migration_execution",
            "image_digest": migration_receipt()["workload_image_digest"],
        }
    )
    deploy_result_path.write_text(json.dumps(initial_result), encoding="utf-8")

    receipt = module.write_migration_success_receipt(
        migration_receipt_path=migration_receipt_path,
        deploy_result_path=deploy_result_path,
        execution_path=execution_path,
        output_path=output_path,
    )

    assert receipt["workload_image_digest"] == migration_receipt()["workload_image_digest"]


def test_manifest_lists_migration_success_receipt_script_entrypoint() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "scripts/write_migration_success_receipt.py" in manifest["scripts"]["entrypoints"]
