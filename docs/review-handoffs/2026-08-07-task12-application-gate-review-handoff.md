# Review Handoff — Task 12 application gate extension

**Date:** 2026-08-07
**Branch:** `feat/staff-employer-workspace`
**Target PR base:** `develop`
**Planning base:** `origin/develop` at merged planning tip `b06923a` (`docs: accept employer workspace planning packet (#12)`)
**Review surface:** local uncommitted working tree
**Ahead commits vs `origin/develop` at handoff creation:** `0` (`git rev-list --count origin/develop..HEAD`)
**PR status:** no PR yet; review/remediation must complete before any commit/push/PR-open step

## Update — remediation round after independent review

Independent review returned **Changes requested** on the local uncommitted working tree and identified three frontend safety-boundary issues:
- **High:** unknown/conflict create abandonment cleared immutable create authority before the required search completed successfully
- **Medium:** pending create requests did not register the generic `beforeunload` warning
- **Medium:** superseded/unmounted detail reads were invalidated in state but not actually aborted at the fetch boundary

Those findings are now remediated in this same working tree:
- `apps/web/src/employers/EmployerCreateForm.tsx` now keeps unknown/conflict attempts frozen until the follow-up search returns an accepted usable result, preserves bounded retry guidance on failed abandonment search, and warns on `beforeunload` while create is pending or unknown.
- `apps/web/src/api/employerClient.ts` now accepts an optional detail-read abort signal.
- `apps/web/src/employers/EmployerSearch.tsx` now aborts the active detail read on superseding selection, filter edit, reset/pagehide path, new base search, and unmount.
- `apps/web/src/employers/EmployerWorkspace.test.tsx` and `apps/web/src/api/employerClient.test.ts` now cover the remediated behaviors.

This packet therefore supersedes the earlier pre-review version and should be used for the **independent re-review**.

## 1. Scope of this handoff

This handoff covers **Task 12 only**: extending the existing required `application` CI gate in place so it qualifies the frontend and backend together without introducing a second required check.

The slice now includes the approved router mitigation needed to satisfy the frontend audit gate:
- original planned dependency `react-router-dom@7.18.2` failed `npm audit --audit-level=high`
- no published `react-router-dom@8.3.0` package exists on npm
- the branch now uses `react-router@8.3.0` directly for the same bounded declarative surface actually used by this tracer

## 2. Review surface and caveats

This is an **uncommitted working tree**, not a committed PR candidate yet.

Observed live state:
- branch: `feat/staff-employer-workspace`
- `HEAD` equals `origin/develop`: `b06923aa9899c66935c35f06d8880cfa17ad0d89`
- `git rev-list --count origin/develop..HEAD`: `0`
- `git diff --check`: clean
- `gitleaks git --log-opts='origin/develop..HEAD'`: `0 commits scanned`, `no leaks found`

Interpretation:
- exact-range PR hygiene is **not yet meaningful** because nothing is committed ahead of `origin/develop`
- substantive review must target the **live working tree diff**, not `origin/develop...HEAD`

## 3. Primary files changed for Task 12

### Production / CI / dependency surface
- `.github/workflows/application-quality.yml`
- `apps/web/package.json`
- `apps/web/package-lock.json`
- `apps/web/eslint.config.js`
- `apps/web/vite.config.ts`
- `apps/web/src/app/App.tsx`
- `apps/web/src/app/AppShell.tsx`
- `apps/web/src/api/employerClient.ts`
- `apps/web/src/employers/EmployerCreateForm.tsx`
- `apps/web/src/employers/EmployerSearch.tsx`
- `pyproject.toml`
- `uv.lock`

### Test coverage added / updated
- `apps/web/src/api/employerClient.test.ts`
- `apps/web/src/app/App.test.tsx`
- `apps/web/src/app/AppShell.test.tsx`
- `apps/web/src/employers/EmployerWorkspace.test.tsx`
- `apps/web/src/i18n/LanguageProvider.test.tsx`
- `tests/integration/api/test_staff_employers.py`
- `tests/unit/api/test_employer_schemas.py`

### Living docs / evidence
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md`

## 4. What changed

### A. Existing required `application` workflow widened in place
`.github/workflows/application-quality.yml` now keeps the existing backend ordering and adds the frontend gate in the same required job:
- pinned `actions/setup-node`
- exact Node/npm/config assertions
- lockfile validator self-test and real lockfile validation
- `npm ci --ignore-scripts`
- frontend `verify`
- frontend tree inspection via `npm ls --all`
- frontend `npm audit --audit-level=high`
- frontend CycloneDX generation/validation and separate artifact upload
- preserved backend lock/sync/lint/type/security/migration/test/audit/SBOM flow

### B. Frontend parity fixes surfaced by the widened gate
The widened workflow exposed repo-level frontend issues that had to be fixed for real parity:
- ESLint flat-config scope corrections for TS-vs-JS config files
- Vitest coverage include/exclude cleanup so lockfile validator tests remain separate from app coverage
- targeted frontend lint/type/test fixes in employer workspace and client files

### C. Router mitigation
The branch no longer depends on `react-router-dom@7.18.2`.

Mitigation now applied:
- `apps/web/package.json` / `apps/web/package-lock.json` pin `react-router@8.3.0`
- imports switched from `react-router-dom` to `react-router`
- only the already-approved declarative symbols are used: `BrowserRouter`, `NavLink`, `Routes`, `Route`, `Navigate`, `Outlet`, `MemoryRouter`

### D. Backend SBOM parity fix
- `pyproject.toml` now includes `cyclonedx-python-lib[json-validation]==11.11.0`
- `uv.lock` refreshed accordingly
- this was required to make backend CycloneDX validation pass in the real CI-order path

## 5. Explicit non-scope still preserved

Reviewer should confirm this slice did **not** add:
- a second required GitHub status/check
- new backend API schema or permission surface beyond the already-approved create-success `no-store` hardening and the earlier Task 12 backend test/doc touchpoints
- identity/session/auth changes
- public routes, hosting, deployment, or cloud/runtime expansion
- browser persistence, analytics, third-party runtime recipients, or relaxed privacy posture
- new product routes beyond the existing `/` redirect and `/employers` workspace boundary

## 6. Observed local verification evidence

## Frontend-focused parity evidence
Observed passing commands/results:

```bash
npm --userconfig apps/web/.npmrc install --package-lock-only --ignore-scripts --prefix apps/web
npm --prefix apps/web run verify
npm --prefix apps/web ls --all
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
```

Observed outcome:
- `npm audit --audit-level=high`: `found 0 vulnerabilities`
- frontend tests: `46 passed`
- frontend coverage:
  - statements `90.54%`
  - branches `86.06%`
  - functions `97.72%`
  - lines `93.77%`
- production build passed
- frontend SBOM validated:
  - path: `build/frontend-sbom.cdx.json`
  - `bomFormat: CycloneDX`
  - `specVersion: 1.5`

## Focused remediation evidence after the review verdict
Observed passing commands/results:

```bash
npm --prefix apps/web run lint
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx src/api/employerClient.test.ts
npm --prefix apps/web run verify
docker compose --env-file .env.test up -d postgres-test
# health wait
set -a && source .env.test && set +a
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py -k 'Cache_Control or no_store or replay'
docker compose --env-file .env.test down
git diff --check
```

Observed outcome:
- focused frontend rerun: `42 passed`
- `npm --prefix apps/web run verify`: passed again end-to-end
- updated frontend coverage:
  - statements `91.05%`
  - branches `86.85%`
  - functions `97.8%`
  - lines `94.12%`
- targeted backend regression: `2 passed, 11 deselected`
- `git diff --check`: clean

## Full canonical local `application` parity evidence
Observed passing end-to-end sequence in workflow order with approved local PostgreSQL service:

```bash
docker compose --env-file .env.test up -d postgres-test
# health wait
node --test apps/web/scripts/validate-lockfile.test.mjs
node apps/web/scripts/validate-lockfile.mjs apps/web/package-lock.json
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
npm --prefix apps/web run verify
npm --prefix apps/web ls --all
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv sync --locked --all-groups
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
set -a && source .env.test && set +a
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95
env -u PYTHONPATH uv run alembic downgrade base
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pip-audit --skip-editable
env -u PYTHONPATH uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
git diff --check
docker compose --env-file .env.test down
```

Observed outcome:
- backend tests: `101 passed`
- backend total coverage: `96.81%`
- `pip-audit --skip-editable`: no known vulnerabilities
- backend SBOM validated:
  - path: `build/backend-sbom.cdx.json`
  - `bomFormat: CycloneDX`
  - `specVersion: 1.6`
- final `git diff --check`: clean
- approved `postgres-test` service was torn down after verification

## 7. Reviewer focus areas

Prioritize these trust-boundary questions:

1. **workflow-shape integrity** — the existing required `application` job was widened in place, not replaced with parallel required checks
2. **truthful CI lifecycle/order** — service-first lifecycle remains accurate and consistent with the job-level PostgreSQL service model
3. **frontend supply-chain mitigation** — replacing `react-router-dom@7.18.2` with `react-router@8.3.0` is the narrowest approved path and does not widen the product/runtime boundary
4. **router-surface drift** — confirm the branch still uses only the approved single-route declarative browser surface
5. **frontend privacy posture** — no browser persistence, URL-carried state, remote assets, telemetry, or reflected diagnostic leakage were introduced while fixing parity
6. **backend SBOM fix minimality** — `cyclonedx-python-lib[json-validation]` addition is the narrowest deterministic remedy for the CI SBOM validation failure
7. **doc/ADR alignment** — living docs and ADR-0005 now truthfully describe the accepted mitigation and current next step: independent review before PR
8. **working-tree caveat discipline** — no claim in the packet should treat `0` ahead commits as final PR-range proof

Any **High** or **Blocker** finding should block commit/push/PR preparation.

## 8. Range-hygiene caveats

Commands run:

```bash
git rev-list --count origin/develop..HEAD
git diff --check
/opt/homebrew/bin/gitleaks git --no-banner --redact --log-opts='origin/develop..HEAD'
```

Observed results:
- `git rev-list --count origin/develop..HEAD`: `0`
- `git diff --check`: clean
- Gitleaks: `0 commits scanned`, `no leaks found`

Interpretation:
- these are **working-tree readiness caveats**, not final PR-range proof
- after review remediation and closeout commit, final-head verification must be rerun on the actual immutable review range before push/PR

## 9. Stop boundary before PR open

Do **not** open a PR from this handoff state yet.

Required next sequence:
1. independent **re-review** of the remediated local working tree using this updated packet
2. clear any remaining findings
3. rerun final-head verification on the exact post-remediation committed head
4. push branch
5. only then open the PR against `develop`
