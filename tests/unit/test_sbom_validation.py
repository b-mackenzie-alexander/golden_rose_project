import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "validate_sbom.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_sbom", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_frontend_sbom() -> dict[str, Any]:
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:11111111-1111-4111-8111-111111111111",
        "version": 1,
        "metadata": {
            "timestamp": "2026-08-07T00:00:00Z",
            "lifecycles": [{"phase": "build"}],
            "tools": [
                {
                    "vendor": "npm",
                    "name": "npm",
                    "version": "10.9.8",
                }
            ],
            "component": {
                "bom-ref": "pkg:npm/%40golden-rose/web@0.0.0",
                "type": "application",
                "name": "web",
                "version": "0.0.0",
                "purl": "pkg:npm/%40golden-rose/web@0.0.0",
            },
        },
        "components": [
            {
                "bom-ref": "pkg:npm/react@19.2.8",
                "type": "library",
                "name": "react",
                "version": "19.2.8",
                "purl": "pkg:npm/react@19.2.8",
            }
        ],
        "dependencies": [
            {
                "ref": "pkg:npm/%40golden-rose/web@0.0.0",
                "dependsOn": ["pkg:npm/react@19.2.8"],
            },
            {"ref": "pkg:npm/react@19.2.8", "dependsOn": []},
        ],
    }


def make_backend_sbom() -> dict[str, Any]:
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.6.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "cyclonedx-py",
                        "version": "7.3.1",
                    }
                ]
            },
            "component": {
                "bom-ref": "golden-rose@0.1.0",
                "type": "application",
                "name": "golden-rose",
                "version": "0.1.0",
            },
        },
        "components": [
            {
                "bom-ref": "pkg:pypi/fastapi@0.141.1",
                "type": "library",
                "name": "fastapi",
                "version": "0.141.1",
                "purl": "pkg:pypi/fastapi@0.141.1",
            }
        ],
        "dependencies": [
            {"ref": "golden-rose@0.1.0", "dependsOn": ["pkg:pypi/fastapi@0.141.1"]},
            {"ref": "pkg:pypi/fastapi@0.141.1", "dependsOn": []},
        ],
    }


def dump_json(document: dict[str, Any]) -> str:
    return json.dumps(document)


@pytest.mark.parametrize(
    ("document", "spec", "name", "version", "purl"),
    [
        (make_frontend_sbom(), "1.5", "web", "0.0.0", "pkg:npm/%40golden-rose/web@0.0.0"),
        (make_backend_sbom(), "1.6", "golden-rose", "0.1.0", None),
    ],
)
def test_accepts_bounded_valid_sboms(
    document: dict[str, Any],
    spec: str,
    name: str,
    version: str,
    purl: str | None,
) -> None:
    module = load_module()

    module.validate_sbom_document(
        dump_json(document),
        expected_spec=spec,
        expected_name=name,
        expected_version=version,
        expected_purl=purl,
    )


@pytest.mark.parametrize(
    ("document_text", "spec", "name", "version", "expected_message"),
    [
        ("{", "1.5", "web", "0.0.0", "valid JSON"),
        (
            dump_json({**make_frontend_sbom(), "bomFormat": "SPDX"}),
            "1.5",
            "web",
            "0.0.0",
            "bomFormat",
        ),
        (
            dump_json({**make_frontend_sbom(), "specVersion": "1.4"}),
            "1.5",
            "web",
            "0.0.0",
            "specVersion",
        ),
        (
            dump_json({**make_frontend_sbom(), "version": "one"}),
            "1.5",
            "web",
            "0.0.0",
            "schema validation",
        ),
        (
            dump_json(
                {
                    **make_frontend_sbom(),
                    "metadata": {
                        **make_frontend_sbom()["metadata"],
                        "component": {
                            **make_frontend_sbom()["metadata"]["component"],
                            "name": "wrong",
                        },
                    },
                }
            ),
            "1.5",
            "web",
            "0.0.0",
            "root component name",
        ),
        (
            dump_json(
                {
                    **make_frontend_sbom(),
                    "metadata": {
                        **make_frontend_sbom()["metadata"],
                        "component": {
                            **make_frontend_sbom()["metadata"]["component"],
                            "type": "library",
                        },
                    },
                }
            ),
            "1.5",
            "web",
            "0.0.0",
            "root component type",
        ),
        (
            dump_json(
                {
                    **make_frontend_sbom(),
                    "metadata": {
                        **make_frontend_sbom()["metadata"],
                        "component": {
                            **make_frontend_sbom()["metadata"]["component"],
                            "version": "9.9.9",
                        },
                    },
                }
            ),
            "1.5",
            "web",
            "0.0.0",
            "root component version",
        ),
        (
            dump_json({**make_frontend_sbom(), "components": []}),
            "1.5",
            "web",
            "0.0.0",
            "components",
        ),
        (
            dump_json({**make_frontend_sbom(), "dependencies": []}),
            "1.5",
            "web",
            "0.0.0",
            "dependencies",
        ),
        (
            dump_json(
                {
                    **make_frontend_sbom(),
                    "dependencies": [{"ref": "pkg:npm/%40golden-rose/web@0.0.0", "dependsOn": []}],
                }
            ),
            "1.5",
            "web",
            "0.0.0",
            "dependency edge",
        ),
        (
            dump_json(
                {
                    **make_frontend_sbom(),
                    "metadata": {**make_frontend_sbom()["metadata"], "tools": []},
                }
            ),
            "1.5",
            "web",
            "0.0.0",
            "generator metadata",
        ),
        (
            dump_json(
                {
                    **make_frontend_sbom(),
                    "dependencies": [
                        {
                            "ref": "pkg:npm/%40golden-rose/web@0.0.0",
                            "dependsOn": ["pkg:npm/unknown@1.0.0"],
                        }
                    ],
                }
            ),
            "1.5",
            "web",
            "0.0.0",
            "unknown dependency reference",
        ),
    ],
)
def test_rejects_invalid_sbom_shapes(
    document_text: str,
    spec: str,
    name: str,
    version: str,
    expected_message: str,
) -> None:
    module = load_module()

    with pytest.raises(module.SbomValidationError, match=expected_message):
        module.validate_sbom_document(
            document_text,
            expected_spec=spec,
            expected_name=name,
            expected_version=version,
        )


def test_rejects_unknown_dependency_properties_before_canonicalization() -> None:
    module = load_module()
    document = make_frontend_sbom()
    document["dependencies"][0]["unexpected"] = "must-not-be-erased"

    with pytest.raises(module.SbomValidationError, match="unsupported properties"):
        module.validate_sbom_document(
            dump_json(document),
            expected_spec="1.5",
            expected_name="web",
            expected_version="0.0.0",
            expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
        )


def test_rejects_wrong_frontend_purl() -> None:
    module = load_module()
    document = make_frontend_sbom()
    document["metadata"]["component"]["purl"] = "pkg:npm/%40golden-rose/other@0.0.0"

    with pytest.raises(module.SbomValidationError, match="root component purl"):
        module.validate_sbom_document(
            dump_json(document),
            expected_spec="1.5",
            expected_name="web",
            expected_version="0.0.0",
            expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
        )


def test_merges_schema_valid_duplicate_dependency_refs() -> None:
    module = load_module()
    document = make_frontend_sbom()
    document["dependencies"].append(
        {"ref": "pkg:npm/%40golden-rose/web@0.0.0", "dependsOn": []},
    )

    normalized = module.validate_sbom_document(
        dump_json(document),
        expected_spec="1.5",
        expected_name="web",
        expected_version="0.0.0",
        expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
    )

    assert normalized["dependencies"] == make_frontend_sbom()["dependencies"]


def test_deduplicates_exact_generator_dependency_rows_before_schema_validation() -> None:
    module = load_module()
    document = make_frontend_sbom()
    document["dependencies"].append(document["dependencies"][0].copy())

    normalized = module.validate_sbom_document(
        dump_json(document),
        expected_spec="1.5",
        expected_name="web",
        expected_version="0.0.0",
        expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
    )

    assert normalized["dependencies"] == make_frontend_sbom()["dependencies"]


def test_normalizes_missing_dependency_lists_to_empty_lists() -> None:
    module = load_module()
    document = make_backend_sbom()
    document["dependencies"].append({"ref": "pkg:pypi/fastapi@0.141.1"})

    normalized = module.validate_sbom_document(
        dump_json(document),
        expected_spec="1.6",
        expected_name="golden-rose",
        expected_version="0.1.0",
    )

    assert normalized["dependencies"][-1] == {"ref": "pkg:pypi/fastapi@0.141.1", "dependsOn": []}


def test_rejects_malformed_present_dependency_lists() -> None:
    module = load_module()
    document = make_backend_sbom()
    document["dependencies"][0]["dependsOn"] = "pkg:pypi/fastapi@0.141.1"

    with pytest.raises(module.SbomValidationError, match="dependsOn must be a list"):
        module.validate_sbom_document(
            dump_json(document),
            expected_spec="1.6",
            expected_name="golden-rose",
            expected_version="0.1.0",
        )


def test_rejects_raw_exact_duplicate_component_entries() -> None:
    module = load_module()
    document = make_frontend_sbom()
    document["components"].append(document["components"][0].copy())

    with pytest.raises(module.SbomValidationError, match="duplicate component"):
        module.validate_sbom_document(
            dump_json(document),
            expected_spec="1.5",
            expected_name="web",
            expected_version="0.0.0",
            expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
        )


def test_merges_properties_for_otherwise_identical_duplicate_components() -> None:
    module = load_module()
    document = make_frontend_sbom()
    first_component = document["components"][0]
    first_component["properties"] = [
        {"name": "cdx:npm:package:path", "value": "node_modules/react"}
    ]
    duplicate_component = first_component.copy()
    duplicate_component["properties"] = [
        {"name": "cdx:npm:package:path", "value": "node_modules/example/node_modules/react"}
    ]
    document["components"].append(duplicate_component)

    normalized = module.validate_sbom_document(
        dump_json(document),
        expected_spec="1.5",
        expected_name="web",
        expected_version="0.0.0",
        expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
    )

    assert normalized["components"][0]["properties"] == [
        {
            "name": "cdx:npm:package:path",
            "value": "node_modules/example/node_modules/react",
        },
        {"name": "cdx:npm:package:path", "value": "node_modules/react"},
    ]


def test_rejects_conflicting_duplicate_component_entries() -> None:
    module = load_module()
    document = make_frontend_sbom()
    conflicting_component = document["components"][0].copy()
    conflicting_component["version"] = "0.0.0"
    document["components"].append(conflicting_component)

    with pytest.raises(module.SbomValidationError, match="conflicting duplicate component"):
        module.validate_sbom_document(
            dump_json(document),
            expected_spec="1.5",
            expected_name="web",
            expected_version="0.0.0",
            expected_purl="pkg:npm/%40golden-rose/web@0.0.0",
        )
