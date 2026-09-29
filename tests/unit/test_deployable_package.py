from pathlib import Path

import pytest

from scripts.validate_deployable_package import (
    ENV_TEMPLATE_PATH,
    INPUTS_TEMPLATE_PATH,
    RUNBOOK_PATH,
    PackageValidationError,
    validate,
)

ROOT = Path(__file__).resolve().parents[2]


def _copy_package(tmp_path: Path) -> Path:
    for relative_path in (RUNBOOK_PATH, ENV_TEMPLATE_PATH, INPUTS_TEMPLATE_PATH):
        source = ROOT / relative_path
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def test_deployable_package_artifacts_are_placeholder_only_and_complete() -> None:
    checked = validate(ROOT)

    assert checked == [
        str(RUNBOOK_PATH),
        str(ENV_TEMPLATE_PATH),
        str(INPUTS_TEMPLATE_PATH),
    ]


def test_deployable_package_rejects_synthetic_production_auth(tmp_path: Path) -> None:
    root = _copy_package(tmp_path)
    env_path = root / ENV_TEMPLATE_PATH
    env_path.write_text(
        env_path.read_text(encoding="utf-8").replace(
            "GOLDEN_ROSE_AUTH_MODE=staff_oidc",
            "GOLDEN_ROSE_AUTH_MODE=synthetic",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="GOLDEN_ROSE_AUTH_MODE"):
        validate(root)


def test_deployable_package_rejects_demo_access_in_production_template(tmp_path: Path) -> None:
    root = _copy_package(tmp_path)
    env_path = root / ENV_TEMPLATE_PATH
    env_path.write_text(
        env_path.read_text(encoding="utf-8").replace(
            "GOLDEN_ROSE_DEMO_ACCESS_ENABLED=false",
            "GOLDEN_ROSE_DEMO_ACCESS_ENABLED=true",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="GOLDEN_ROSE_DEMO_ACCESS_ENABLED"):
        validate(root)


def test_deployable_package_rejects_concrete_private_values(tmp_path: Path) -> None:
    root = _copy_package(tmp_path)
    inputs_path = root / INPUTS_TEMPLATE_PATH
    inputs_path.write_text(
        inputs_path.read_text(encoding="utf-8").replace(
            "<https-staff-oidc-issuer-url>",
            "https://accounts.private.example.test",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="concrete URL"):
        validate(root)


def test_deployable_package_rejects_missing_handoff_owner(tmp_path: Path) -> None:
    root = _copy_package(tmp_path)
    inputs_path = root / INPUTS_TEMPLATE_PATH
    inputs_path.write_text(
        inputs_path.read_text(encoding="utf-8").replace(
            '    "acceptance_owner": "<private-owner-record>"',
            '    "release_owner": "<private-owner-record>"',
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="operations.acceptance_owner"):
        validate(root)
