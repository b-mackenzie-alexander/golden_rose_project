from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import stat
import subprocess
from collections.abc import Callable, Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any

APPROVED_PROJECT_LABELS = {
    "environment": "develop",
    "data_boundary": "fictional-synthetic-only",
    "managed_by": "terraform",
    "service": "staff-tracer",
    "cost_center": "develop",
    "owner": "technical-owner",
    "teardown": "intentional-runbook-only",
}
APPROVED_APIS = {
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
}
APPROVED_ALERT_POLICIES = {
    "Develop private synthetic health failures",
    "Develop private synthetic readiness failures",
    "Develop private synthetic service error events",
}
APPROVED_NOTIFICATION_CHANNEL = "Develop private synthetic alert route"
APPROVED_BUDGET_NAME = "Develop private synthetic workload monthly cost guardrail"
APPROVED_BUDGET_THRESHOLDS = [0.5, 0.75, 1.0]
BASIC_ROLES = {"roles/owner", "roles/editor", "roles/viewer"}
GITHUB_REPOSITORY = "b-mackenzie-alexander/golden_rose_project"
SERVICE_ACCOUNT_USER_ROLE = "roles/iam.serviceAccountUser"
WIF_ROLES = {"roles/iam.workloadIdentityUser", "roles/iam.serviceAccountTokenCreator"}


class VerificationError(ValueError):
    pass


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the live Golden Rose GCP foundation posture in read-only mode."
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--control-plane-project-id", required=True)
    parser.add_argument("--region", default="us-east4")
    parser.add_argument("--state-bucket-name", required=True)
    parser.add_argument("--private-invoker-principal", required=True)
    parser.add_argument("--deployer-principal", required=True)
    parser.add_argument("--state-authority-principal", required=True)
    parser.add_argument("--recovery-authority-principal", required=True)
    parser.add_argument("--bootstrap-operator-principal", required=True)
    parser.add_argument(
        "--bootstrap-operator-status",
        choices=["bootstrap-active", "bootstrap-retired"],
        required=True,
    )
    parser.add_argument("--observability-viewer-principal", required=True)
    parser.add_argument("--recovery-policy-review-status", required=True)
    parser.add_argument("--log-retention-days", required=True, type=int)
    parser.add_argument("--billing-account-id")
    parser.add_argument("--evidence-root")
    parser.add_argument("--evidence-name", default="gcp-foundation-evidence.md")
    return parser.parse_args(argv)


def _load_json(stdout: str, *, context: str) -> Any:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"{context} returned malformed JSON") from exc


def _run_json_command(command: Sequence[str], *, context: str) -> Any:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise VerificationError(f"{context} failed: {stderr or 'unknown error'}")
    return _load_json(result.stdout, context=context)


def _dedupe_strings(values: object, *, label: str) -> list[str]:
    if not isinstance(values, list):
        raise VerificationError(f"{label} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise VerificationError(f"{label} contains a non-string entry")
        if value in seen:
            raise VerificationError(
                f"duplicate {label[:-1] if label.endswith('s') else label} {value}"
            )
        seen.add(value)
        normalized.append(value)
    return normalized


def _mapping(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerificationError(f"{label} must be an object")
    return value


def _reject_symlink_path_components(path: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else Path.cwd() / path
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise VerificationError(f"{label} must not contain symlink components")
    return candidate.resolve(strict=False)


def _validated_evidence_output_path(evidence_root: str, evidence_name: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}\.md", evidence_name):
        raise VerificationError("evidence output must be a simple markdown basename")
    root = _reject_symlink_path_components(Path(evidence_root).expanduser(), "evidence root")
    root.mkdir(parents=True, exist_ok=True)
    root = _reject_symlink_path_components(root, "evidence root")
    destination = root / evidence_name
    if destination.exists() and destination.is_symlink():
        raise VerificationError("evidence output path must not be a symlink")
    return destination


def _open_directory_no_follow(path: Path) -> int:
    absolute_path = path if path.is_absolute() else Path.cwd() / path
    descriptor = os.open(absolute_path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in absolute_path.parts[1:]:
            next_descriptor = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
    except OSError as exc:
        os.close(descriptor)
        raise VerificationError(
            "evidence parent must be a real directory without symlink components"
        ) from exc
    return descriptor


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        path_stat = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise VerificationError("evidence parent path cannot be revalidated") from exc
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISDIR(path_stat.st_mode):
        raise VerificationError("evidence parent path is not the reviewed directory")
    return (path_stat.st_dev, path_stat.st_ino)


def _atomic_write_text(
    path: Path, content: str, *, before_replace: Callable[[], None] | None = None
) -> None:
    directory_fd = _open_directory_no_follow(path.parent)
    expected_directory_identity = os.fstat(directory_fd)
    temporary_name = f".{path.name}.{secrets.token_hex(16)}.tmp"
    try:
        try:
            destination_stat = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            destination_stat = None
        if destination_stat is not None and stat.S_ISLNK(destination_stat.st_mode):
            raise VerificationError("evidence output path must not be a symlink")
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(temporary_fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if before_replace is not None:
            before_replace()
        if _directory_identity(path.parent) != (
            expected_directory_identity.st_dev,
            expected_directory_identity.st_ino,
        ):
            raise VerificationError(
                "evidence parent identity changed during descriptor-anchored write"
            )
        try:
            os.replace(temporary_name, path.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        except OSError as exc:
            raise VerificationError(
                "evidence parent changed during descriptor-anchored write"
            ) from exc
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name, dir_fd=directory_fd)
        os.close(directory_fd)


def collect_foundation_snapshot(command_runner: Callable[[Sequence[str]], Any]) -> dict[str, Any]:
    project_labels = _mapping(command_runner(("project-labels",)), label="project labels")
    enabled_apis = _dedupe_strings(command_runner(("enabled-apis",)), label="enabled APIs")
    service_account_payload = command_runner(("service-accounts",))
    if isinstance(service_account_payload, dict):
        service_accounts = _dedupe_strings(
            service_account_payload.get("workload", []), label="service accounts"
        )
        control_plane_service_accounts = _dedupe_strings(
            service_account_payload.get("control_plane", []),
            label="control-plane service accounts",
        )
    else:
        service_accounts = _dedupe_strings(service_account_payload, label="service accounts")
        control_plane_service_accounts = []
    cloud_run_service = _mapping(command_runner(("cloud-run-service",)), label="cloud run service")
    cloud_run_service_iam = _mapping(
        command_runner(("cloud-run-service-iam",)), label="cloud run service iam"
    )
    migration_job = _mapping(command_runner(("migration-job",)), label="migration job")
    cloud_sql = _mapping(command_runner(("cloud-sql",)), label="cloud sql")
    service_account_keys = _mapping(
        command_runner(("service-account-keys",)), label="service account keys"
    )
    project_iam = _mapping(command_runner(("project-iam",)), label="project iam")
    service_account_iam = _mapping(
        command_runner(("service-account-iam",)), label="service account iam"
    )
    artifact_registry_iam = _mapping(
        command_runner(("artifact-registry-iam",)), label="artifact registry iam"
    )
    state_bucket = _mapping(command_runner(("state-bucket",)), label="state bucket")
    state_bucket_iam = _mapping(command_runner(("state-bucket-iam",)), label="state bucket iam")
    budget = _mapping(command_runner(("budget",)), label="budget")
    notification_channels = _dedupe_strings(
        command_runner(("notification-channels",)), label="notification channels"
    )
    alert_policies = _dedupe_strings(command_runner(("alert-policies",)), label="alert policies")
    logging = _mapping(command_runner(("logging",)), label="logging")

    return {
        "project_labels": project_labels,
        "enabled_apis": enabled_apis,
        "resource_inventory": {
            "service_accounts": service_accounts,
            "control_plane_service_accounts": control_plane_service_accounts,
            "cloud_run_service": "staff-tracer",
            "cloud_run_job": "run-migrations",
            "cloud_sql_instance": str(cloud_sql.get("name", "")),
            "state_bucket": str(state_bucket.get("name", "")),
        },
        "cloud_run_service": cloud_run_service,
        "cloud_run_service_iam": cloud_run_service_iam,
        "migration_job": migration_job,
        "cloud_sql": cloud_sql,
        "service_account_keys": service_account_keys,
        "project_iam": project_iam,
        "service_account_iam": service_account_iam,
        "artifact_registry_iam": artifact_registry_iam,
        "state_bucket": state_bucket,
        "state_bucket_iam": state_bucket_iam,
        "budget": budget,
        "notification_channels": notification_channels,
        "alert_policies": alert_policies,
        "logging": logging,
    }


def _expected_service_accounts(project_id: str) -> set[str]:
    return {
        f"staff-tracer-migration@{project_id}.iam.gserviceaccount.com",
        f"staff-tracer-runtime@{project_id}.iam.gserviceaccount.com",
    }


def _expected_control_plane_service_accounts(control_plane_project_id: str) -> set[str]:
    return {
        f"golden-rose-deployer@{control_plane_project_id}.iam.gserviceaccount.com",
        f"golden-rose-image-publisher@{control_plane_project_id}.iam.gserviceaccount.com",
        f"golden-rose-provisioner@{control_plane_project_id}.iam.gserviceaccount.com",
    }


def _expected_artifact_registry_writer_member(contract: dict[str, Any]) -> str:
    return "serviceAccount:golden-rose-image-publisher@{}.iam.gserviceaccount.com".format(
        contract["control_plane_project_id"]
    )


def _expected_state_bucket_iam(contract: dict[str, Any]) -> dict[str, set[str]]:
    members = {
        str(contract["state_authority_principal"]),
        str(contract["recovery_authority_principal"]),
    }
    if contract["bootstrap_operator_status"] == "bootstrap-active":
        members.add(str(contract["bootstrap_operator_principal"]))
    return {"roles/storage.objectAdmin": members}


def _expected_project_iam(contract: dict[str, Any]) -> dict[str, set[str]]:
    project_id = str(contract["project_id"])
    observability_principal = str(contract["observability_viewer_principal"])
    return {
        "roles/cloudsql.client": {
            f"serviceAccount:staff-tracer-runtime@{project_id}.iam.gserviceaccount.com",
            f"serviceAccount:staff-tracer-migration@{project_id}.iam.gserviceaccount.com",
        },
        "roles/logging.logWriter": {
            f"serviceAccount:staff-tracer-runtime@{project_id}.iam.gserviceaccount.com",
            f"serviceAccount:staff-tracer-migration@{project_id}.iam.gserviceaccount.com",
        },
        "roles/monitoring.metricWriter": {
            f"serviceAccount:staff-tracer-runtime@{project_id}.iam.gserviceaccount.com",
            f"serviceAccount:staff-tracer-migration@{project_id}.iam.gserviceaccount.com",
        },
        "roles/logging.viewer": {observability_principal},
        "roles/monitoring.viewer": {observability_principal},
    }


def _as_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def evaluate_foundation_snapshot(snapshot: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    if snapshot.get("project_labels") != APPROVED_PROJECT_LABELS:
        violations.append("project labels drifted from the approved develop posture")

    enabled_apis = (
        set(snapshot.get("enabled_apis", []))
        if isinstance(snapshot.get("enabled_apis"), list)
        else set()
    )
    if enabled_apis != APPROVED_APIS:
        violations.append(
            f"approved APIs drifted: expected {sorted(APPROVED_APIS)} got {sorted(enabled_apis)}"
        )

    resource_inventory = _mapping(
        snapshot.get("resource_inventory", {}), label="resource inventory"
    )
    if _as_set(resource_inventory.get("service_accounts")) != _expected_service_accounts(
        str(contract["project_id"])
    ):
        violations.append("service-account inventory drifted from the approved foundation")
    control_plane_accounts = _as_set(resource_inventory.get("control_plane_service_accounts"))
    if control_plane_accounts != _expected_control_plane_service_accounts(
        str(contract["control_plane_project_id"])
    ):
        violations.append("control-plane service-account inventory drifted")
    if resource_inventory.get("cloud_run_service") != "staff-tracer":
        violations.append("cloud run service inventory drifted from staff-tracer")
    if resource_inventory.get("cloud_run_job") != "run-migrations":
        violations.append("migration job inventory drifted from run-migrations")
    if resource_inventory.get("cloud_sql_instance") != "develop-postgres":
        violations.append("cloud sql inventory drifted from develop-postgres")
    if resource_inventory.get("state_bucket") != contract["state_bucket_name"]:
        violations.append("state bucket inventory drifted from the reviewed bucket name")

    cloud_run_service = _mapping(snapshot.get("cloud_run_service", {}), label="cloud run service")
    if cloud_run_service.get("labels") != APPROVED_PROJECT_LABELS:
        violations.append("cloud run service labels drifted from the approved develop posture")
    if cloud_run_service.get("ingress") != "INGRESS_TRAFFIC_INTERNAL_ONLY":
        violations.append("cloud run service ingress is not internal-only")
    if (
        cloud_run_service.get("service_account")
        != f"staff-tracer-runtime@{contract['project_id']}.iam.gserviceaccount.com"
    ):
        violations.append("cloud run service runtime identity drifted from staff-tracer-runtime")

    cloud_run_service_iam = _mapping(
        snapshot.get("cloud_run_service_iam", {}), label="cloud run service iam"
    )
    actual_invokers = _as_set(cloud_run_service_iam.get("roles/run.invoker"))
    if "allUsers" in actual_invokers or "allAuthenticatedUsers" in actual_invokers:
        violations.append("public Cloud Run invoker detected")
    if actual_invokers != {str(contract["private_invoker_principal"])}:
        violations.append("cloud run invoker bindings drifted from the approved private principal")

    migration_job = _mapping(snapshot.get("migration_job", {}), label="migration job")
    if migration_job.get("labels") != APPROVED_PROJECT_LABELS:
        violations.append("migration job labels drifted from the approved develop posture")
    if (
        migration_job.get("service_account")
        != f"staff-tracer-migration@{contract['project_id']}.iam.gserviceaccount.com"
    ):
        violations.append("migration job identity drifted from staff-tracer-migration")
    if migration_job.get("parallelism") != 1 or migration_job.get("task_count") != 1:
        violations.append("migration job lost serialized execution posture")

    cloud_sql = _mapping(snapshot.get("cloud_sql", {}), label="cloud sql")
    if cloud_sql.get("database_version") != "POSTGRES_16":
        violations.append("cloud sql version drifted from POSTGRES_16")
    if cloud_sql.get("deletion_protection") is not True:
        violations.append("cloud sql deletion protection is not enabled")
    if cloud_sql.get("ipv4_enabled") is not False or not cloud_sql.get("private_network"):
        violations.append("public Cloud SQL path detected")
    expected_sql_labels = dict(APPROVED_PROJECT_LABELS)
    expected_sql_labels["recovery_policy_review_status"] = contract["recovery_policy_review_status"]
    if cloud_sql.get("labels") != expected_sql_labels:
        violations.append("cloud sql labels drifted from the approved recovery posture")

    service_account_keys = _mapping(
        snapshot.get("service_account_keys", {}), label="service account keys"
    )
    expected_key_accounts = _expected_service_accounts(
        str(contract["project_id"])
    ) | _expected_control_plane_service_accounts(str(contract["control_plane_project_id"]))
    if set(service_account_keys) != expected_key_accounts:
        violations.append("service-account key inventory drifted from reviewed identities")
    for service_account, keys in service_account_keys.items():
        if _as_set(keys):
            violations.append(f"service account keys detected for {service_account}")

    project_iam = _mapping(snapshot.get("project_iam", {}), label="project iam")
    for basic_role in BASIC_ROLES:
        if basic_role in project_iam:
            violations.append(f"basic role detected in project IAM: {basic_role}")
    expected_project_iam = _expected_project_iam(contract)
    if set(project_iam) != set(expected_project_iam):
        violations.append("project IAM role inventory drifted from reviewed authority boundary")
    for role, expected_members in expected_project_iam.items():
        actual_members = _as_set(project_iam.get(role))
        if actual_members != expected_members:
            violations.append(
                f"project IAM drifted for {role}: expected {sorted(expected_members)} "
                f"got {sorted(actual_members)}"
            )

    service_account_iam = _mapping(
        snapshot.get("service_account_iam", {}), label="service account iam"
    )
    deployer_principal = str(contract["deployer_principal"])
    runtime_email = f"staff-tracer-runtime@{contract['project_id']}.iam.gserviceaccount.com"
    migration_email = f"staff-tracer-migration@{contract['project_id']}.iam.gserviceaccount.com"
    for email in (runtime_email, migration_email):
        actual = _mapping(service_account_iam.get(email, {}), label=f"service account iam {email}")
        if {SERVICE_ACCOUNT_USER_ROLE} != set(actual):
            violations.append(f"service-account IAM drifted for {email}")
        elif _as_set(actual.get(SERVICE_ACCOUNT_USER_ROLE)) != {deployer_principal}:
            violations.append(f"deployer service-account user binding drifted for {email}")
    for email in (
        f"golden-rose-provisioner@{contract['control_plane_project_id']}.iam.gserviceaccount.com",
        f"golden-rose-image-publisher@{contract['control_plane_project_id']}.iam.gserviceaccount.com",
        f"golden-rose-deployer@{contract['control_plane_project_id']}.iam.gserviceaccount.com",
    ):
        actual = _mapping(service_account_iam.get(email, {}), label=f"service account iam {email}")
        if set(actual) != WIF_ROLES:
            violations.append(f"WIF service-account IAM drifted for {email}")
            continue
        for role in WIF_ROLES:
            members = _as_set(actual.get(role))
            if len(members) != 1 or not next(iter(members)).endswith(
                f"/attribute.repository/{GITHUB_REPOSITORY}"
            ):
                violations.append(f"WIF principal binding drifted for {email} role {role}")

    artifact_registry_iam = _mapping(
        snapshot.get("artifact_registry_iam", {}), label="artifact registry iam"
    )
    if set(artifact_registry_iam) != {"roles/artifactregistry.writer"}:
        violations.append("Artifact Registry IAM roles drifted from reviewed writer-only boundary")
    artifact_registry_writers = _as_set(artifact_registry_iam.get("roles/artifactregistry.writer"))
    if (
        "allUsers" in artifact_registry_writers
        or "allAuthenticatedUsers" in artifact_registry_writers
    ):
        violations.append("public Artifact Registry writer detected")
    if artifact_registry_writers != {_expected_artifact_registry_writer_member(contract)}:
        violations.append(
            "Artifact Registry writer bindings drifted from the reviewed publisher principal"
        )

    state_bucket = _mapping(snapshot.get("state_bucket", {}), label="state bucket")
    if state_bucket.get("name") != contract["state_bucket_name"]:
        violations.append("state bucket name drifted")
    if state_bucket.get("versioning_enabled") is not True:
        violations.append("state bucket versioning is not enabled")
    if state_bucket.get("uniform_bucket_level_access") is not True:
        violations.append("state bucket uniform bucket-level access is not enabled")
    if state_bucket.get("public_access_prevention") != "enforced":
        violations.append("state bucket public access prevention is not enforced")
    if int(state_bucket.get("retention_period", 0) or 0) <= 0:
        violations.append("state bucket retention posture is missing")
    state_bucket_iam = _mapping(snapshot.get("state_bucket_iam", {}), label="state bucket iam")
    for role, members in state_bucket_iam.items():
        actual_members = _as_set(members)
        if "allUsers" in actual_members or "allAuthenticatedUsers" in actual_members:
            violations.append("public state bucket IAM binding detected")
        if role in BASIC_ROLES:
            violations.append(f"basic role detected in state bucket IAM: {role}")
    expected_state_iam = _expected_state_bucket_iam(contract)
    if set(state_bucket_iam) != set(expected_state_iam):
        violations.append("state bucket IAM roles drifted from reviewed authority boundary")
    else:
        for role, expected_members in expected_state_iam.items():
            if _as_set(state_bucket_iam.get(role)) != expected_members:
                violations.append(
                    "state bucket IAM members drifted from reviewed authority boundary"
                )

    budget = _mapping(snapshot.get("budget", {}), label="budget")
    if budget.get("display_name") != APPROVED_BUDGET_NAME:
        violations.append("budget display name drifted from the reviewed guardrail")
    if list(budget.get("threshold_percents", [])) != APPROVED_BUDGET_THRESHOLDS:
        violations.append("budget thresholds drifted from the approved 50/75/100 posture")
    if list(budget.get("notification_channels", [])) != [APPROVED_NOTIFICATION_CHANNEL]:
        violations.append("budget alert route drifted from the reviewed notification channel")

    notification_channels = (
        set(snapshot.get("notification_channels", []))
        if isinstance(snapshot.get("notification_channels"), list)
        else set()
    )
    if notification_channels != {APPROVED_NOTIFICATION_CHANNEL}:
        violations.append("notification channel inventory drifted from the reviewed alert route")

    alert_policies = (
        set(snapshot.get("alert_policies", []))
        if isinstance(snapshot.get("alert_policies"), list)
        else set()
    )
    if alert_policies != APPROVED_ALERT_POLICIES:
        violations.append("alert policy inventory drifted from the reviewed observability posture")

    logging = _mapping(snapshot.get("logging", {}), label="logging")
    if logging.get("default_bucket_retention_days") != contract["log_retention_days"]:
        violations.append("default logging retention drifted from the reviewed posture")
    if _as_set(logging.get("sinks")):
        violations.append("unexpected logging sink detected")

    return violations


def _redact_text(text: str) -> str:
    redacted = re.sub(r"serviceAccount:[^\s]+", "serviceAccount:[REDACTED]", text)
    redacted = re.sub(r"group:[^\s]+", "group:[REDACTED]", redacted)
    redacted = re.sub(r"principalSet://[^\s]+", "[REDACTED]", redacted)
    redacted = re.sub(r"principal://[^\s]+", "[REDACTED]", redacted)
    redacted = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", "[REDACTED]", redacted)
    redacted = re.sub(r"projects/[^/\s]+", "projects/[REDACTED]", redacted)
    redacted = re.sub(r"(?<=\bin )[a-z][a-z0-9-]{4,}", "[REDACTED]", redacted)
    return redacted


def render_violations(violations: Sequence[str]) -> str:
    return "\n".join(f"- {_redact_text(violation)}" for violation in violations)


def _render_evidence_markdown(snapshot: dict[str, Any], violations: Sequence[str]) -> str:
    status = "passed" if not violations else "failed"
    lines = [
        "# GCP foundation evidence",
        "",
        f"Status: {status}",
        "Mode: read-only",
        "",
        "## Summary",
        f"- Enabled APIs checked: {len(snapshot.get('enabled_apis', []))}",
        f"- Alert policies checked: {len(snapshot.get('alert_policies', []))}",
        f"- Violations: {len(violations)}",
        "",
        "## Violations",
    ]
    if violations:
        lines.extend(render_violations(violations).splitlines())
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Value-safety note")
    lines.append(
        "- Project IDs, principals, emails, and exact resource paths are redacted in this artifact."
    )
    return "\n".join(lines) + "\n"


def _build_live_command_runner(contract: dict[str, Any]) -> Callable[[Sequence[str]], Any]:
    project_id = str(contract["project_id"])
    control_plane_project_id = str(contract["control_plane_project_id"])
    region = str(contract["region"])
    state_bucket_name = str(contract["state_bucket_name"])
    billing_account_id = contract.get("billing_account_id")

    def command_runner(command: Sequence[str]) -> Any:
        key = tuple(command)
        if key == ("project-labels",):
            project = _run_json_command(
                ["gcloud", "projects", "describe", project_id, "--format=json"],
                context="project labels",
            )
            return _mapping(project, label="project").get("labels", {})
        if key == ("enabled-apis",):
            services = _run_json_command(
                [
                    "gcloud",
                    "services",
                    "list",
                    "--project",
                    project_id,
                    "--enabled",
                    "--format=json",
                ],
                context="enabled APIs",
            )
            return [
                service.get("config", {}).get("name")
                for service in services
                if isinstance(service, dict)
            ]
        if key == ("service-accounts",):
            accounts = _run_json_command(
                [
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "list",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="service accounts",
            )
            workload_accounts = [
                account.get("email") for account in accounts if isinstance(account, dict)
            ]
            control_plane_accounts = _run_json_command(
                [
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "list",
                    "--project",
                    control_plane_project_id,
                    "--format=json",
                ],
                context="control-plane service accounts",
            )
            return {
                "workload": workload_accounts,
                "control_plane": [
                    account.get("email")
                    for account in control_plane_accounts
                    if isinstance(account, dict)
                ],
            }
        if key == ("cloud-run-service",):
            service = _run_json_command(
                [
                    "gcloud",
                    "run",
                    "services",
                    "describe",
                    "staff-tracer",
                    "--project",
                    project_id,
                    "--region",
                    region,
                    "--format=json",
                ],
                context="cloud run service",
            )
            template = _mapping(service, label="service").get("template", {})
            return {
                "labels": _mapping(service, label="service").get("labels", {}),
                "ingress": service.get("ingress"),
                "service_account": _mapping(template, label="service template").get(
                    "serviceAccount"
                ),
            }
        if key == ("cloud-run-service-iam",):
            policy = _run_json_command(
                [
                    "gcloud",
                    "run",
                    "services",
                    "get-iam-policy",
                    "staff-tracer",
                    "--project",
                    project_id,
                    "--region",
                    region,
                    "--format=json",
                ],
                context="cloud run service iam",
            )
            return _bindings_to_role_map(policy)
        if key == ("migration-job",):
            job = _run_json_command(
                [
                    "gcloud",
                    "run",
                    "jobs",
                    "describe",
                    "run-migrations",
                    "--project",
                    project_id,
                    "--region",
                    region,
                    "--format=json",
                ],
                context="migration job",
            )
            template = _mapping(job, label="job").get("template", {})
            task_template = _mapping(template, label="job template").get("template", {})
            return {
                "labels": _mapping(job, label="job").get("labels", {}),
                "service_account": task_template.get("serviceAccount"),
                "parallelism": template.get("parallelism"),
                "task_count": template.get("taskCount"),
            }
        if key == ("cloud-sql",):
            instance = _run_json_command(
                [
                    "gcloud",
                    "sql",
                    "instances",
                    "describe",
                    "develop-postgres",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="cloud sql",
            )
            settings = _mapping(instance, label="cloud sql").get("settings", {})
            ip_configuration = _mapping(settings, label="cloud sql settings").get(
                "ipConfiguration", {}
            )
            return {
                "name": instance.get("name"),
                "database_version": instance.get("databaseVersion"),
                "deletion_protection": instance.get("deletionProtectionEnabled"),
                "ipv4_enabled": _mapping(ip_configuration, label="ip configuration").get(
                    "ipv4Enabled"
                ),
                "private_network": _mapping(ip_configuration, label="ip configuration").get(
                    "privateNetwork"
                ),
                "labels": _mapping(settings, label="cloud sql settings").get("userLabels", {}),
            }
        if key == ("service-account-keys",):
            keys: dict[str, Any] = {}
            account_projects = {
                **dict.fromkeys(_expected_service_accounts(project_id), project_id),
                **dict.fromkeys(
                    _expected_control_plane_service_accounts(control_plane_project_id),
                    control_plane_project_id,
                ),
            }
            for email, account_project_id in sorted(account_projects.items()):
                key_list = _run_json_command(
                    [
                        "gcloud",
                        "iam",
                        "service-accounts",
                        "keys",
                        "list",
                        "--iam-account",
                        email,
                        "--managed-by=user",
                        "--project",
                        account_project_id,
                        "--format=json",
                    ],
                    context=f"service account keys {email}",
                )
                keys[email] = key_list
            return keys
        if key == ("project-iam",):
            policy = _run_json_command(
                ["gcloud", "projects", "get-iam-policy", project_id, "--format=json"],
                context="project iam",
            )
            return _bindings_to_role_map(policy)
        if key == ("service-account-iam",):
            service_account_policies: dict[str, Any] = {}
            account_projects = {
                **dict.fromkeys(_expected_service_accounts(project_id), project_id),
                **dict.fromkeys(
                    _expected_control_plane_service_accounts(control_plane_project_id),
                    control_plane_project_id,
                ),
            }
            for email, account_project_id in sorted(account_projects.items()):
                policy = _run_json_command(
                    [
                        "gcloud",
                        "iam",
                        "service-accounts",
                        "get-iam-policy",
                        email,
                        "--project",
                        account_project_id,
                        "--format=json",
                    ],
                    context=f"service account iam {email}",
                )
                service_account_policies[email] = _bindings_to_role_map(policy)
            return service_account_policies
        if key == ("artifact-registry-iam",):
            policy = _run_json_command(
                [
                    "gcloud",
                    "artifacts",
                    "repositories",
                    "get-iam-policy",
                    "staff-tracer-images",
                    "--project",
                    project_id,
                    "--location",
                    region,
                    "--format=json",
                ],
                context="artifact registry iam",
            )
            return _bindings_to_role_map(policy)
        if key == ("state-bucket",):
            bucket = _run_json_command(
                [
                    "gcloud",
                    "storage",
                    "buckets",
                    "describe",
                    f"gs://{state_bucket_name}",
                    "--format=json",
                ],
                context="state bucket",
            )
            iam_configuration = _mapping(bucket, label="bucket").get("iamConfiguration", {})
            retention_policy = _mapping(bucket, label="bucket").get("retentionPolicy", {})
            return {
                "name": bucket.get("name", "").replace("gs://", ""),
                "versioning_enabled": _mapping(bucket, label="bucket")
                .get("versioning", {})
                .get("enabled"),
                "uniform_bucket_level_access": _mapping(
                    iam_configuration, label="iam configuration"
                )
                .get("uniformBucketLevelAccess", {})
                .get("enabled"),
                "public_access_prevention": _mapping(
                    iam_configuration, label="iam configuration"
                ).get("publicAccessPrevention"),
                "retention_period": retention_policy.get("retentionPeriod"),
            }
        if key == ("state-bucket-iam",):
            policy = _run_json_command(
                [
                    "gcloud",
                    "storage",
                    "buckets",
                    "get-iam-policy",
                    f"gs://{state_bucket_name}",
                    "--format=json",
                ],
                context="state bucket iam",
            )
            return _bindings_to_role_map(policy)
        if key == ("budget",):
            if not billing_account_id:
                raise VerificationError("budget verification requires --billing-account-id")
            budgets = _run_json_command(
                [
                    "gcloud",
                    "beta",
                    "billing",
                    "budgets",
                    "list",
                    "--billing-account",
                    str(billing_account_id),
                    "--format=json",
                ],
                context="budget",
            )
            for budget in budgets:
                if isinstance(budget, dict) and budget.get("displayName") == APPROVED_BUDGET_NAME:
                    thresholds = [
                        rule.get("thresholdPercent")
                        for rule in budget.get("thresholdRules", [])
                        if isinstance(rule, dict)
                    ]
                    channels = budget.get("allUpdatesRule", {}).get(
                        "monitoringNotificationChannels", []
                    )
                    return {
                        "display_name": budget.get("displayName"),
                        "threshold_percents": thresholds,
                        "notification_channels": channels,
                    }
            return {}
        if key == ("notification-channels",):
            channels = _run_json_command(
                [
                    "gcloud",
                    "monitoring",
                    "channels",
                    "list",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="notification channels",
            )
            return [channel.get("displayName") for channel in channels if isinstance(channel, dict)]
        if key == ("alert-policies",):
            policies = _run_json_command(
                [
                    "gcloud",
                    "alpha",
                    "monitoring",
                    "policies",
                    "list",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="alert policies",
            )
            return [policy.get("displayName") for policy in policies if isinstance(policy, dict)]
        if key == ("logging",):
            bucket = _run_json_command(
                [
                    "gcloud",
                    "logging",
                    "buckets",
                    "describe",
                    "_Default",
                    "--location=global",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="logging bucket",
            )
            sinks = _run_json_command(
                ["gcloud", "logging", "sinks", "list", "--project", project_id, "--format=json"],
                context="logging sinks",
            )
            return {
                "default_bucket_retention_days": bucket.get("retentionDays"),
                "sinks": [sink.get("name") for sink in sinks if isinstance(sink, dict)],
            }
        raise VerificationError(f"unsupported read-only foundation command {key!r}")

    return command_runner


def _bindings_to_role_map(policy: Any) -> dict[str, list[str]]:
    bindings = _mapping(policy, label="policy").get("bindings", [])
    if not isinstance(bindings, list):
        raise VerificationError("policy bindings must be a list")
    role_map: dict[str, list[str]] = {}
    for binding in bindings:
        if not isinstance(binding, dict):
            raise VerificationError("policy binding must be an object")
        role = binding.get("role")
        members = binding.get("members", [])
        if not isinstance(role, str):
            raise VerificationError("policy binding missing role")
        if "condition" in binding:
            raise VerificationError(f"conditional IAM binding is not reviewed for {role}")
        role_members = role_map.setdefault(role, [])
        for member in _dedupe_strings(members, label=f"members for {role}"):
            if member in role_members:
                raise VerificationError(f"duplicate member {member} for {role}")
            role_members.append(member)
    return role_map


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    contract = {
        "project_id": args.project_id,
        "control_plane_project_id": args.control_plane_project_id,
        "region": args.region,
        "state_bucket_name": args.state_bucket_name,
        "private_invoker_principal": args.private_invoker_principal,
        "deployer_principal": args.deployer_principal,
        "state_authority_principal": args.state_authority_principal,
        "recovery_authority_principal": args.recovery_authority_principal,
        "bootstrap_operator_principal": args.bootstrap_operator_principal,
        "bootstrap_operator_status": args.bootstrap_operator_status,
        "observability_viewer_principal": args.observability_viewer_principal,
        "recovery_policy_review_status": args.recovery_policy_review_status,
        "log_retention_days": args.log_retention_days,
        "billing_account_id": args.billing_account_id,
    }
    snapshot = collect_foundation_snapshot(_build_live_command_runner(contract))
    violations = evaluate_foundation_snapshot(snapshot, contract)

    if args.evidence_root:
        destination = _validated_evidence_output_path(args.evidence_root, args.evidence_name)
        _atomic_write_text(destination, _render_evidence_markdown(snapshot, violations))

    if violations:
        print("gcp foundation verification failed")
        print(render_violations(violations))
        return 1

    print("gcp foundation verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
