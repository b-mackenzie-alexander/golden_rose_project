import base64
import hashlib
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
SIGNATURE_TYPES = (
    "https://sigstore.dev/cosign/sign/v1",
    "https://slsa.dev/provenance/v1",
    "https://spdx.dev/Document",
    "https://golden-rose.nousresearch.com/attestations/application-sbom-checksums/v1",
)


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_deploy_image_authority", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PredicateMutator = Callable[[dict[str, Any]], None]


def signature(signature_type: str = SIGNATURE_TYPES[0]) -> dict[str, Any]:
    return {
        "critical": {
            "identity": {"docker-reference": IMAGE},
            "image": {"docker-manifest-digest": DIGEST},
            "type": signature_type,
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
        "buildDefinition": {
            "buildType": "https://mobyproject.org/buildkit@v1",
            "externalParameters": {
                "source": {
                    "repository": "https://github.com/b-mackenzie-alexander/golden_rose_project",
                    "ref": "refs/heads/develop",
                },
                "dockerfile": "Dockerfile",
                "platform": "linux/amd64",
            },
            "internalParameters": {},
            "resolvedDependencies": [
                {
                    "uri": "git+https://github.com/b-mackenzie-alexander/golden_rose_project@refs/heads/develop",
                    "digest": {"gitCommit": SOURCE_COMMIT},
                },
                {
                    "uri": (
                        "pkg:docker/docker.io/library/"
                        "node@22.22.3-bookworm-slim?platform=linux%2Famd64"
                    ),
                    "digest": {
                        "sha256": "16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
                    },
                },
                {
                    "uri": (
                        "pkg:docker/docker.io/library/"
                        "python@3.12.12-slim-bookworm?platform=linux%2Famd64"
                    ),
                    "digest": {
                        "sha256": "2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
                    },
                },
            ],
        },
        "runDetails": {
            "builder": {"id": "https://github.com/actions/runner/github-hosted"},
            "metadata": {
                "invocationId": "https://github.com/b-mackenzie-alexander/golden_rose_project/actions/runs/123/attempts/1"
            },
        },
    }


def image_sbom_predicate() -> dict[str, Any]:
    repository = IMAGE.split("@", 1)[0]
    platform_digest = "e" * 64
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": repository,
        "documentNamespace": "https://anchore.com/syft/image/staff-tracer-test",
        "creationInfo": {
            "creators": ["Organization: Anchore, Inc", "Tool: syft-1.37.0"],
            "created": "2026-09-03T17:00:54Z",
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Image-staff-tracer",
                "name": repository,
                "versionInfo": DIGEST,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "primaryPackagePurpose": "CONTAINER",
                "checksums": [{"algorithm": "SHA256", "checksumValue": platform_digest}],
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            f"pkg:oci/{repository}@sha256%3A{platform_digest}?arch=amd64"
                        ),
                    }
                ],
            }
        ],
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Image-staff-tracer",
            }
        ],
    }


def application_sbom_predicate() -> dict[str, Any]:
    backend_sbom = b'{"bomFormat":"CycloneDX","metadata":{"component":{"name":"golden-rose"}}}'
    frontend_sbom = b'{"bomFormat":"CycloneDX","metadata":{"component":{"name":"web"}}}'
    return {
        "backend_sbom_sha256": hashlib.sha256(backend_sbom).hexdigest(),
        "frontend_sbom_sha256": hashlib.sha256(frontend_sbom).hexdigest(),
        "backend_sbom_base64": base64.b64encode(backend_sbom).decode(),
        "frontend_sbom_base64": base64.b64encode(frontend_sbom).decode(),
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
    files["signature"].write_text(
        json.dumps([signature(signature_type) for signature_type in SIGNATURE_TYPES]),
        encoding="utf-8",
    )
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


def test_deploy_authority_rejects_repository_only_signature_identity(tmp_path: Path) -> None:
    module = load_module()
    files = write_evidence(tmp_path, valid_attestations())
    payload = json.loads(files["signature"].read_text())
    payload[0]["critical"]["identity"]["docker-reference"] = IMAGE.split("@", 1)[0]
    files["signature"].write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(module.DeployImageAuthorityError, match="signature subject"):
        verify(module, files)


def test_deploy_authority_rejects_wrong_signature_type(tmp_path: Path) -> None:
    module = load_module()
    files = write_evidence(tmp_path, valid_attestations())
    payload = json.loads(files["signature"].read_text())
    payload[0]["critical"]["type"] = "unreviewed signature type"
    files["signature"].write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(module.DeployImageAuthorityError, match="signature type"):
        verify(module, files)


def test_deploy_authority_rejects_missing_primary_signature_type(tmp_path: Path) -> None:
    module = load_module()
    files = write_evidence(tmp_path, valid_attestations())
    payload = json.loads(files["signature"].read_text())
    payload[0]["critical"]["type"] = SIGNATURE_TYPES[1]
    files["signature"].write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(module.DeployImageAuthorityError, match="signature type set"):
        verify(module, files)


def test_publish_authority_binds_signed_checksums_to_exact_sbom_files(tmp_path: Path) -> None:
    module = load_module()
    attestations = valid_attestations()
    backend_sbom_path = tmp_path / "backend-sbom.cdx.json"
    frontend_sbom_path = tmp_path / "frontend-sbom.cdx.json"
    backend_sbom_path.write_text(
        '{"bomFormat":"CycloneDX","metadata":{"component":{"name":"golden-rose"}}}',
        encoding="utf-8",
    )
    frontend_sbom_path.write_text(
        '{"bomFormat":"CycloneDX","metadata":{"component":{"name":"web"}}}',
        encoding="utf-8",
    )
    statement = json.loads(base64.b64decode(attestations["application"]["payload"]))
    statement["predicate"]["backend_sbom_sha256"] = hashlib.sha256(
        backend_sbom_path.read_bytes()
    ).hexdigest()
    statement["predicate"]["frontend_sbom_sha256"] = hashlib.sha256(
        frontend_sbom_path.read_bytes()
    ).hexdigest()
    statement["predicate"]["backend_sbom_base64"] = base64.b64encode(
        backend_sbom_path.read_bytes()
    ).decode()
    statement["predicate"]["frontend_sbom_base64"] = base64.b64encode(
        frontend_sbom_path.read_bytes()
    ).decode()
    attestations["application"]["payload"] = base64.b64encode(
        json.dumps(statement).encode()
    ).decode()
    files = write_evidence(tmp_path, attestations)

    assert (
        module.verify_deploy_image_authority(
            image=IMAGE,
            signature_path=files["signature"],
            provenance_path=files["provenance"],
            image_sbom_path=files["image"],
            application_sbom_path=files["application"],
            expected_identity=IDENTITY,
            expected_source_commit=SOURCE_COMMIT,
            backend_sbom_path=backend_sbom_path,
            frontend_sbom_path=frontend_sbom_path,
        )
        == DIGEST
    )

    backend_sbom_path.write_text('{"bomFormat":"CycloneDX","changed":true}', encoding="utf-8")
    with pytest.raises(module.DeployImageAuthorityError, match="backend checksum"):
        module.verify_deploy_image_authority(
            image=IMAGE,
            signature_path=files["signature"],
            provenance_path=files["provenance"],
            image_sbom_path=files["image"],
            application_sbom_path=files["application"],
            expected_identity=IDENTITY,
            expected_source_commit=SOURCE_COMMIT,
            backend_sbom_path=backend_sbom_path,
            frontend_sbom_path=frontend_sbom_path,
        )


@pytest.mark.parametrize(
    ("attestation_name", "mutate", "error"),
    [
        (
            "provenance",
            lambda predicate: predicate["buildDefinition"]["resolvedDependencies"][0][
                "digest"
            ].update({"gitCommit": "e" * 40}),
            "source revision",
        ),
        (
            "provenance",
            lambda predicate: predicate["buildDefinition"]["externalParameters"].update(
                {"platform": "linux/arm64"}
            ),
            "platform",
        ),
        (
            "provenance",
            lambda predicate: predicate["runDetails"]["builder"].update(
                {"id": "https://example.invalid/builder"}
            ),
            "builder",
        ),
        (
            "image",
            lambda predicate: predicate.update({"packages": []}),
            "component inventory",
        ),
        (
            "image",
            lambda predicate: predicate.update({"relationships": []}),
            "component inventory subject",
        ),
        (
            "image",
            lambda predicate: predicate.update({"documentDescribes": "SPDXRef-Image-staff-tracer"}),
            "pinned SPDX 2.3 schema",
        ),
        (
            "image",
            lambda predicate: predicate["packages"][0]["externalRefs"][0].update(
                {"referenceLocator": "e" * 64 + "?arch=amd64"}
            ),
            "amd64 OCI purl",
        ),
        (
            "image",
            lambda predicate: predicate["packages"][0]["externalRefs"][0].update(
                {
                    "referenceLocator": predicate["packages"][0]["externalRefs"][0][
                        "referenceLocator"
                    ]
                    + "&tag=latest"
                }
            ),
            "amd64 OCI purl",
        ),
        (
            "image",
            lambda predicate: predicate["packages"][0]["externalRefs"][0].update(
                {
                    "referenceLocator": predicate["packages"][0]["externalRefs"][0][
                        "referenceLocator"
                    ]
                    + "&tag="
                }
            ),
            "amd64 OCI purl",
        ),
        (
            "image",
            lambda predicate: predicate["creationInfo"].update({"created": "9999-99-99T99:99:99Z"}),
            "creationInfo",
        ),
        (
            "image",
            lambda predicate: predicate["packages"][0].update({"licenseConcluded": ""}),
            "schema-complete component inventory",
        ),
        (
            "application",
            lambda predicate: predicate.update({"image_digest": "sha256:" + "f" * 64}),
            "image digest",
        ),
        (
            "application",
            lambda predicate: predicate.pop("backend_sbom_base64"),
            "embedded backend SBOM is missing",
        ),
        (
            "application",
            lambda predicate: predicate.update(
                {"backend_sbom_base64": base64.b64encode(b'{"bomFormat":"CycloneDX"}').decode()}
            ),
            "embedded backend",
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
