# Task 10 Privacy Localization Accessibility Transition Plan

> **For Hermes:** Use subagent-driven-development skill only if Beatrice explicitly asks for delegated execution; otherwise execute this plan task-by-task in strict exact-node TDD. This is a lane-transition planning artifact, not product-code implementation.

**Goal:** Transition from the exhausted Task 9 workspace-authority node list into the already-approved ADR-0007 Task 10 evidence lane: privacy, localization, accessibility, and diagnostic boundaries for the bounded draft-Employer revision slice.

**Architecture:** ADR-0007 remains the controlling implementation authority. Task 10 should not expand product scope; it should add exact evidence nodes around existing revision behavior, using non-vacuous browser side-channel instrumentation, bilingual catalog parity checks, automated axe coverage, and backend/API value-safety diagnostics. Production code changes are permitted only when an exact Task 10 RED exposes a real gap.

**Tech Stack:** React, TypeScript, Vite/Vitest, Testing Library, axe-core test helper, Python/FastAPI/Pydantic/pytest for the named backend value-safety node, existing `uv`/`npm` toolchains.

---

## Current context

- Branch: `feat/staff-draft-employer-revision`.
- Current working tree is intentionally active and uncommitted for the bounded draft-Employer revision slice.
- ADR-0007 and `.hermes/plans/2026-08-08_111916-phase-1-draft-employer-revision-plan.md` are the controlling sources.
- Task 9 exact workspace nodes are complete through `WORKSPACE(revision values never enter URL history storage console or diagnostic output)`.
- The current ADR-0007-approved Task 9 node list is exhausted.
- Task 10 is already present in ADR-0007 as the next approved lane: **Prove privacy, localization, accessibility, and diagnostic boundaries**.
- Human browser/manual accessibility/fluent-language qualification remains deferred until a shared deployed `develop` environment exists; Task 10 may prove automated coverage only.

## Scope for this transition

### In scope

- Add exact Task 10 evidence nodes from the ADR-0007 ledger:
  - `LANG(keeps exact English and Spanish revision keys in parity)`
  - `FORM(passes axe in both locales across every revision and recovery state)` or an equivalent split if the existing form suite requires smaller selectors
  - `FORM(announces and focuses every revision transition with reduced-motion-safe behavior)`
  - `WORKSPACE(revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels)`
  - `DIAG(revision controls preserve value-independent Testing Library diagnostics)`
  - `API(test_revision_error_and_exception_diagnostics_are_value_safe)`
  - `CLIENT(rejects actor attribution fields from routine revision and detail browser responses)`
- Classify immediate passes as honest GREEN regressions.
- Treat harness/instrumentation setup failures separately from product REDs.
- Keep all evidence synthetic/local and value-safe.
- Update `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md` after each completed material node or after a small coherent Task 10 group if the node is harness-only.

### Out of scope

- No new product fields beyond `display_name` and `employer_type`.
- No contact, worksite, staffing request, lifecycle, audit timeline/read API, upload, public-plane, identity-provider, deployment, infrastructure, or live-data work.
- No claims that human browser QA, manual accessibility review, or fluent English/Spanish review has occurred.
- No service start unless Beatrice gives explicit scoped approval for the backend/API node that requires PostgreSQL-backed integration evidence.
- No broad refactor of the revision state machine or workspace authority model unless an exact Task 10 RED requires a local fix.

## Required preparation before execution

1. Re-read the controlling Task 10 section of `.hermes/plans/2026-08-08_111916-phase-1-draft-employer-revision-plan.md`.
2. Re-read the exact files involved before each node:
   - `apps/web/src/i18n/messages.ts`
   - `apps/web/src/i18n/LanguageProvider.test.tsx`
   - `apps/web/src/employers/EmployerRevisionForm.tsx`
   - `apps/web/src/employers/EmployerRevisionForm.test.tsx`
   - `apps/web/src/employers/EmployerWorkspace.tsx`
   - `apps/web/src/employers/EmployerWorkspace.test.tsx`
   - `apps/web/src/api/employerClient.ts`
   - `apps/web/src/api/employerClient.test.ts`
   - `apps/web/src/test/valueSafeDiagnostics.ts`
   - `apps/web/src/test/valueSafeDiagnostics.test.ts`
   - `tests/integration/api/test_staff_employers.py` only for the API diagnostic node
3. Rebaseline live git state before the first code/test edit:
   - `git status --short --branch`
4. Keep the exact-node discipline:
   - add one exact test node;
   - run only that selector;
   - record honest RED, harness-only setup failure, or immediate-pass GREEN regression;
   - implement the smallest change only if needed;
   - rerun that selector;
   - then run the focused file/suite for that node.

---

## Task 10.1: English/Spanish revision catalog parity

**Objective:** Prove every revision and recovery message key exists in both English and Spanish catalogs and is not a key-placeholder echo.

**Files:**
- Modify test: `apps/web/src/i18n/LanguageProvider.test.tsx`
- Modify only if RED requires: `apps/web/src/i18n/messages.ts`

**Step 1: Add exact test node**

Add selector:

```text
keeps exact English and Spanish revision keys in parity
```

The test should assert, at minimum:
- English and Spanish catalogs have the same revision-related keys.
- Catalog metadata remains `Proposed` / `Proposed` unless a separate review changes it.
- Required keys cover edit/open, submit, validation, no-op, pending, forbidden, not-found, stale, conflict, unknown, retry, reload, refresh failure, confirmed save success, and search-invalidated guidance.
- No Spanish revision value equals its message key.

**Step 2: Run focused selector**

```bash
npm --prefix apps/web run test -- --run src/i18n/LanguageProvider.test.tsx -t 'keeps exact English and Spanish revision keys in parity'
```

Expected first classification: likely immediate-pass GREEN or RED for missing exact coverage/key inventory.

**Step 3: Minimal GREEN if needed**

If RED is missing keys or placeholder values, add only the missing message keys/values in `apps/web/src/i18n/messages.ts`. Do not rewrite existing copy or claim fluent-language review.

**Step 4: Verify focused file**

```bash
npm --prefix apps/web run test -- --run src/i18n/LanguageProvider.test.tsx
npm --prefix apps/web run typecheck
```

---

## Task 10.2: Automated axe coverage for revision/recovery states

**Objective:** Prove automated axe coverage in both locales across every revision and recovery state that Task 8/9 exposes.

**Files:**
- Modify test: `apps/web/src/employers/EmployerRevisionForm.test.tsx`
- Modify only if RED requires: `apps/web/src/employers/EmployerRevisionForm.tsx`
- Modify only if helper gap appears: `apps/web/src/test/axe.ts`

**Step 1: Add exact test node**

Add selector:

```text
passes axe in both locales across every revision and recovery state
```

Use existing `runAxe` helper patterns. Cover at least:
- editing state,
- client validation failure,
- pending state,
- definitive validation/forbidden failure,
- command not-found,
- stale refresh-required state,
- idempotency conflict reload-required state,
- unknown outcome retry/reload state,
- confirmed-save refresh failure,
- success state.

Run in English and Spanish. If one monolithic test becomes hard to classify honestly, split into smaller exact selectors while preserving the ADR node name as the parent description.

**Step 2: Run focused selector**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx -t 'passes axe in both locales across every revision and recovery state'
```

Expected first classification: possible immediate-pass GREEN regression if previous automated accessibility coverage is complete; otherwise RED should name the missing semantic/label/aria relationship.

**Step 3: Minimal GREEN if needed**

Fix only the missing semantic/label/focus/aria issue. Do not redesign layout or copy.

**Step 4: Verify focused file**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx
npm --prefix apps/web run typecheck
```

---

## Task 10.3: Announcement and focus transitions with reduced-motion safety

**Objective:** Prove every revision transition has one deliberate focus target and does not depend on animation/motion behavior.

**Files:**
- Modify test: `apps/web/src/employers/EmployerRevisionForm.test.tsx`
- Modify only if RED requires: `apps/web/src/employers/EmployerRevisionForm.tsx`
- Modify only if existing styling cannot express the state: `apps/web/src/styles.css`

**Step 1: Add exact test node**

Add selector:

```text
announces and focuses every revision transition with reduced-motion-safe behavior
```

Assert focus for:
- validation/no-op error field or heading per existing contract,
- validation failure heading,
- forbidden failure heading,
- not-found heading,
- stale heading,
- conflict heading,
- unknown heading,
- refresh-failure heading,
- success heading.

Also assert that reduced-motion mode does not remove the status/alert/focusable heading path. Use existing style/media helper patterns if present; otherwise keep the assertion DOM-level and value-independent.

**Step 2: Run focused selector**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx -t 'announces and focuses every revision transition with reduced-motion-safe behavior'
```

**Step 3: Minimal GREEN if needed**

Add only missing `tabIndex={-1}`, refs, `aria-live`, or deterministic focus calls. Avoid broad state-machine rewrites.

**Step 4: Verify focused file**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerRevisionForm.test.tsx
npm --prefix apps/web run typecheck
```

---

## Task 10.4: Non-vacuous browser side-channel instrumentation

**Objective:** Prove revision browser flow does not access cache/service-worker surfaces and does not expose values to URL/history/storage/console/diagnostics.

**Files:**
- Modify test: `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify only if RED requires: `apps/web/src/employers/EmployerWorkspace.tsx`, `apps/web/src/employers/EmployerSearch.tsx`, or `apps/web/src/employers/EmployerRevisionForm.tsx`

**Step 1: Add exact test node or reconcile existing coverage**

ADR selector:

```text
revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels
```

Important: Task 9 cycle 20 already added a narrower exact node:

```text
revision values never enter URL history storage console or diagnostic output
```

For Task 10, either:
- add the ADR-exact selector as a wrapper/expanded node that reuses the same fixture shape but includes explicit `caches` and `navigator.serviceWorker.register` instrumentation before render, or
- rename/refactor only if the resulting selector remains stable and existing evidence is not lost.

The test must instrument, not merely observe absent jsdom globals:
- `globalThis.caches` getter/open,
- `navigator.serviceWorker.register`,
- `history.replaceState` / `history.pushState`,
- `Storage.prototype.getItem` / `setItem`,
- console methods,
- value-safe Testing Library diagnostics.

**Step 2: Run focused selector**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx -t 'revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels'
```

Expected first classification: likely immediate-pass GREEN regression if the Task 9 cycle 20 test is adapted exactly; classify honestly.

**Step 3: Minimal GREEN if needed**

Remove only the leaking side-channel behavior. Do not change backend/API contracts.

**Step 4: Verify focused file**

```bash
npm --prefix apps/web run test -- --run src/employers/EmployerWorkspace.test.tsx
npm --prefix apps/web run typecheck
```

---

## Task 10.5: Value-independent Testing Library diagnostics for revision controls

**Objective:** Prove test diagnostics remain value-independent for revision-specific controls and recovery output.

**Files:**
- Modify test: `apps/web/src/test/valueSafeDiagnostics.test.ts`
- Modify only if RED requires: `apps/web/src/test/valueSafeDiagnostics.ts`

**Step 1: Add exact test node**

Add selector:

```text
revision controls preserve value-independent Testing Library diagnostics
```

Render representative revision labels/inputs/recovery text containing synthetic secrets, then force a failed Testing Library query. Assert the diagnostic contains `VALUE_SAFE_TESTING_LIBRARY_MESSAGE` and excludes:
- synthetic display name,
- UUID command ID,
- expected version marker,
- opaque cursor/body markers.

**Step 2: Run focused selector**

```bash
npm --prefix apps/web run test -- --run src/test/valueSafeDiagnostics.test.ts -t 'revision controls preserve value-independent Testing Library diagnostics'
```

**Step 3: Minimal GREEN if needed**

Patch only the diagnostic redaction helper/test setup.

**Step 4: Verify diagnostics file**

```bash
npm --prefix apps/web run test -- --run src/test/valueSafeDiagnostics.test.ts
npm --prefix apps/web run typecheck
```

---

## Task 10.6: Backend/API revision error diagnostics are value-safe

**Objective:** Prove backend/API revision error and exception evidence contains no Employer name, UUID, payload, SQL, connection string, or response body.

**Files:**
- Modify test: `tests/integration/api/test_staff_employers.py`
- Modify only if RED requires: `src/golden_rose/api/staff/employers.py`, `src/golden_rose/api/errors.py`, or revision application error mapping

**Service boundary:** This node likely requires the approved PostgreSQL test service shell from ADR-0007 Task 12. Do not start Docker/PostgreSQL without explicit scoped approval.

**Step 1: Add exact test node**

Add selector:

```text
test_revision_error_and_exception_diagnostics_are_value_safe
```

Assert value-safe bounded diagnostics for at least:
- known revision validation/no-op/stale/idempotency conflict paths,
- unexpected exception path if the existing test harness can inject it safely,
- no emitted problem body/log/assertion includes submitted display name, command UUID, SQL text, connection URL, or raw response body.

**Step 2: Run focused selector after service approval only**

```bash
env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py::test_revision_error_and_exception_diagnostics_are_value_safe -q
```

Expected first classification: RED if backend diagnostics leak dynamic values or the node is absent; harness-only if PostgreSQL/service setup is missing.

**Step 3: Minimal GREEN if needed**

Patch only bounded error mapping/diagnostic redaction. Do not parse dynamic problem bodies for browser authority.

**Step 4: Verify focused API file after service approval**

```bash
env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py -q
```

---

## Task 10.7: Actor attribution fields rejected from routine browser contracts

**Objective:** Prove `updated_by` and other actor attribution fields do not reach routine revision/detail browser responses.

**Files:**
- Modify test: `apps/web/src/api/employerClient.test.ts`
- Modify only if RED requires: `apps/web/src/api/employerClient.ts` or `apps/web/src/api/employerContracts.ts`

**Step 1: Add exact test node**

Add selector:

```text
rejects actor attribution fields from routine revision and detail browser responses
```

Assert:
- revision success body containing `updated_by` is rejected as unknown/malformed success rather than accepted into frontend state;
- exact detail body containing `updated_by` is rejected or ignored according to the existing strict parser contract; choose the stricter behavior already used for unknown fields and do not weaken existing parsing;
- no actor field appears in returned frontend records.

**Step 2: Run focused selector**

```bash
npm --prefix apps/web run test -- --run src/api/employerClient.test.ts -t 'rejects actor attribution fields from routine revision and detail browser responses'
```

**Step 3: Minimal GREEN if needed**

Tighten strict response guards only for actor-attribution leakage. Do not change accepted success shape beyond ADR-0007.

**Step 4: Verify focused client file**

```bash
npm --prefix apps/web run test -- --run src/api/employerClient.test.ts
npm --prefix apps/web run typecheck
```

---

## Task 10 closeout verification

After Task 10 nodes are complete, run the focused Task 10 verification from ADR-0007:

```bash
npm --prefix apps/web run test -- --run \
  src/employers/EmployerRevisionForm.test.tsx \
  src/employers/EmployerWorkspace.test.tsx \
  src/test/valueSafeDiagnostics.test.ts
npm --prefix apps/web run test -- --run src/i18n/LanguageProvider.test.tsx src/api/employerClient.test.ts
npm --prefix apps/web run typecheck
git diff --check
```

If the backend/API diagnostic node was executed under approved PostgreSQL service scope, also record its focused command and result separately in `NOTES.md`.

Do **not** run `npm --prefix apps/web run test` or full non-service gates here unless explicitly transitioning into ADR-0007 Task 11 after Task 10 closeout.

## Documentation updates

After each material node or coherent sub-lane:

- Update `CURRENT_WORK.md` with the new Task 10 status and next exact node.
- Update `ROADMAP.md` to replace the exhausted Task 9 wording with Task 10 progress.
- Append `NOTES.md` evidence at the bottom of the existing 2026-08-11 section in chronological order.
- Keep language precise:
  - `Observed` for actual test/code evidence;
  - `Validated` only after executable evidence exists;
  - `Proposed` for human/manual review still pending.

## Stop boundary

Stop and ask Beatrice before any of the following:

- starting PostgreSQL/Docker or sourcing `.env.test`;
- committing, pushing, opening PRs, or running exact-final-head gates;
- extending beyond ADR-0007 Task 10 into Task 11;
- adding new product surface beyond draft Employer name/type revision;
- claiming human browser/manual accessibility/fluent-language qualification.

## Transition recommendation

Proceed next with Task 10.1 (`LANG(keeps exact English and Spanish revision keys in parity)`) as the first exact-node TDD cycle. It is non-service, narrow, and gives a clean transition from workspace-authority behavior into automated localization/privacy/accessibility evidence.
