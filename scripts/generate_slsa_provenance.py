from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
GITHUB_REPOSITORY_PATTERN = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_INVOCATION_PATTERN = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[0-9]+/attempts/[1-9][0-9]*$"
)
EXPECTED_BUILDKIT_BUILD_TYPE = "https://mobyproject.org/buildkit@v1"
EXPECTED_BUILDER_ID = "https://github.com/actions/runner/github-hosted"
EXPECTED_DOCKERFILE = "Dockerfile"
EXPECTED_PLATFORM = "linux/amd64"
EXPECTED_SOURCE_REF = "refs/heads/develop"


def _required_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _validate_materials(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("BuildKit provenance materials must be a non-empty array")
    for material in value:
        if not isinstance(material, dict):
            raise ValueError("BuildKit provenance materials must be objects")
        uri = material.get("uri")
        digest = material.get("digest")
        if (
            not isinstance(uri, str)
            or not uri.strip()
            or not isinstance(digest, dict)
            or not digest
        ):
            raise ValueError("BuildKit provenance materials must include URI and digest")
        if not all(
            isinstance(algorithm, str) and algorithm and isinstance(value, str) and value
            for algorithm, value in digest.items()
        ):
            raise ValueError("BuildKit provenance material digests must be non-empty strings")
    return deepcopy(value)


def generate_slsa_v1_predicate(
    metadata: dict[str, Any],
    *,
    source_repository: str,
    source_ref: str,
    source_commit: str,
    dockerfile: str,
    platform: str,
    builder_id: str,
    invocation_id: str,
) -> dict[str, Any]:
    digest = metadata.get("containerimage.digest")
    if not isinstance(digest, str) or not DIGEST_PATTERN.fullmatch(digest):
        raise ValueError("container image digest must be immutable SHA-256")
    descriptor = _required_object(metadata.get("containerimage.descriptor"), "image descriptor")
    if descriptor.get("digest") != digest:
        raise ValueError("image descriptor digest must match the container image digest")

    if not GITHUB_REPOSITORY_PATTERN.fullmatch(source_repository):
        raise ValueError("source repository must be a canonical HTTPS GitHub URL")
    if source_ref != EXPECTED_SOURCE_REF:
        raise ValueError("source ref must be refs/heads/develop")
    if not GIT_SHA_PATTERN.fullmatch(source_commit):
        raise ValueError("source commit must be a full lowercase git SHA")
    if dockerfile != EXPECTED_DOCKERFILE:
        raise ValueError("build entry point must be Dockerfile")
    if platform != EXPECTED_PLATFORM:
        raise ValueError("output platform must be linux/amd64")
    if builder_id != EXPECTED_BUILDER_ID:
        raise ValueError("builder identity must be the GitHub-hosted Actions runner")
    if not GITHUB_INVOCATION_PATTERN.fullmatch(invocation_id):
        raise ValueError("invocation ID must identify a GitHub Actions run attempt")

    provenance = _required_object(metadata.get("buildx.build.provenance"), "BuildKit provenance")
    if provenance.get("buildType") != EXPECTED_BUILDKIT_BUILD_TYPE:
        raise ValueError("BuildKit provenance build type is unexpected")
    invocation = _required_object(provenance.get("invocation"), "BuildKit invocation")
    config_source = _required_object(
        invocation.get("configSource"), "BuildKit invocation config source"
    )
    if config_source.get("entryPoint") != dockerfile:
        raise ValueError("BuildKit invocation entry point is unexpected")
    parameters = _required_object(invocation.get("parameters"), "BuildKit parameters")
    root = _required_object(parameters.get("root"), "BuildKit source root")
    root_config = _required_object(root.get("configSource"), "BuildKit root config source")
    if root_config.get("path") != dockerfile:
        raise ValueError("BuildKit Dockerfile path is unexpected")
    request = _required_object(root.get("request"), "BuildKit source request")
    args = _required_object(request.get("args"), "BuildKit source arguments")
    observed_source = args.get("vcs:source")
    if (
        not isinstance(observed_source, str)
        or observed_source.removesuffix(".git") != source_repository
    ):
        raise ValueError("BuildKit source repository is unexpected")
    if args.get("vcs:revision") != source_commit:
        raise ValueError("BuildKit source revision is unexpected")

    materials = _validate_materials(provenance.get("materials"))
    source_dependency = {
        "uri": f"git+{source_repository}@{source_ref}",
        "digest": {"gitCommit": source_commit},
    }
    return {
        "buildDefinition": {
            "buildType": EXPECTED_BUILDKIT_BUILD_TYPE,
            "externalParameters": {
                "source": {"repository": source_repository, "ref": source_ref},
                "dockerfile": dockerfile,
                "platform": platform,
            },
            "internalParameters": {},
            "resolvedDependencies": [source_dependency, *materials],
        },
        "runDetails": {
            "builder": {"id": builder_id},
            "metadata": {"invocationId": invocation_id},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a validated SLSA v1 predicate from Docker Buildx metadata."
    )
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--invocation-id", required=True)
    parser.add_argument("--dockerfile", default=EXPECTED_DOCKERFILE)
    parser.add_argument("--platform", default=EXPECTED_PLATFORM)
    parser.add_argument("--builder-id", default=EXPECTED_BUILDER_ID)
    args = parser.parse_args()

    try:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Buildx metadata must be readable JSON") from exc
    if not isinstance(metadata, dict):
        raise ValueError("Buildx metadata must be a JSON object")
    predicate = generate_slsa_v1_predicate(
        metadata,
        source_repository=args.source_repository,
        source_ref=args.source_ref,
        source_commit=args.source_commit,
        dockerfile=args.dockerfile,
        platform=args.platform,
        builder_id=args.builder_id,
        invocation_id=args.invocation_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(predicate, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        raise SystemExit(f"SLSA provenance generation failed: {exc}") from exc
