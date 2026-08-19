import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "verify_image_provenance.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_image_provenance", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def valid_sbom() -> dict[str, object]:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {"component": {"name": "staff-tracer"}},
        "components": [],
    }


def valid_metadata() -> dict[str, object]:
    return {
        "containerimage.digest": "sha256:" + "a" * 64,
        "containerimage.descriptor": {
            "digest": "sha256:" + "a" * 64,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
        "buildx.build.provenance": {
            "predicateType": "https://slsa.dev/provenance/v1",
            "materials": [
                {
                    "uri": "pkg:docker/node@22.22.3-bookworm-slim",
                    "digest": {
                        "sha256": "16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
                    },
                },
                {
                    "uri": "pkg:docker/python@3.12.12-slim-bookworm",
                    "digest": {
                        "sha256": "2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
                    },
                },
            ],
        },
    }


def valid_buildkit_metadata() -> dict[str, object]:
    return {
        "containerimage.digest": "sha256:" + "a" * 64,
        "containerimage.descriptor": {
            "digest": "sha256:" + "a" * 64,
            "mediaType": "application/vnd.oci.image.index.v1+json",
        },
        "buildx.build.provenance": {
            "buildType": "https://mobyproject.org/buildkit@v1",
            "materials": [
                {
                    "uri": (
                        "pkg:docker/node@22.22.3-bookworm-slim?digest="
                        "sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
                    ),
                    "digest": {
                        "sha256": "16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
                    },
                },
                {
                    "uri": (
                        "pkg:docker/python@3.12.12-slim-bookworm?digest="
                        "sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
                    ),
                    "digest": {
                        "sha256": "2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
                    },
                },
            ],
        },
    }


def test_verify_image_provenance_accepts_pr_mode_with_pinned_bases_and_sboms(
    tmp_path: Path,
) -> None:
    module = load_module()
    metadata_path = tmp_path / "image-metadata.json"
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"

    write_json(metadata_path, valid_metadata())
    write_json(backend_sbom_path, valid_sbom())
    write_json(frontend_sbom_path, valid_sbom())

    result = module.verify_image_provenance(
        mode="pr",
        dockerfile_path=ROOT / "Dockerfile",
        metadata_path=metadata_path,
        backend_sbom_path=backend_sbom_path,
        frontend_sbom_path=frontend_sbom_path,
        published_image_repository=None,
    )

    assert result.digest == "sha256:" + "a" * 64
    assert result.canonical_image_ref is None


def test_verify_image_provenance_accepts_current_buildkit_metadata_shape(
    tmp_path: Path,
) -> None:
    module = load_module()
    metadata_path = tmp_path / "image-metadata.json"
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"

    write_json(metadata_path, valid_buildkit_metadata())
    write_json(backend_sbom_path, valid_sbom())
    write_json(frontend_sbom_path, valid_sbom())

    result = module.verify_image_provenance(
        mode="pr",
        dockerfile_path=ROOT / "Dockerfile",
        metadata_path=metadata_path,
        backend_sbom_path=backend_sbom_path,
        frontend_sbom_path=frontend_sbom_path,
        published_image_repository=None,
    )

    assert result.digest == "sha256:" + "a" * 64
    assert result.canonical_image_ref is None


def test_verify_image_provenance_returns_canonical_digest_reference_for_publish_mode(
    tmp_path: Path,
) -> None:
    module = load_module()
    metadata_path = tmp_path / "image-metadata.json"
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"

    write_json(metadata_path, valid_metadata())
    write_json(backend_sbom_path, valid_sbom())
    write_json(frontend_sbom_path, valid_sbom())

    result = module.verify_image_provenance(
        mode="publish",
        dockerfile_path=ROOT / "Dockerfile",
        metadata_path=metadata_path,
        backend_sbom_path=backend_sbom_path,
        frontend_sbom_path=frontend_sbom_path,
        published_image_repository="us-east4-docker.pkg.dev/example-project/application-images/staff-tracer",
    )

    assert (
        result.canonical_image_ref
        == "us-east4-docker.pkg.dev/example-project/application-images/staff-tracer@"
        + "sha256:"
        + "a" * 64
    )


@pytest.mark.parametrize(
    "bad_payload, expected_message",
    [
        ({}, "containerimage.digest"),
        ({**valid_metadata(), "containerimage.digest": "staff-tracer:latest"}, "immutable"),
        (
            {
                **valid_metadata(),
                "buildx.build.provenance": {
                    "predicateType": "https://example.com/other",
                    "materials": [],
                },
            },
            "predicateType",
        ),
        (
            {
                **valid_buildkit_metadata(),
                "buildx.build.provenance": {
                    "buildType": "https://example.com/other",
                    "materials": [],
                },
            },
            "buildType",
        ),
        (
            {
                **valid_metadata(),
                "buildx.build.provenance": {
                    "predicateType": "https://slsa.dev/provenance/v1",
                    "materials": [
                        {
                            "uri": "pkg:docker/node@22.22.3-bookworm-slim",
                            "digest": {"sha256": "0" * 64},
                        }
                    ],
                },
            },
            "base-image material URI/digest evidence",
        ),
    ],
)
def test_verify_image_provenance_rejects_unreviewed_metadata_shapes(
    tmp_path: Path, bad_payload: dict[str, object], expected_message: str
) -> None:
    module = load_module()
    metadata_path = tmp_path / "image-metadata.json"
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"

    write_json(metadata_path, bad_payload)
    write_json(backend_sbom_path, valid_sbom())
    write_json(frontend_sbom_path, valid_sbom())

    with pytest.raises(ValueError, match=expected_message):
        module.verify_image_provenance(
            mode="pr",
            dockerfile_path=ROOT / "Dockerfile",
            metadata_path=metadata_path,
            backend_sbom_path=backend_sbom_path,
            frontend_sbom_path=frontend_sbom_path,
            published_image_repository=None,
        )


def test_verify_image_provenance_rejects_placeholder_sbom_evidence(tmp_path: Path) -> None:
    module = load_module()
    metadata_path = tmp_path / "image-metadata.json"
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"

    write_json(metadata_path, valid_metadata())
    write_json(backend_sbom_path, {})
    write_json(frontend_sbom_path, valid_sbom())

    with pytest.raises(ValueError, match="CycloneDX"):
        module.verify_image_provenance(
            mode="pr",
            dockerfile_path=ROOT / "Dockerfile",
            metadata_path=metadata_path,
            backend_sbom_path=backend_sbom_path,
            frontend_sbom_path=frontend_sbom_path,
            published_image_repository=None,
        )
