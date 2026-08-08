# Dependency purpose, license, and advisory review

- **Date:** 2026-08-07
- **Reviewer:** Hermes Agent
- **Owner:** Beatrice
- **Reviewed manifests and locks:** `pyproject.toml`, `uv.lock`, `apps/web/package.json`, `apps/web/package-lock.json`
- **Observed generation tools:**
  - frontend SBOM: `npm sbom --sbom-format cyclonedx --sbom-type application` under Node `22.22.3` / npm `10.9.8`
  - backend SBOM: `uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON` from `cyclonedx-bom==7.3.1`
  - backend validation library: `cyclonedx-python-lib[json-validation]==11.11.0`
- **Observed advisory checks at review time:**
  - `npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high --json` reported `0` vulnerabilities (`0` high / `0` critical)
  - `env -u PYTHONPATH uv run pip-audit --skip-editable --format=json` reported no known vulnerabilities
- **Scope note:** these audit results are point-in-time evidence only, not a permanent guarantee. Repeat this review whenever a manifest, lockfile, runtime version, or SBOM generation tool changes.

## Direct frontend dependencies

| Scope | Dependency | Version | Declared license | Bounded purpose |
| --- | --- | --- | --- | --- |
| runtime | `react` | `19.2.8` | MIT | Render the bounded staff workspace UI. |
| runtime | `react-dom` | `19.2.8` | MIT | Mount React UI into the browser DOM. |
| runtime | `react-router` | `8.3.0` | MIT | Staff-only client routing for the employer workspace. |
| dev | `@eslint/js` | `10.0.1` | MIT | ESLint baseline rules for frontend linting. |
| dev | `@testing-library/jest-dom` | `7.0.0` | MIT | DOM-focused matcher extensions for frontend tests. |
| dev | `@testing-library/react` | `16.3.2` | MIT | React rendering/query helpers for browser-surface tests. |
| dev | `@testing-library/user-event` | `14.6.3` | MIT | Higher-level synthetic user interaction helpers. |
| dev | `@types/node` | `22.20.1` | MIT | Type definitions for Node-based frontend tooling. |
| dev | `@types/react` | `19.2.18` | MIT | Type definitions for React. |
| dev | `@types/react-dom` | `19.2.4` | MIT | Type definitions for React DOM. |
| dev | `@vitejs/plugin-react` | `6.0.5` | MIT | Vite React transform/plugin support. |
| dev | `@vitest/coverage-v8` | `4.1.10` | MIT | V8-backed Vitest coverage provider. |
| dev | `axe-core` | `4.13.0` | MPL-2.0 | Automated accessibility audit engine used only in test qualification. |
| dev | `eslint` | `10.8.0` | MIT | Frontend lint runner. |
| dev | `eslint-plugin-react-hooks` | `7.1.1` | MIT | React Hooks lint rules. |
| dev | `eslint-plugin-react-refresh` | `0.5.3` | MIT | Fast Refresh safety lint rules. |
| dev | `jsdom` | `30.0.1` | MIT | Browser-like DOM runtime for Vitest. |
| dev | `typescript` | `5.9.3` | Apache-2.0 | TypeScript compiler and language services. |
| dev | `typescript-eslint` | `8.66.0` | MIT | TypeScript-aware ESLint integration. |
| dev | `vite` | `8.2.1` | MIT | Frontend build and dev/preview toolchain. |
| dev | `vitest` | `4.1.10` | MIT | Frontend test runner. |

## Direct backend dependencies

| Scope | Dependency | Version | Declared license | Bounded purpose |
| --- | --- | --- | --- | --- |
| runtime | `fastapi` | `0.141.1` | MIT | Staff API framework for create/search/detail routes. |
| runtime | `pydantic` | `2.13.4` | MIT | Request/response and domain validation primitives. |
| runtime | `pydantic-settings` | `2.14.2` | MIT | Environment-backed application settings. |
| runtime | `sqlalchemy` | `2.0.51` | MIT | ORM/session/DDL abstraction for PostgreSQL persistence. |
| runtime | `psycopg[binary]` | `3.3.4` | LGPL-3.0-only | PostgreSQL driver for backend runtime and migrations. |
| runtime | `alembic` | `1.19.0` | MIT | Schema migration runner. |
| runtime | `uvicorn` | `0.52.1` | BSD-3-Clause | Local/test ASGI serving. |
| dev | `bandit` | `1.9.4` | Apache-2.0 | Python static security analysis. |
| dev | `cyclonedx-bom` | `7.3.1` | Apache-2.0 | Backend CycloneDX SBOM generation. |
| dev | `cyclonedx-python-lib[json-validation]` | `11.11.0` | Apache-2.0 | Schema validation for backend and frontend SBOM review. |
| dev | `httpx` | `0.28.1` | BSD-3-Clause | HTTP client used by tests and tooling. |
| dev | `mypy` | `2.3.0` | MIT | Python type checking. |
| dev | `pip-audit` | `2.10.1` | Apache-2.0 | Python advisory scan. |
| dev | `pytest` | `9.1.1` | MIT | Python test runner. |
| dev | `pytest-cov` | `7.1.0` | MIT | Coverage reporting for pytest. |
| dev | `ruff` | `0.16.1` | MIT | Python formatting and linting. |

## Transitive license summary

### Frontend installed tree
Observed `243` installed frontend packages in `apps/web/node_modules`.

| License family | Count |
| --- | ---: |
| MIT | 193 |
| Apache-2.0 | 17 |
| ISC | 11 |
| BSD-2-Clause | 8 |
| BSD-3-Clause | 6 |
| MPL-2.0 | 3 |
| MIT-0 | 2 |
| BlueOak-1.0.0 | 1 |
| CC-BY-4.0 | 1 |
| CC0-1.0 | 1 |

### Python installed environment
Observed `86` installed Python distributions in the project `uv` environment. Installed metadata was dominated by permissive families (MIT, Apache, BSD), with additional MPL/LGPL entries and a small number of packages whose installed metadata did not normalize to a single SPDX-style identifier.

Representative observed counts from installed metadata:
- MIT family: `46`
- Apache family: `15`
- BSD family: `13`
- LGPL family: `3`
- MPL family: `3`
- PSF/PSFL family: `2`
- one package still reported license metadata as unspecified in the installed environment

## Notable license disposition

### LGPL
- **Direct runtime:** `psycopg[binary]==3.3.4` declared `LGPL-3.0-only`.
  - **Disposition:** accepted. It is the reviewed PostgreSQL adapter already required by the backend tracer; this closeout does not modify or redistribute the library itself.
- **Observed Python transitive:** `chardet==5.2.0` reported `LGPL`.
  - **Disposition:** accepted. It is a transitive utility dependency in the reviewed local tool environment, not custom-modified application code.

### MPL
- **Direct frontend dev:** `axe-core==4.13.0` declared `MPL-2.0`.
  - **Disposition:** accepted. It is a test-only accessibility engine used for local/CI qualification, not a Golden Rose runtime feature.
- **Observed frontend transitive:** `lightningcss@1.33.0`, `lightningcss-darwin-arm64@1.33.0` declared `MPL-2.0`.
  - **Disposition:** accepted. They are build-tool dependencies under Vite’s asset pipeline.
- **Observed Python transitive:** `certifi==2026.7.22`, `fqdn==1.5.1`, `pathspec==1.1.1` reported MPL-family metadata.
  - **Disposition:** accepted. They are supporting libraries/tools; no local modification or relicensing action is introduced by this branch.

### Creative Commons / data licenses
- **Observed frontend transitive:** `caniuse-lite@1.0.30001807` declared `CC-BY-4.0`; `mdn-data@2.27.1` declared `CC0-1.0`.
  - **Disposition:** accepted. These packages provide compatibility/reference data for build tooling, not Golden Rose business content or user data.

### Other notable families
- **Apache-2.0:** accepted across direct tooling (`typescript`, `bandit`, `cyclonedx-bom`, `cyclonedx-python-lib`, `pip-audit`) as standard permissive developer tooling.
- **BSD / ISC / BlueOak / MIT-0:** accepted as permissive transitive tooling/runtime licenses with no additional action required for this bounded local/test tracer.
- **GPL / AGPL:** none observed in the reviewed direct dependencies or the notable transitive subset gathered for this closeout task.

## Deprecation and advisory disposition

- `npm audit --audit-level=high` was clean at review time for the full locked frontend tree.
- `pip-audit --skip-editable` was clean at review time for the Python environment.
- No reviewed direct frontend dependency reported a package-level `deprecated` flag in installed metadata.
- `react-router@8.3.0` remains selected because:
  1. the reviewed audit run was clean at the configured severity;
  2. the current bounded employer workspace is already implemented and tested against the v8 route surface; and
  3. replacing the router in this closeout branch would create unapproved scope drift without a demonstrated security or compliance benefit.

## Re-run trigger

Repeat this review whenever any of the following change:
- `pyproject.toml`
- `uv.lock`
- `apps/web/package.json`
- `apps/web/package-lock.json`
- Node or npm runtime version
- Python runtime version
- SBOM generation or validation tooling
- audit tooling or configured severity gates
