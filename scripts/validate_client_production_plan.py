from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CLOUD_RUN_TYPES = {
    "google_cloud_run_service",
    "google_cloud_run_v2_job",
    "google_cloud_run_v2_service",
}
SQL_INSTANCE_TYPE = "google_sql_database_instance"
SECRET_VERSION_TYPE = "google_secret_manager_secret_version"

ALLOWED_MANAGED_ACTIONS = {
    ("no-op",),
    ("create",),
    ("update",),
}
ALLOWED_DATA_ACTIONS = {
    ("no-op",),
    ("read",),
}
BROAD_IAM_MEMBERS = {"allUsers", "allAuthenticatedUsers"}
BROAD_IAM_ROLES = {"roles/editor", "roles/owner"}
DIGEST_PATTERN = re.compile(r"@sha256:[0-9a-fA-F]{64}(?:$|[^0-9a-fA-F])")

REQUIRED_EXACT_ENV = {
    "GOLDEN_ROSE_ENVIRONMENT": "production",
    "GOLDEN_ROSE_AUTH_MODE": "staff_oidc",
}
REQUIRED_STAFF_OIDC_ENV = {
    "GOLDEN_ROSE_STAFF_OIDC_AUDIENCE",
    "GOLDEN_ROSE_STAFF_OIDC_ISSUER",
    "GOLDEN_ROSE_STAFF_OIDC_JWKS_URL",
}
FORBIDDEN_TRUE_ENV = {
    "GOLDEN_ROSE_DEMO_ACCESS_ENABLED",
    "GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED",
}


class PlanValidationError(ValueError):
    pass


def _load_plan(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlanValidationError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PlanValidationError("Terraform plan JSON must contain an object")
    return document


def _resource_changes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    changes = plan.get("resource_changes")
    if not isinstance(changes, list):
        raise PlanValidationError("Terraform plan JSON is missing resource_changes")
    normalized: list[dict[str, Any]] = []
    for index, change in enumerate(changes):
        if not isinstance(change, dict):
            raise PlanValidationError(f"resource_changes[{index}] must be an object")
        normalized.append(change)
    return normalized


def _address(change: dict[str, Any], index: int) -> str:
    value = change.get("address")
    if isinstance(value, str) and value:
        return value
    resource_type = change.get("type")
    name = change.get("name")
    if isinstance(resource_type, str) and isinstance(name, str):
        return f"{resource_type}.{name}"
    return f"resource_changes[{index}]"


def _change(change: dict[str, Any], address: str) -> dict[str, Any]:
    value = change.get("change")
    if not isinstance(value, dict):
        raise PlanValidationError(f"{address} is missing change details")
    return value


def _actions(change: dict[str, Any], address: str) -> tuple[str, ...]:
    raw_actions = change.get("actions")
    if not isinstance(raw_actions, list) or any(
        not isinstance(action, str) for action in raw_actions
    ):
        raise PlanValidationError(f"{address} has invalid action metadata")
    return tuple(raw_actions)


def _after(change: dict[str, Any]) -> dict[str, Any]:
    value = change.get("after")
    return value if isinstance(value, dict) else {}


def _is_iam_type(resource_type: str) -> bool:
    return resource_type.startswith("google_") and (
        "_iam_" in resource_type or resource_type.endswith("_iam_policy")
    )


def _walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk(item))
    return values


def _walk_strings(value: Any) -> list[str]:
    strings: list[str] = []
    for item in _walk(value):
        if isinstance(item, str):
            strings.append(item)
            if item.strip().startswith("{"):
                try:
                    parsed = json.loads(item)
                except json.JSONDecodeError:
                    continue
                strings.extend(_walk_strings(parsed))
    return strings


def _has_truthy_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        if key in value and bool(value[key]):
            return True
        return any(_has_truthy_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_has_truthy_key(item, key) for item in value)
    return False


def _find_key_values(value: Any, key: str) -> list[Any]:
    matches: list[Any] = []
    if isinstance(value, dict):
        if key in value:
            matches.append(value[key])
        for item in value.values():
            matches.extend(_find_key_values(item, key))
    elif isinstance(value, list):
        for item in value:
            matches.extend(_find_key_values(item, key))
    return matches


def _validate_actions(
    *,
    address: str,
    mode: str,
    actions: tuple[str, ...],
) -> None:
    if "delete" in actions:
        raise PlanValidationError(f"{address} has forbidden delete or replacement action")
    if mode == "data":
        if actions not in ALLOWED_DATA_ACTIONS:
            raise PlanValidationError(f"{address} has unsupported data-source action")
        return
    if actions not in ALLOWED_MANAGED_ACTIONS:
        raise PlanValidationError(f"{address} has unsupported managed-resource action")


def _validate_sql_private(change: dict[str, Any], address: str) -> None:
    after = _after(change)
    after_unknown = change.get("after_unknown")
    if _has_truthy_key(after, "ipv4_enabled"):
        raise PlanValidationError(f"{address} enables public SQL IPv4 access")
    if _has_truthy_key(after, "authorized_networks"):
        raise PlanValidationError(f"{address} configures SQL authorized networks")
    if _has_truthy_key(after_unknown, "ipv4_enabled") or _has_truthy_key(
        after_unknown, "authorized_networks"
    ):
        raise PlanValidationError(f"{address} has unknown SQL network posture")


def _validate_iam(change: dict[str, Any], address: str) -> None:
    after = _after(change)
    strings = set(_walk_strings(after))
    broad_members = sorted(strings & BROAD_IAM_MEMBERS)
    if broad_members:
        raise PlanValidationError(f"{address} grants broad IAM members: {broad_members}")
    broad_roles = sorted(strings & BROAD_IAM_ROLES)
    if broad_roles:
        raise PlanValidationError(f"{address} grants broad IAM role: {broad_roles}")


def _is_digest_image(value: str) -> bool:
    return bool(DIGEST_PATTERN.search(value))


def _collect_env(value: Any) -> dict[str, str | None]:
    env: dict[str, str | None] = {}
    if isinstance(value, dict):
        env_variables = value.get("env_variables")
        if isinstance(env_variables, dict):
            for key, item in env_variables.items():
                if isinstance(key, str):
                    env[key] = item if isinstance(item, str) else None
        name = value.get("name")
        if isinstance(name, str) and ("value" in value or "value_source" in value):
            env[name] = value.get("value") if isinstance(value.get("value"), str) else None
        for item in value.values():
            env.update(_collect_env(item))
    elif isinstance(value, list):
        for item in value:
            env.update(_collect_env(item))
    return env


def _is_enabled(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_cloud_run(change: dict[str, Any], address: str) -> None:
    after = _after(change)
    images = [value for value in _find_key_values(after, "image") if isinstance(value, str)]
    if not images:
        raise PlanValidationError(f"{address} is missing Cloud Run container image")
    for _image in images:
        if not _is_digest_image(_image):
            raise PlanValidationError(f"{address} must use an immutable image digest")

    env = _collect_env(after)
    for key, expected in REQUIRED_EXACT_ENV.items():
        if env.get(key) != expected:
            raise PlanValidationError(f"{address} must set {key}={expected}")
    for key in REQUIRED_STAFF_OIDC_ENV:
        if key not in env:
            raise PlanValidationError(f"{address} is missing required staff OIDC env {key}")
        if env[key] == "":
            raise PlanValidationError(f"{address} has empty staff OIDC env {key}")
    for key in FORBIDDEN_TRUE_ENV:
        if key in env and _is_enabled(env[key]):
            raise PlanValidationError(f"{address} must not enable {key} in production")

    synthetic_staff_id = env.get("GOLDEN_ROSE_SYNTHETIC_STAFF_ID")
    if synthetic_staff_id not in (None, "", "<unset>"):
        raise PlanValidationError(f"{address} must not configure GOLDEN_ROSE_SYNTHETIC_STAFF_ID")


def _validate_no_secret_payload(change: dict[str, Any], address: str, resource_type: str) -> None:
    if resource_type == SECRET_VERSION_TYPE:
        raise PlanValidationError(f"{address} is a Secret Manager payload version")
    after = _after(change)
    after_unknown = change.get("after_unknown")
    if _find_key_values(after, "secret_data") or _has_truthy_key(after_unknown, "secret_data"):
        raise PlanValidationError(f"{address} includes secret payload data")


def validate_plan(path: Path) -> list[str]:
    plan = _load_plan(path)
    checked: list[str] = []
    cloud_run_addresses: list[str] = []
    for index, resource_change in enumerate(_resource_changes(plan)):
        address = _address(resource_change, index)
        change = _change(resource_change, address)
        actions = _actions(change, address)
        mode = resource_change.get("mode")
        mode_text = mode if isinstance(mode, str) else "managed"
        _validate_actions(address=address, mode=mode_text, actions=actions)
        if mode_text == "data":
            checked.append(address)
            continue

        resource_type = resource_change.get("type")
        if not isinstance(resource_type, str):
            raise PlanValidationError(f"{address} is missing resource type")
        _validate_no_secret_payload(change, address, resource_type)
        if resource_type == SQL_INSTANCE_TYPE:
            _validate_sql_private(change, address)
        if _is_iam_type(resource_type):
            _validate_iam(change, address)
        if resource_type in CLOUD_RUN_TYPES:
            _validate_cloud_run(change, address)
            cloud_run_addresses.append(address)
        checked.append(address)

    if not cloud_run_addresses:
        raise PlanValidationError("plan does not include a verifiable Cloud Run service or job")
    return checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a value-safe Terraform JSON plan for client production review."
    )
    parser.add_argument(
        "plan_json",
        type=Path,
        help="Operator-held Terraform JSON plan produced with terraform show -json.",
    )
    args = parser.parse_args(argv)
    try:
        checked = validate_plan(args.plan_json)
    except PlanValidationError as exc:
        print(f"client production plan validation failed: {exc}", file=sys.stderr)
        return 1
    print("client production plan validation passed")
    for address in checked:
        print(f"- {address}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
