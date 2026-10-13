from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote

from jsonschema import Draft7Validator

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_BUILDKIT_BUILD_TYPE = "https://mobyproject.org/buildkit@v1"
EXPECTED_IMAGE_PLATFORM = "linux/amd64"
EXPECTED_SOURCE_REF = "refs/heads/develop"
EXPECTED_DOCKERFILE = "Dockerfile"
EXPECTED_BUILDER_ID = "https://github.com/actions/runner/github-hosted"
SPDX_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "infra/policy/spdx-2.3.schema.json"
SPDX_SCHEMA_SHA256 = "239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b"
EXPECTED_BASE_MATERIALS = {
    "pkg:docker/node@22.22.3-bookworm-slim": (
        "16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
    ),
    "pkg:docker/python@3.12.12-slim-bookworm": (
        "2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
    ),
}
REQUIRED_PREDICATES = {
    "provenance": "https://slsa.dev/provenance/v1",
    "image SBOM": "https://spdx.dev/Document",
    "application SBOM": "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1",
}
EXPECTED_SIGNATURE_TYPES = {"https://sigstore.dev/cosign/sign/v1", *REQUIRED_PREDICATES.values()}


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
    observed_types: set[str] = set()
    for record in payload:
        critical = record.get("critical")
        if not isinstance(critical, dict):
            raise DeployImageAuthorityError("signature lacks signed critical image identity")
        identity = critical.get("identity")
        image = critical.get("image")
        if not isinstance(identity, dict) or not isinstance(image, dict):
            raise DeployImageAuthorityError("signature lacks signed image subject")
        signature_type = critical.get("type")
        if not isinstance(signature_type, str) or signature_type not in EXPECTED_SIGNATURE_TYPES:
            raise DeployImageAuthorityError("signature type is unexpected")
        observed_types.add(signature_type)
        if (
            identity.get("docker-reference") != f"{repository}@{digest}"
            or image.get("docker-manifest-digest") != digest
        ):
            raise DeployImageAuthorityError(
                "signature subject does not match the immutable OCI image"
            )
    if observed_types != EXPECTED_SIGNATURE_TYPES:
        raise DeployImageAuthorityError("signature type set is incomplete")


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
    predicate: Any, *, expected_source_commit: str, expected_source: str
) -> None:
    if not isinstance(predicate, dict):
        raise DeployImageAuthorityError("provenance predicate must be an object")
    definition = predicate.get("buildDefinition")
    if not isinstance(definition, dict):
        raise DeployImageAuthorityError("provenance predicate build definition is missing")
    if definition.get("buildType") != EXPECTED_BUILDKIT_BUILD_TYPE:
        raise DeployImageAuthorityError("provenance predicate build type is unexpected")
    external = definition.get("externalParameters")
    expected_external = {
        "source": {
            "repository": expected_source,
            "ref": EXPECTED_SOURCE_REF,
        },
        "dockerfile": EXPECTED_DOCKERFILE,
        "platform": EXPECTED_IMAGE_PLATFORM,
    }
    if external != expected_external:
        if isinstance(external, dict) and external.get("platform") != EXPECTED_IMAGE_PLATFORM:
            raise DeployImageAuthorityError("provenance predicate platform must be linux/amd64")
        raise DeployImageAuthorityError("provenance predicate external parameters are unexpected")

    dependencies = definition.get("resolvedDependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise DeployImageAuthorityError("provenance predicate resolved dependencies are missing")
    expected_source_uri = f"git+{expected_source}@{EXPECTED_SOURCE_REF}"
    if not any(
        isinstance(dependency, dict)
        and dependency.get("uri") == expected_source_uri
        and isinstance(dependency.get("digest"), dict)
        and dependency["digest"].get("gitCommit") == expected_source_commit
        for dependency in dependencies
    ):
        raise DeployImageAuthorityError("provenance predicate source revision is unexpected")
    observed_materials = {
        dependency["uri"].split("?", 1)[0]: dependency["digest"].get("sha256")
        for dependency in dependencies
        if isinstance(dependency, dict)
        and isinstance(dependency.get("uri"), str)
        and isinstance(dependency.get("digest"), dict)
    }
    for material_uri, material_digest in EXPECTED_BASE_MATERIALS.items():
        if observed_materials.get(material_uri) != material_digest:
            raise DeployImageAuthorityError(
                "provenance predicate must bind the expected base-image materials"
            )

    run_details = predicate.get("runDetails")
    if not isinstance(run_details, dict):
        raise DeployImageAuthorityError("provenance predicate run details are missing")
    builder = run_details.get("builder")
    if not isinstance(builder, dict) or builder.get("id") != EXPECTED_BUILDER_ID:
        raise DeployImageAuthorityError("provenance predicate builder is unexpected")
    run_metadata = run_details.get("metadata")
    invocation_id = run_metadata.get("invocationId") if isinstance(run_metadata, dict) else None
    source_web_url = expected_source.removesuffix(".git")
    if not isinstance(invocation_id, str) or not re.fullmatch(
        re.escape(source_web_url) + r"/actions/runs/[0-9]+/attempts/[1-9][0-9]*",
        invocation_id,
    ):
        raise DeployImageAuthorityError("provenance predicate invocation ID is unexpected")


def _validate_spdx_schema(payload: dict[str, Any]) -> None:
    try:
        schema_bytes = SPDX_SCHEMA_PATH.read_bytes()
        if hashlib.sha256(schema_bytes).hexdigest() != SPDX_SCHEMA_SHA256:
            raise DeployImageAuthorityError("pinned SPDX 2.3 schema checksum is unexpected")
        schema = json.loads(schema_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise DeployImageAuthorityError("pinned SPDX 2.3 schema is unavailable") from exc
    errors = sorted(
        Draft7Validator(schema).iter_errors(payload), key=lambda error: list(error.path)
    )
    if errors:
        path = ".".join(str(part) for part in errors[0].path) or "document"
        raise DeployImageAuthorityError(
            f"image SBOM predicate fails pinned SPDX 2.3 schema at {path}"
        )


def _assert_image_sbom_semantics(predicate: Any, *, repository: str, digest: str) -> None:
    if not isinstance(predicate, dict):
        raise DeployImageAuthorityError("image SBOM predicate must be an object")
    _validate_spdx_schema(predicate)
    if predicate.get("spdxVersion") != "SPDX-2.3":
        raise DeployImageAuthorityError("image SBOM predicate must use SPDX-2.3")
    if predicate.get("dataLicense") != "CC0-1.0":
        raise DeployImageAuthorityError("image SBOM predicate data license must be CC0-1.0")
    if predicate.get("SPDXID") != "SPDXRef-DOCUMENT":
        raise DeployImageAuthorityError("image SBOM predicate document identifier is missing")
    if predicate.get("name") != repository:
        raise DeployImageAuthorityError("image SBOM predicate document name must match the image")
    namespace = predicate.get("documentNamespace")
    if not isinstance(namespace, str) or not namespace.startswith(
        "https://anchore.com/syft/image/"
    ):
        raise DeployImageAuthorityError("image SBOM predicate document namespace is unexpected")
    creation_info = predicate.get("creationInfo")
    creators = creation_info.get("creators") if isinstance(creation_info, dict) else None
    created = creation_info.get("created") if isinstance(creation_info, dict) else None
    if (
        not isinstance(creators, list)
        or "Tool: syft-1.37.0" not in creators
        or not isinstance(created, str)
        or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", created)
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate creationInfo must identify Syft 1.37.0"
        )
    try:
        datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise DeployImageAuthorityError(
            "image SBOM predicate creationInfo must contain a valid timestamp"
        ) from exc
    packages = predicate.get("packages")
    required_package_fields = {
        "SPDXID",
        "name",
        "downloadLocation",
        "filesAnalyzed",
        "licenseConcluded",
        "licenseDeclared",
        "copyrightText",
    }
    if (
        not isinstance(packages, list)
        or not packages
        or not all(
            isinstance(package, dict)
            and required_package_fields.issubset(package)
            and isinstance(package.get("SPDXID"), str)
            and package["SPDXID"].strip()
            and isinstance(package.get("name"), str)
            and package["name"].strip()
            and isinstance(package.get("filesAnalyzed"), bool)
            and all(
                isinstance(package.get(field), str) and package[field].strip()
                for field in (
                    "downloadLocation",
                    "licenseConcluded",
                    "licenseDeclared",
                    "copyrightText",
                )
            )
            for package in packages
        )
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate must contain a schema-complete component inventory"
        )
    package_ids = {package["SPDXID"] for package in packages}
    document_describes = predicate.get("documentDescribes")
    has_document_describes = "documentDescribes" in predicate
    if has_document_describes and (
        not isinstance(document_describes, list)
        or not document_describes
        or not all(isinstance(item, str) and item in package_ids for item in document_describes)
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate documentDescribes must name declared packages"
        )

    relationships = predicate.get("relationships")
    if "relationships" in predicate and (
        not isinstance(relationships, list)
        or not all(
            isinstance(relationship, dict)
            and isinstance(relationship.get("spdxElementId"), str)
            and isinstance(relationship.get("relationshipType"), str)
            and isinstance(relationship.get("relatedSpdxElement"), str)
            for relationship in relationships
        )
    ):
        raise DeployImageAuthorityError("image SBOM predicate relationships are malformed")
    described_by_relationship = [
        relationship["relatedSpdxElement"]
        for relationship in relationships or []
        if relationship["spdxElementId"] == predicate["SPDXID"]
        and relationship["relationshipType"] == "DESCRIBES"
    ]
    if described_by_relationship and not all(
        item in package_ids for item in described_by_relationship
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate must describe a final-image component inventory subject"
        )
    if not has_document_describes and not described_by_relationship:
        raise DeployImageAuthorityError(
            "image SBOM predicate must describe a final-image component inventory subject"
        )
    described_ids = set(document_describes or []) | set(described_by_relationship)
    described_packages = [package for package in packages if package["SPDXID"] in described_ids]
    if len(described_packages) != 1:
        raise DeployImageAuthorityError(
            "image SBOM predicate must describe exactly one image package"
        )
    image_package = described_packages[0]
    if (
        image_package.get("name") != repository
        or image_package.get("versionInfo") != digest
        or image_package.get("primaryPackagePurpose") != "CONTAINER"
        or image_package.get("filesAnalyzed") is not False
        or image_package.get("downloadLocation") != "NOASSERTION"
    ):
        raise DeployImageAuthorityError(
            "image SBOM predicate described package does not match the reviewed image"
        )
    checksums = image_package.get("checksums")
    sha256_checksums = {
        checksum.get("checksumValue")
        for checksum in checksums or []
        if isinstance(checksum, dict) and checksum.get("algorithm") == "SHA256"
    }
    if not sha256_checksums or not all(
        isinstance(checksum, str) and SHA256_HEX_PATTERN.fullmatch(checksum)
        for checksum in sha256_checksums
    ):
        raise DeployImageAuthorityError("image SBOM predicate image package checksum is missing")
    external_refs = image_package.get("externalRefs")
    valid_purl = False
    for reference in external_refs or []:
        if (
            not isinstance(reference, dict)
            or reference.get("referenceCategory") != "PACKAGE-MANAGER"
            or reference.get("referenceType") != "purl"
            or not isinstance(reference.get("referenceLocator"), str)
        ):
            continue
        decoded = unquote(reference["referenceLocator"])
        purl_base, separator, purl_query = decoded.partition("?")
        expected_purl_prefix = f"pkg:oci/{repository}@sha256:"
        if not purl_base.startswith(expected_purl_prefix):
            continue
        purl_digest = purl_base.removeprefix(expected_purl_prefix)
        query = parse_qs(purl_query, keep_blank_values=True)
        if (
            separator
            and SHA256_HEX_PATTERN.fullmatch(purl_digest)
            and purl_digest in sha256_checksums
            and query == {"arch": ["amd64"]}
        ):
            valid_purl = True
            break
    if not valid_purl:
        raise DeployImageAuthorityError(
            "image SBOM predicate must bind the image package to an amd64 OCI purl"
        )


def _decode_embedded_application_sbom(predicate: dict[str, Any], *, label: str) -> bytes:
    encoded_field = f"{label}_sbom_base64"
    checksum_field = f"{label}_sbom_sha256"
    encoded = predicate.get(encoded_field)
    if not isinstance(encoded, str) or not encoded:
        raise DeployImageAuthorityError(
            f"application SBOM predicate embedded {label} SBOM is missing"
        )
    try:
        content = base64.b64decode(encoded, validate=True)
        payload = json.loads(content)
    except (ValueError, json.JSONDecodeError) as exc:
        raise DeployImageAuthorityError(
            f"application SBOM predicate embedded {label} SBOM is malformed"
        ) from exc
    if not isinstance(payload, dict) or payload.get("bomFormat") != "CycloneDX":
        raise DeployImageAuthorityError(
            f"application SBOM predicate embedded {label} SBOM must be CycloneDX"
        )
    metadata = payload.get("metadata")
    component = metadata.get("component") if isinstance(metadata, dict) else None
    if (
        not isinstance(component, dict)
        or not isinstance(component.get("name"), str)
        or not component["name"].strip()
    ):
        raise DeployImageAuthorityError(
            f"application SBOM predicate embedded {label} SBOM lacks component identity"
        )
    if hashlib.sha256(content).hexdigest() != predicate[checksum_field]:
        raise DeployImageAuthorityError(
            f"application SBOM predicate embedded {label} checksum does not match"
        )
    return content


def _assert_application_sbom_semantics(
    predicate: Any,
    *,
    digest: str,
    backend_sbom_path: Path | None = None,
    frontend_sbom_path: Path | None = None,
) -> None:
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
    backend_sbom = _decode_embedded_application_sbom(predicate, label="backend")
    frontend_sbom = _decode_embedded_application_sbom(predicate, label="frontend")
    if backend_sbom_path is not None and backend_sbom_path.read_bytes() != backend_sbom:
        raise DeployImageAuthorityError(
            "application SBOM predicate embedded backend checksum/content does not "
            "match the reviewed SBOM"
        )
    if frontend_sbom_path is not None and frontend_sbom_path.read_bytes() != frontend_sbom:
        raise DeployImageAuthorityError(
            "application SBOM predicate embedded frontend SBOM does not match the reviewed SBOM"
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
    backend_sbom_path: Path | None = None,
    frontend_sbom_path: Path | None = None,
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
            expected_source_commit=expected_source_commit,
            expected_source=expected_source,
        )
    elif label == "image SBOM":
        _assert_image_sbom_semantics(attestation_predicate, repository=repository, digest=digest)
    elif label == "application SBOM":
        _assert_application_sbom_semantics(
            attestation_predicate,
            digest=digest,
            backend_sbom_path=backend_sbom_path,
            frontend_sbom_path=frontend_sbom_path,
        )


def verify_deploy_image_authority(
    *,
    image: str,
    signature_path: Path,
    provenance_path: Path,
    image_sbom_path: Path,
    application_sbom_path: Path,
    expected_identity: str,
    expected_source_commit: str,
    backend_sbom_path: Path | None = None,
    frontend_sbom_path: Path | None = None,
) -> str:
    if (backend_sbom_path is None) != (frontend_sbom_path is None):
        raise DeployImageAuthorityError("backend and frontend SBOM paths must be provided together")
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
        backend_sbom_path=backend_sbom_path,
        frontend_sbom_path=frontend_sbom_path,
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
    parser.add_argument("--backend-sbom", type=Path)
    parser.add_argument("--frontend-sbom", type=Path)
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
            backend_sbom_path=args.backend_sbom,
            frontend_sbom_path=args.frontend_sbom,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeployImageAuthorityError as exc:
        raise SystemExit(f"deploy image authority verification failed: {exc}") from exc
