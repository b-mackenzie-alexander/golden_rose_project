import hashlib
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


def valid_signature_verification(subject: str, digest: str) -> dict[str, object]:
    return {
        "subject": subject,
        "digest": digest,
        "certificate_identity": "https://github.com/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop",
        "certificate_oidc_issuer": "https://token.actions.githubusercontent.com",
        "transparency_log_included": True,
    }


def valid_provenance_verification(subject: str, digest: str) -> dict[str, object]:
    return {
        **valid_signature_verification(subject, digest),
        "predicate_type": "https://slsa.dev/provenance/v1",
        "source_commit": "b" * 40,
        "builder_id": "https://github.com/actions/runner",
    }


def valid_image_sbom(digest: str) -> dict[str, object]:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {
            "component": {
                "name": "staff-tracer",
                "purl": (
                    f"pkg:oci/staff-tracer@{digest}"
                    "?repository_url=us-east4-docker.pkg.dev/example-project/"
                    "application-images/staff-tracer"
                ),
                "properties": [
                    {
                        "name": "syft:source:image:platform",
                        "value": "linux/amd64",
                    }
                ],
            }
        },
        "components": [{"name": "busybox", "version": "1.0.0"}],
    }


def valid_application_sbom_attestation(
    subject: str, digest: str, *, backend_sbom_path: Path, frontend_sbom_path: Path
) -> dict[str, object]:
    return {
        **valid_signature_verification(subject, digest),
        "predicate_type": "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1",
        "backend_sbom_sha256": hashlib.sha256(backend_sbom_path.read_bytes()).hexdigest(),
        "frontend_sbom_sha256": hashlib.sha256(frontend_sbom_path.read_bytes()).hexdigest(),
    }


def _publish_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "metadata": tmp_path / "image-metadata.json",
        "backend_sbom": tmp_path / "backend-sbom.cdx.json",
        "frontend_sbom": tmp_path / "frontend-sbom.cdx.json",
        "signature": tmp_path / "publish-signature-verification.json",
        "provenance": tmp_path / "publish-provenance-verification.json",
        "image_sbom": tmp_path / "image-sbom.cdx.json",
        "app_sbom": tmp_path / "publish-application-sbom-verification.json",
    }


def _write_valid_publish_evidence(tmp_path: Path) -> tuple[dict[str, Path], str, str]:
    paths = _publish_paths(tmp_path)
    digest = "sha256:" + "a" * 64
    subject = "us-east4-docker.pkg.dev/example-project/application-images/staff-tracer@" + digest
    write_json(paths["metadata"], valid_metadata())
    write_json(paths["backend_sbom"], valid_sbom())
    write_json(paths["frontend_sbom"], valid_sbom())
    write_json(paths["signature"], valid_signature_verification(subject, digest))
    write_json(paths["provenance"], valid_provenance_verification(subject, digest))
    write_json(paths["image_sbom"], valid_image_sbom(digest))
    write_json(
        paths["app_sbom"],
        valid_application_sbom_attestation(
            subject,
            digest,
            backend_sbom_path=paths["backend_sbom"],
            frontend_sbom_path=paths["frontend_sbom"],
        ),
    )
    return paths, digest, subject


def _verify_publish(module: ModuleType, paths: dict[str, Path]):
    return module.verify_image_provenance(
        mode="publish",
        dockerfile_path=ROOT / "Dockerfile",
        metadata_path=paths["metadata"],
        backend_sbom_path=paths["backend_sbom"],
        frontend_sbom_path=paths["frontend_sbom"],
        published_image_repository="us-east4-docker.pkg.dev/example-project/application-images/staff-tracer",
        signature_verification_path=paths["signature"],
        provenance_verification_path=paths["provenance"],
        image_sbom_path=paths["image_sbom"],
        application_sbom_verification_path=paths["app_sbom"],
    )


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
    paths, _, subject = _write_valid_publish_evidence(tmp_path)

    result = _verify_publish(module, paths)

    assert result.canonical_image_ref == subject


def test_publish_evidence_binds_source_commit_builder_and_subject_digest(tmp_path: Path) -> None:
    module = load_module()
    paths, digest, _ = _write_valid_publish_evidence(tmp_path)

    result = _verify_publish(module, paths)

    assert result.digest == digest


def test_backend_and_frontend_sboms_are_attached_or_attested_to_exact_digest(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths, _, subject = _write_valid_publish_evidence(tmp_path)

    result = _verify_publish(module, paths)

    assert result.canonical_image_ref == subject


def test_deploy_rejects_valid_sbom_from_different_digest(tmp_path: Path) -> None:
    module = load_module()
    paths, _, _ = _write_valid_publish_evidence(tmp_path)
    write_json(paths["image_sbom"], valid_image_sbom("sha256:" + "b" * 64))

    with pytest.raises(ValueError, match="digest"):
        _verify_publish(module, paths)


def test_deploy_rejects_unsigned_or_untrusted_provenance(tmp_path: Path) -> None:
    module = load_module()
    paths, digest, subject = _write_valid_publish_evidence(tmp_path)
    bad_provenance = valid_provenance_verification(subject, digest)
    bad_provenance["transparency_log_included"] = False
    write_json(paths["provenance"], bad_provenance)

    with pytest.raises(ValueError, match="transparency"):
        _verify_publish(module, paths)


def test_local_pr_mode_does_not_overclaim_publish_attestation(tmp_path: Path) -> None:
    module = load_module()
    metadata_path = tmp_path / "image-metadata.json"
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"
    signature_verification_path = tmp_path / "publish-signature-verification.json"

    write_json(metadata_path, valid_metadata())
    write_json(backend_sbom_path, valid_sbom())
    write_json(frontend_sbom_path, valid_sbom())
    write_json(signature_verification_path, {"unexpected": True})

    with pytest.raises(ValueError, match="not allowed in pr mode"):
        module.verify_image_provenance(
            mode="pr",
            dockerfile_path=ROOT / "Dockerfile",
            metadata_path=metadata_path,
            backend_sbom_path=backend_sbom_path,
            frontend_sbom_path=frontend_sbom_path,
            published_image_repository=None,
            signature_verification_path=signature_verification_path,
        )


def test_deploy_rejects_unsigned_or_untrusted_image_sbom_attestation(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths, digest, _ = _write_valid_publish_evidence(tmp_path)
    bad_image_sbom = valid_image_sbom(digest)
    metadata = bad_image_sbom["metadata"]
    assert isinstance(metadata, dict)
    component = metadata["component"]
    assert isinstance(component, dict)
    properties = component["properties"]
    assert isinstance(properties, list)
    first_property = properties[0]
    assert isinstance(first_property, dict)
    first_property["value"] = "linux/arm64"
    write_json(paths["image_sbom"], bad_image_sbom)

    with pytest.raises(ValueError, match="linux/amd64"):
        _verify_publish(module, paths)


def test_deploy_rejects_unsigned_or_untrusted_application_sbom_checksum_attestation(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths, digest, subject = _write_valid_publish_evidence(tmp_path)
    bad_attestation = valid_application_sbom_attestation(
        subject,
        digest,
        backend_sbom_path=paths["backend_sbom"],
        frontend_sbom_path=paths["frontend_sbom"],
    )
    bad_attestation["backend_sbom_sha256"] = "0" * 64
    write_json(paths["app_sbom"], bad_attestation)

    with pytest.raises(ValueError, match="backend checksum"):
        _verify_publish(module, paths)


def test_deploy_rejects_wrong_attestation_subject_predicate_identity_issuer_or_transparency_proof(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths, digest, subject = _write_valid_publish_evidence(tmp_path)
    bad_signature = valid_signature_verification(subject, digest)
    bad_signature["certificate_identity"] = (
        "https://github.com/example/other/.github/workflows/build.yml@refs/heads/main"
    )
    write_json(paths["signature"], bad_signature)

    with pytest.raises(ValueError, match="certificate identity"):
        _verify_publish(module, paths)


def test_image_sbom_is_schema_valid_linux_amd64_digest_bound_and_nonempty(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths, digest, _ = _write_valid_publish_evidence(tmp_path)

    result = _verify_publish(module, paths)

    assert result.digest == digest


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
