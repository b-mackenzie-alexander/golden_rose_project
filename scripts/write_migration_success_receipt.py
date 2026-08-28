from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class MigrationSuccessReceiptError(ValueError):
    pass


def load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MigrationSuccessReceiptError(f"missing {label} file") from exc
    except json.JSONDecodeError as exc:
        raise MigrationSuccessReceiptError(f"invalid JSON in {label} file") from exc
    if not isinstance(payload, dict):
        raise MigrationSuccessReceiptError(f"{label} file must be a JSON object")
    return payload


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def extract_execution_reference(payload: dict[str, Any]) -> str:
    for key in ("name",):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("name")
        if isinstance(value, str) and value.strip():
            return value
    raise MigrationSuccessReceiptError("migration execution reference is required")


def build_migration_success_receipt(
    *,
    migration_receipt: dict[str, Any],
    migration_receipt_sha256: str,
    deploy_result: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, str]:
    if migration_receipt.get("stage") != "migration":
        raise MigrationSuccessReceiptError("migration receipt must describe the migration stage")
    source_sha = migration_receipt.get("source_sha")
    if not isinstance(source_sha, str) or not GIT_SHA_PATTERN.fullmatch(source_sha):
        raise MigrationSuccessReceiptError(
            "migration receipt source SHA must be a full lowercase git SHA"
        )
    workload_image_digest = migration_receipt.get("workload_image_digest")
    if not isinstance(workload_image_digest, str) or not DIGEST_PATTERN.fullmatch(
        workload_image_digest
    ):
        raise MigrationSuccessReceiptError(
            "migration receipt workload image digest must be an immutable sha256 digest"
        )
    if (
        deploy_result.get("result") != "success"
        or deploy_result.get("current_stage") != "migration_execution"
    ):
        raise MigrationSuccessReceiptError(
            "migration success receipt requires a successful waited migration result"
        )
    deploy_image_digest = deploy_result.get("image_digest")
    if deploy_image_digest != workload_image_digest:
        raise MigrationSuccessReceiptError(
            "migration success receipt deploy result image digest must match the reviewed "
            "image digest"
        )
    execution_reference = extract_execution_reference(execution)
    return {
        "stage": "migration",
        "result": "success",
        "migration_receipt_sha256": migration_receipt_sha256,
        "source_sha": source_sha,
        "workload_image_digest": workload_image_digest,
        "execution_reference": execution_reference,
    }


def write_migration_success_receipt(
    *,
    migration_receipt_path: Path,
    deploy_result_path: Path,
    execution_path: Path,
    output_path: Path,
) -> dict[str, str]:
    migration_receipt = load_json(migration_receipt_path, label="migration receipt")
    deploy_result = load_json(deploy_result_path, label="deploy result")
    execution = load_json(execution_path, label="migration execution")
    receipt = build_migration_success_receipt(
        migration_receipt=migration_receipt,
        migration_receipt_sha256=sha256_file(migration_receipt_path),
        deploy_result=deploy_result,
        execution=execution,
    )
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write a minimized migration-success receipt only after a successful waited "
            "migration execution."
        )
    )
    parser.add_argument("--migration-receipt", type=Path, required=True)
    parser.add_argument("--deploy-result", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_migration_success_receipt(
        migration_receipt_path=args.migration_receipt,
        deploy_result_path=args.deploy_result,
        execution_path=args.execution,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MigrationSuccessReceiptError, OSError) as exc:
        raise SystemExit(f"migration success receipt failed: {exc}") from exc
