from pathlib import Path

import pytest

from scripts.validate_deployable_package import (
    ENV_TEMPLATE_PATH,
    HANDOFF_TEMPLATE_PATH,
    INPUTS_TEMPLATE_PATH,
    PACKAGE_INDEX_PATH,
    POLICY_TEMPLATE_PATH,
    READINESS_CHECKLIST_PATH,
    RUNBOOK_PATH,
    PackageValidationError,
    validate,
)

ROOT = Path(__file__).resolve().parents[2]


def _copy_package(tmp_path: Path) -> Path:
    for relative_path in (
        RUNBOOK_PATH,
        ENV_TEMPLATE_PATH,
        INPUTS_TEMPLATE_PATH,
        POLICY_TEMPLATE_PATH,
        HANDOFF_TEMPLATE_PATH,
        READINESS_CHECKLIST_PATH,
        PACKAGE_INDEX_PATH,
    ):
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
        str(POLICY_TEMPLATE_PATH),
        str(HANDOFF_TEMPLATE_PATH),
        str(READINESS_CHECKLIST_PATH),
        str(PACKAGE_INDEX_PATH),
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


def test_deployable_package_rejects_policy_with_demo_access(tmp_path: Path) -> None:
    root = _copy_package(tmp_path)
    policy_path = root / POLICY_TEMPLATE_PATH
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8").replace(
            '"demo_access_enabled": false',
            '"demo_access_enabled": true',
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="demo_access_enabled"):
        validate(root)


def test_deployable_package_rejects_policy_missing_forbidden_replacements(
    tmp_path: Path,
) -> None:
    root = _copy_package(tmp_path)
    policy_path = root / POLICY_TEMPLATE_PATH
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8").replace(
            '      "replace"\n',
            '      "recreate"\n',
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="forbidden_actions"):
        validate(root)


def test_deployable_package_rejects_policy_missing_staff_oidc_check(
    tmp_path: Path,
) -> None:
    root = _copy_package(tmp_path)
    policy_path = root / POLICY_TEMPLATE_PATH
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8").replace(
            '      "staff_oidc_configuration_required",\n',
            "",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="fail_closed_checks"):
        validate(root)


def test_deployable_package_rejects_policy_concrete_artifact_evidence(
    tmp_path: Path,
) -> None:
    root = _copy_package(tmp_path)
    policy_path = root / POLICY_TEMPLATE_PATH
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8").replace(
            "<value-safe-cosign-admission-record>",
            "signed-by-prod-operator",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="signature_evidence"):
        validate(root)


def test_deployable_package_rejects_handoff_template_concrete_acceptance(
    tmp_path: Path,
) -> None:
    root = _copy_package(tmp_path)
    handoff_path = root / HANDOFF_TEMPLATE_PATH
    handoff_path.write_text(
        handoff_path.read_text(encoding="utf-8").replace(
            "<private-acceptance-record>",
            "owner accepted production handoff",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="acceptance_checklist"):
        validate(root)


def test_deployable_package_rejects_readiness_checklist_production_activation(
    tmp_path: Path,
) -> None:
    root = _copy_package(tmp_path)
    readiness_path = root / READINESS_CHECKLIST_PATH
    readiness_path.write_text(
        readiness_path.read_text(encoding="utf-8").replace(
            "not-executed-without-separate-approval",
            "production-deployed",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="activation_boundary"):
        validate(root)


def test_deployable_package_rejects_package_index_missing_validator(
    tmp_path: Path,
) -> None:
    root = _copy_package(tmp_path)
    index_path = root / PACKAGE_INDEX_PATH
    index_path.write_text(
        index_path.read_text(encoding="utf-8").replace(
            '"path": "scripts/validate_client_package_index.py"',
            '"path": "scripts/validate_unreviewed_package_index.py"',
        ),
        encoding="utf-8",
    )

    with pytest.raises(PackageValidationError, match="source_artifacts"):
        validate(root)
