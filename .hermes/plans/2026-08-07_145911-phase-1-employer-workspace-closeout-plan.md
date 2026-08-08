# Phase 1 Employer Workspace Post-Merge Closeout Implementation Plan

> **For Hermes:** Use `plan-driven-tdd-execution`, `test-driven-development`, `audit-remediation-and-rereview`, and `living-doc-slice-hygiene` to execute this plan in strict task order. Do not begin the draft-Employer revision slice from this branch.

**Goal:** Close the evidence-backed PR #13 Employer-workspace defects, harden its authority/runtime/privacy/supply-chain boundaries, and reconcile project truth before the next Phase 1 slice is planned for implementation.

**Architecture:** Preserve the existing synthetic/local staff-only create/search/detail product boundary. Add one forward-only authority-integrity migration, move SQLAlchemy engine ownership to FastAPI lifespan, harden browser authority and BFCache state transitions, complete operation-specific frontend failure handling, validate the existing RFC 3339 and SBOM contracts correctly, and make test diagnostics value-independent. Update repository and Obsidian status so automated evidence is distinguished from human qualification that becomes mandatory only after a shared `develop` environment is deployed.

**Tech Stack:** Python 3.12, uv, FastAPI, synchronous SQLAlchemy 2, psycopg 3, Alembic, PostgreSQL 16, pytest; Node.js 22.22.3, npm 10.9.8, React 19, TypeScript 5.9, Vite 8, Vitest, Testing Library, axe-core; GitHub Actions and CycloneDX 1.5/1.6.

---

## 1. Authoritative baseline

- **Repository:** `b-mackenzie-alexander/golden_rose_project`
- **Integration base:** `origin/develop`
- **PR #13 merge commit:** `f8236e6ce32cd97d7398c1ba7052db1b2a23d088`
- **PR #13 implementation head:** `9910895bce9f299fc2f16f0460cf30871532a48e`
- **Planning branch:** `fix/employer-workspace-closeout`
- **Rebaseline evidence:** local `develop` was fast-forwarded to `f8236e6`; the retired `feat/staff-employer-workspace` tree was proven equal to the merge tree before the new branch was created.
- **Current working-tree intent:** this plan file only. No remediation code, migration, service, deployment, commit, push, or PR is authorized merely by writing the plan.

## 2. Finding disposition agreed with Beatrice

| Item | Classification | Closeout disposition |
|---|---|---|
| Human browser, manual accessibility, and fluent English/Spanish qualification | Future qualification gate; prior documentation overclaimed timing | Move to the deployed-`develop` qualification stage. Record that it has not happened. Automated parity/accessibility evidence remains valid but is not human validation. |
| Production BFCache canonical reload is unwired; late asynchronous completions can repopulate reset state | Immediate source-level privacy/authority defect | Remediate now and prove through production-route and late-completion tests. Human browser BFCache validation remains deferred. |
| Concurrent unknown-outcome retries can race and regress authoritative success to unknown | High browser-authority defect | Remediate now with mutual exclusion and generation protection while preserving reuse of the original command ID. |
| Definitive create validation/forbidden failures are silent | Immediate frontend correctness defect | Add localized, accessible operation-specific states and direct tests. |
| Search/detail/pagination contract-defined failures can disappear | Immediate frontend correctness/recovery defect | Complete the bounded failure union, localized rendering, focus behavior, and preserved-results pagination behavior. |
| Receipt/Employer/event correspondence is not fully database-enforced | Immediate authority-spine integrity defect | Add forward migration, matching SQLAlchemy metadata, and live PostgreSQL rejection tests. |
| Runtime role can still `TRUNCATE` or modify DDL/triggers | Deployment-readiness boundary | Do not overclaim production immutability. Defer runtime/migration-owner role separation and denial tests until a deployed database role model exists. |
| Valid RFC 3339 numeric offsets are rejected | Immediate transport-contract defect | Correct calendar/offset validation and add valid/invalid direct client tests. |
| SBOM checks are structural stubs; license/purpose/deprecation disposition is absent | Immediate evidence-integrity gap; no vulnerable dependency observed | Strengthen schema/identity/graph/tool validation and persist a bounded dependency review. |
| Test diagnostics serialize DOM and depend on sentinel naming for redaction | Immediate privacy hardening | Make CI diagnostics value-independent and regression-test arbitrary synthetic values. |
| A new SQLAlchemy engine/pool is created per request | Observed lifecycle flaw; exact load impact unmeasured | Move engine ownership to FastAPI lifespan, reuse it for request sessions, and dispose it on shutdown. Pool sizing/load tests remain deployment work. |
| Repository and Obsidian status are materially stale | Immediate workflow/evidence-integrity defect | Reconcile before next-slice planning; preserve historical evidence without pretending deferred human review occurred. |

## 3. Hard scope boundaries

### In scope

- Existing Employer create/search/detail browser and API contracts only.
- Browser authority, privacy lifecycle, error recovery, parser correctness, test-log safety, and focused coverage.
- Existing `Employer`, `CommandReceipt`, and `AuditEvent` authority correspondence only.
- FastAPI/SQLAlchemy application lifecycle ownership without production pool tuning.
- Existing frontend/backend SBOM generation and dependency evidence.
- Repository and Obsidian truth reconciliation.

### Out of scope

- Draft Employer revision, new permissions, `updated_at`/`updated_by`, or expected-version update commands.
- EmployerContact, Worksite, StaffingRequest, ShiftNeed, map, queue, calendar, or audit-timeline UI.
- Real identity, sessions, MFA, public routes, client/live data, uploads, integrations, legal behavior, exports, matching, ranking, or referral decisions.
- GCP provisioning, frontend/backend deployment, production roles, production connection-pool sizing, load testing, or live browser qualification.
- Runtime-role `TRUNCATE`/DDL/trigger privilege enforcement before a real deployment role exists.
- Human linguistic approval, manual accessibility conformance, or client acceptance before deployed `develop` exists.

Any apparent need to widen these boundaries stops execution and returns to planning.

## 4. Execution rules

1. Follow the tasks below in exact order.
2. For every code or migration task: add one focused failing regression, run it and record the honest RED, implement only that node, then run focused GREEN before continuing.
3. An immediate pass must be classified as a harness-only RED or regression reclassification; do not fabricate a RED.
4. Do not start PostgreSQL, FastAPI, Vite, Docker, or a browser without separate explicit approval for the exact service-backed task.
5. Use fictional synthetic values only. Do not print or persist Employer names, command IDs, cursors, API bodies, database URLs, or SQL parameters in evidence.
6. Do not commit, push, open a PR, or update Obsidian until explicitly approved for that operation.
7. Any High/Blocker finding during implementation or rereview blocks PR preparation. Every Medium finding must be remediated or explicitly documented with its rationale, owner, and Beatrice's acceptance before PR preparation; an undisposed Medium also blocks PR preparation.
8. Final-head evidence must be generated after all code/docs are committed; any later commit invalidates it.

---

### Task 1: Establish honest post-merge project state and closeout authority

**Objective:** Make the repository state truthful before remediation code begins and record the accepted distinction between immediate defects and post-deployment human qualification.

**Files:**
- Create: `docs/adr/ADR-0006-phase-1-employer-workspace-post-merge-closeout.md`
- Modify: `docs/adr/README.md`
- Modify: `docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md`
- Modify: `.hermes/plans/2026-08-06_115420-phase-1-employer-workspace-frontend-plan.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`
- Modify: `SECURITY.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `docs/review-handoffs/2026-08-07-task12-application-gate-review-handoff.md`
- Modify: `NOTES.md`

**Step 1: Record the post-merge closeout decision**

ADR-0006 must state:

- PR #13 merged the local/synthetic workspace at `f8236e6` but independent post-merge review found closeout defects.
- The closeout may change browser/runtime/database/CI behavior only as enumerated here.
- No next-slice domain expansion is authorized.
- Automated English/Spanish catalog parity, jsdom behavior, and axe checks are existing machine evidence.
- Human browser, manual accessibility, contrast/zoom/reflow/reduced-motion, and fluent-language review have not occurred and are not possible against a shared target yet.
- Those human gates activate after a shared `develop` deployment exists and block promotion/client acceptance, not current local implementation.
- BFCache wiring and late-state invalidation remain immediate code defects despite deferred human proof.
- Runtime-role immutability and pool sizing remain deployment-readiness gates.

**Step 2: Preserve historical plan evidence without rewriting history**

Add a dated post-merge disposition section near the top of the prior frontend plan. Do not erase its original task sequence. Explicitly reclassify the human portions of Tasks 13–16 as deferred to deployed-`develop` qualification and state that no repository evidence claims they ran. Link ADR-0006 for the accepted correction.

**Step 3: Reconcile active state surfaces**

Update living docs to say:

- PR #13 is merged into protected `develop` at `f8236e6`.
- The retired feature branch is historical.
- `fix/employer-workspace-closeout` is the planned remediation lane.
- The workspace is implemented but not fully closeout-qualified.
- Approved immediate findings are listed without overstating unexecuted remediation.
- The next product candidate is draft Employer revision, but its implementation planning begins only after closeout merges.

Mark the Task 12 handoff as historical/superseded review evidence; retain its original observed commands and results.

**Step 4: Verify documentation hygiene**

Run:

```bash
git diff --check
```

Expected: PASS with no whitespace errors. No service starts.

---

### Task 2: Enforce receipt → Employer → creation-event authority correspondence

**Objective:** Make PostgreSQL reject individually valid but mutually inconsistent receipt/entity/event rows without changing ordinary create semantics.

**Files:**
- Create: `migrations/versions/0002_enforce_command_authority_relationships.py`
- Modify: `src/golden_rose/persistence/models.py`
- Modify: `tests/integration/test_initial_migration.py`
- Regression: `tests/integration/application/test_create_draft_employer.py`
- Regression: `tests/integration/api/test_staff_employers.py`

**Step 1: Add the live-schema RED nodes**

Add focused tests that require:

1. named FK `fk_command_receipts_result_employer` from `command_receipts.result_entity_id` to `employers.employer_id`, with both live-schema inspection and SQLAlchemy metadata assertions proving `DEFERRABLE INITIALLY DEFERRED`;
2. named unique constraint `uq_command_receipts_command_result` over `(command_id, result_entity_id)`;
3. named composite FK `fk_audit_events_command_result` from `(command_id, entity_id)` to `(command_receipts.command_id, command_receipts.result_entity_id)`;
4. named unique constraint `uq_audit_events_command_event_type` over `(command_id, event_type)`;
5. receipt insertion naming a nonexistent Employer fails at transaction commit;
6. an event pairing one valid command with a different valid Employer fails;
7. a duplicate `employer.created` event for one command fails;
8. one valid receipt/Employer/event transaction still commits.

Because the authoritative writer reserves the command before inserting the Employer, the receipt-to-Employer FK must be `DEFERRABLE INITIALLY DEFERRED`; otherwise the existing concurrency-safe write order would be broken.

**Step 2: Run focused RED with separately approved PostgreSQL**

After explicit service approval and migration to the current pre-change head, source the ignored synthetic test environment in the current shell before every Task 2 Alembic/pytest command. Do not print `.env.test` or the resulting database URL:

```bash
set -a && source .env.test && set +a
env -u PYTHONPATH uv run pytest \
  tests/integration/test_initial_migration.py::test_live_schema_exposes_authority_relationships \
  tests/integration/test_initial_migration.py::test_receipt_requires_its_result_employer \
  tests/integration/test_initial_migration.py::test_audit_event_command_must_name_receipt_result \
  tests/integration/test_initial_migration.py::test_create_command_rejects_duplicate_creation_event -v
```

Expected: FAIL because migration 0002 and metadata constraints do not exist.

**Step 3: Implement the forward migration and metadata parity**

- Add the deferrable receipt-result FK.
- Add the receipt composite unique key required by PostgreSQL for the composite reference.
- Add the composite event-to-receipt-result FK.
- Add bounded duplicate event prevention.
- Match names in SQLAlchemy metadata and assert the receipt-result FK's exact `deferrable=True` and `initially="DEFERRED"` settings.
- Downgrade in reverse dependency order.
- Do not alter existing columns, command type/schema, event payload, create status/body, or transaction order.

**Step 4: Run focused GREEN and existing authority regressions**

Run in the same shell where the required synthetic database environment was sourced:

```bash
env -u PYTHONPATH uv run alembic upgrade head
env -u PYTHONPATH uv run pytest tests/integration/test_initial_migration.py -v
env -u PYTHONPATH uv run pytest tests/integration/application/test_create_draft_employer.py -v
env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py -v
```

Expected: PASS. Identical replay still persists exactly one receipt, Employer, and creation event; conflicts remain redacted and write-free.

**Step 5: Prove migration reversibility**

Run in the same shell where the required synthetic database environment was sourced:

```bash
env -u PYTHONPATH uv run alembic downgrade 0001
env -u PYTHONPATH uv run alembic upgrade head
```

Expected: PASS. Do not claim runtime-role protection from `TRUNCATE`, DDL, or trigger changes.

---

### Task 3: Move database engine ownership to FastAPI lifespan

**Objective:** Create one application-owned SQLAlchemy engine/pool, reuse it for request sessions, and dispose it deterministically at shutdown.

**Files:**
- Modify: `src/golden_rose/main.py`
- Modify: `src/golden_rose/api/dependencies.py`
- Modify: `src/golden_rose/database.py` only if a narrow engine-factory protocol/helper is needed
- Modify: `tests/unit/test_main.py`
- Create or modify: `tests/unit/api/test_dependencies.py`
- Modify: all API integration tests that instantiate `TestClient` without entering its lifespan context, including:
  - `tests/integration/api/test_staff_employers.py`
  - `tests/integration/api/test_staff_employer_reads.py`

**Step 1: Add lifecycle RED nodes**

Require tests that prove:

- `create_app()` still rejects production + synthetic auth before serving or opening a database engine;
- entering application lifespan calls the engine factory exactly once;
- multiple request sessions use the same application-owned engine;
- each request closes its `Session`;
- application shutdown calls `engine.dispose()` exactly once;
- startup engine-factory failure prevents serving and does not leave partial app state;
- dependency overrides remain usable in tests.

**Step 2: Run unit RED**

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_main.py tests/unit/api/test_dependencies.py -v
```

Expected: FAIL because `get_db_session()` currently creates a new engine per request and no lifespan owns disposal.

**Step 3: Implement minimal lifecycle ownership**

- Keep `Settings()` validation in `create_app()` so invalid production auth fails before lifespan.
- Add a FastAPI lifespan context that creates the engine once, stores it on `app.state`, yields, and disposes in `finally`.
- Let the app factory accept a narrow engine-factory injection seam for deterministic tests; production uses `create_database_engine`.
- Change `get_db_session()` to receive `Request`, read the application-owned engine, and open/close only a request-scoped `Session`.
- Use `with TestClient(app)` wherever the real lifecycle is required.
- Do not tune pool size, timeout, recycling, or production health checks in this slice.

**Step 4: Run focused GREEN and API regressions**

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_main.py tests/unit/api/test_dependencies.py -v
env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py tests/integration/api/test_staff_employer_reads.py -v
```

Expected: PASS with one engine per app lifespan and no create/read/search contract change.

---

### Task 4: Wire production BFCache canonical reload and invalidate late completions

**Objective:** Ensure persisted page restoration uses the production reload path and pagehide/reset cannot be undone by late asynchronous create results.

**Files:**
- Create: `apps/web/src/browser/privacyLifecycle.ts`
- Modify: `apps/web/src/app/App.tsx`
- Modify: `apps/web/src/app/App.test.tsx`
- Modify: `apps/web/src/employers/EmployerWorkspace.tsx`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify: `apps/web/src/employers/EmployerCreateForm.tsx`

**Step 1: Add production-route BFCache RED**

Mock only the narrow `reloadCanonicalDocument()` helper, render `AppRoutes` at `/employers`, dispatch `pageshow` with `persisted: true`, and require one reload call. The RED must exercise the production route wiring, not direct `<EmployerWorkspace onPersistedRestore={spy}>` injection.

Run:

```bash
npm --prefix apps/web run test -- --run src/app/App.test.tsx -t "reloads the canonical document after a persisted restore"
```

Expected: FAIL because `AppRoutes` currently mounts `<EmployerWorkspace />` without a reload callback.

**Step 2: Implement explicit production wiring**

- Export a zero-argument helper whose only behavior is `window.location.reload()`.
- Make `EmployerWorkspace` require the callback and remove optional chaining.
- Pass the helper explicitly from the production route.
- Keep non-persisted `pageshow` a no-op.

**Step 3: Add late-completion RED nodes**

Require both:

- a create request resolving success after `pagehide` cannot restore created detail or form state;
- a create request resolving unknown/conflict after `pagehide` cannot restore frozen authority state.

Expected RED: current reset clears state, but `submitAttempt()` later writes it back.

**Step 4: Add generation invalidation**

Use a monotonic operation-generation ref:

- each create operation captures its generation;
- reset/pagehide increments the generation;
- every asynchronous completion checks it before any state write or `onCreateSuccess` call;
- stale `finally` blocks cannot clear a newer pending operation.

Do not try to abort create requests: unknown-outcome authority requires retry-safe completion handling, not cancellation.

**Step 5: Run focused GREEN**

```bash
npm --prefix apps/web run test -- --run src/app/App.test.tsx src/employers/EmployerWorkspace.test.tsx
```

Expected: PASS. Human browser BFCache walkthrough remains deferred until deployed `develop`.

---

### Task 5: Serialize unknown-outcome retry and abandonment authority

**Objective:** Prevent concurrent retry/abandon operations and guarantee stale responses cannot regress authoritative success.

**Files:**
- Modify: `apps/web/src/employers/EmployerCreateForm.tsx`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`

**Step 1: Add race RED nodes**

Add tests that prove:

1. while an unknown-outcome retry is pending, retry and abandon controls are disabled;
2. repeated activation issues exactly one retry request with the original immutable command ID and payload;
3. authoritative success followed by a late unknown response remains success;
4. a newer authoritative state is not cleared by an older request’s `finally` block;
5. abandonment search cannot start while create retry is pending, and retry cannot start while abandonment search is pending.

Use deferred promises to control completion order. Assert authority state and call count, not scheduler-dependent timing.

**Step 2: Run focused RED**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx -t "serializes unknown create retry authority"
```

Expected: FAIL because retry is disabled only by abandonment-search state and every completion may write state.

**Step 3: Implement minimal mutual exclusion**

- Treat `pendingAttempt !== null || isAbandonSearchPending` as one operation lock.
- Guard both handlers as well as disabling buttons; UI disabling alone is not an authority boundary.
- Reuse the generation mechanism from Task 4.
- Preserve the original command ID and submitted payload for legitimate unknown retry.
- Do not generate a new command ID until a definitive no-commit outcome or successful follow-up search releases the old attempt.

**Step 4: Run focused GREEN**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx
```

Expected: PASS with no duplicate request and no success-to-unknown regression.

---

### Task 6: Render definitive create failures explicitly

**Objective:** Give staff localized, accessible feedback for server validation and authorization denial while safely disposing the old command identity.

**Files:**
- Modify: `apps/web/src/i18n/messages.ts`
- Modify: `apps/web/src/i18n/LanguageProvider.test.tsx`
- Modify: `apps/web/src/employers/EmployerCreateForm.tsx`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`

**Step 1: Add one RED per failure state**

Add separate tests for:

- `validation` (`400`/`422`): visible correction guidance, focus/live-region behavior, input retained for correction, old command ID released, corrected resubmission uses a fresh UUID;
- `forbidden` (`403`): visible access-denied guidance, no raw status/body, old command ID released, later authorized resubmission uses a fresh UUID;
- English/Spanish key parity and Proposed review metadata remain explicit.

**Step 2: Run focused RED**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx src/i18n/LanguageProvider.test.tsx -t "create"
```

Expected: FAIL because those failures currently produce no operator state.

**Step 3: Implement bounded create failure state**

- Add typed `validation | forbidden` create-failure state.
- Add operation-specific English/Spanish heading/body copy.
- Use value-free `aria-live` output and deliberate focus.
- Do not render raw status, problem body, submitted name/type, command ID, or exception text.
- Keep local input validation separate from server rejection.

**Step 4: Run focused GREEN**

Run the same tests; expected PASS.

---

### Task 7: Complete search, pagination, and detail failure recovery

**Objective:** Ensure every contract-defined read failure produces a bounded state without discarding accepted prior results unnecessarily.

**Files:**
- Modify: `apps/web/src/i18n/messages.ts`
- Modify: `apps/web/src/i18n/LanguageProvider.test.tsx`
- Modify: `apps/web/src/employers/EmployerSearch.tsx`
- Modify: `apps/web/src/employers/EmployerDetail.tsx`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`

**Step 1: Add base-search conflict RED**

A base-search `conflict` must render localized bounded guidance rather than silently returning.

**Step 2: Add pagination RED matrix**

For `validation`, `forbidden`, `conflict`, `unavailable`, and `unexpected`:

- keep previously accepted results visible;
- retain the submitted filter snapshot and cursor unless the response proves the cursor unusable;
- render operation-specific value-free guidance;
- expose only safe retry/rerun behavior appropriate to the classification;
- do not append partial or duplicate items.

**Step 3: Add detail RED matrix**

For `validation`, `forbidden`, `not_found`, `conflict`, `unavailable`, and `unexpected`:

- stop the loading state;
- render localized value-free guidance;
- never retain stale detail from another selection;
- preserve search results;
- retain existing abort/version protection.

**Step 4: Run RED**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx -t "failure"
```

Expected: FAIL for currently discarded classifications.

**Step 5: Implement exhaustive typed UI unions**

Make switch statements exhaustive over the read-operation failure subsets. Do not add a raw generic fallback that reflects transport data.

**Step 6: Run focused GREEN**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx src/i18n/LanguageProvider.test.tsx
```

Expected: PASS in both locales.

---

### Task 8: Correct RFC 3339 offset validation and fully test the API client boundary

**Objective:** Accept every bounded timestamp shape promised by the backend contract and directly prove operation/status/media/body classifications.

**Files:**
- Modify: `apps/web/src/api/employerClient.ts`
- Modify: `apps/web/src/api/employerClient.test.ts`
- Modify: `apps/web/vite.config.ts`

**Step 1: Add valid timestamp RED table**

Cover:

- `Z`;
- `+00:00`;
- positive and negative nonzero offsets;
- fractional seconds;
- leap-day in a leap year;
- year/month/day values that cross a UTC date boundary after offset normalization.

Expected: nonzero offsets currently fail because UTC-normalized components are compared to the original local components.

**Step 2: Add invalid timestamp RED table**

Reject:

- impossible month/day combinations;
- non-leap February 29;
- hour/minute/second overflow;
- malformed or out-of-range numeric offsets;
- missing timezone;
- date-only or space-separated values;
- trailing content/control characters.

**Step 3: Implement calendar-before-offset validation**

Validate the captured local calendar/time components independently, then verify that JavaScript can parse the full offset-bearing instant. Do not compare the original offset-local clock to `toISOString()` UTC components. Keep the accepted contract explicit about leap seconds if they remain unsupported.

**Step 4: Add direct operation matrices**

For create, search, and detail, test:

- every recognized status;
- unrecognized and unexpected 2xx status;
- wrong/missing JSON media type;
- unreadable JSON;
- schema-invalid JSON;
- body cancellation and cancellation failure;
- network failure and abort behavior;
- requested-detail ID mismatch;
- valid offset timestamps in actual response objects.

Component mocks do not count as client-boundary proof.

**Step 5: Add focused client coverage enforcement**

Add a file-specific threshold for `src/api/employerClient.ts` that is met by the new direct tests and is no weaker than the repository’s global statement/line/function/branch thresholds. Do not lower global coverage.

**Step 6: Run focused GREEN**

```bash
npm --prefix apps/web run test -- --run src/api/employerClient.test.ts
npm --prefix apps/web run test:coverage -- --run src/api/employerClient.test.ts
```

Expected: PASS with valid numeric offsets accepted and invalid calendar/offset values rejected.

---

### Task 9: Make frontend test diagnostics value-independent

**Objective:** Ensure failed tests cannot serialize Employer/input/API values into CI logs, even when values do not follow a sentinel naming convention.

**Files:**
- Create: `apps/web/src/test/valueSafeDiagnostics.ts`
- Create: `apps/web/src/test/valueSafeDiagnostics.test.ts`
- Modify: `apps/web/src/test/setup.ts`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`

**Step 1: Add naming-independent RED**

Trigger a Testing Library query failure against a DOM containing:

- an arbitrary synthetic Employer-like name with no `SYNTHETIC_*` prefix;
- a UUID;
- a cursor-like token;
- an input value and dynamic text node.

Require the thrown error to omit every value while retaining a generic failure label and normal JavaScript stack/source location.

**Step 2: Run RED**

```bash
npm --prefix apps/web run test -- --run src/test/valueSafeDiagnostics.test.ts
```

Expected: FAIL because `prettyDOM(container)` serializes arbitrary values.

**Step 3: Implement value-independent diagnostics**

- Remove full DOM serialization from the CI error path.
- Do not attempt pattern-based redaction of unknown operational strings.
- Return a fixed privacy-safe Testing Library failure message; rely on the test name and stack/source location for diagnostics.
- Do not add a verbose CI mode.
- A future local detailed mode, if ever needed, requires its own explicit design and synthetic-only guard; it is not part of this closeout.

**Step 4: Run focused GREEN**

```bash
npm --prefix apps/web run test -- --run src/test/valueSafeDiagnostics.test.ts
npm --prefix apps/web run test
```

Expected: the focused diagnostic test and complete existing frontend test suite pass, and no dynamic value appears in captured diagnostics.

---

### Task 10: Strengthen SBOM validation and persist dependency disposition

**Objective:** Prove generated SBOMs are schema-valid Golden Rose application graphs and document direct dependency purpose/license/deprecation review without adding an unnecessary scanner.

**Files:**
- Create: `scripts/validate_sbom.py`
- Create: `tests/unit/test_sbom_validation.py`
- Create: `docs/security/dependency-purpose-license-review.md`
- Modify: `.github/workflows/application-quality.yml`
- Modify: `SECURITY.md`
- Modify: `README.md` if local verification commands change

**Step 1: Add validator RED nodes**

Test rejection of:

- malformed JSON;
- wrong `bomFormat` or unsupported `specVersion`;
- schema-invalid CycloneDX content;
- missing/wrong root application name, type, or version;
- empty components;
- empty or broken dependency graph;
- missing generator metadata;
- dependency references to unknown components.

Test acceptance of bounded frontend CycloneDX 1.5 and backend CycloneDX 1.6 fixtures.

**Step 2: Run RED**

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_sbom_validation.py -v
```

Expected: FAIL because no validator exists.

**Step 3: Implement using existing locked tooling**

- Use `cyclonedx.validation.json.JsonStrictValidator` and the already direct-pinned `cyclonedx-python-lib[json-validation]==11.11.0`; add no new dependency.
- Select schema from the document’s exact supported spec version.
- Before compatibility canonicalization, reject unknown dependency-object keys, malformed present `dependsOn`, exact duplicate components, and conflicting component identity/evidence. Canonicalize only the locked generators' evidenced quirks: exact/divergent same-ref dependency rows, omitted backend `dependsOn`, and differing `properties` on otherwise-identical npm components.
- Strict-validate the full canonical JSON string, then assert root component identity, application type, expected version, nonempty components/dependencies, resolvable references, and tool metadata. Do not require every environment package to be root-reachable; the backend environment generator legitimately includes schema-valid isolated package nodes.
- Accept explicit CLI arguments for expected name/version/spec so one script validates both applications.
- Emit value-free pass/fail text only; do not print the document or component inventory on failure.

Expected roots:

- frontend: component name `web`, version `0.0.0`, type `application`, purl `pkg:npm/%40golden-rose/web@0.0.0`, CycloneDX `1.5`;
- backend: component name `golden-rose`, version `0.1.0`, type `application`, CycloneDX `1.6`.

**Step 4: Replace CI stub assertions**

After each SBOM is generated, invoke the validator with the expected identity. Keep artifact upload and 14-day retention unchanged.

**Step 5: Record dependency disposition**

The review document must include:

- date, reviewer/owner, manifests/locks reviewed, and exact generation tools;
- every direct runtime and development dependency with bounded purpose and declared license;
- current transitive license summary and explicit disposition of LGPL/MPL/CC/other notable licenses;
- deprecation/advisory disposition, including why `react-router@8.3.0` remains selected;
- statement that vulnerability audits were clean at review time but are not permanent guarantees;
- trigger to repeat review when a manifest/lock/runtime version changes.

Do not commit generated SBOM JSON.

**Step 6: Run GREEN**

```bash
env -u PYTHONPATH uv run pytest tests/unit/test_sbom_validation.py -v
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
env -u PYTHONPATH uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
env -u PYTHONPATH uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
env -u PYTHONPATH uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
```

Expected: PASS with no SBOM content printed.

---

### Task 11: Run focused and complete non-service verification

**Objective:** Catch shared regressions before requesting service-backed final qualification.

**Files:** all changed code/tests/config/docs.

**Step 1: Frontend gate**

```bash
npm --prefix apps/web run verify
npm --prefix apps/web ls --all
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
```

Expected: PASS, no High/Critical vulnerability, production build emits local assets only.

**Step 2: Backend no-service gate**

```bash
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run pytest tests/unit -v
env -u PYTHONPATH uv run pip-audit --skip-editable
```

Expected: PASS. Record exact observed counts; do not copy stale counts from PR #13.

**Step 3: Diff and secret hygiene**

```bash
git diff --check
```

Expected: PASS. Confirm `.env*`, generated SBOMs, `dist/`, and coverage remain untracked/ignored. Do not run a whole-directory scanner that could read ignored local credential files; exact committed-range Gitleaks runs in Task 14.

---

### Task 12: Run the approved PostgreSQL migration and complete application gate

**Objective:** Prove the migration, application lifespan, frontend, and backend together in the committed workflow order.

**Prerequisite:** Obtain separate explicit approval to start the loopback-only disposable `postgres-test` service and confirm ignored `.env.test` already contains synthetic credentials. Never print it.

**Step 1: Start and health-check PostgreSQL**

```bash
docker compose --env-file .env.test up -d postgres-test
docker compose --env-file .env.test ps postgres-test
```

Stop if the listener is not bound only to `127.0.0.1:55432` or health does not become `healthy`.

**Step 2: Run the exact workflow-order gate**

```bash
test "$(node --version)" = "v22.22.3"
test "$(npm --version)" = "10.9.8"
test "$(npm --userconfig apps/web/.npmrc config get registry)" = "https://registry.npmjs.org/"
test "$(npm --userconfig apps/web/.npmrc config get ignore-scripts)" = "true"
node --test apps/web/scripts/validate-lockfile.test.mjs
node apps/web/scripts/validate-lockfile.mjs apps/web/package-lock.json
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv sync --locked --all-groups
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
npm --prefix apps/web run verify
npm --prefix apps/web ls --all
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
env -u PYTHONPATH uv run python scripts/validate_sbom.py build/frontend-sbom.cdx.json --spec 1.5 --name web --version 0.0.0 --purl 'pkg:npm/%40golden-rose/web@0.0.0'
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
mkdir -p build
env -u PYTHONPATH uv run cyclonedx-py environment --pyproject pyproject.toml --output-reproducible --of JSON -o build/backend-sbom.cdx.json
env -u PYTHONPATH uv run python scripts/validate_sbom.py build/backend-sbom.cdx.json --spec 1.6 --name golden-rose --version 0.1.0
git diff --check
```

Expected: all checks pass; migration down/up proves 0002 reversibility; full test coverage remains at least 95%.

**Step 3: Always tear down in `finally`**

```bash
docker compose --env-file .env.test down
docker compose --env-file .env.test ps -a
```

Expected: empty service list. Record shutdown evidence in `NOTES.md` and the review handoff.

No API, Vite, browser, GCP, or public listener is required for this closeout gate.

---

### Task 13: Reconcile final living docs and prepare independent rereview

**Objective:** Record only observed remediation evidence, preserve deferred gates honestly, and hand the exact working tree to an independent reviewer.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`
- Modify as required by actual contract changes: `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `SECURITY.md`, `TECHNOLOGY_DECISIONS.md`, ADR-0005, ADR-0006
- Create: `docs/review-handoffs/2026-08-07-employer-workspace-closeout-review-handoff.md`

**Step 1: Record observed evidence only**

Include:

- exact branch/base and working-tree/commit status;
- each finding, remediation location, focused RED reason, and GREEN result;
- exact test counts and coverage from current runs;
- migration up/down/up evidence;
- SBOM identity/schema/graph validation and dependency-review path;
- vulnerability/secret-scan results;
- explicit service teardown;
- explicit statement that human browser/accessibility/fluent-language review has not occurred and activates after deployed `develop` exists;
- explicit statement that runtime-role immutability, pool sizing/load, GCP, live data, and next-slice implementation remain deferred.

**Step 2: Independent rereview focus**

Require an alternate session to verify:

1. production-route BFCache wiring and late-completion invalidation;
2. retry/abandon mutual exclusion and authoritative-success precedence;
3. complete create/read failure mappings in both locales;
4. offset parser correctness and direct client status/media/body cancellation matrices;
5. database FK/composite/unique integrity and preserved create concurrency/idempotency;
6. one-engine-per-app lifecycle and deterministic disposal;
7. value-independent test diagnostics;
8. real SBOM validation and license/deprecation disposition;
9. living-doc/deferred-gate truth with no claim of human review.

Any High/Blocker blocks commit/push/PR preparation. Every Medium must be remediated or explicitly documented with rationale, owner, and Beatrice's acceptance; an undisposed Medium also blocks PR preparation.

**Step 3: Verify final uncommitted review surface**

```bash
git status --short --branch
git diff --stat
git diff --check
```

State clearly that this is an uncommitted working-tree surface; do not imply a committed PR range.

---

### Task 14: Commit, final-head qualification, PR, merge, and continuity sync

**Objective:** Move the independently cleared closeout through protected `develop` without stale evidence or continuity drift.

**Prerequisites:** Explicit approval for commit/push/PR operations; independent rereview has no open High/Blocker.

**Step 1: Commit the reviewed remediation**

Use a focused commit message such as:

```text
fix: close employer workspace post-merge findings
```

Do not commit generated SBOMs, coverage, build output, `.env*`, client data, or raw review artifacts.

**Step 2: Repeat complete final-head qualification**

Rerun Task 12 against the exact committed head after documentation/handoff reconciliation. Any later commit requires another complete final-head run.

**Step 3: Scan the exact PR range**

```bash
git diff --check origin/develop...HEAD
/opt/homebrew/bin/gitleaks git --no-banner --redact --log-opts='origin/develop..HEAD'
```

Expected: no whitespace errors or leaks; at least one real commit is scanned.

**Step 4: Push and open PR to `develop`**

PR body must distinguish:

- observed defects remediated;
- automated evidence completed;
- human browser/accessibility/fluent-language qualification deferred until deployed `develop`;
- deployment/runtime-role/load/live-data work not authorized;
- next product slice not included.

Wait for required `application`, `check`, and `enforce` statuses. Do not merge with an open High/Blocker or failed required check.

**Step 5: After merge, rebaseline continuity**

Under separate approval:

- verify the actual merge commit on `origin/develop`;
- update the Golden Rose Obsidian implementation-progress and engagement-index notes;
- state that closeout is merged and human qualification remains pending deployed `develop`;
- fast-forward local `develop` and retire the closeout branch only after patch-equivalence proof;
- begin a separate planning lane for the bounded end-to-end draft Employer revision slice.

---

## 5. Final acceptance checklist

- [ ] PR #13 merge state and the closeout branch are accurately recorded.
- [ ] Human browser/manual accessibility/fluent review is marked deferred—not complete and not an overdue pre-merge defect.
- [ ] Production BFCache persisted restore invokes canonical reload through the real route.
- [ ] Pagehide/reset invalidates late create completions.
- [ ] Unknown retry and abandonment are mutually exclusive and stale completions cannot regress success.
- [ ] Create validation/forbidden failures render localized bounded guidance.
- [ ] Search/pagination/detail failure unions are complete and preserve accepted results appropriately.
- [ ] Numeric-offset RFC 3339 values are accepted; invalid calendar/offset forms are rejected.
- [ ] Direct create/search/detail client matrices cover status, media type, malformed body, cancellation, network, and abort paths.
- [ ] CommandReceipt result references Employer; audit event command/entity matches the receipt result; duplicate creation event is rejected.
- [ ] Existing create authorization, atomicity, replay, conflict, and concurrency behavior remains green.
- [ ] One SQLAlchemy engine is owned per application lifespan; sessions close per request; engine disposes at shutdown.
- [ ] Test failure diagnostics are value-independent.
- [ ] Frontend/backend SBOMs pass strict schema and Golden Rose identity/graph/tool checks.
- [ ] Direct dependency purpose/license and relevant transitive/deprecation disposition is tracked.
- [ ] npm audit, pip-audit, Bandit, Gitleaks, lint, typecheck, build, migrations, tests, and coverage pass.
- [ ] PostgreSQL is torn down and no other service is started.
- [ ] Repository docs and Obsidian do not overclaim deployment, human review, production immutability, or next-slice authorization.
- [ ] Independent rereview clears the remediation before PR preparation.
- [ ] Final-head evidence matches the exact committed PR range.

## 6. Next-slice boundary after closeout

The next recommended product-planning candidate remains a strictly bounded end-to-end **draft Employer revision** slice over only `display_name` and `employer_type`, with expected-version concurrency, actor/payload-bound idempotency, updated attribution, and localized browser edit states. Its ADR must first resolve replay semantics after later mutations and may reuse the strengthened receipt/database/browser foundations from this closeout. It is not part of this plan and receives no implementation authorization from the closeout merge.
