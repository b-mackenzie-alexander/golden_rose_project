import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "verify_migration_database_readback.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_migration_database_readback", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def migration_receipt() -> dict[str, object]:
    return {
        "stage": "migration",
        "source_sha": "a" * 40,
        "workload_image_digest": "sha256:" + "b" * 64,
    }


def migration_success_receipt(migration_path: Path) -> dict[str, object]:
    return {
        "stage": "migration",
        "result": "success",
        "migration_receipt_sha256": hashlib.sha256(migration_path.read_bytes()).hexdigest(),
        "source_sha": "a" * 40,
        "workload_image_digest": "sha256:" + "b" * 64,
        "execution_reference": (
            "projects/example/locations/us-east4/jobs/run-migrations/executions/1"
        ),
    }


def readback_receipt(migration_path: Path, success_path: Path) -> dict[str, object]:
    return {
        "schema": "golden-rose.migration-database-readback/v1",
        "migration_receipt_sha256": hashlib.sha256(migration_path.read_bytes()).hexdigest(),
        "migration_success_receipt_sha256": hashlib.sha256(success_path.read_bytes()).hexdigest(),
        "source_sha": "a" * 40,
        "workload_image_digest": "sha256:" + "b" * 64,
        "execution_reference": (
            "projects/example/locations/us-east4/jobs/run-migrations/executions/1"
        ),
        "verification_result": "passed",
        "approval_reference": "operator-held",
    }


def test_readback_receipt_requires_exact_post_migration_database_authority_binding(
    tmp_path: Path,
) -> None:
    module = load_module()
    migration_path = tmp_path / "migration.json"
    success_path = tmp_path / "migration-success.json"
    readback_path = tmp_path / "readback.json"
    write_json(migration_path, migration_receipt())
    write_json(success_path, migration_success_receipt(migration_path))
    write_json(readback_path, readback_receipt(migration_path, success_path))

    module.verify_readback_receipt(
        readback_receipt_path=readback_path,
        migration_receipt_path=migration_path,
        migration_success_receipt_path=success_path,
    )


def test_readback_receipt_rejects_unbound_or_failed_authority_evidence(tmp_path: Path) -> None:
    module = load_module()
    migration_path = tmp_path / "migration.json"
    success_path = tmp_path / "migration-success.json"
    readback_path = tmp_path / "readback.json"
    write_json(migration_path, migration_receipt())
    write_json(success_path, migration_success_receipt(migration_path))
    invalid = readback_receipt(migration_path, success_path)
    invalid["verification_result"] = "failed"
    write_json(readback_path, invalid)

    with pytest.raises(module.MigrationDatabaseReadbackError, match="verification result"):
        module.verify_readback_receipt(
            readback_receipt_path=readback_path,
            migration_receipt_path=migration_path,
            migration_success_receipt_path=success_path,
        )
