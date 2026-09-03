import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qs, unquote, urlparse

from jsonschema import Draft7Validator

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ARTIFACT_REGISTRY_REPOSITORY_PATTERN = re.compile(
    r"^[a-z0-9-]+-docker\.pkg\.dev/[a-z][a-z0-9-]*/[a-z0-9-]+/[a-z0-9-]+$"
)
EXPECTED_BASE_IMAGES = {
    "node:22.22.3-bookworm-slim": (
        "sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
    ),
    "python:3.12.12-slim-bookworm": (
        "sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
    ),
}
EXPECTED_BASE_MATERIALS = {
    "pkg:docker/node@22.22.3-bookworm-slim": (
        "sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
    ),
    "pkg:docker/python@3.12.12-slim-bookworm": (
        "sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
    ),
}
EXPECTED_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
EXPECTED_BUILDKIT_BUILD_TYPE = "https://mobyproject.org/buildkit@v1"
EXPECTED_GITHUB_CERTIFICATE_IDENTITY = (
    "https://github.com/b-mackenzie-alexander/golden_rose_project/"
    ".github/workflows/build-image.yml@refs/heads/develop"
)
EXPECTED_GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
EXPECTED_APPLICATION_SBOM_ATTESTATION_PREDICATE = (
    "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1"
)
EXPECTED_IMAGE_SBOM_PLATFORM = "linux/amd64"
SPDX_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "infra/policy/spdx-2.3.schema.json"
SPDX_SCHEMA_SHA256 = "239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b"


class VerificationResult:
    def __init__(self, *, digest: str, canonical_image_ref: str | None) -> None:
        self.digest = digest
        self.canonical_image_ref = canonical_image_ref


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing JSON evidence file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON document in {path}")
    return payload


def _read_required_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    if not text.strip():
        raise ValueError(f"required file is empty: {path}")
    return text


def _validate_digest(digest: Any) -> str:
    if not isinstance(digest, str):
        raise ValueError("containerimage.digest must be a string")
    if not DIGEST_PATTERN.fullmatch(digest):
        raise ValueError("containerimage.digest must be immutable sha256")
    return digest


def _validate_repository(repository: str) -> str:
    if not ARTIFACT_REGISTRY_REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError(
            "published image repository must be a value-safe Artifact Registry repository"
        )
    return repository


def _validate_sbom(path: Path) -> None:
    payload = _load_json(path)
    if payload.get("bomFormat") != "CycloneDX":
        raise ValueError(f"SBOM evidence must declare CycloneDX bomFormat: {path}")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"SBOM evidence must include metadata: {path}")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_trust_identity(
    payload: dict[str, Any], *, expected_digest: str, expected_subject: str
) -> None:
    if payload.get("subject") != expected_subject:
        raise ValueError("verification evidence subject must match the canonical image reference")
    if payload.get("digest") != expected_digest:
        raise ValueError("verification evidence digest must match the canonical image digest")
    if payload.get("certificate_identity") != EXPECTED_GITHUB_CERTIFICATE_IDENTITY:
        raise ValueError(
            "verification evidence certificate identity must match the reviewed build workflow"
        )
    if payload.get("certificate_oidc_issuer") != EXPECTED_GITHUB_OIDC_ISSUER:
        raise ValueError("verification evidence certificate OIDC issuer must be GitHub Actions")
    if payload.get("transparency_log_included") is not True:
        raise ValueError("verification evidence must prove transparency log inclusion")


def _validate_signature_verification(
    path: Path, *, expected_digest: str, expected_subject: str
) -> None:
    payload = _load_json(path)
    _validate_trust_identity(
        payload, expected_digest=expected_digest, expected_subject=expected_subject
    )


def _validate_provenance_verification(
    path: Path, *, expected_digest: str, expected_subject: str
) -> None:
    payload = _load_json(path)
    _validate_trust_identity(
        payload, expected_digest=expected_digest, expected_subject=expected_subject
    )
    if payload.get("predicate_type") != EXPECTED_PROVENANCE_PREDICATE:
        raise ValueError("provenance verification must use the reviewed SLSA predicate type")
    source_commit = payload.get("source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("provenance verification source_commit must be a full git SHA")
    builder_id = payload.get("builder_id")
    if not isinstance(builder_id, str) or not builder_id.strip():
        raise ValueError("provenance verification builder_id must be non-empty")


def _decode_image_sbom_attestation(
    path: Path, *, expected_digest: str, expected_subject: str
) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get("bomFormat") == "CycloneDX":
        return payload
    if payload.get("payloadType") != "application/vnd.in-toto+json":
        raise ValueError("image SBOM must be CycloneDX JSON or a verified DSSE envelope")
    encoded_statement = payload.get("payload")
    signatures = payload.get("signatures")
    if not isinstance(encoded_statement, str) or not isinstance(signatures, list) or not signatures:
        raise ValueError("image SBOM DSSE envelope is incomplete")
    try:
        statement = json.loads(base64.b64decode(encoded_statement, validate=True))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("image SBOM DSSE payload is malformed") from exc
    if not isinstance(statement, dict):
        raise ValueError("image SBOM DSSE statement must be an object")
    if statement.get("_type") != "https://in-toto.io/Statement/v0.1":
        raise ValueError("image SBOM attestation must be an in-toto v0.1 statement")
    if statement.get("predicateType") != "https://spdx.dev/Document":
        raise ValueError("image SBOM attestation predicate type must be SPDX")
    subjects = statement.get("subject")
    expected_repository = expected_subject.removesuffix(f"@{expected_digest}")
    if not isinstance(subjects, list) or not any(
        isinstance(subject, dict)
        and subject.get("name") == expected_repository
        and isinstance(subject.get("digest"), dict)
        and subject["digest"].get("sha256") == expected_digest.removeprefix("sha256:")
        for subject in subjects
    ):
        raise ValueError("image SBOM attestation subject must match the reviewed immutable image")
    predicate = statement.get("predicate")
    if not isinstance(predicate, dict):
        raise ValueError("image SBOM attestation predicate must be an object")
    return predicate


def _validate_spdx_schema(payload: dict[str, Any]) -> None:
    try:
        schema_bytes = SPDX_SCHEMA_PATH.read_bytes()
        if hashlib.sha256(schema_bytes).hexdigest() != SPDX_SCHEMA_SHA256:
            raise ValueError("pinned SPDX 2.3 schema checksum is unexpected")
        schema = json.loads(schema_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("pinned SPDX 2.3 schema is unavailable") from exc
    errors = sorted(
        Draft7Validator(schema).iter_errors(payload), key=lambda error: list(error.path)
    )
    if errors:
        path = ".".join(str(part) for part in errors[0].path) or "document"
        raise ValueError(f"image SBOM fails pinned SPDX 2.3 schema at {path}")


def _validate_spdx_image_inventory(
    payload: dict[str, Any],
    *,
    expected_name: str,
    expected_version: str,
    expected_tag: str | None,
) -> None:
    _validate_spdx_schema(payload)
    if payload.get("spdxVersion") != "SPDX-2.3":
        raise ValueError("image SBOM must use SPDX-2.3")
    if payload.get("dataLicense") != "CC0-1.0":
        raise ValueError("image SBOM data license must be CC0-1.0")
    if payload.get("SPDXID") != "SPDXRef-DOCUMENT":
        raise ValueError("image SBOM document identifier is missing")
    if payload.get("name") != expected_name:
        raise ValueError("image SBOM document name must match the scanned image")
    namespace = payload.get("documentNamespace")
    if not isinstance(namespace, str) or not namespace.startswith(
        "https://anchore.com/syft/image/"
    ):
        raise ValueError("image SBOM document namespace is unexpected")
    creation_info = payload.get("creationInfo")
    creators = creation_info.get("creators") if isinstance(creation_info, dict) else None
    created = creation_info.get("created") if isinstance(creation_info, dict) else None
    if (
        not isinstance(creators, list)
        or "Tool: syft-1.37.0" not in creators
        or not isinstance(created, str)
        or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", created)
    ):
        raise ValueError("image SBOM creationInfo must identify Syft 1.37.0")
    packages = payload.get("packages")
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
            for package in packages
        )
    ):
        raise ValueError(
            "image SBOM attestation must contain a schema-complete component inventory"
        )
    package_ids = {package["SPDXID"] for package in packages}
    document_describes = payload.get("documentDescribes")
    has_document_describes = "documentDescribes" in payload
    if has_document_describes and (
        not isinstance(document_describes, list)
        or not document_describes
        or not all(isinstance(item, str) and item in package_ids for item in document_describes)
    ):
        raise ValueError("image SBOM documentDescribes must name declared packages")

    document_id = payload.get("SPDXID")
    relationships = payload.get("relationships")
    if "relationships" in payload and (
        not isinstance(relationships, list)
        or not all(
            isinstance(relationship, dict)
            and isinstance(relationship.get("spdxElementId"), str)
            and isinstance(relationship.get("relationshipType"), str)
            and isinstance(relationship.get("relatedSpdxElement"), str)
            for relationship in relationships
        )
    ):
        raise ValueError("image SBOM relationships are malformed")
    described_by_relationship = [
        relationship["relatedSpdxElement"]
        for relationship in relationships or []
        if relationship["spdxElementId"] == document_id
        and relationship["relationshipType"] == "DESCRIBES"
    ]
    if described_by_relationship and not all(
        item in package_ids for item in described_by_relationship
    ):
        raise ValueError("image SBOM attestation must describe a final-image subject")
    if not has_document_describes and not described_by_relationship:
        raise ValueError("image SBOM attestation must describe a final-image subject")
    described_ids = set(document_describes or []) | set(described_by_relationship)
    described_packages = [package for package in packages if package["SPDXID"] in described_ids]
    if len(described_packages) != 1:
        raise ValueError("image SBOM must describe exactly one image package")
    image_package = described_packages[0]
    if (
        image_package.get("name") != expected_name
        or image_package.get("versionInfo") != expected_version
        or image_package.get("primaryPackagePurpose") != "CONTAINER"
        or image_package.get("filesAnalyzed") is not False
        or image_package.get("downloadLocation") != "NOASSERTION"
    ):
        raise ValueError("image SBOM described package does not match the scanned image")
    checksums = image_package.get("checksums")
    sha256_checksums = {
        checksum.get("checksumValue")
        for checksum in checksums or []
        if isinstance(checksum, dict) and checksum.get("algorithm") == "SHA256"
    }
    if not sha256_checksums or not all(
        isinstance(checksum, str) and re.fullmatch(r"[0-9a-f]{64}", checksum)
        for checksum in sha256_checksums
    ):
        raise ValueError("image SBOM image package checksum is missing")
    valid_purl = False
    for reference in image_package.get("externalRefs") or []:
        if (
            not isinstance(reference, dict)
            or reference.get("referenceCategory") != "PACKAGE-MANAGER"
            or reference.get("referenceType") != "purl"
            or not isinstance(reference.get("referenceLocator"), str)
        ):
            continue
        decoded = unquote(reference["referenceLocator"])
        purl_base, separator, purl_query = decoded.partition("?")
        purl_digest = purl_base.removeprefix(f"pkg:oci/{expected_name}@sha256:")
        query = parse_qs(purl_query)
        if (
            separator
            and re.fullmatch(r"[0-9a-f]{64}", purl_digest)
            and purl_digest in sha256_checksums
            and query.get("arch") == ["amd64"]
            and (expected_tag is None or query.get("tag") == [expected_tag])
        ):
            valid_purl = True
            break
    if not valid_purl:
        raise ValueError("image SBOM must bind the image package to the expected amd64 OCI purl")


def _validate_raw_spdx_image_sbom(path: Path, *, image_name: str) -> None:
    local_reference = image_name.rsplit("/", 1)[-1]
    expected_name, separator, expected_tag = local_reference.rpartition(":")
    if not separator or not expected_name or not expected_tag:
        raise ValueError("PR image name must include a repository and tag")
    _validate_spdx_image_inventory(
        _load_json(path),
        expected_name=expected_name,
        expected_version=expected_tag,
        expected_tag=expected_tag,
    )


def _validate_image_sbom(path: Path, *, expected_digest: str, expected_subject: str) -> None:
    payload = _decode_image_sbom_attestation(
        path, expected_digest=expected_digest, expected_subject=expected_subject
    )
    if payload.get("bomFormat") != "CycloneDX":
        expected_repository = expected_subject.removesuffix(f"@{expected_digest}")
        _validate_spdx_image_inventory(
            payload,
            expected_name=expected_repository,
            expected_version=expected_digest,
            expected_tag=None,
        )
        return
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("image SBOM must include metadata")
    component = metadata.get("component")
    if not isinstance(component, dict):
        raise ValueError("image SBOM must include a metadata.component")
    purl = component.get("purl")
    if not isinstance(purl, str) or f"@{expected_digest}" not in purl:
        raise ValueError("image SBOM root component must be bound to the reviewed digest")
    properties = component.get("properties")
    if not isinstance(properties, list) or not any(
        isinstance(item, dict)
        and item.get("name") == "syft:source:image:platform"
        and item.get("value") == EXPECTED_IMAGE_SBOM_PLATFORM
        for item in properties
    ):
        raise ValueError("image SBOM must prove linux/amd64 platform binding")
    components = payload.get("components")
    if not isinstance(components, list) or len(components) < 1:
        raise ValueError("image SBOM must contain a non-empty component inventory")


def _validate_application_sbom_attestation(
    path: Path,
    *,
    expected_digest: str,
    expected_subject: str,
    backend_sbom_path: Path,
    frontend_sbom_path: Path,
) -> None:
    payload = _load_json(path)
    _validate_trust_identity(
        payload, expected_digest=expected_digest, expected_subject=expected_subject
    )
    if payload.get("predicate_type") != EXPECTED_APPLICATION_SBOM_ATTESTATION_PREDICATE:
        raise ValueError("application SBOM attestation predicate type must be reviewed")
    if payload.get("backend_sbom_sha256") != _sha256_file(backend_sbom_path):
        raise ValueError(
            "application SBOM attestation backend checksum must match the reviewed backend SBOM"
        )
    if payload.get("frontend_sbom_sha256") != _sha256_file(frontend_sbom_path):
        raise ValueError(
            "application SBOM attestation frontend checksum must match the reviewed frontend SBOM"
        )


def _validate_dockerfile_bases(dockerfile_path: Path) -> None:
    dockerfile = _read_required_text(dockerfile_path)
    for image, digest in EXPECTED_BASE_IMAGES.items():
        pinned = f"FROM {image}@{digest}"
        if pinned not in dockerfile:
            raise ValueError(f"Dockerfile missing pinned base image {pinned}")


def _normalized_material_uri(uri: str) -> str:
    parsed = urlparse(uri)
    query_digest = parse_qs(parsed.query).get("digest", [])
    normalized_base = uri.split("?", 1)[0]
    if query_digest and (
        len(query_digest) != 1 or query_digest[0] not in EXPECTED_BASE_MATERIALS.values()
    ):
        raise ValueError("provenance materials must include exact expected base-image digest")
    return normalized_base


def _validate_provenance_materials(materials: Any) -> None:
    if not isinstance(materials, list) or not materials:
        raise ValueError("buildx.build.provenance materials must be present")

    observed_materials: dict[str, str] = {}
    for material in materials:
        if not isinstance(material, dict):
            raise ValueError("buildx.build.provenance materials must be objects")
        uri = material.get("uri")
        digest_block = material.get("digest")
        if not isinstance(uri, str) or not isinstance(digest_block, dict):
            raise ValueError("buildx.build.provenance materials must include uri and digest")
        sha256_digest = digest_block.get("sha256")
        if not isinstance(sha256_digest, str):
            raise ValueError("buildx.build.provenance materials must include sha256 digests")
        observed_materials[_normalized_material_uri(uri)] = f"sha256:{sha256_digest}"

    for expected_uri, expected_digest in EXPECTED_BASE_MATERIALS.items():
        if observed_materials.get(expected_uri) != expected_digest:
            raise ValueError(
                "buildx.build.provenance materials must include exact expected base-image "
                "material URI/digest evidence"
            )


def _validate_metadata(metadata: dict[str, Any]) -> str:
    digest = _validate_digest(metadata.get("containerimage.digest"))
    descriptor = metadata.get("containerimage.descriptor")
    if not isinstance(descriptor, dict):
        raise ValueError("containerimage.descriptor must be an object")
    descriptor_digest = descriptor.get("digest")
    if descriptor_digest != digest:
        raise ValueError("containerimage.descriptor digest must match containerimage.digest")
    provenance = metadata.get("buildx.build.provenance")
    if not isinstance(provenance, dict):
        raise ValueError("buildx.build.provenance must be an object")
    predicate_type = provenance.get("predicateType")
    build_type = provenance.get("buildType")
    if predicate_type is None:
        if build_type != EXPECTED_BUILDKIT_BUILD_TYPE:
            raise ValueError("buildx.build.provenance buildType must be reviewed")
    elif predicate_type != EXPECTED_PROVENANCE_PREDICATE:
        raise ValueError("buildx.build.provenance predicateType must be reviewed")
    _validate_provenance_materials(provenance.get("materials"))
    return digest


def verify_image_provenance(
    *,
    mode: Literal["pr", "publish"],
    dockerfile_path: Path,
    metadata_path: Path,
    backend_sbom_path: Path,
    frontend_sbom_path: Path,
    published_image_repository: str | None,
    signature_verification_path: Path | None = None,
    provenance_verification_path: Path | None = None,
    image_sbom_path: Path | None = None,
    application_sbom_verification_path: Path | None = None,
    pr_image_sbom_path: Path | None = None,
) -> VerificationResult:
    _validate_dockerfile_bases(dockerfile_path)
    _validate_sbom(backend_sbom_path)
    _validate_sbom(frontend_sbom_path)
    metadata = _load_json(metadata_path)
    digest = _validate_metadata(metadata)

    if mode == "pr":
        if published_image_repository is not None:
            raise ValueError("published image repository is not allowed in pr mode")
        if any(
            path is not None
            for path in (
                signature_verification_path,
                provenance_verification_path,
                image_sbom_path,
                application_sbom_verification_path,
            )
        ):
            raise ValueError("publish attestation evidence is not allowed in pr mode")
        if pr_image_sbom_path is not None:
            image_name = metadata.get("image.name")
            if not isinstance(image_name, str):
                raise ValueError("Buildx metadata image.name is required for PR SBOM binding")
            _validate_raw_spdx_image_sbom(pr_image_sbom_path, image_name=image_name)
        return VerificationResult(digest=digest, canonical_image_ref=None)

    if pr_image_sbom_path is not None:
        raise ValueError("PR image SBOM evidence is not allowed in publish mode")
    if published_image_repository is None:
        raise ValueError("published image repository is required in publish mode")
    repository = _validate_repository(published_image_repository)
    canonical_image_ref = f"{repository}@{digest}"
    if None in (
        signature_verification_path,
        provenance_verification_path,
        image_sbom_path,
        application_sbom_verification_path,
    ):
        raise ValueError(
            "publish mode requires signature, provenance, image SBOM, and "
            "application SBOM attestation evidence"
        )
    assert signature_verification_path is not None
    assert provenance_verification_path is not None
    assert image_sbom_path is not None
    assert application_sbom_verification_path is not None
    _validate_signature_verification(
        signature_verification_path,
        expected_digest=digest,
        expected_subject=canonical_image_ref,
    )
    _validate_provenance_verification(
        provenance_verification_path,
        expected_digest=digest,
        expected_subject=canonical_image_ref,
    )
    _validate_image_sbom(
        image_sbom_path, expected_digest=digest, expected_subject=canonical_image_ref
    )
    _validate_application_sbom_attestation(
        application_sbom_verification_path,
        expected_digest=digest,
        expected_subject=canonical_image_ref,
        backend_sbom_path=backend_sbom_path,
        frontend_sbom_path=frontend_sbom_path,
    )
    return VerificationResult(digest=digest, canonical_image_ref=canonical_image_ref)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify image digest, SBOM, and provenance evidence."
    )
    parser.add_argument("--mode", choices=("pr", "publish"), required=True)
    parser.add_argument("--dockerfile", type=Path, required=True)
    parser.add_argument("--metadata-path", type=Path, required=True)
    parser.add_argument("--backend-sbom-path", type=Path, required=True)
    parser.add_argument("--frontend-sbom-path", type=Path, required=True)
    parser.add_argument("--published-image-repository")
    parser.add_argument("--signature-verification-path", type=Path)
    parser.add_argument("--provenance-verification-path", type=Path)
    parser.add_argument("--image-sbom-path", type=Path)
    parser.add_argument("--application-sbom-verification-path", type=Path)
    parser.add_argument("--pr-image-sbom-path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = verify_image_provenance(
        mode=args.mode,
        dockerfile_path=args.dockerfile,
        metadata_path=args.metadata_path,
        backend_sbom_path=args.backend_sbom_path,
        frontend_sbom_path=args.frontend_sbom_path,
        published_image_repository=args.published_image_repository,
        signature_verification_path=args.signature_verification_path,
        provenance_verification_path=args.provenance_verification_path,
        image_sbom_path=args.image_sbom_path,
        application_sbom_verification_path=args.application_sbom_verification_path,
        pr_image_sbom_path=args.pr_image_sbom_path,
    )
    if result.canonical_image_ref is not None:
        print(result.canonical_image_ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
