from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PRINCIPAL_PATTERN = re.compile(r"^user:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+$")
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
SCHEMA = "golden-rose.tester-authority/v1"


class TesterAuthorityReceiptError(ValueError):
    pass


def _load_receipt(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise TesterAuthorityReceiptError("tester authority receipt must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise TesterAuthorityReceiptError("tester authority receipt must be an object")
    return payload, hashlib.sha256(raw).hexdigest()


def _run_cosign(command: list[str]) -> None:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode:
        raise TesterAuthorityReceiptError("cosign verify-blob failed")


def verify_and_derive_tester_authority(
    *,
    receipt_path: Path,
    bundle_path: Path,
    certificate_identity: str,
    expected_project_id: str,
    expected_region: str,
    expected_service: str,
    verifier_runner: Callable[[list[str]], None] = _run_cosign,
) -> dict[str, str]:
    if not certificate_identity.startswith("https://github.com/"):
        raise TesterAuthorityReceiptError(
            "tester receipt certificate identity must be a reviewed GitHub workflow identity"
        )
    command = [
        "cosign",
        "verify-blob",
        str(receipt_path),
        "--bundle",
        str(bundle_path),
        "--certificate-identity",
        certificate_identity,
        "--certificate-oidc-issuer",
        OIDC_ISSUER,
    ]
    verifier_runner(command)
    receipt, digest = _load_receipt(receipt_path)
    if receipt.get("schema") != SCHEMA:
        raise TesterAuthorityReceiptError("tester authority receipt schema is not reviewed")
    principal = receipt.get("principal")
    if not isinstance(principal, str) or not PRINCIPAL_PATTERN.fullmatch(principal):
        raise TesterAuthorityReceiptError(
            "tester authority receipt principal must be one exact user principal"
        )
    scope = receipt.get("scope")
    if not isinstance(scope, dict) or scope != {
        "project_id": expected_project_id,
        "region": expected_region,
        "service": expected_service,
        "role": "roles/run.invoker",
    }:
        raise TesterAuthorityReceiptError(
            "tester authority receipt scope does not match the reviewed target"
        )
    if (
        not isinstance(receipt.get("approval_reference"), str)
        or not receipt["approval_reference"].strip()
    ):
        raise TesterAuthorityReceiptError("tester authority receipt approval reference is required")
    return {"private_invoker_principal": principal, "tester_authority_receipt_sha256": digest}


def write_terraform_vars(path: Path, derived: dict[str, str]) -> None:
    path.write_text(json.dumps(derived, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify and derive exact private tester Terraform inputs from a signed "
            "authority receipt."
        )
    )
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--certificate-identity")
    parser.add_argument("--project-id")
    parser.add_argument("--region", default="us-east4")
    parser.add_argument("--service", default="staff-tracer")
    parser.add_argument("--terraform-vars-output", type=Path)
    parser.add_argument(
        "--external",
        action="store_true",
        help=(
            "Read reviewed receipt inputs from Terraform external-data JSON and emit derived JSON."
        ),
    )
    args = parser.parse_args()
    if args.external:
        try:
            query = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise TesterAuthorityReceiptError(
                "Terraform tester authority query must be valid JSON"
            ) from exc
        if not isinstance(query, dict) or not all(
            isinstance(query.get(key), str) and query[key]
            for key in (
                "receipt",
                "bundle",
                "certificate_identity",
                "project_id",
                "region",
                "service",
            )
        ):
            raise TesterAuthorityReceiptError("Terraform tester authority query is incomplete")
        derived = verify_and_derive_tester_authority(
            receipt_path=Path(query["receipt"]),
            bundle_path=Path(query["bundle"]),
            certificate_identity=query["certificate_identity"],
            expected_project_id=query["project_id"],
            expected_region=query["region"],
            expected_service=query["service"],
        )
        print(json.dumps(derived, sort_keys=True))
        return 0
    if (
        args.receipt is None
        or args.bundle is None
        or args.certificate_identity is None
        or args.project_id is None
        or args.terraform_vars_output is None
    ):
        parser.error(
            "--receipt, --bundle, --certificate-identity, --project-id, and "
            "--terraform-vars-output are required unless --external is used"
        )
    derived = verify_and_derive_tester_authority(
        receipt_path=args.receipt,
        bundle_path=args.bundle,
        certificate_identity=args.certificate_identity,
        expected_project_id=args.project_id,
        expected_region=args.region,
        expected_service=args.service,
    )
    write_terraform_vars(args.terraform_vars_output, derived)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TesterAuthorityReceiptError as exc:
        raise SystemExit(f"tester authority verification failed: {exc}") from exc
