import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "verify_tester_authority_receipt.py"
PRINCIPAL = "user:private.tester@example.com"
RECEIPT = {
    "schema": "golden-rose.tester-authority/v1",
    "principal": PRINCIPAL,
    "scope": {
        "project_id": "example-project",
        "region": "us-east4",
        "service": "staff-tracer",
        "role": "roles/run.invoker",
    },
    "approval_reference": "operator-held",
    "issued_at": "2026-08-24T00:00:00Z",
    "expires_at": "2026-08-25T00:00:00Z",
}


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_tester_authority_receipt", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verified_receipt_derives_only_the_scoped_principal_and_receipt_digest(
    tmp_path: Path,
) -> None:
    module = load_module()
    receipt = tmp_path / "tester-receipt.json"
    bundle = tmp_path / "tester-receipt.sigstore.json"
    output = tmp_path / "tester-authority.tfvars.json"
    receipt.write_bytes(json.dumps(RECEIPT, sort_keys=True).encode("utf-8"))
    bundle.write_text(
        '{"mediaType":"application/vnd.dev.sigstore.bundle+json;version=0.3"}', encoding="utf-8"
    )
    observed_commands: list[list[str]] = []

    derived = module.verify_and_derive_tester_authority(
        receipt_path=receipt,
        bundle_path=bundle,
        certificate_identity="https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
        expected_project_id="example-project",
        expected_region="us-east4",
        expected_service="staff-tracer",
        verifier_runner=lambda command: observed_commands.append(command),
    )
    module.write_terraform_vars(output, derived)

    assert observed_commands == [
        [
            "cosign",
            "verify-blob",
            str(receipt),
            "--bundle",
            str(bundle),
            "--certificate-identity",
            "https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
            "--certificate-oidc-issuer",
            "https://token.actions.githubusercontent.com",
        ]
    ]
    assert derived["private_invoker_principal"] == PRINCIPAL
    assert len(derived["tester_authority_receipt_sha256"]) == 64
    assert json.loads(output.read_text(encoding="utf-8")) == derived


def test_receipt_contract_rejects_arbitrary_principal_and_hex_digest_substitution(
    tmp_path: Path,
) -> None:
    module = load_module()
    receipt = tmp_path / "tester-receipt.json"
    bundle = tmp_path / "tester-receipt.sigstore.json"
    tampered = dict(RECEIPT)
    tampered["principal"] = "group:attackers@example.com"
    receipt.write_text(json.dumps(tampered), encoding="utf-8")
    bundle.write_text("{}", encoding="utf-8")

    with pytest.raises(module.TesterAuthorityReceiptError, match="principal"):
        module.verify_and_derive_tester_authority(
            receipt_path=receipt,
            bundle_path=bundle,
            certificate_identity="https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
            expected_project_id="example-project",
            expected_region="us-east4",
            expected_service="staff-tracer",
            verifier_runner=lambda command: None,
        )


def test_receipt_contract_rejects_unverified_bundle_before_deriving(tmp_path: Path) -> None:
    module = load_module()
    receipt = tmp_path / "tester-receipt.json"
    bundle = tmp_path / "tester-receipt.sigstore.json"
    receipt.write_text(json.dumps(RECEIPT), encoding="utf-8")
    bundle.write_text("{}", encoding="utf-8")

    def rejected_verifier(command: list[str]) -> None:
        raise module.TesterAuthorityReceiptError("cosign verify-blob failed")

    with pytest.raises(module.TesterAuthorityReceiptError, match="cosign verify-blob failed"):
        module.verify_and_derive_tester_authority(
            receipt_path=receipt,
            bundle_path=bundle,
            certificate_identity="https://github.com/example/authority/.github/workflows/tester-authority.yml@refs/heads/main",
            expected_project_id="example-project",
            expected_region="us-east4",
            expected_service="staff-tracer",
            verifier_runner=rejected_verifier,
        )
