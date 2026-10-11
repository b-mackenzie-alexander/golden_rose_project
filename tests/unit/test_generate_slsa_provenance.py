import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "generate_slsa_provenance.py"
DIGEST = "sha256:" + "a" * 64
SOURCE_REPOSITORY = "https://github.com/b-mackenzie-alexander/golden_rose_project"
SOURCE_REF = "refs/heads/develop"
SOURCE_COMMIT = "b" * 40
INVOCATION_ID = (
    "https://github.com/b-mackenzie-alexander/golden_rose_project/actions/runs/123/attempts/1"
)


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("generate_slsa_provenance", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_metadata() -> dict[str, object]:
    return {
        "containerimage.digest": DIGEST,
        "containerimage.descriptor": {
            "digest": DIGEST,
            "mediaType": "application/vnd.oci.image.index.v1+json",
        },
        "buildx.build.provenance": {
            "builder": {"id": ""},
            "buildType": "https://mobyproject.org/buildkit@v1",
            "materials": [
                {
                    "uri": (
                        "pkg:docker/public.ecr.aws/docker/library/"
                        "python@3.12.12-slim-bookworm?platform=linux%2Famd64"
                    ),
                    "digest": {"sha256": "c" * 64},
                }
            ],
            "invocation": {
                "configSource": {"entryPoint": "Dockerfile"},
                "parameters": {
                    "root": {
                        "configSource": {"path": "Dockerfile"},
                        "request": {
                            "args": {
                                "vcs:source": SOURCE_REPOSITORY,
                                "vcs:revision": SOURCE_COMMIT,
                            }
                        },
                    }
                },
                "environment": {"platform": "linux/arm64"},
            },
        },
    }


def generate(module: ModuleType, metadata: dict[str, object]) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        module.generate_slsa_v1_predicate(
            metadata,
            source_repository=SOURCE_REPOSITORY,
            source_ref=SOURCE_REF,
            source_commit=SOURCE_COMMIT,
            dockerfile="Dockerfile",
            platform="linux/amd64",
            builder_id="https://github.com/actions/runner/github-hosted",
            invocation_id=INVOCATION_ID,
        ),
    )


def test_generates_slsa_v1_predicate_from_validated_buildx_metadata() -> None:
    module = load_module()

    predicate = generate(module, valid_metadata())

    definition = predicate["buildDefinition"]
    assert definition["buildType"] == "https://mobyproject.org/buildkit@v1"
    assert definition["externalParameters"] == {
        "source": {"repository": SOURCE_REPOSITORY, "ref": SOURCE_REF},
        "dockerfile": "Dockerfile",
        "platform": "linux/amd64",
    }
    assert definition["resolvedDependencies"] == [
        {
            "uri": f"git+{SOURCE_REPOSITORY}@{SOURCE_REF}",
            "digest": {"gitCommit": SOURCE_COMMIT},
        },
        {
            "uri": (
                "pkg:docker/public.ecr.aws/docker/library/"
                "python@3.12.12-slim-bookworm?platform=linux%2Famd64"
            ),
            "digest": {"sha256": "c" * 64},
        },
    ]
    assert predicate["runDetails"] == {
        "builder": {"id": "https://github.com/actions/runner/github-hosted"},
        "metadata": {"invocationId": INVOCATION_ID},
    }


def test_accepts_buildx_git_suffix_as_the_same_canonical_repository() -> None:
    module = load_module()
    metadata = cast(dict[str, Any], valid_metadata())
    args = metadata["buildx.build.provenance"]["invocation"]["parameters"]["root"]["request"][
        "args"
    ]
    args["vcs:source"] = SOURCE_REPOSITORY + ".git"

    predicate = generate(module, metadata)

    assert predicate["buildDefinition"]["externalParameters"]["source"]["repository"] == (
        SOURCE_REPOSITORY
    )


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (
            lambda payload: payload.update({"containerimage.digest": "sha256:" + "f" * 64}),
            "descriptor digest",
        ),
        (
            lambda payload: payload["buildx.build.provenance"].update(
                {"buildType": "https://example.invalid/build"}
            ),
            "build type",
        ),
        (
            lambda payload: payload["buildx.build.provenance"]["invocation"]["parameters"]["root"][
                "request"
            ]["args"].update({"vcs:revision": "d" * 40}),
            "source revision",
        ),
        (
            lambda payload: payload["buildx.build.provenance"].update({"materials": []}),
            "materials",
        ),
    ],
)
def test_rejects_untrusted_buildx_metadata(mutate, error: str) -> None:
    module = load_module()
    metadata = deepcopy(valid_metadata())
    mutate(metadata)

    with pytest.raises(ValueError, match=error):
        generate(module, metadata)


def test_cli_writes_the_validated_predicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module()
    metadata_path = tmp_path / "metadata.json"
    output_path = tmp_path / "predicate.json"
    metadata_path.write_text(json.dumps(valid_metadata()), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_slsa_provenance.py",
            "--metadata",
            str(metadata_path),
            "--output",
            str(output_path),
            "--source-repository",
            SOURCE_REPOSITORY,
            "--source-ref",
            SOURCE_REF,
            "--source-commit",
            SOURCE_COMMIT,
            "--invocation-id",
            INVOCATION_ID,
        ],
    )

    assert module.main() == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["buildDefinition"]
