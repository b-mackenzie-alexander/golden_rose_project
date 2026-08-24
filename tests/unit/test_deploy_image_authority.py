import base64
import importlib.util
import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "verify_deploy_image_authority.py"
DIGEST = "sha256:" + "a" * 64
IMAGE = f"us-east4-docker.pkg.dev/example/staff-tracer-images/staff-tracer@{DIGEST}"
IDENTITY = "https://github.com/b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop"
SOURCE_COMMIT = "b" * 40


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_deploy_image_authority", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PredicateMutator = Callable[[dict[str, Any]], None]


def signature() -> dict[str, Any]:
    return {
        "critical": {
            "identity": {"docker-reference": IMAGE.split("@", 1)[0]},
            "image": {"docker-manifest-digest": DIGEST},
            "type": "cosign container image signature",
        }
    }


def envelope(predicate_type: str, predicate: dict[str, Any]) -> dict[str, Any]:
    statement = {
        "_type": "https://in-toto.io/Statement/v0.1",
        "predicateType": predicate_type,
        "subject": [{"name": IMAGE.split("@", 1)[0], "digest": {"sha256": "a" * 64}}],
        "predicate": predicate,
    }
    return {
        "payloadType": "application/vnd.in-toto+json",
        "payload": base64.b64encode(json.dumps(statement).encode()).decode(),
        "signatures": [{"sig": "verified-by-cosign"}],
    }


def provenance_predicate() -> dict[str, Any]:
    return {
        "containerimage.digest": DIGEST,
        "containerimage.descriptor": {
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "digest": DIGEST,
            "size": 856,
        },
        "buildx.build.provenance": {
            "builder": {"id": ""},
            "buildType": "https://mobyproject.org/buildkit@v1",
            "materials": [],
            "invocation": {
                "configSource": {"entryPoint": "Dockerfile"},
                "parameters": {
                    "frontend": "dockerfile.v0",
                    "root": {
                        "configSource": {"path": "Dockerfile"},
                        "request": {
                            "args": {
                                "vcs:revision": SOURCE_COMMIT,
                                "vcs:source": "https://github.com/b-mackenzie-alexander/golden_rose_project.git",
                            }
                        },
                    },
                },
                "environment": {"platform": "linux/amd64"},
            },
        },
    }


def image_sbom_predicate() -> dict[str, Any]:
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "sbom-staff-tracer",
        "documentNamespace": "https://anchore.com/syft/image/staff-tracer",
        "creationInfo": {"creators": ["Tool: syft-v1.20.0"]},
        "documentDescribes": ["SPDXRef-Image-staff-tracer"],
        "packages": [{"SPDXID": "SPDXRef-Image-staff-tracer", "name": "staff-tracer"}],
    }


def application_sbom_predicate() -> dict[str, Any]:
    return {
        "backend_sbom_sha256": "c" * 64,
        "frontend_sbom_sha256": "d" * 64,
        "image_digest": DIGEST,
    }


def valid_attestations() -> dict[str, dict[str, Any]]:
    return {
        "provenance": envelope("https://slsa.dev/provenance/v1", provenance_predicate()),
        "image": envelope("https://spdx.dev/Document", image_sbom_predicate()),
        "application": envelope(
            "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1",
            application_sbom_predicate(),
        ),
    }


def write_evidence(tmp_path: Path, attestations: dict[str, dict[str, Any]]) -> dict[str, Path]:
    files = {name: tmp_path / f"{name}.json" for name in ("signature", *attestations)}
    files["signature"].write_text(json.dumps([signature()]), encoding="utf-8")
    for name, payload in attestations.items():
        files[name].write_text(json.dumps(payload), encoding="utf-8")
    return files


def verify(module: ModuleType, files: dict[str, Path]) -> str:
    return cast(
        str,
        module.verify_deploy_image_authority(
            image=IMAGE,
            signature_path=files["signature"],
            provenance_path=files["provenance"],
            image_sbom_path=files["image"],
            application_sbom_path=files["application"],
            expected_identity=IDENTITY,
            expected_source_commit=SOURCE_COMMIT,
        ),
    )


def test_deploy_authority_accepts_actual_shaped_cosign_v3_predicates(tmp_path: Path) -> None:
    module = load_module()
    assert verify(module, write_evidence(tmp_path, valid_attestations())) == DIGEST


@pytest.mark.parametrize(
    ("attestation_name", "mutate", "error"),
    [
        (
            "provenance",
            lambda predicate: predicate["buildx.build.provenance"]["invocation"]["parameters"][
                "root"
            ]["request"]["args"].update({"vcs:revision": "e" * 40}),
            "source revision",
        ),
        (
            "image",
            lambda predicate: predicate.update({"packages": []}),
            "component inventory",
        ),
        (
            "image",
            lambda predicate: predicate.update({"documentDescribes": []}),
            "component inventory subject",
        ),
        (
            "application",
            lambda predicate: predicate.update({"image_digest": "sha256:" + "f" * 64}),
            "image digest",
        ),
        (
            "application",
            lambda predicate: predicate.update({"backend_sbom_sha256": "not-a-checksum"}),
            "checksum",
        ),
    ],
)
def test_deploy_authority_rejects_semantically_invalid_signed_predicates(
    tmp_path: Path, attestation_name: str, mutate: PredicateMutator, error: str
) -> None:
    module = load_module()
    attestations = deepcopy(valid_attestations())
    statement = json.loads(base64.b64decode(attestations[attestation_name]["payload"]))
    predicate = statement["predicate"]
    mutate(predicate)
    attestations[attestation_name]["payload"] = base64.b64encode(
        json.dumps(statement).encode()
    ).decode()
    with pytest.raises(module.DeployImageAuthorityError, match=error):
        verify(module, write_evidence(tmp_path, attestations))
