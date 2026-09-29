import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_client_production_plan import PlanValidationError, validate_plan

DIGEST_IMAGE = "us-docker.pkg.dev/client/repo/golden-rose@sha256:" + ("a" * 64)


def _cloud_run_after(*, image: str = DIGEST_IMAGE) -> dict[str, Any]:
    return {
        "template": {
            "containers": [
                {
                    "image": image,
                    "env": [
                        {"name": "GOLDEN_ROSE_ENVIRONMENT", "value": "production"},
                        {"name": "GOLDEN_ROSE_AUTH_MODE", "value": "staff_oidc"},
                        {
                            "name": "GOLDEN_ROSE_STAFF_OIDC_ISSUER",
                            "value_source": {"secret_key_ref": {"secret": "oidc-issuer"}},
                        },
                        {
                            "name": "GOLDEN_ROSE_STAFF_OIDC_AUDIENCE",
                            "value_source": {"secret_key_ref": {"secret": "oidc-audience"}},
                        },
                        {
                            "name": "GOLDEN_ROSE_STAFF_OIDC_JWKS_URL",
                            "value_source": {"secret_key_ref": {"secret": "oidc-jwks"}},
                        },
                        {"name": "GOLDEN_ROSE_DEMO_ACCESS_ENABLED", "value": "false"},
                        {
                            "name": "GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED",
                            "value": "false",
                        },
                    ],
                }
            ]
        }
    }


def _resource_change(
    *,
    address: str,
    resource_type: str,
    after: dict[str, Any],
    actions: list[str] | None = None,
    mode: str = "managed",
    after_unknown: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "address": address,
        "mode": mode,
        "type": resource_type,
        "name": address.rsplit(".", 1)[-1],
        "change": {
            "actions": actions or ["create"],
            "after": after,
            "after_unknown": after_unknown or {},
        },
    }


def _write_plan(tmp_path: Path, resource_changes: list[dict[str, Any]]) -> Path:
    path = tmp_path / "tfplan.json"
    path.write_text(
        json.dumps({"format_version": "1.2", "resource_changes": resource_changes}),
        encoding="utf-8",
    )
    return path


def _valid_plan(tmp_path: Path) -> Path:
    return _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=_cloud_run_after(),
            ),
            _resource_change(
                address="google_sql_database_instance.main",
                resource_type="google_sql_database_instance",
                after={
                    "settings": {
                        "ip_configuration": {
                            "ipv4_enabled": False,
                            "authorized_networks": [],
                        }
                    }
                },
            ),
            _resource_change(
                address="google_project_iam_member.runtime",
                resource_type="google_project_iam_member",
                after={
                    "role": "roles/cloudsql.client",
                    "member": "serviceAccount:runtime@example.invalid",
                },
            ),
        ],
    )


def test_client_production_plan_accepts_private_staff_oidc_posture(tmp_path: Path) -> None:
    checked = validate_plan(_valid_plan(tmp_path))

    assert checked == [
        "google_cloud_run_v2_service.staff",
        "google_sql_database_instance.main",
        "google_project_iam_member.runtime",
    ]


def test_client_production_plan_rejects_delete_or_replacement(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                actions=["delete", "create"],
                after=_cloud_run_after(),
            )
        ],
    )

    with pytest.raises(PlanValidationError, match="delete or replacement"):
        validate_plan(plan)


def test_client_production_plan_rejects_public_sql_networking(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=_cloud_run_after(),
            ),
            _resource_change(
                address="google_sql_database_instance.main",
                resource_type="google_sql_database_instance",
                after={
                    "settings": {
                        "ip_configuration": {
                            "ipv4_enabled": True,
                            "authorized_networks": [{"name": "office"}],
                        }
                    }
                },
            ),
        ],
    )

    with pytest.raises(PlanValidationError, match="public SQL IPv4"):
        validate_plan(plan)


def test_client_production_plan_rejects_broad_iam(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=_cloud_run_after(),
            ),
            _resource_change(
                address="google_project_iam_binding.owner",
                resource_type="google_project_iam_binding",
                after={"role": "roles/owner", "members": ["allUsers"]},
            ),
        ],
    )

    with pytest.raises(PlanValidationError, match="broad IAM members"):
        validate_plan(plan)


def test_client_production_plan_rejects_mutable_cloud_run_image(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=_cloud_run_after(image="us-docker.pkg.dev/client/repo/golden-rose:latest"),
            )
        ],
    )

    with pytest.raises(PlanValidationError, match="immutable image digest"):
        validate_plan(plan)


def test_client_production_plan_rejects_missing_staff_oidc_env(tmp_path: Path) -> None:
    cloud_run = _cloud_run_after()
    env = cloud_run["template"]["containers"][0]["env"]
    cloud_run["template"]["containers"][0]["env"] = [
        item for item in env if item["name"] != "GOLDEN_ROSE_STAFF_OIDC_JWKS_URL"
    ]
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=cloud_run,
            )
        ],
    )

    with pytest.raises(PlanValidationError, match="STAFF_OIDC_JWKS_URL"):
        validate_plan(plan)


def test_client_production_plan_rejects_demo_access(tmp_path: Path) -> None:
    cloud_run = _cloud_run_after()
    for item in cloud_run["template"]["containers"][0]["env"]:
        if item["name"] == "GOLDEN_ROSE_DEMO_ACCESS_ENABLED":
            item["value"] = "true"
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=cloud_run,
            )
        ],
    )

    with pytest.raises(PlanValidationError, match="DEMO_ACCESS_ENABLED"):
        validate_plan(plan)


def test_client_production_plan_rejects_synthetic_staff_actor(tmp_path: Path) -> None:
    cloud_run = _cloud_run_after()
    cloud_run["template"]["containers"][0]["env"].append(
        {"name": "GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "value": "synthetic-staff-id"}
    )
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=cloud_run,
            )
        ],
    )

    with pytest.raises(PlanValidationError, match="SYNTHETIC_STAFF_ID"):
        validate_plan(plan)


def test_client_production_plan_rejects_secret_payload_resources(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_cloud_run_v2_service.staff",
                resource_type="google_cloud_run_v2_service",
                after=_cloud_run_after(),
            ),
            _resource_change(
                address="google_secret_manager_secret_version.database_url",
                resource_type="google_secret_manager_secret_version",
                after={"secret_data": "redacted-fixture"},
            ),
        ],
    )

    with pytest.raises(PlanValidationError, match="Secret Manager payload"):
        validate_plan(plan)


def test_client_production_plan_requires_verifiable_cloud_run(tmp_path: Path) -> None:
    plan = _write_plan(
        tmp_path,
        [
            _resource_change(
                address="google_sql_database_instance.main",
                resource_type="google_sql_database_instance",
                after={"settings": {"ip_configuration": {"ipv4_enabled": False}}},
            )
        ],
    )

    with pytest.raises(PlanValidationError, match="verifiable Cloud Run"):
        validate_plan(plan)
