from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
STAGES = {"migration", "service"}
RESOURCE_TYPE_BY_STAGE = {
    "migration": "google_cloud_run_v2_job",
    "service": "google_cloud_run_v2_service",
}
PROJECTION_FIELDS = {
    "migration": {
        "resource_type",
        "name",
        "location",
        "service_account",
        "image_digest",
        "environment",
        "vpc_access",
        "command",
        "max_retries",
        "timeout",
        "task_count",
        "parallelism",
    },
    "service": {
        "resource_type",
        "name",
        "location",
        "service_account",
        "image_digest",
        "environment",
        "vpc_access",
        "ingress",
        "iam",
    },
}


class ReceiptError(ValueError):
    pass


def _require_exact_object(value: Any, *, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ReceiptError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _require_nonempty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReceiptError(f"{label} must be a non-empty string")
    return value


def _normalize_iam_role_map(value: Any, *, label: str) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not value:
        raise ReceiptError(f"{label} must be a non-empty object")
    normalized: dict[str, list[str]] = {}
    for role, members in value.items():
        normalized_role = _require_nonempty_string(role, label=f"{label} role")
        if (
            not isinstance(members, list)
            or not members
            or not all(isinstance(member, str) and member for member in members)
            or len(set(members)) != len(members)
        ):
            raise ReceiptError(f"{label} members must be a unique non-empty string list")
        normalized[normalized_role] = sorted(members)
    return dict(sorted(normalized.items()))


def _extract_iam_role_map(policy: Any) -> dict[str, list[str]]:
    if not isinstance(policy, dict) or not isinstance(policy.get("bindings"), list):
        raise ReceiptError("live resource IAM policy must contain bindings")
    role_map: dict[str, set[str]] = {}
    for binding in policy["bindings"]:
        if not isinstance(binding, dict) or "condition" in binding:
            raise ReceiptError("live resource IAM policy binding is not approved")
        role = _require_nonempty_string(binding.get("role"), label="live resource IAM policy role")
        members = binding.get("members")
        if (
            not isinstance(members, list)
            or not members
            or not all(isinstance(member, str) and member for member in members)
        ):
            raise ReceiptError("live resource IAM policy members must be a non-empty string list")
        role_map.setdefault(role, set()).update(members)
    return _normalize_iam_role_map(
        {role: sorted(members) for role, members in role_map.items()},
        label="live resource IAM policy",
    )


def normalize_configuration_projection(projection: Any) -> dict[str, Any]:
    """Validate and canonically normalize a receipt or live resource projection."""
    if not isinstance(projection, dict):
        raise ReceiptError("configuration projection must be an object")
    resource_type = projection.get("resource_type")
    stage = next(
        (
            stage
            for stage, expected_type in RESOURCE_TYPE_BY_STAGE.items()
            if resource_type == expected_type
        ),
        None,
    )
    if stage is None:
        raise ReceiptError("configuration projection resource_type is not approved")
    normalized = _require_exact_object(
        projection, fields=PROJECTION_FIELDS[stage], label="configuration projection"
    ).copy()
    for field in ("name", "location", "service_account", "image_digest"):
        normalized[field] = _require_nonempty_string(
            normalized[field], label=f"configuration projection {field}"
        )
    if not DIGEST_PATTERN.fullmatch(normalized["image_digest"]):
        raise ReceiptError("configuration projection image_digest must be a SHA-256 OCI digest")

    environment = normalized["environment"]
    if not isinstance(environment, list):
        raise ReceiptError("configuration projection environment must be a list")
    normalized_environment: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for entry in environment:
        if not isinstance(entry, dict):
            raise ReceiptError("configuration projection environment entries must be objects")
        if set(entry) == {"name", "value"}:
            normalized_entry = {
                "name": _require_nonempty_string(entry["name"], label="environment name"),
                "value": _require_nonempty_string(entry["value"], label="environment value"),
            }
        elif set(entry) == {"name", "secret", "version"}:
            normalized_entry = {
                "name": _require_nonempty_string(entry["name"], label="environment name"),
                "secret": _require_nonempty_string(entry["secret"], label="environment secret"),
                "version": _require_nonempty_string(
                    entry["version"], label="environment secret version"
                ),
            }
        else:
            raise ReceiptError("configuration projection environment entry schema is not approved")
        if normalized_entry["name"] in seen_names:
            raise ReceiptError("configuration projection environment names must be unique")
        seen_names.add(normalized_entry["name"])
        normalized_environment.append(normalized_entry)
    normalized["environment"] = sorted(normalized_environment, key=lambda entry: entry["name"])

    vpc_access = _require_exact_object(
        normalized["vpc_access"],
        fields={"egress", "network", "subnetwork"},
        label="configuration projection vpc_access",
    )
    normalized["vpc_access"] = {
        field: _require_nonempty_string(vpc_access[field], label=f"vpc_access {field}")
        for field in ("egress", "network", "subnetwork")
    }
    if stage == "migration":
        command = normalized["command"]
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(item, str) and item for item in command)
        ):
            raise ReceiptError("configuration projection command must be a non-empty string list")
        for field in ("max_retries", "task_count", "parallelism"):
            if (
                not isinstance(normalized[field], int)
                or isinstance(normalized[field], bool)
                or normalized[field] < 0
            ):
                raise ReceiptError(
                    f"configuration projection {field} must be a non-negative integer"
                )
        normalized["timeout"] = _require_nonempty_string(
            normalized["timeout"], label="configuration projection timeout"
        )
    else:
        normalized["ingress"] = _require_nonempty_string(
            normalized["ingress"], label="configuration projection ingress"
        )
        normalized["iam"] = _normalize_iam_role_map(
            normalized["iam"], label="configuration projection IAM"
        )
    return normalized


def compare_configuration_projections(expected: Any, live: Any) -> None:
    """Purely compare validated receipt and live configuration projections."""
    if normalize_configuration_projection(expected) != normalize_configuration_projection(live):
        raise ReceiptError("configuration projection does not match the live selected resource")


def extract_live_configuration_projection(
    resource: Any, *, stage: str, iam_policy: Any | None = None
) -> dict[str, Any]:
    """Extract the reviewed projection from a Cloud Run v2 describe response."""
    if stage not in STAGES or not isinstance(resource, dict):
        raise ReceiptError("live resource projection input is invalid")
    template = resource.get("template")
    if stage == "migration" and isinstance(template, dict):
        template = template.get("template")
    if not isinstance(template, dict):
        raise ReceiptError("live resource does not contain a Cloud Run v2 template")
    containers = template.get("containers")
    vpc_access = template.get("vpcAccess")
    if (
        not isinstance(containers, list)
        or len(containers) != 1
        or not isinstance(containers[0], dict)
    ):
        raise ReceiptError("live resource must contain exactly one container")
    if not isinstance(vpc_access, dict):
        raise ReceiptError("live resource must contain vpcAccess")
    interfaces = vpc_access.get("networkInterfaces")
    if (
        not isinstance(interfaces, list)
        or len(interfaces) != 1
        or not isinstance(interfaces[0], dict)
    ):
        raise ReceiptError("live resource must contain exactly one VPC network interface")
    container = containers[0]
    environment = []
    for entry in container.get("env", []):
        if not isinstance(entry, dict):
            raise ReceiptError("live resource environment entry is invalid")
        if "value" in entry:
            environment.append({"name": entry.get("name"), "value": entry["value"]})
        else:
            secret_ref = entry.get("valueSource", {}).get("secretKeyRef", {})
            environment.append(
                {
                    "name": entry.get("name"),
                    "secret": secret_ref.get("secret"),
                    "version": secret_ref.get("version"),
                }
            )
    image = container.get("image")
    projection: dict[str, Any] = {
        "resource_type": RESOURCE_TYPE_BY_STAGE[stage],
        "name": resource.get("name"),
        "location": resource.get("location"),
        "service_account": template.get("serviceAccount"),
        "image_digest": image.rsplit("@", 1)[-1] if isinstance(image, str) else image,
        "environment": environment,
        "vpc_access": {
            "egress": vpc_access.get("egress"),
            "network": interfaces[0].get("network"),
            "subnetwork": interfaces[0].get("subnetwork"),
        },
    }
    if stage == "migration":
        projection.update(
            {
                "command": container.get("command"),
                "max_retries": template.get("maxRetries"),
                "timeout": template.get("timeout"),
                "task_count": template.get("taskCount"),
                "parallelism": template.get("parallelism"),
            }
        )
    else:
        projection.update(
            {
                "ingress": resource.get("ingress"),
                "iam": _extract_iam_role_map(iam_policy),
            }
        )
    return normalize_configuration_projection(projection)


def _load_receipt(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReceiptError("stage receipt is not valid JSON") from exc
    if not isinstance(receipt, dict):
        raise ReceiptError("stage receipt must be an object")
    return receipt, hashlib.sha256(raw).hexdigest()


def validate_stage_receipt(
    receipt: dict[str, Any], *, expected_stage: str, expected_source_sha: str, expected_digest: str
) -> None:
    if expected_stage not in STAGES:
        raise ReceiptError("deployment stage must be migration or service")
    required = {
        "stage",
        "source_sha",
        "plan_hash",
        "provider_lock_digest",
        "non_secret_input_digest",
        "approval_reference",
        "evaluated_inventory",
        "workload_image_digest",
        "configuration_projection",
    }
    missing = sorted(required - set(receipt))
    if missing:
        raise ReceiptError(f"stage receipt missing required fields: {missing}")
    if receipt["stage"] != expected_stage:
        raise ReceiptError("stage receipt stage does not match selected transition")
    if receipt["source_sha"] != expected_source_sha:
        raise ReceiptError("stage receipt source SHA does not match deploy commit")
    if receipt["workload_image_digest"] != expected_digest or not DIGEST_PATTERN.fullmatch(
        expected_digest
    ):
        raise ReceiptError("stage receipt image digest does not match reviewed image")
    for field in ("plan_hash", "provider_lock_digest", "non_secret_input_digest"):
        if not isinstance(receipt[field], str) or not SHA256_PATTERN.fullmatch(receipt[field]):
            raise ReceiptError(f"stage receipt {field} must be a SHA-256 hex digest")
    inventory = receipt["evaluated_inventory"]
    if not isinstance(inventory, dict):
        raise ReceiptError("stage receipt inventory must be an object")
    if inventory.get("google_cloud_run_v2_job") != 1:
        raise ReceiptError("stage receipt must contain exactly one migration job")
    service_count = inventory.get("google_cloud_run_v2_service")
    if expected_stage == "migration" and service_count != 0:
        raise ReceiptError("migration receipt must not contain a Cloud Run service")
    if expected_stage == "service" and service_count != 1:
        raise ReceiptError("service receipt must contain exactly one Cloud Run service")
    projection = normalize_configuration_projection(receipt["configuration_projection"])
    if projection["resource_type"] != RESOURCE_TYPE_BY_STAGE[expected_stage]:
        raise ReceiptError(
            "stage receipt configuration projection does not match selected transition"
        )
    if projection["image_digest"] != expected_digest:
        raise ReceiptError(
            "stage receipt configuration projection image digest does not match reviewed image"
        )


def validate_migration_success_receipt(
    receipt: dict[str, Any],
    *,
    migration_receipt_sha256: str,
    expected_digest: str,
    expected_source_sha: str,
) -> None:
    receipt = _require_exact_object(
        receipt,
        fields={
            "stage",
            "result",
            "migration_receipt_sha256",
            "source_sha",
            "workload_image_digest",
            "execution_reference",
        },
        label="migration success receipt",
    )
    if receipt.get("stage") != "migration" or receipt.get("result") != "success":
        raise ReceiptError("migration success receipt must record a successful migration stage")
    if receipt.get("migration_receipt_sha256") != migration_receipt_sha256:
        raise ReceiptError("migration success receipt is not bound to the migration stage receipt")
    if receipt.get("source_sha") != expected_source_sha:
        raise ReceiptError(
            "migration success receipt source SHA does not match the reviewed source"
        )
    if receipt.get("workload_image_digest") != expected_digest:
        raise ReceiptError("migration success receipt is not bound to the reviewed image digest")
    execution_reference = receipt.get("execution_reference")
    if not isinstance(execution_reference, str) or not execution_reference.strip():
        raise ReceiptError("migration success receipt execution reference is required")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate signed-stage receipt content after Cosign verification."
    )
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=sorted(STAGES))
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--migration-receipt", type=Path)
    parser.add_argument("--migration-success-receipt", type=Path)
    parser.add_argument("--live-configuration-projection", type=Path)
    args = parser.parse_args()
    receipt, receipt_sha256 = _load_receipt(args.receipt)
    validate_stage_receipt(
        receipt,
        expected_stage=args.stage,
        expected_source_sha=args.source_sha,
        expected_digest=args.image_digest,
    )
    if args.live_configuration_projection is not None:
        live_projection, _ = _load_receipt(args.live_configuration_projection)
        compare_configuration_projections(receipt["configuration_projection"], live_projection)
    if args.stage == "service":
        if args.migration_receipt is None:
            raise ReceiptError("service transition requires the signed migration stage receipt")
        if args.migration_success_receipt is None:
            raise ReceiptError(
                "service transition requires a separately signed migration success receipt"
            )
        migration_receipt, migration_receipt_sha256 = _load_receipt(args.migration_receipt)
        validate_stage_receipt(
            migration_receipt,
            expected_stage="migration",
            expected_source_sha=args.source_sha,
            expected_digest=args.image_digest,
        )
        migration_success_receipt, _ = _load_receipt(args.migration_success_receipt)
        validate_migration_success_receipt(
            migration_success_receipt,
            migration_receipt_sha256=migration_receipt_sha256,
            expected_digest=args.image_digest,
            expected_source_sha=args.source_sha,
        )
    print(receipt_sha256)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ReceiptError) as exc:
        raise SystemExit(f"stage receipt verification failed: {exc}") from exc
