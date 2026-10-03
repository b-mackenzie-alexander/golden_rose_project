from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from typing import Any

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
INDEX_MEDIA_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}
MANIFEST_MEDIA_TYPES = {
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
}


class DeploymentDigestError(ValueError):
    pass


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve the runtime image manifest digest Cloud Run should use from an OCI "
            "index or image manifest JSON document."
        )
    )
    parser.add_argument("--root-digest", required=True)
    parser.add_argument("--platform", default="linux/amd64")
    return parser.parse_args(argv)


def _load_document(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeploymentDigestError("image manifest JSON is malformed") from exc
    if not isinstance(payload, dict):
        raise DeploymentDigestError("image manifest JSON must be an object")
    return payload


def resolve_deployment_digest(document: dict[str, Any], *, root_digest: str, platform: str) -> str:
    if not DIGEST_PATTERN.fullmatch(root_digest):
        raise DeploymentDigestError("root digest must be a sha256 OCI digest")
    try:
        os_name, architecture = platform.split("/", 1)
    except ValueError as exc:
        raise DeploymentDigestError("platform must be formatted as os/architecture") from exc
    if not os_name or not architecture:
        raise DeploymentDigestError("platform must be formatted as os/architecture")

    media_type = document.get("mediaType")
    if media_type in MANIFEST_MEDIA_TYPES:
        return root_digest
    if media_type not in INDEX_MEDIA_TYPES:
        raise DeploymentDigestError("image document must be an OCI index or image manifest")

    manifests = document.get("manifests")
    if not isinstance(manifests, list):
        raise DeploymentDigestError("image index manifests must be a list")

    matches: list[str] = []
    for descriptor in manifests:
        if not isinstance(descriptor, dict):
            raise DeploymentDigestError("image index contains a malformed descriptor")
        descriptor_platform = descriptor.get("platform")
        if not isinstance(descriptor_platform, dict):
            continue
        if (
            descriptor_platform.get("os") == os_name
            and descriptor_platform.get("architecture") == architecture
        ):
            digest = descriptor.get("digest")
            if not isinstance(digest, str) or not DIGEST_PATTERN.fullmatch(digest):
                raise DeploymentDigestError("matching image descriptor digest is invalid")
            matches.append(digest)

    if not matches:
        raise DeploymentDigestError(f"image index does not contain platform {platform}")
    if len(matches) > 1:
        raise DeploymentDigestError(f"image index contains multiple {platform} manifests")
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        digest = resolve_deployment_digest(
            _load_document(sys.stdin.read()),
            root_digest=args.root_digest,
            platform=args.platform,
        )
    except DeploymentDigestError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
