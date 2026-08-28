from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
READBACK_SCHEMA = "golden-rose.migration-database-readback/v1"
REQUIRED_FIELDS = {
    "schema",
    "migration_receipt_sha256",
    "migration_success_receipt_sha256",
    "source_sha",
    "workload_image_digest",
    "execution_reference",
    "verification_result",
    "approval_reference",
}


class MigrationDatabaseReadbackError(ValueError):
    pass


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MigrationDatabaseReadbackError(f"missing {label}") from exc
    except json.JSONDecodeError as exc:
        raise MigrationDatabaseReadbackError(f"invalid JSON in {label}") from exc
    if not isinstance(payload, dict):
        raise MigrationDatabaseReadbackError(f"{label} must be a JSON object")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_nonempty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise MigrationDatabaseReadbackError(f"{field} must be a non-empty string")
    return value


def verify_readback_receipt(
    *,
    readback_receipt_path: Path,
    migration_receipt_path: Path,
    migration_success_receipt_path: Path,
) -> None:
    readback = _load_json(readback_receipt_path, label="migration database readback receipt")
    migration = _load_json(migration_receipt_path, label="migration receipt")
    success = _load_json(migration_success_receipt_path, label="migration success receipt")
    if set(readback) != REQUIRED_FIELDS:
        raise MigrationDatabaseReadbackError(
            "readback receipt fields must match the reviewed schema"
        )
    if readback.get("schema") != READBACK_SCHEMA:
        raise MigrationDatabaseReadbackError("readback receipt schema must be reviewed")
    if readback.get("migration_receipt_sha256") != _sha256_file(migration_receipt_path):
        raise MigrationDatabaseReadbackError("readback receipt must bind the migration receipt")
    if readback.get("migration_success_receipt_sha256") != _sha256_file(
        migration_success_receipt_path
    ):
        raise MigrationDatabaseReadbackError(
            "readback receipt must bind the migration success receipt"
        )
    if migration.get("stage") != "migration" or success.get("stage") != "migration":
        raise MigrationDatabaseReadbackError("readback receipt requires migration-stage evidence")
    if success.get("result") != "success":
        raise MigrationDatabaseReadbackError(
            "readback receipt requires successful migration evidence"
        )
    for field, pattern in (
        ("source_sha", GIT_SHA_PATTERN),
        ("workload_image_digest", DIGEST_PATTERN),
    ):
        value = _require_nonempty_string(readback, field)
        if (
            not pattern.fullmatch(value)
            or value != migration.get(field)
            or value != success.get(field)
        ):
            raise MigrationDatabaseReadbackError(
                f"readback receipt {field} must bind migration evidence"
            )
    if readback.get("execution_reference") != success.get("execution_reference"):
        raise MigrationDatabaseReadbackError(
            "readback receipt must bind the waited migration execution"
        )
    if readback.get("verification_result") != "passed":
        raise MigrationDatabaseReadbackError("readback receipt verification result must be passed")
    _require_nonempty_string(readback, "approval_reference")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify signed post-migration database/schema/authority readback binding."
    )
    parser.add_argument("--readback-receipt", type=Path, required=True)
    parser.add_argument("--migration-receipt", type=Path, required=True)
    parser.add_argument("--migration-success-receipt", type=Path, required=True)
    args = parser.parse_args()
    verify_readback_receipt(
        readback_receipt_path=args.readback_receipt,
        migration_receipt_path=args.migration_receipt,
        migration_success_receipt_path=args.migration_success_receipt,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MigrationDatabaseReadbackError, OSError) as exc:
        raise SystemExit(f"migration database readback verification failed: {exc}") from exc
