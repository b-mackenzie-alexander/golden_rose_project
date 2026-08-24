from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from typing import Any

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_BUILDKIT_BUILD_TYPE = "https://mobyproject.org/buildkit@v1"
EXPECTED_IMAGE_PLATFORM = "linux/amd64"
REQUIRED_PREDICATES = {
    "provenance": "https://slsa.dev/provenance/v1",
    "image SBOM": "https://spdx.dev/Document",
    "application SBOM": "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1",
}


class DeployImageAuthorityError(ValueError):
    pass


def _load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeployImageAuthorityError(f"{label} Cosign output is not valid JSON") from exc


def _expected_subject(image: str) -> tuple[str, str]:
    repository, separator, digest = image.partition("@")
    if not separator or not repository or not DIGEST_PATTERN.fullmatch(digest):
        raise DeployImageAuthorityError("image must be a digest-bound OCI reference")
    return repository, digest


def _assert_signature(payload: Any, *, repository: str, digest: str) -> None:
    if (
        not isinstance(payload, list)
        or not payload
        or not all(isinstance(item, dict) for item in payload)
    ):
        raise DeployImageAuthorityError("signature Cosign output must be a non-empty JSON array")
    for record in payload:
        critical = record.get("critical")
        if not isinstance(critical, dict):
            raise DeployImageAuthorityError("signature lacks signed critical image identity")
        identity = critical.get("identity")
        image = critical.get("image")
        if not isinstance(identity, dict) or not isinstance(image, dict):
            raise DeployImageAuthorityError("signature lacks signed image subject")
        if (
            identity.get("docker-reference") != repository
            or image.get("docker-manifest-digest") != digest
        ):
            raise DeployImageAuthorityError(
                "signature subject does not match the immutable OCI image"
            )


def _decode_statement(path: Path, label: str) -> dict[str, Any]:
    envelope = _load_json(path, label)
    if (
        not isinstance(envelope, dict)
        or envelope.get("payloadType") != "application/vnd.in-toto+json"
    ):
        raise DeployImageAuthorityError(f"{label} must be a verified DSSE envelope")
    payload = envelope.get("payload")
    signatures = envelope.get("signatures")
    if not isinstance(payload, str) or not isinstance(signatures, list) or not signatures:
        raise DeployImageAuthorityError(f"{label} DSSE envelope is incomplete")
    try:
        statement = json.loads(base64.b64decode(payload, validate=True))
    except (ValueError, json.JSONDecodeError) as exc:
        raise DeployImageAuthorityError(f"{label} DSSE payload is malformed") from exc
    if not isinstance(statement, dict):
        raise DeployImageAuthorityError(f"{label} DSSE statement must be an object")
    return statement


def _assert_provenance_semantics(
    predicate: Any, *, digest: str, expected_source_commit: str, expected_source: str
) -> None:
    if not isinstance(predicate, dict):
        raise DeployImageAuthorityError("provenance predicate must be an object")
    descriptor = predicate.get("containerimage.descriptor")
    if (
        predicate.get("containerimage.digest") != digest
        or not isinstance(descriptor, dict)
        or descriptor.get("digest") != digest
    ):
        raise DeployImageAuthorityError(
            "provenance predicate image digest does not match the immutable OCI image"
        )
    provenance = predicate.get("buildx.build.provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("buildType") != EXPECTED_BUILDKIT_BUILD_TYPE
    ):
        raise DeployImageAuthorityError("provenance predicate build type is unexpected")
    invocation = provenance.get("invocation")
    if not isinstance(invocation, dict):
        raise DeployImageAuthorityError("provenance predicate invocation is missing")
    environment = invocation.get("environment")
    if not isinstance(environment, dict) or environment.get("platform") != EXPECTED_IMAGE_PLATFORM:
        raise DeployImageAuthorityError("provenance predicate platform must be linux/amd64")
    parameters = invocation.get("parameters")
    if not isinstance(parameters, dict):
        raise DeployImageAuthorityError("provenance predicate parameters are missing")
    root = parameters.get("root")
    if not isinstance(root, dict):
        raise DeployImageAuthorityError("provenance predicate source root is missing")
    request = root.get("request")
    if not isinstance(request, dict):
        raise DeployImageAuthorityError("provenance predicate source request is missing")
    args = request.get("args")
    if not isinstance(args, dict) or args.get("vcs:source") != expected_source:
        raise DeployImageAuthorityError("provenance predicate source repository is unexpected")
    if args.get("vcs:revision") != expected_source_commit:
        raise DeployImageAuthorityError("provenance predicate source revision is unexpected")


def _assert_image_sbom_semantics(predicate: Any) -> None:
    if not isinstance(predicate, dict):
        raise DeployImageAuthorityError("image SBOM predicate must be an object")
    spdx_version = predicate.get("spdxVersion")
    if not isinstance(spdx_version, str) or not re.fullmatch(r"SPDX-[0-9]+\.[0-9]+", spdx_version):
        raise DeployImageAuthorityError("image SBOM predicate must be an SPDX document")
    if predicate.get("SPDXID") != "SPDXRef-DOCUMENT":
        raise DeployImageAuthorityError("image SBOM predicate document identifier is missing")
    if not isinstance(predicate.get("name"), str) or not predicate["name"].strip():
        raise DeployImageAuthorityError("image SBOM predicate document name is missing")
    packages = predicate.get("packages")
    if (
        not isinstance(packages, list)
        or not packages
        or not all(
            isinstance(package, dict)
            and isinstance(package.get("SPDXID"), str)
            and package["SPDXID"].strip()
            and isinstance(package.get("name"), str)
            and package["name"].strip()
            for package in packages
        )
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate must contain a non-empty component inventory"
        )
    described = predicate.get("documentDescribes")
    package_ids = {package["SPDXID"] for package in packages}
    if (
        not isinstance(described, list)
        or not described
        or not all(isinstance(item, str) and item in package_ids for item in described)
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate must describe a final-image component inventory subject"
        )


def _assert_application_sbom_semantics(predicate: Any, *, digest: str) -> None:
    if not isinstance(predicate, dict):
        raise DeployImageAuthorityError("application SBOM predicate must be an object")
    if predicate.get("image_digest") != digest:
        raise DeployImageAuthorityError(
            "application SBOM predicate image digest does not match the immutable OCI image"
        )
    for field in ("backend_sbom_sha256", "frontend_sbom_sha256"):
        if not isinstance(predicate.get(field), str) or not SHA256_HEX_PATTERN.fullmatch(
            predicate[field]
        ):
            raise DeployImageAuthorityError(
                f"application SBOM predicate {field} must be a SHA-256 checksum"
            )


def _assert_attestation(
    path: Path,
    *,
    predicate: str,
    repository: str,
    digest: str,
    label: str,
    expected_source_commit: str,
    expected_source: str,
) -> None:
    statement = _decode_statement(path, label)
    if statement.get("_type") != "https://in-toto.io/Statement/v0.1":
        raise DeployImageAuthorityError(f"{label} must be an in-toto v0.1 statement")
    if statement.get("predicateType") != predicate:
        raise DeployImageAuthorityError(f"{label} attestation predicate is missing or unexpected")
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or not any(
        isinstance(subject, dict)
        and subject.get("name") == repository
        and isinstance(subject.get("digest"), dict)
        and subject["digest"].get("sha256") == digest.removeprefix("sha256:")
        for subject in subjects
    ):
        raise DeployImageAuthorityError(
            f"{label} predicate subject does not match the immutable OCI image"
        )
    attestation_predicate = statement.get("predicate")
    if label == "provenance":
        _assert_provenance_semantics(
            attestation_predicate,
            digest=digest,
            expected_source_commit=expected_source_commit,
            expected_source=expected_source,
        )
    elif label == "image SBOM":
        _assert_image_sbom_semantics(attestation_predicate)
    elif label == "application SBOM":
        _assert_application_sbom_semantics(attestation_predicate, digest=digest)


def verify_deploy_image_authority(
    *,
    image: str,
    signature_path: Path,
    provenance_path: Path,
    image_sbom_path: Path,
    application_sbom_path: Path,
    expected_identity: str,
    expected_source_commit: str,
) -> str:
    if not expected_identity.startswith("https://github.com/"):
        raise DeployImageAuthorityError(
            "expected certificate identity must be the reviewed GitHub workflow identity"
        )
    repository, digest = _expected_subject(image)
    if not GIT_SHA_PATTERN.fullmatch(expected_source_commit):
        raise DeployImageAuthorityError("expected source commit must be a full lowercase git SHA")
    expected_source = (
        "https://github.com/"
        + expected_identity.removeprefix("https://github.com/").split("/.github/workflows/", 1)[0]
        + ".git"
    )
    _assert_signature(_load_json(signature_path, "signature"), repository=repository, digest=digest)
    _assert_attestation(
        provenance_path,
        predicate=REQUIRED_PREDICATES["provenance"],
        repository=repository,
        digest=digest,
        label="provenance",
        expected_source_commit=expected_source_commit,
        expected_source=expected_source,
    )
    _assert_attestation(
        image_sbom_path,
        predicate=REQUIRED_PREDICATES["image SBOM"],
        repository=repository,
        digest=digest,
        label="image SBOM",
        expected_source_commit=expected_source_commit,
        expected_source=expected_source,
    )
    _assert_attestation(
        application_sbom_path,
        predicate=REQUIRED_PREDICATES["application SBOM"],
        repository=repository,
        digest=digest,
        label="application SBOM",
        expected_source_commit=expected_source_commit,
        expected_source=expected_source,
    )
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate raw direct Cosign OCI verification outputs for deploy authority."
    )
    parser.add_argument("--image", required=True)
    parser.add_argument("--signature", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--image-sbom", required=True, type=Path)
    parser.add_argument("--application-sbom", required=True, type=Path)
    parser.add_argument("--certificate-identity", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    print(
        verify_deploy_image_authority(
            image=args.image,
            signature_path=args.signature,
            provenance_path=args.provenance,
            image_sbom_path=args.image_sbom,
            application_sbom_path=args.application_sbom,
            expected_identity=args.certificate_identity,
            expected_source_commit=args.source_commit,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeployImageAuthorityError as exc:
        raise SystemExit(f"deploy image authority verification failed: {exc}") from exc
