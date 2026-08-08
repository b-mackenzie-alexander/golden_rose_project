# Review Handoff — Employer workspace post-merge closeout rereview

**Date:** 2026-08-08
**Branch:** `fix/employer-workspace-closeout`
**Target PR base:** `develop`
**Planning base / merge tip:** `origin/develop` at `b0a459b53241199df24f0b3c27d87198175d230d` (`docs: add employer workspace closeout plan (#14)`)
**Review surface:** local uncommitted working tree
**Ahead commits vs `origin/develop` at handoff creation:** `0`
**Behind commits vs `origin/develop` at handoff creation:** `0`
**PR status:** no PR yet; commit/push/PR-open remain blocked on this rereview

## 1. Current branch truth

This handoff covers the **exact uncommitted closeout working tree** only.

Observed live branch state at handoff creation:
- `git rev-parse HEAD` → `b0a459b53241199df24f0b3c27d87198175d230d`
- `git rev-parse origin/develop` → `b0a459b53241199df24f0b3c27d87198175d230d`
- `git rev-list --count origin/develop..HEAD` → `0`
- `git rev-list --count HEAD..origin/develop` → `0`

Interpretation:
- the remediation is **not** a committed PR range yet
- exact-range `origin/develop...HEAD` review is not meaningful yet
- review must target the **live working-tree diff** and current local evidence

## 2. Scope of this rereview

This rereview covers the bounded post-merge closeout authorized by:
- `docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md`
- `docs/adr/ADR-0006-phase-1-employer-workspace-post-merge-closeout.md`
- `.hermes/plans/2026-08-07_145911-phase-1-employer-workspace-closeout-plan.md`

It is limited to source-level/browser/runtime/database/CI/privacy closeout work for the already-merged synthetic/local Employer workspace.

It must confirm the lane did **not** widen into:
- draft Employer revision implementation
- adjacent entities or permissions
- real identity/session/auth
- deployment/GCP/runtime-serving expansion
- public routes or public data flows
- live/client data use
- human browser/manual accessibility/fluent-language claims

## 3. Primary files in the uncommitted review surface

### Browser / frontend
- `apps/web/src/app/App.tsx`
- `apps/web/src/app/App.test.tsx`
- `apps/web/src/browser/privacyLifecycle.ts`
- `apps/web/src/employers/EmployerWorkspace.tsx`
- `apps/web/src/employers/EmployerWorkspace.test.tsx`
- `apps/web/src/employers/EmployerCreateForm.tsx`
- `apps/web/src/employers/EmployerSearch.tsx`
- `apps/web/src/employers/EmployerDetail.tsx`
- `apps/web/src/api/employerClient.ts`
- `apps/web/src/api/employerClient.test.ts`
- `apps/web/src/i18n/messages.ts`
- `apps/web/src/i18n/LanguageProvider.test.tsx`
- `apps/web/src/test/setup.ts`
- `apps/web/src/test/valueSafeDiagnostics.ts`
- `apps/web/src/test/valueSafeDiagnostics.test.ts`
- `apps/web/vite.config.ts`

### Backend / database / runtime
- `src/golden_rose/main.py`
- `src/golden_rose/api/dependencies.py`
- `src/golden_rose/persistence/models.py`
- `migrations/versions/0002_enforce_command_authority_relationships.py`
- `tests/unit/test_main.py`
- `tests/unit/api/test_dependencies.py`
- `tests/integration/test_initial_migration.py`
- `tests/integration/api/test_staff_employers.py`
- `tests/integration/api/test_staff_employer_reads.py`

### SBOM / security / docs
- `scripts/validate_sbom.py`
- `tests/unit/test_sbom_validation.py`
- `.github/workflows/application-quality.yml`
- `docs/security/dependency-purpose-license-review.md`
- `README.md`
- `SECURITY.md`
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`

## 4. Observed findings, remediations, and local GREEN evidence

### Task 1 — repository truth / authority reconciliation
- **Finding:** living docs and ADR authority were stale after PR #13 merged and before closeout execution began.
- **Remediation:** recorded ADR-0006, marked the Task 12 handoff historical, and updated project-truth documents to establish `fix/employer-workspace-closeout` as the active remediation lane.
- **Primary files:** `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `docs/adr/ADR-0006-phase-1-employer-workspace-post-merge-closeout.md`, `docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md`, `docs/review-handoffs/2026-08-07-task12-application-gate-review-handoff.md`
- **Observed GREEN:** `git diff --check` passed after the Task 1 documentation set landed.

### Task 2 — database authority correspondence
- **Focused RED reason:** migration/test coverage exposed missing command-result/event integrity enforcement at the database layer.
- **Remediation:** added bidirectional composite authority relationships and Alembic migration `0002_enforce_command_authority_relationships.py`; a deferred receipt → creation-event FK plus the event → receipt/result FK now require exactly one matching creation event for every committed receipt/result pair. Expanded integration coverage rejects missing Employers, orphan receipts, mismatched events, and duplicate events, and proves a populated valid predecessor schema upgrades without data loss.
- **Primary files:** `src/golden_rose/persistence/models.py`, `migrations/versions/0002_enforce_command_authority_relationships.py`, `tests/integration/test_initial_migration.py`
- **Observed post-review GREEN:** focused migration/create qualification passed with `25 passed`; real PostgreSQL accepted valid create transactions, rejected orphan receipts at commit, preserved populated predecessor authority during upgrade, and completed trap-protected teardown.

### Task 3 — one-engine-per-app lifespan ownership
- **Focused RED reason:** unit tests proved engine/session ownership was request-scoped instead of app-lifespan-scoped.
- **Remediation:** `create_app()` now owns one SQLAlchemy engine per application lifespan and disposes deterministically at shutdown; request dependencies reuse the app-owned engine and close per-request sessions. Unit evidence now explicitly resumes each dependency generator through teardown and proves a request-level FastAPI override is entered and finalized without calling the real session path.
- **Primary files:** `src/golden_rose/main.py`, `src/golden_rose/api/dependencies.py`, `tests/unit/test_main.py`, `tests/unit/api/test_dependencies.py`, `tests/integration/api/test_staff_employers.py`, `tests/integration/api/test_staff_employer_reads.py`
- **Observed GREEN:** combined Task 3 verification passed with `33 passed` and one pre-existing warning.

### Task 4 — BFCache persisted-restore reload and late-completion invalidation
- **Focused RED reason:** production-route BFCache restore was not wired through the real route and stale create completions could repopulate state after `pagehide` reset.
- **Remediation:** added `apps/web/src/browser/privacyLifecycle.ts`, required real-route canonical reload wiring in `App.tsx`/`EmployerWorkspace.tsx`, and generation-based invalidation in `EmployerCreateForm.tsx`. Independent review found parent-state reset alone left a scheduler-dependent interval; the form now retires command authority synchronously on `pagehide`, and direct-form coverage proves a same-window completion cannot publish success or call `onCreateSuccess`.
- **Observed GREEN:** focused route/workspace verification passed with `40 passed`; typecheck and `git diff --check` also passed.

### Task 5 — retry/abandon mutual exclusion and authoritative-success precedence
- **Focused RED reason:** unknown-outcome retry and abandonment operations could race or stale-finally clear newer authoritative state.
- **Remediation:** `EmployerCreateForm.tsx` now uses synchronous authority-operation locking plus generation guards so retry and abandon are mutually exclusive and stale completions cannot regress authoritative success. A post-review regression also proves a late abandonment-search completion cannot restore recovery state after `pagehide`.
- **Observed GREEN:** focused node passed, then full Task 5 verification passed with `36 passed`, typecheck clean, and clean diff hygiene.

### Task 6 — bounded definitive create failure rendering in both locales
- **Focused RED reason:** validation and forbidden create failures lacked localized bounded guidance/focus/live-region structure.
- **Remediation:** added explicit localized failure copy in `apps/web/src/i18n/messages.ts`, parity assertions in `LanguageProvider.test.tsx`, and operation-specific failure-state handling in `EmployerCreateForm.tsx`.
- **Observed GREEN:** focused create tests passed, then full Task 6 verification passed with `40 passed`, typecheck clean, and clean diff hygiene.

### Task 7 — complete read/search/detail failure matrices
- **Focused RED/coverage target:** base-search conflict mapping, pagination failure preservation, and detail validation/conflict/unexpected handling across localized bounded states.
- **Remediation:** completed failure unions in `EmployerSearch.tsx` and `EmployerDetail.tsx`; added localized copy and preserved accepted-result behavior under pagination failure.
- **Observed GREEN:** focused selector ran as a GREEN regression (`4 passed`, `35 skipped`), and full Task 7 verification passed with `41 passed`, typecheck clean, and clean diff hygiene.

### Task 8 — RFC 3339 numeric-offset correctness and direct client matrices
- **Focused RED reason:** valid nonzero offset timestamps were rejected, and abort/cancellation/media-type/unreadable-body client paths were under-covered.
- **Remediation:** replaced UTC-roundtrip validation with calendar-before-offset validation, including backend-representable years `0001`–`0099`; hardened abort recognition during both fetch and response-body consumption; expanded direct client tests; and added focused file-level coverage enforcement in `apps/web/vite.config.ts`.
- **Observed GREEN:** direct client suite passed with `12 passed`; focused client coverage passed at `91.97%` statements / `91.13%` branches / `100%` functions / `95.74%` lines.

### Task 9 — value-independent diagnostics
- **Focused RED reason:** Testing Library failures still serialized DOM and leaked raw values such as names, UUIDs, and cursor-like tokens.
- **Remediation:** `apps/web/src/test/setup.ts` now overrides `getElementError()` to return a fixed privacy-safe message from `valueSafeDiagnostics.ts`; no DOM/value serialization remains in the failure path.
- **Observed GREEN:** focused privacy diagnostic test passed, then the full frontend suite passed with `61 passed`, typecheck clean, and clean diff hygiene.

### Task 10 — real SBOM validation and dependency disposition
- **Focused RED reason:** no repo-local validator existed, then real generated artifacts exposed frontend duplicate entries and backend missing-`dependsOn` quirks that the validator initially rejected.
- **Remediation:** added `scripts/validate_sbom.py`, `tests/unit/test_sbom_validation.py`, `.github/workflows/application-quality.yml` validator wiring, `docs/security/dependency-purpose-license-review.md`, and local README/SECURITY guidance. Before canonicalization, the validator rejects unknown dependency keys, malformed present `dependsOn`, exact duplicate components, and conflicting component identity/evidence. It canonicalizes only evidenced locked-generator duplicate-edge/omitted-list/component-property quirks, strict-validates the complete canonical document, then performs Golden Rose identity/tool/resolvable-graph checks.
- **Observed post-review GREEN:** `tests/unit/test_sbom_validation.py` passed with `23 passed`; freshly generated frontend and backend SBOMs both passed the hardened validator in exact CI order.

### Independent rereview remediation round
- **Frontend High remediated:** command generation is retired synchronously in the form's `pagehide` listener before any parent reset effect; exact RED → GREEN evidence proves late success cannot publish or invoke the success callback.
- **Frontend Mediums remediated:** abandonment-search completions check generation before state writes; response-body `AbortError` remains a silent cancellation; early valid RFC 3339 years are accepted; and the premature next-slice planning handoff was excluded from this closeout surface.
- **Backend Medium remediated:** receipt/Employer/event correspondence is bidirectional and commit-time enforced through a deferred cyclic FK pair with exact unique targets.
- **Backend Lows remediated:** populated predecessor upgrade, cleanup assertion placement, deterministic generator finalization, and request-level dependency override coverage are explicit.
- **CI/SBOM probe finding remediated:** malformed dependency lists and conflicting component identity/evidence fail closed; otherwise-identical npm component properties merge deterministically and exact generator quirks remain narrowly canonicalized.
- **Gate boundary:** these amendments require independent focused rereview, then a commit followed by the complete final-head application gate and exact committed-range Gitleaks scan. No pre-commit result is represented as final-head evidence.

### Task 11 — non-service gate closeout
- **Focused RED reason:** the first non-service closeout gate surfaced live lint/type/style issues in the working tree, including an unused timestamp-regex capture in `employerClient.ts`, Ruff findings in the validator/tests, and test typing/exception granularity issues.
- **Remediation:** removed the unused capture, tightened request/session typing, simplified nested `with` structure, replaced blind `Exception` assertions with SQLAlchemy-specific exceptions, and formatted touched Python files.
- **Observed historical pre-review GREEN:**
  - `npm --prefix apps/web run verify` passed
  - `npm --prefix apps/web ls --all` passed
  - `npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high` found `0 vulnerabilities`
  - `env -u PYTHONPATH uv lock --check`, Ruff format/check, mypy, Bandit, `pytest tests/unit -v`, and `pip-audit --skip-editable` all passed
  - observed counts at that point: lockfile validator `24 passed`; frontend suite `61 passed`; frontend coverage `94.94% / 92.78% / 97.87% / 95.98%`; backend unit suite `72 passed`; mypy checked `45` source files
- **Observed latest post-review pre-commit GREEN:** frontend suite `64 passed` with `95.06% / 92.67% / 97.93% / 96.08%` coverage; backend unit suite `78 passed`; SBOM validator suite `23 passed`; Ruff, mypy, Bandit, both freshly generated SBOM validators, and `git diff --check` passed.

### Task 12 — historical pre-review application gate with teardown
- **Prerequisite honored:** approved loopback-only disposable `postgres-test` was started with `.env.test` kept unread/hidden.
- **Observed runtime start:** `docker compose --env-file .env.test ps postgres-test` showed `127.0.0.1:55432->5432/tcp`; health reached `healthy`.
- **Observed historical workflow order:** lockfile validator self-test and real validation → `npm ci --ignore-scripts` → frontend verify/tree/audit/SBOM → backend lock/sync/Ruff/mypy/Bandit → Alembic upgrade → full pytest coverage → downgrade → upgrade → `pip-audit` → backend SBOM generation → frontend/backend validator calls → `git diff --check`.
- **Observed GREEN results:** full suite `129 passed`; backend coverage `96.90%`; `npm audit` found `0 vulnerabilities`; `pip-audit --skip-editable` found no known vulnerabilities; frontend and backend SBOM validation both passed.
- **Observed teardown:** `docker compose --env-file .env.test down` removed the container and network, and `docker compose --env-file .env.test ps -a` returned an empty service list.
- **Current exact committed-head gate definition:** runtime/registry/ignore-scripts assertions → lockfile self-test and real validation → backend `uv lock --check`/`uv sync --locked --all-groups` → `npm ci --ignore-scripts` → frontend verify/tree/audit/SBOM → immediate frontend SBOM validation → Ruff/mypy/Bandit → Alembic upgrade → full pytest coverage → downgrade → upgrade → `pip-audit` → backend SBOM generation/validation → `git diff --check`. This matches `.github/workflows/application-quality.yml` and the amended Task 12 sequence in the controlling closeout plan.

## 5. Current local verification evidence

### Historical pre-review full application gate
Observed passing sequence and results before independent-review amendments:
- loopback-only PostgreSQL health-checked on `127.0.0.1:55432`
- lockfile self-test: `24 passed`
- frontend verify suite: `61 passed`
- frontend coverage: `94.94%` statements / `92.78%` branches / `97.87%` functions / `95.98%` lines
- frontend `npm audit --audit-level=high`: `0 vulnerabilities`
- backend full pytest suite: `129 passed`
- backend total coverage: `96.90%`
- mypy: `Success: no issues found in 45 source files`
- Bandit: passed
- `pip-audit --skip-editable`: `No known vulnerabilities found`
- frontend SBOM validator: passed (CycloneDX `1.5`, `web`, version `0.0.0`, expected purl)
- backend SBOM validator: passed (CycloneDX `1.6`, `golden-rose`, version `0.1.0`)
- migration reversibility proof: `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` passed
- teardown proof: `docker compose ... down` followed by empty `ps -a`

### Latest post-review pre-commit focused evidence
Observed passing sequence and results:
- frontend verify/tree/audit: passed with `64 passed`
- frontend coverage: `95.06%` statements / `92.67%` branches / `97.93%` functions / `96.08%` lines
- backend no-service quality/security/unit gate: passed with `78 passed`
- SBOM validator suite: `23 passed`
- freshly generated frontend and backend SBOM validators: passed
- focused PostgreSQL migration/create qualification: `25 passed` with empty-service teardown
- populated predecessor cleanup-order rerun: `1 passed` with empty-service teardown
- Ruff, mypy on `45` source files, Bandit, and `git diff --check`: passed
- these remain pre-commit results; Task 14 requires the complete current Task 12 sequence on the exact committed head

### Warnings preserved honestly
- frontend jsdom/axe runs still emit `Not implemented: HTMLCanvasElement's getContext() method`
- backend tests still emit the pre-existing `StarletteDeprecationWarning` from `fastapi.testclient`

## 6. Deferred truths that must remain explicit

The rereview must confirm the docs and any future PR text do **not** overclaim:
- **human browser/manual accessibility/fluent-language qualification has not occurred**
- those human gates activate only after a shared deployed `develop` environment exists
- runtime-role immutability is not yet qualified
- production connection-pool sizing/load behavior is not yet qualified
- no GCP/deployment/runtime-hosting work is included here
- no live/client data use is included here
- the draft Employer revision slice is the next planning candidate only and is **not** part of this closeout

## 7. Secret-scan posture at this handoff

- Exact committed-range Gitleaks has **not** been rerun for this closeout surface because there are still `0` commits ahead of `origin/develop`.
- Per the closeout plan, no whole-directory secret scan should be run against the live working tree because ignored local credential files must not be swept.
- Exact PR-range `gitleaks git --log-opts='origin/develop..HEAD'` remains a **Task 14** requirement after this rereview clears and the remediation is committed.

## 8. Required alternate-session rereview focus

The alternate review session must explicitly verify:
1. production-route BFCache wiring and canonical reload through the real route
2. late create completion invalidation after page reset/pagehide
3. unknown retry / abandonment mutual exclusion and authoritative-success precedence
4. complete create/search/pagination/detail failure mappings in both English and Spanish
5. direct client status/media-type/malformed-body/cancellation/network/abort matrices, including RFC 3339 numeric-offset handling
6. database FK/composite/unique integrity and preserved create-path concurrency/idempotency behavior
7. one-engine-per-app lifecycle ownership, per-request session closure, and deterministic disposal
8. value-independent Testing Library diagnostics with no DOM/value leakage
9. real SBOM validation and dependency purpose/license/deprecation disposition
10. living-doc truth, including explicit non-claims about human review, runtime immutability/load, GCP, live data, and next-slice authorization

## 9. Reviewer decision rules

- Any **High** or **Blocker** finding blocks commit/push/PR preparation.
- Every **Medium** must be either remediated in this working tree or explicitly documented with rationale, owner, and Beatrice's acceptance before PR preparation.
- An undisposed Medium also blocks PR preparation.

## 10. Final local review-surface verification at handoff creation

Observed commands:

```bash
git status --short --branch
git diff --stat
git diff --check
```

Observed truth:
- branch: `fix/employer-workspace-closeout`
- review surface: **uncommitted working tree**
- `git diff --check`: passed
- diff summary at handoff creation: `35 files changed, 2230 insertions(+), 720 deletions(-)`

The next session should review the live diff, not a commit range.

## 11. Final rereview disposition

- Focused frontend rereview: ACCEPT, no residual findings.
- Focused backend/database rereview: ACCEPT, no residual findings after cleanup-order remediation.
- Focused CI/SBOM/documentation delta rereview: ACCEPT, no residual findings after provenance, workflow-order, current-evidence, newline, and locked-generator compatibility reconciliation.
- Overall disposition: this exact uncommitted surface is cleared to stage and commit. Complete Task 12 on the exact committed head and scan exactly `origin/develop..HEAD` with Gitleaks before push/PR/merge.
