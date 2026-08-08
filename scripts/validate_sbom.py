from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator

SUPPORTED_SPECS: dict[str, SchemaVersion] = {
    "1.5": SchemaVersion.V1_5,
    "1.6": SchemaVersion.V1_6,
}


class SbomValidationError(ValueError):
    pass


def _canonicalize_document(document: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(document)
    components = normalized.get("components")
    if isinstance(components, list):
        deduplicated_components: list[dict[str, Any]] = []
        components_by_ref: dict[str, dict[str, Any]] = {}
        for component in components:
            if not isinstance(component, dict):
                deduplicated_components.append(component)
                continue
            component_ref = component.get("bom-ref")
            if isinstance(component_ref, str) and component_ref:
                if component_ref in components_by_ref:
                    existing_component = components_by_ref[component_ref]
                    if existing_component == component:
                        raise SbomValidationError("SBOM contained an exact duplicate component.")
                    existing_identity = {
                        key: value
                        for key, value in existing_component.items()
                        if key != "properties"
                    }
                    duplicate_identity = {
                        key: value for key, value in component.items() if key != "properties"
                    }
                    if existing_identity != duplicate_identity:
                        raise SbomValidationError(
                            "SBOM contained a conflicting duplicate component."
                        )
                    existing_properties = existing_component.get("properties", [])
                    duplicate_properties = component.get("properties", [])
                    if not isinstance(existing_properties, list) or not isinstance(
                        duplicate_properties, list
                    ):
                        raise SbomValidationError("SBOM component properties must be a list.")
                    properties_by_value = {
                        json.dumps(property_value, sort_keys=True): property_value
                        for property_value in [
                            *existing_properties,
                            *duplicate_properties,
                        ]
                    }
                    if properties_by_value:
                        existing_component["properties"] = [
                            properties_by_value[key] for key in sorted(properties_by_value)
                        ]
                    continue
                components_by_ref[component_ref] = component
            deduplicated_components.append(component)
        normalized["components"] = deduplicated_components

    dependencies = normalized.get("dependencies")
    if not isinstance(dependencies, list):
        return normalized

    deduplicated_dependencies: list[dict[str, Any]] = []
    by_ref: dict[str, dict[str, Any]] = {}
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            deduplicated_dependencies.append(dependency)
            continue
        if set(dependency) - {"ref", "dependsOn"}:
            raise SbomValidationError("SBOM dependency contained unsupported properties.")
        ref = dependency.get("ref")
        depends_on = dependency.get("dependsOn")
        if not isinstance(ref, str):
            deduplicated_dependencies.append(dependency)
            continue
        if "dependsOn" in dependency and not isinstance(depends_on, list):
            raise SbomValidationError("SBOM dependency dependsOn must be a list.")
        normalized_depends_on = depends_on if isinstance(depends_on, list) else []
        if ref not in by_ref:
            normalized_dependency = {"ref": ref, "dependsOn": []}
            by_ref[ref] = normalized_dependency
            deduplicated_dependencies.append(normalized_dependency)
        existing_depends_on = by_ref[ref]["dependsOn"]
        for child_ref in normalized_depends_on:
            if child_ref not in existing_depends_on:
                existing_depends_on.append(child_ref)

    normalized["dependencies"] = deduplicated_dependencies
    return normalized


def _load_json(document_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(document_text)
    except json.JSONDecodeError as exc:
        raise SbomValidationError("SBOM must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise SbomValidationError("SBOM root must be a JSON object.")
    return payload


def _require_schema(document_text: str, spec: str) -> None:
    schema_version = SUPPORTED_SPECS.get(spec)
    if schema_version is None:
        raise SbomValidationError("SBOM specVersion is unsupported.")
    validation_error = JsonStrictValidator(schema_version).validate_str(document_text)
    if validation_error is not None:
        raise SbomValidationError("SBOM failed schema validation.")


def _require_tools_metadata(metadata: dict[str, Any]) -> None:
    tools = metadata.get("tools")
    if isinstance(tools, list):
        if tools:
            return
    elif isinstance(tools, dict) and any(
        isinstance(value, list) and value for value in tools.values()
    ):
        return
    raise SbomValidationError("SBOM is missing generator metadata.")


def _require_root_component(
    metadata: dict[str, Any],
    *,
    expected_name: str,
    expected_version: str,
    expected_purl: str | None,
) -> dict[str, Any]:
    component = metadata.get("component")
    if not isinstance(component, dict):
        raise SbomValidationError("SBOM metadata.component must be present.")
    if component.get("name") != expected_name:
        raise SbomValidationError(
            "SBOM root component name did not match the expected application."
        )
    if component.get("type") != "application":
        raise SbomValidationError("SBOM root component type must be application.")
    if component.get("version") != expected_version:
        raise SbomValidationError(
            "SBOM root component version did not match the expected application."
        )
    if expected_purl is not None and component.get("purl") != expected_purl:
        raise SbomValidationError(
            "SBOM root component purl did not match the expected application."
        )
    return component


def _require_component_inventory(document: dict[str, Any]) -> list[dict[str, Any]]:
    components = document.get("components")
    if not isinstance(components, list) or not components:
        raise SbomValidationError("SBOM must include nonempty components.")
    normalized: list[dict[str, Any]] = []
    for component in components:
        if not isinstance(component, dict):
            raise SbomValidationError("SBOM components must be JSON objects.")
        normalized.append(component)
    return normalized


def _require_dependency_graph(
    root_ref: str, component_refs: set[str], document: dict[str, Any]
) -> None:
    dependencies = document.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise SbomValidationError("SBOM must include nonempty dependencies.")

    known_refs = {root_ref, *component_refs}
    dependency_edges = 0

    for dependency in dependencies:
        if not isinstance(dependency, dict):
            raise SbomValidationError("SBOM dependencies must be JSON objects.")
        ref = dependency.get("ref")
        depends_on = dependency.get("dependsOn")
        if not isinstance(ref, str) or ref not in known_refs:
            raise SbomValidationError(
                "SBOM dependency graph contained an unknown dependency reference."
            )
        if not isinstance(depends_on, list):
            raise SbomValidationError("SBOM dependencies must provide dependsOn lists.")
        for child_ref in depends_on:
            if not isinstance(child_ref, str) or child_ref not in known_refs:
                raise SbomValidationError(
                    "SBOM dependency graph contained an unknown dependency reference."
                )
            dependency_edges += 1

    if dependency_edges == 0:
        raise SbomValidationError(
            "SBOM dependency graph must include at least one dependency edge."
        )


def validate_sbom_document(
    document_text: str,
    *,
    expected_spec: str,
    expected_name: str,
    expected_version: str,
    expected_purl: str | None = None,
) -> dict[str, Any]:
    document = _load_json(document_text)
    if document.get("bomFormat") != "CycloneDX":
        raise SbomValidationError("SBOM bomFormat must be CycloneDX.")
    if document.get("specVersion") != expected_spec:
        raise SbomValidationError("SBOM specVersion did not match the expected value.")

    document = _canonicalize_document(document)
    canonical_document_text = json.dumps(document, sort_keys=True)
    _require_schema(canonical_document_text, expected_spec)

    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        raise SbomValidationError("SBOM metadata must be present.")
    _require_tools_metadata(metadata)
    root_component = _require_root_component(
        metadata,
        expected_name=expected_name,
        expected_version=expected_version,
        expected_purl=expected_purl,
    )
    root_ref = root_component.get("bom-ref")
    if not isinstance(root_ref, str) or not root_ref:
        raise SbomValidationError("SBOM root component bom-ref must be present.")

    components = _require_component_inventory(document)
    component_refs = {
        component_ref
        for component in components
        if isinstance(component_ref := component.get("bom-ref"), str) and component_ref
    }
    if len(component_refs) != len(components):
        raise SbomValidationError("SBOM components must each provide a bom-ref.")

    _require_dependency_graph(root_ref, component_refs, document)
    return document


def validate_sbom_file(
    path: Path,
    *,
    expected_spec: str,
    expected_name: str,
    expected_version: str,
    expected_purl: str | None = None,
) -> None:
    original_document_text = path.read_text()
    normalized_document = validate_sbom_document(
        original_document_text,
        expected_spec=expected_spec,
        expected_name=expected_name,
        expected_version=expected_version,
        expected_purl=expected_purl,
    )
    canonical_document_text = json.dumps(normalized_document, indent=2, sort_keys=True) + "\n"
    if canonical_document_text != original_document_text:
        path.write_text(canonical_document_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a Golden Rose CycloneDX SBOM.")
    parser.add_argument("sbom_path", type=Path)
    parser.add_argument("--spec", required=True, choices=sorted(SUPPORTED_SPECS))
    parser.add_argument("--name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--purl")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_sbom_file(
            args.sbom_path,
            expected_spec=args.spec,
            expected_name=args.name,
            expected_version=args.version,
            expected_purl=args.purl,
        )
    except OSError as exc:
        raise SystemExit("SBOM validation failed: unable to read file.") from exc
    except SbomValidationError as exc:
        raise SystemExit(f"SBOM validation failed: {exc}") from exc

    print("SBOM validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
