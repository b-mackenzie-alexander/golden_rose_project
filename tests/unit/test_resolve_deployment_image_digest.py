import pytest

from scripts.resolve_deployment_image_digest import (
    DeploymentDigestError,
    resolve_deployment_digest,
)

ROOT_DIGEST = "sha256:" + "a" * 64
DEPLOYMENT_DIGEST = "sha256:" + "b" * 64
ATTESTATION_DIGEST = "sha256:" + "c" * 64


def test_resolves_linux_amd64_manifest_from_oci_index() -> None:
    document = {
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": DEPLOYMENT_DIGEST,
                "platform": {"os": "linux", "architecture": "amd64"},
            },
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": ATTESTATION_DIGEST,
                "platform": {"os": "unknown", "architecture": "unknown"},
            },
        ],
    }

    assert (
        resolve_deployment_digest(document, root_digest=ROOT_DIGEST, platform="linux/amd64")
        == DEPLOYMENT_DIGEST
    )


def test_returns_root_digest_for_single_image_manifest() -> None:
    document = {"mediaType": "application/vnd.oci.image.manifest.v1+json"}

    assert (
        resolve_deployment_digest(document, root_digest=ROOT_DIGEST, platform="linux/amd64")
        == ROOT_DIGEST
    )


def test_rejects_index_without_requested_platform() -> None:
    document = {
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": DEPLOYMENT_DIGEST,
                "platform": {"os": "linux", "architecture": "arm64"},
            }
        ],
    }

    with pytest.raises(DeploymentDigestError, match="linux/amd64"):
        resolve_deployment_digest(document, root_digest=ROOT_DIGEST, platform="linux/amd64")


def test_rejects_ambiguous_platform_manifests() -> None:
    document = {
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": DEPLOYMENT_DIGEST,
                "platform": {"os": "linux", "architecture": "amd64"},
            },
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": "sha256:" + "d" * 64,
                "platform": {"os": "linux", "architecture": "amd64"},
            },
        ],
    }

    with pytest.raises(DeploymentDigestError, match="multiple"):
        resolve_deployment_digest(document, root_digest=ROOT_DIGEST, platform="linux/amd64")
