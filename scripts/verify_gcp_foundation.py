from __future__ import annotations

import argparse
import importlib.util
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
from urllib.parse import urlparse

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
}
APPROVED_ALERT_POLICIES_BASE = {
    "Develop private synthetic health failures",
    "Develop private synthetic service error events",
}
APPROVED_ALERT_POLICIES_SERVICE = {
    *APPROVED_ALERT_POLICIES_BASE,
    "Develop private synthetic readiness failures",
}
APPROVED_NOTIFICATION_CHANNEL = "Develop private synthetic alert route"
APPROVED_BUDGET_NAME = "Develop private synthetic workload monthly cost guardrail"
APPROVED_BUDGET_THRESHOLDS = [0.5, 0.75, 1.0]
BASIC_ROLES = {"roles/owner", "roles/editor", "roles/viewer"}
NAMED_TESTER_PRINCIPAL_PATTERN = re.compile(r"^user:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+$")

APPROVED_LOGGING_EXCLUSION_NAME = "develop-exclude-uuid-bearing-staff-paths"
APPROVED_LOGGING_EXCLUSION_FILTER_FRAGMENT = "/api/staff/v1/employers/[0-9a-fA-F-]{36}"
APPROVED_READINESS_UPTIME_DISPLAY_NAME = "Develop private synthetic authenticated readiness"
GITHUB_REPOSITORY = "b-mackenzie-alexander/golden_rose_project"
GITHUB_PROTECTED_REF = "refs/heads/develop"
BUILD_IMAGE_WORKFLOW_REF = (
    f"{GITHUB_REPOSITORY}/.github/workflows/build-image.yml@{GITHUB_PROTECTED_REF}"
)
DEPLOY_DEVELOP_WORKFLOW_REF = (
    f"{GITHUB_REPOSITORY}/.github/workflows/deploy-develop.yml@{GITHUB_PROTECTED_REF}"
)
WIF_ROLE = "roles/iam.workloadIdentityUser"


class VerificationError(ValueError):
    pass


def derive_tester_authority_contract(
    *,
    receipt_path: Path,
    bundle_path: Path,
    certificate_identity: str,
    project_id: str,
    region: str,
    service: str = "staff-tracer",
    verifier_runner: Callable[[list[str]], None] | None = None,
) -> dict[str, str]:
    """Derive the sole accepted tester contract before querying live IAM."""
    module_path = Path(__file__).with_name("verify_tester_authority_receipt.py")
    spec = importlib.util.spec_from_file_location("verify_tester_authority_receipt", module_path)
    if spec is None or spec.loader is None:
        raise VerificationError("could not load tester authority receipt verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        verifier_kwargs: dict[str, object] = {}
        if verifier_runner is not None:
            verifier_kwargs["verifier_runner"] = verifier_runner
        derived = module.verify_and_derive_tester_authority(
            receipt_path=receipt_path,
            bundle_path=bundle_path,
            certificate_identity=certificate_identity,
            expected_project_id=project_id,
            expected_region=region,
            expected_service=service,
            **verifier_kwargs,
        )
    except module.TesterAuthorityReceiptError as exc:
        raise VerificationError(f"tester authority receipt verification failed: {exc}") from exc
    return {key: str(value) for key, value in derived.items()}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the live Golden Rose GCP foundation posture in read-only mode."
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--control-plane-project-id", required=True)
    parser.add_argument("--region", default="us-east4")
    parser.add_argument("--state-bucket-name", required=True)
    parser.add_argument("--tester-authority-receipt", required=True, type=Path)
    parser.add_argument("--tester-authority-bundle", required=True, type=Path)
    parser.add_argument("--tester-authority-certificate-identity", required=True)
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
    parser.add_argument(
        "--mode",
        choices=["foundation", "migration", "service"],
        default="service",
        help="Deployment stage verification mode (default: service).",
    )
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


def _canonical_channel_resource_names(notification_channels: dict[str, Any]) -> set[str]:
    canonical_names: set[str] = set()
    for resource_name, display_name in notification_channels.items():
        if display_name == APPROVED_NOTIFICATION_CHANNEL:
            canonical_names.add(str(resource_name))
    return canonical_names


def _is_reviewed_named_tester_principal(value: str) -> bool:
    return bool(NAMED_TESTER_PRINCIPAL_PATTERN.fullmatch(value))


def _dedupe_uptime_checks(values: object) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise VerificationError("uptime checks must be a list")
    normalized: list[dict[str, Any]] = []
    display_names: set[str] = set()
    for value in values:
        uptime_check = _mapping(value, label="uptime check")
        display_name = uptime_check.get("display_name")
        if not isinstance(display_name, str):
            raise VerificationError("uptime check missing display_name")
        if display_name in display_names:
            raise VerificationError(f"duplicate uptime check {display_name}")
        display_names.add(display_name)
        normalized.append(uptime_check)
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
    project_number = str(command_runner(("project-number",)))
    cloud_run_service = _mapping(command_runner(("cloud-run-service",)), label="cloud run service")
    cloud_run_service_iam = _mapping(
        command_runner(("cloud-run-service-iam",)), label="cloud run service iam"
    )
    migration_job = _mapping(command_runner(("migration-job",)), label="migration job")
    migration_job_iam = _mapping(command_runner(("migration-job-iam",)), label="migration job iam")
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
    notification_channels = _mapping(
        command_runner(("notification-channels",)), label="notification channels"
    )
    alert_policies = _dedupe_strings(command_runner(("alert-policies",)), label="alert policies")
    logging = _mapping(command_runner(("logging",)), label="logging")
    uptime_checks = _dedupe_uptime_checks(command_runner(("uptime-checks",)))
    workload_identity_provider = _mapping(
        command_runner(("workload-identity-provider",)),
        label="workload identity provider",
    )

    return {
        "project_labels": project_labels,
        "project_number": project_number,
        "enabled_apis": enabled_apis,
        "resource_inventory": {
            "service_accounts": service_accounts,
            "control_plane_service_accounts": control_plane_service_accounts,
            "cloud_run_service": str(cloud_run_service.get("name", "")),
            "cloud_run_job": str(migration_job.get("name", "")),
            "cloud_sql_instance": str(cloud_sql.get("name", "")),
            "state_bucket": str(state_bucket.get("name", "")),
        },
        "cloud_run_service": cloud_run_service,
        "cloud_run_service_iam": cloud_run_service_iam,
        "migration_job": migration_job,
        "migration_job_iam": migration_job_iam,
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
        "uptime_checks": uptime_checks,
        "workload_identity_provider": workload_identity_provider,
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


def _expected_deployer_principal(contract: dict[str, Any]) -> str:
    return (
        f"serviceAccount:golden-rose-deployer@{contract['control_plane_project_id']}"
        ".iam.gserviceaccount.com"
    )


def _expected_monitoring_service_agent_principal(project_number: object) -> str:
    return (
        "serviceAccount:service-"
        f"{project_number}@gcp-sa-monitoring-notification.iam.gserviceaccount.com"
    )


def _expected_migration_job_iam(contract: dict[str, Any]) -> dict[str, set[str]]:
    deployer_principal = _expected_deployer_principal(contract)
    return {
        "roles/run.jobsExecutor": {deployer_principal},
        "roles/run.viewer": {deployer_principal},
    }


def _expected_service_iam(contract: dict[str, Any], project_number: object) -> dict[str, set[str]]:
    return {
        "roles/run.invoker": {
            str(contract["private_invoker_principal"]),
            _expected_monitoring_service_agent_principal(project_number),
        },
        "roles/run.viewer": {_expected_deployer_principal(contract)},
    }


def _expected_readiness_uptime_check(
    contract: dict[str, Any], service_uri: object
) -> dict[str, Any]:
    parsed_uri = urlparse(str(service_uri))
    return {
        "display_name": APPROVED_READINESS_UPTIME_DISPLAY_NAME,
        "period": "300s",
        "timeout": "10s",
        "selected_regions": ["USA"],
        "monitored_resource": {
            "type": "uptime_url",
            "labels": {"host": parsed_uri.netloc, "project_id": str(contract["project_id"])},
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


def _expected_workload_identity_provider_snapshot() -> dict[str, Any]:
    return {
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
        "required_condition_fragments": {
            f'attribute.repository == "{GITHUB_REPOSITORY}"',
            'attribute.repository_owner == "b-mackenzie-alexander"',
            f'attribute.ref == "{GITHUB_PROTECTED_REF}"',
            'attribute.environment == "develop"',
            'attribute.event_name == "workflow_dispatch"',
            f'attribute.workflow_ref == "{BUILD_IMAGE_WORKFLOW_REF}"',
            f'attribute.workflow_ref == "{DEPLOY_DEVELOP_WORKFLOW_REF}"',
        },
    }


def _expected_control_plane_service_account_iam(
    contract: dict[str, Any],
) -> dict[str, dict[str, str]]:
    control_plane_project_id = str(contract["control_plane_project_id"])
    return {
        f"golden-rose-provisioner@{control_plane_project_id}.iam.gserviceaccount.com": {},
        f"golden-rose-image-publisher@{control_plane_project_id}.iam.gserviceaccount.com": {
            WIF_ROLE: f"/attribute.workflow_ref/{BUILD_IMAGE_WORKFLOW_REF}"
        },
        f"golden-rose-deployer@{control_plane_project_id}.iam.gserviceaccount.com": {
            WIF_ROLE: f"/attribute.workflow_ref/{DEPLOY_DEVELOP_WORKFLOW_REF}"
        },
    }


def _as_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def evaluate_foundation_snapshot(
    snapshot: dict[str, Any],
    contract: dict[str, Any],
    mode: str = "service",
) -> list[str]:
    violations: list[str] = []

    if mode not in ("foundation", "migration", "service"):
        raise VerificationError(
            f"mode must be one of: foundation, migration, service; got {mode!r}"
        )

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
    if mode != "foundation" and resource_inventory.get("cloud_run_job") != "run-migrations":
        violations.append("migration job inventory drifted from run-migrations")
    if mode == "service" and resource_inventory.get("cloud_run_service") != "staff-tracer":
        violations.append("cloud run service inventory drifted from staff-tracer")
    if resource_inventory.get("cloud_sql_instance") != "develop-postgres":
        violations.append("cloud sql inventory drifted from develop-postgres")
    if resource_inventory.get("state_bucket") != contract["state_bucket_name"]:
        violations.append("state bucket inventory drifted from the reviewed bucket name")

    # Stage-mode checks: foundation must have no workload, migration must have
    # job but no service, service must have both job and service.
    cloud_run_service_name = resource_inventory.get("cloud_run_service", "")
    cloud_run_job_name = resource_inventory.get("cloud_run_job", "")

    if mode == "foundation":
        if cloud_run_service_name:
            violations.append("foundation verifier mode rejects present cloud_run_service workload")
        if cloud_run_job_name:
            violations.append("foundation verifier mode rejects present cloud_run_job workload")
    elif mode == "migration":
        if not cloud_run_job_name:
            violations.append("migration verifier mode requires cloud_run_job to be present")
        if cloud_run_service_name:
            violations.append("migration verifier mode rejects present cloud_run_service workload")
    elif mode == "service":
        if not cloud_run_job_name:
            violations.append("service verifier mode requires cloud_run_job to be present")
        if not cloud_run_service_name:
            violations.append("service verifier mode requires cloud_run_service to be present")

    cloud_run_service = _mapping(snapshot.get("cloud_run_service", {}), label="cloud run service")
    if mode == "service":
        if cloud_run_service.get("labels") != APPROVED_PROJECT_LABELS:
            violations.append("cloud run service labels drifted from the approved develop posture")
        if cloud_run_service.get("ingress") != "INGRESS_TRAFFIC_ALL":
            violations.append(
                "cloud run service ingress is not the reviewed "
                "iam-private internet-reachable posture"
            )
        if (
            cloud_run_service.get("service_account")
            != f"staff-tracer-runtime@{contract['project_id']}.iam.gserviceaccount.com"
        ):
            violations.append(
                "cloud run service runtime identity drifted from staff-tracer-runtime"
            )
        image = str(cloud_run_service.get("image", ""))
        if not re.search(r"@sha256:[0-9a-f]{64}$", image):
            violations.append("service verifier mode requires digest-bound cloud run service image")
    elif cloud_run_service:
        violations.append(
            "non-service verifier modes reject cloud run service configuration presence"
        )

    cloud_run_service_iam = _mapping(
        snapshot.get("cloud_run_service_iam", {}), label="cloud run service iam"
    )
    if mode == "service":
        actual_invokers = _as_set(cloud_run_service_iam.get("roles/run.invoker"))
        if "allUsers" in actual_invokers or "allAuthenticatedUsers" in actual_invokers:
            violations.append("public Cloud Run invoker detected")
        expected_service_iam = _expected_service_iam(contract, snapshot.get("project_number"))
        expected_monitoring_agent = _expected_monitoring_service_agent_principal(
            snapshot.get("project_number")
        )
        if expected_monitoring_agent not in actual_invokers:
            violations.append(
                "cloud run monitoring invoker bindings drifted from the reviewed "
                "service-agent authority"
            )
        if set(cloud_run_service_iam) != set(expected_service_iam):
            violations.append(
                "cloud run service IAM roles drifted from the reviewed resource authority boundary"
            )
        for role, expected_members in expected_service_iam.items():
            if _as_set(cloud_run_service_iam.get(role)) != expected_members:
                violations.append(
                    f"cloud run service IAM drifted for {role} from the reviewed "
                    "resource authority boundary"
                )
        if not _is_reviewed_named_tester_principal(str(contract["private_invoker_principal"])):
            violations.append(
                "reviewed private invoker principal is not a named tester user principal"
            )
    elif cloud_run_service_iam:
        violations.append("non-service verifier modes reject cloud run invoker IAM presence")

    migration_job = _mapping(snapshot.get("migration_job", {}), label="migration job")
    if mode in {"migration", "service"}:
        if migration_job.get("labels") != APPROVED_PROJECT_LABELS:
            violations.append("migration job labels drifted from the approved develop posture")
        if (
            migration_job.get("service_account")
            != f"staff-tracer-migration@{contract['project_id']}.iam.gserviceaccount.com"
        ):
            violations.append("migration job identity drifted from staff-tracer-migration")
        if migration_job.get("parallelism") != 1 or migration_job.get("task_count") != 1:
            violations.append("migration job lost serialized execution posture")
        image = str(migration_job.get("image", ""))
        if not re.search(r"@sha256:[0-9a-f]{64}$", image):
            violations.append("migration verifier modes require digest-bound migration job image")
        migration_job_iam = _mapping(
            snapshot.get("migration_job_iam", {}), label="migration job iam"
        )
        expected_migration_job_iam = _expected_migration_job_iam(contract)
        if set(migration_job_iam) != set(expected_migration_job_iam):
            violations.append(
                "migration job IAM roles drifted from the reviewed resource authority boundary"
            )
        for role, expected_members in expected_migration_job_iam.items():
            if _as_set(migration_job_iam.get(role)) != expected_members:
                violations.append(
                    f"migration job IAM drifted for {role} from the reviewed "
                    "resource authority boundary"
                )
    elif migration_job:
        violations.append("foundation verifier mode rejects migration job configuration presence")
    elif _mapping(snapshot.get("migration_job_iam", {}), label="migration job iam"):
        violations.append("foundation verifier mode rejects migration job IAM presence")

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
    runtime_email = f"staff-tracer-runtime@{contract['project_id']}.iam.gserviceaccount.com"
    migration_email = f"staff-tracer-migration@{contract['project_id']}.iam.gserviceaccount.com"
    for email in (runtime_email, migration_email):
        actual = _mapping(service_account_iam.get(email, {}), label=f"service account iam {email}")
        if actual:
            violations.append(f"service-account IAM drifted for {email}")
    expected_control_plane_iam = _expected_control_plane_service_account_iam(contract)
    for email, expected_roles in expected_control_plane_iam.items():
        actual = _mapping(service_account_iam.get(email, {}), label=f"service account iam {email}")
        if set(actual) != set(expected_roles):
            violations.append(f"WIF service-account IAM drifted for {email}")
            continue
        for role, expected_suffix in expected_roles.items():
            members = _as_set(actual.get(role))
            if len(members) != 1:
                violations.append(f"WIF principal binding drifted for {email} role {role}")
                continue
            member = next(iter(members))
            if not member.startswith("principalSet://iam.googleapis.com/") or not member.endswith(
                expected_suffix
            ):
                violations.append(f"WIF principal binding drifted for {email} role {role}")

    workload_identity_provider = _mapping(
        snapshot.get("workload_identity_provider", {}),
        label="workload identity provider",
    )
    expected_provider = _expected_workload_identity_provider_snapshot()
    if workload_identity_provider.get("pool_id") != expected_provider["pool_id"]:
        violations.append("workload identity pool drifted from reviewed bootstrap pool")
    if workload_identity_provider.get("provider_id") != expected_provider["provider_id"]:
        violations.append("workload identity provider drifted from reviewed bootstrap provider")
    if (
        workload_identity_provider.get("attribute_mapping")
        != expected_provider["attribute_mapping"]
    ):
        violations.append("workload identity provider attribute mapping drifted")
    attribute_condition = str(workload_identity_provider.get("attribute_condition", ""))
    for fragment in expected_provider["required_condition_fragments"]:
        if fragment not in attribute_condition:
            violations.append(
                f"workload identity provider missing required exact authority claim {fragment!r}"
            )

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
    notification_channels = _mapping(
        snapshot.get("notification_channels", {}), label="notification channels"
    )
    approved_channel_resource_names = _canonical_channel_resource_names(notification_channels)
    if (
        approved_channel_resource_names != {"projects/example-project/notificationChannels/123"}
        and len(approved_channel_resource_names) != 1
    ):
        violations.append("notification channel inventory drifted from the reviewed alert route")
    if (
        _as_set(budget.get("notification_channel_resource_names"))
        != approved_channel_resource_names
    ):
        violations.append(
            "budget alert route drifted from the reviewed notification channel identity"
        )
    if set(notification_channels.values()) != {APPROVED_NOTIFICATION_CHANNEL}:
        violations.append("notification channel inventory drifted from the reviewed alert route")

    alert_policies = (
        set(snapshot.get("alert_policies", []))
        if isinstance(snapshot.get("alert_policies"), list)
        else set()
    )
    expected_alert_policies = (
        APPROVED_ALERT_POLICIES_SERVICE if mode == "service" else APPROVED_ALERT_POLICIES_BASE
    )
    if alert_policies != expected_alert_policies:
        violations.append("alert policy inventory drifted from the reviewed observability posture")

    logging = _mapping(snapshot.get("logging", {}), label="logging")
    if logging.get("default_bucket_retention_days") != contract["log_retention_days"]:
        violations.append("default logging retention drifted from the reviewed posture")
    if _as_set(logging.get("sinks")):
        violations.append("unexpected logging sink detected")
    logging_exclusions = _mapping(logging.get("exclusions", {}), label="logging exclusions")
    if logging_exclusions.get(APPROVED_LOGGING_EXCLUSION_NAME) is None:
        violations.append("uuid-bearing staff path logging exclusion is missing")
    elif APPROVED_LOGGING_EXCLUSION_FILTER_FRAGMENT not in str(
        logging_exclusions.get(APPROVED_LOGGING_EXCLUSION_NAME)
    ):
        violations.append("uuid-bearing staff path logging exclusion filter drifted")

    uptime_checks = _dedupe_uptime_checks(snapshot.get("uptime_checks", []))
    if mode == "service":
        if len(uptime_checks) != 1 or uptime_checks[0].get("display_name") != (
            APPROVED_READINESS_UPTIME_DISPLAY_NAME
        ):
            violations.append(
                "service verifier mode requires exactly one authenticated readiness uptime check"
            )
        elif uptime_checks[0] != _expected_readiness_uptime_check(
            contract, cloud_run_service.get("uri")
        ):
            violations.append(
                "authenticated readiness uptime check configuration drifted from the reviewed "
                "host, readiness GET, TLS, and OIDC service-agent posture"
            )
    elif uptime_checks:
        violations.append(
            "non-service verifier modes reject authenticated readiness uptime check presence"
        )

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


def validate_stage_plan_receipt(
    receipt: dict[str, Any],
    expected_stage: str,
) -> list[str]:
    """Validate a saved-plan receipt contract.

    Required fields: stage, source_sha, plan_hash, provider_lock_digest,
    non_secret_input_digest, evaluated_inventory, approval_reference.
    Optional for migration/service: workload_image_digest.

    Returns a list of violation strings; empty means the receipt is valid.
    """
    violations: list[str] = []

    required_fields = [
        "stage",
        "source_sha",
        "plan_hash",
        "provider_lock_digest",
        "non_secret_input_digest",
        "evaluated_inventory",
        "approval_reference",
    ]

    for field in required_fields:
        if field not in receipt:
            violations.append(f"saved-plan receipt missing required field {field!r}")

    if "stage" in receipt and receipt["stage"] != expected_stage:
        violations.append(
            f"saved-plan receipt stage is {receipt['stage']!r} but expected {expected_stage!r}"
        )

    inventory = receipt.get("evaluated_inventory", {})
    if not isinstance(inventory, dict):
        violations.append("saved-plan receipt evaluated_inventory must be an object")
        inventory = {}

    service_count = int(inventory.get("google_cloud_run_v2_service", 0))
    job_count = int(inventory.get("google_cloud_run_v2_job", 0))

    if expected_stage == "foundation":
        if service_count > 0:
            violations.append(
                "saved-plan receipt evaluated_inventory contains cloud_run_service "
                "in foundation stage; foundation must have no executable workload"
            )
        if job_count > 0:
            violations.append(
                "saved-plan receipt evaluated_inventory contains cloud_run_job "
                "in foundation stage; foundation must have no executable workload"
            )
    elif expected_stage == "migration":
        if service_count > 0:
            violations.append(
                "saved-plan receipt evaluated_inventory contains cloud_run_service "
                "in migration stage; migration must not have a service"
            )
        if job_count < 1:
            violations.append(
                "saved-plan receipt evaluated_inventory missing cloud_run_job "
                "in migration stage; migration must have the job"
            )
    elif expected_stage == "service":
        if job_count < 1:
            violations.append(
                "saved-plan receipt evaluated_inventory missing cloud_run_job "
                "in service stage; service requires both job and service"
            )
        if service_count < 1:
            violations.append(
                "saved-plan receipt evaluated_inventory missing cloud_run_service "
                "in service stage; service requires both job and service"
            )

    # Workload image digest required for migration and service stages
    if (
        expected_stage in ("migration", "service")
        and job_count > 0
        and not receipt.get("workload_image_digest")
    ):
        violations.append(
            f"saved-plan receipt missing workload_image_digest for {expected_stage} stage "
            "with present executable workload"
        )

    return violations


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
        if key == ("project-number",):
            project = _run_json_command(
                ["gcloud", "projects", "describe", project_id, "--format=json"],
                context="project number",
            )
            project_number = _mapping(project, label="project").get("projectNumber")
            if not isinstance(project_number, str) or not project_number.isdecimal():
                raise VerificationError("project number is missing or malformed")
            return project_number
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
            try:
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
            except VerificationError as exc:
                if "not found" in str(exc).lower() or "not_found" in str(exc).lower():
                    return {}
                raise
            template = _mapping(service, label="service").get("template", {})
            containers = _mapping(template, label="service template").get("containers", [])
            container = containers[0] if isinstance(containers, list) and containers else {}
            return {
                "name": service.get("name"),
                "uri": service.get("uri"),
                "labels": _mapping(service, label="service").get("labels", {}),
                "ingress": service.get("ingress"),
                "service_account": _mapping(template, label="service template").get(
                    "serviceAccount"
                ),
                "image": _mapping(container, label="cloud run service container").get("image"),
            }
        if key == ("cloud-run-service-iam",):
            try:
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
            except VerificationError as exc:
                if "not found" in str(exc).lower() or "not_found" in str(exc).lower():
                    return {}
                raise
            return _bindings_to_role_map(policy)
        if key == ("migration-job",):
            try:
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
            except VerificationError as exc:
                if "not found" in str(exc).lower() or "not_found" in str(exc).lower():
                    return {}
                raise
            template = _mapping(job, label="job").get("template", {})
            task_template = _mapping(template, label="job template").get("template", {})
            containers = _mapping(task_template, label="job task template").get("containers", [])
            container = containers[0] if isinstance(containers, list) and containers else {}
            return {
                "name": job.get("name"),
                "labels": _mapping(job, label="job").get("labels", {}),
                "service_account": task_template.get("serviceAccount"),
                "parallelism": template.get("parallelism"),
                "task_count": template.get("taskCount"),
                "image": _mapping(container, label="migration job container").get("image"),
            }
        if key == ("migration-job-iam",):
            try:
                policy = _run_json_command(
                    [
                        "gcloud",
                        "run",
                        "jobs",
                        "get-iam-policy",
                        "run-migrations",
                        "--project",
                        project_id,
                        "--region",
                        region,
                        "--format=json",
                    ],
                    context="migration job iam",
                )
            except VerificationError as exc:
                if "not found" in str(exc).lower() or "not_found" in str(exc).lower():
                    return {}
                raise
            return _bindings_to_role_map(policy)
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
        if key == ("workload-identity-provider",):
            pool = _run_json_command(
                [
                    "gcloud",
                    "iam",
                    "workload-identity-pools",
                    "describe",
                    "golden-rose-github",
                    "--project",
                    control_plane_project_id,
                    "--location",
                    "global",
                    "--format=json",
                ],
                context="workload identity pool",
            )
            provider = _run_json_command(
                [
                    "gcloud",
                    "iam",
                    "workload-identity-pools",
                    "providers",
                    "describe",
                    "golden-rose-github-provider",
                    "--project",
                    control_plane_project_id,
                    "--location",
                    "global",
                    "--workload-identity-pool",
                    "golden-rose-github",
                    "--format=json",
                ],
                context="workload identity provider",
            )
            return {
                "pool_id": pool.get("workloadIdentityPoolId"),
                "provider_id": provider.get("workloadIdentityPoolProviderId"),
                "attribute_mapping": provider.get("attributeMapping", {}),
                "attribute_condition": provider.get("attributeCondition", ""),
            }
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
                        "notification_channel_resource_names": channels,
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
            return {
                str(channel.get("name")): str(channel.get("displayName"))
                for channel in channels
                if isinstance(channel, dict)
            }
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
        if key == ("uptime-checks",):
            configs = _run_json_command(
                [
                    "gcloud",
                    "monitoring",
                    "uptime",
                    "list-configs",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="uptime checks",
            )
            return [
                {
                    "display_name": config.get("displayName"),
                    "period": config.get("period"),
                    "timeout": config.get("timeout"),
                    "selected_regions": config.get("selectedRegions"),
                    "monitored_resource": {
                        "type": _mapping(
                            config.get("monitoredResource", {}), label="uptime monitored resource"
                        ).get("type"),
                        "labels": _mapping(
                            _mapping(
                                config.get("monitoredResource", {}),
                                label="uptime monitored resource",
                            ).get("labels", {}),
                            label="uptime monitored resource labels",
                        ),
                    },
                    "http_check": {
                        "request_method": _mapping(
                            config.get("httpCheck", {}), label="uptime http check"
                        ).get("requestMethod"),
                        "path": _mapping(
                            config.get("httpCheck", {}), label="uptime http check"
                        ).get("path"),
                        "port": _mapping(
                            config.get("httpCheck", {}), label="uptime http check"
                        ).get("port"),
                        "use_ssl": _mapping(
                            config.get("httpCheck", {}), label="uptime http check"
                        ).get("useSsl"),
                        "validate_ssl": _mapping(
                            config.get("httpCheck", {}), label="uptime http check"
                        ).get("validateSsl"),
                        "service_agent_authentication": _mapping(
                            _mapping(config.get("httpCheck", {}), label="uptime http check").get(
                                "serviceAgentAuthentication", {}
                            ),
                            label="uptime service agent authentication",
                        ),
                    },
                }
                for config in configs
                if isinstance(config, dict)
            ]
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
            exclusions = _run_json_command(
                [
                    "gcloud",
                    "logging",
                    "exclusions",
                    "list",
                    "--project",
                    project_id,
                    "--format=json",
                ],
                context="logging exclusions",
            )
            return {
                "default_bucket_retention_days": bucket.get("retentionDays"),
                "sinks": [sink.get("name") for sink in sinks if isinstance(sink, dict)],
                "exclusions": {
                    str(exclusion.get("name")): str(exclusion.get("filter"))
                    for exclusion in exclusions
                    if isinstance(exclusion, dict)
                },
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
    tester_authority = derive_tester_authority_contract(
        receipt_path=args.tester_authority_receipt,
        bundle_path=args.tester_authority_bundle,
        certificate_identity=args.tester_authority_certificate_identity,
        project_id=args.project_id,
        region=args.region,
    )
    contract = {
        "project_id": args.project_id,
        "control_plane_project_id": args.control_plane_project_id,
        "region": args.region,
        "state_bucket_name": args.state_bucket_name,
        "private_invoker_principal": tester_authority["private_invoker_principal"],
        "tester_authority_receipt_sha256": tester_authority["tester_authority_receipt_sha256"],
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
    violations = evaluate_foundation_snapshot(snapshot, contract, mode=args.mode)

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
