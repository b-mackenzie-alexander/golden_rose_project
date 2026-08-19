import argparse
import json
import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

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
) -> VerificationResult:
    _validate_dockerfile_bases(dockerfile_path)
    _validate_sbom(backend_sbom_path)
    _validate_sbom(frontend_sbom_path)
    metadata = _load_json(metadata_path)
    digest = _validate_metadata(metadata)

    if mode == "pr":
        if published_image_repository is not None:
            raise ValueError("published image repository is not allowed in pr mode")
        return VerificationResult(digest=digest, canonical_image_ref=None)

    if published_image_repository is None:
        raise ValueError("published image repository is required in publish mode")
    repository = _validate_repository(published_image_repository)
    return VerificationResult(digest=digest, canonical_image_ref=f"{repository}@{digest}")


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
    )
    if result.canonical_image_ref is not None:
        print(result.canonical_image_ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
