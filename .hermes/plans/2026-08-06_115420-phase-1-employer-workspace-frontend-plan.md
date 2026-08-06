# Phase 1 Employer Workspace Frontend Tracer Implementation Plan

> **For Hermes:** Use `subagent-driven-development` and `frontend-slice-tdd` to execute this plan task-by-task. Every behavior node is strict RED → verify meaningful RED → minimal GREEN → verify GREEN. Do not write production UI code before its failing test.

**Goal:** Add a local/test-only, staff-facing browser workspace that exercises the merged Employer create, bounded-search, and exact-detail API contracts without widening into real identity, contacts, worksites, staffing requests, deployment, public access, or live data. Before browser consumption, close the observed create-success cache gap with a header-only `Cache-Control: no-store` regression.

**Architecture:** Create a standalone `apps/web/` React/TypeScript/Vite application with one canonical `/employers` route, a small typed `fetch` client, component-local state, a typed English/Spanish message catalog, and plain tokenized CSS. The frontend calls only the existing staff API through relative `/api/staff/v1/...` paths; Vite proxies those paths to a separately approved loopback backend during local development and production-build preview. No browser storage, URL search parameters, analytics, service worker, state-management library, UI framework, or frontend authorization claim is introduced.

**Tech Stack:** Node.js 22.22.3, npm 10.9.8 with lockfile version 3, React 19.2.8, React DOM 19.2.8, React Router DOM 7.18.2, TypeScript 5.9.3, Vite 8.2.1, `@vitejs/plugin-react` 6.0.5, Vitest 4.1.10, jsdom 30.0.1, Testing Library, `axe-core` 4.13.0, ESLint 10, and the existing FastAPI/PostgreSQL backend contracts.

---

## 0. Authority, baseline, and status

### 0.1 Authoritative baseline

- Repository: `golden_rose_project`
- Planning branch: `docs/phase-1-employer-workspace-plan`
- Implementation branch only after this Accepted packet merges and Beatrice separately approves implementation repository operations: `feat/staff-employer-workspace`
- Implementation base: the exact then-current merged `origin/develop`; do not branch from this planning branch or the retired PR #11 feature branch.
- Baseline observed on 2026-08-06:
  - PR #11 merged to `develop`.
  - `origin/develop` and local `develop` resolved to `b9eaee60392855e519e60e52ed95736752852de4`.
  - the worktree was clean after fast-forwarding `develop`;
  - `env -u PYTHONPATH uv run pytest tests/unit -q` returned `48 passed`;
  - no PostgreSQL, API, frontend, or cloud service was started.
- PR #11's exact Employer create/read/search contracts are implementation authority. ADR-0002, ADR-0004, the merged tests, and current source override examples in this plan if a non-material spelling difference is discovered.
- GCP architecture/provisioning remains owned by another planning lane and is non-scope here.

### 0.2 Evidence classification

- **Observed:** the repository has no `package.json`, frontend subtree, JavaScript lockfile, logo, palette, or approved visual-brand specification.
- **Observed:** the merged backend supports one staff create endpoint, one exact-detail endpoint, and one bounded POST search endpoint under `/api/staff/v1/employers`.
- **Observed:** search/detail success and affected problem responses use `Cache-Control: no-store`, but fresh and replayed create successes currently omit it. The plan treats that as a blocking response-cache hardening prerequisite before browser consumption; search still requires a bounded name fragment and exposes no unfiltered list or count.
- **Observed:** Node `v22.22.3` and npm `10.9.8` are available in the planning environment. The selected package versions and their engine/peer requirements were checked from npm on 2026-08-06; TypeScript 5.9.3 is deliberately selected rather than TypeScript 7 because the selected `typescript-eslint` line declares `<6.1.0` support.
- **Accepted planning direction:** Beatrice accepted the stack, route, visual baseline, localization mechanism, and browser-state rules on 2026-08-06 after independent planning rereviews cleared all Blocker/High/Medium findings. This is not implementation or service-start approval.
- **Validated only after implementation:** behavior, accessibility checks, production build, dependency/SBOM gates, backend regressions, and the required separately approved local browser walkthrough.

### 0.3 Planning and execution gates

Planning gates 1–3 are satisfied locally as of 2026-08-06: this plan/ADR were independently reviewed, all Blocker/High/Medium planning findings were remediated and cleared on focused rereview, and Beatrice explicitly accepted the product/architecture direction and ADR-0005. Implementation may start only after the remaining gates:

1. this exact planning packet passes protected PR/CI and merges to `develop`;
2. a fresh coding session fetches/prunes, switches to `develop`, fast-forwards only, confirms a clean tree, and records the exact merged planning tip;
3. Beatrice explicitly approves implementation repository operations;
4. any service start is separately approved at execution time.

If the first intended RED passes, classify it under the project's regression-reclassification procedure before continuing. If RED fails because of environment/configuration noise, repair the harness and rerun until the failure is attributable to missing behavior.

### 0.4 Acceptance and bounded operational impact

- **Technical acceptance owner:** Beatrice accepts only the synthetic/local repository increment after independent review, required local evidence, and protected PR/CI. This is not client acceptance or production authorization.
- **Language review owner:** before the mandatory pre-merge bilingual walkthrough (and before any client walkthrough), Beatrice records a separate fluent English/Spanish reviewer by name, the catalog version reviewed, findings/remediation, and review state. Counsel/client approval remains required if later copy becomes legal, policy, fee, consent, or contract content.
- **Support/incident posture:** there is no production support rota, incident channel, SLA, telemetry, or monitoring expansion. During implementation or walkthrough, unexpected exposure, non-loopback binding, unsafe browser state, or data-boundary drift is a stop/teardown/escalation condition recorded in the review handoff.
- **Recovery:** no migration or live data is introduced. Keep the API header hardening and frontend work in separate commits; rollback is a reviewed `git revert` of the affected commit(s), while ordinary in-scope defects use a forward fix. Never rewrite protected history.
- **Training/change impact:** no staff training or operational cutover is authorized. A synthetic walkthrough may gather usability evidence only; it does not establish production readiness.
- **External dependencies:** this narrow technical tracer has no client/counsel dependency for implementation because it excludes legal/policy wording and live data. Any scope expansion returns to planning and the appropriate approval gate.

## 1. Bounded product contract

### 1.1 Authorized user outcome

A synthetic local/test staff user can:

1. enter a bounded Employer name fragment and optional Employer type;
2. submit a search explicitly;
3. review one bounded page of minimized results;
4. load the next page with the same filter-bound cursor when available;
5. select a result and view the existing minimized Employer detail;
6. create one draft Employer using only `employer_type` and `display_name`;
7. understand loading, initial, empty, success, validation, forbidden, unavailable, unknown-outcome, and unexpected-error states in English or Spanish;
8. complete the workflow with keyboard and screen-reader semantics.

The UI is an interface to server authority. It does not grant permissions, infer access from visible controls, broaden search, or create a separate data authority.

### 1.2 Route and navigation

- `/` redirects to `/employers`.
- `/employers` is the only product route in this slice; its navigation link alone carries `aria-current="page"`.
- Search text, selected Employer name/type, cursor, and API problem detail never appear in URL path, query, or fragment.
- Selection is in-memory component state and is intentionally lost on refresh.
- Unknown routes render a small localized not-found page with a link to `/employers`; no navigation item is marked current there.
- The shell has named `banner`, `navigation`, and `main` landmarks.

### 1.3 Browser-state and privacy rules

- No `localStorage`, `sessionStorage`, IndexedDB, Cache API, service worker, cookies created by this frontend, analytics, telemetry SDK, or error-reporting SDK.
- Treat browser back/forward-cache restoration as persistence: invalidate/abort reads on `pagehide`, and on `pageshow` with `persisted === true` force a canonical reload through a tiny testable navigation seam before restored Employer/form state is reused. Do not use fetch `keepalive`. If the operator leaves despite an unknown-create warning, the accepted in-memory-key-loss rule applies and the fresh workspace instructs search-before-create.
- Employer/search forms and text inputs set browser autocomplete off and disable spellcheck, autocorrect, and autocapitalization so household/person-identifying names are not intentionally offered to browser form-history or language services. Tests assert these attributes; live browser policy still requires separate validation.
- No Employer names/types, search text, cursor, command ID, or API payloads in `console.*`, thrown error messages, DOM data attributes, page title, or browser navigation URL. The selected Employer UUID necessarily appears only in the existing exact-detail staff API request path; it never becomes a UI route/query/fragment or link/referrer target.
- Render accepted Employer values only through React text nodes. Do not use `dangerouslySetInnerHTML`, DOM `innerHTML`/`outerHTML`, `document.write`, string-to-markup parsing, dynamic script/style injection, or Employer values in attribute/class/URL construction; hostile-looking fixture text must remain inert text.
- Tests use fixed obviously fictional sentinel values only and no inline/file snapshots, `screen.debug`/`prettyDOM`, raw payload equality diagnostics, or test-log artifacts. Configure the Testing Library error boundary/test helpers to redact input/text values and API-shaped objects from custom diagnostics; tests assert narrow roles/fields rather than serializing whole responses, and CI uploads only the two SBOM artifacts.
- Browser evidence is a textual checklist only. Do not capture/upload screenshots, video, DOM dumps, HAR/network exports, traces, or storage exports containing Employer/API values.
- `fetch` uses relative same-origin paths, `cache: "no-store"`, `credentials: "same-origin"`, `mode: "same-origin"`, `redirect: "error"`, `referrerPolicy: "no-referrer"`, and `Accept: "application/json"`.
- Write/search requests use `Content-Type: application/json`.
- The frontend keeps only current in-memory form, result page, cursor, selected detail, and one pending create-command identifier.
- Component unmount or superseding requests abort in-flight reads through `AbortController`; an abort is not shown as an application error.
- Frontend validation improves usability but never substitutes for server validation or authorization.
- All displayed Employer data is fictional synthetic data created for tests/walkthroughs; it is never copied, transformed, hashed, or derived from client/live records.

### 1.4 Existing API contracts consumed with one header-only hardening

#### Search

```text
POST /api/staff/v1/employers/search
```

Request:

```json
{
  "display_name_query": "synthetic",
  "employer_type": "household",
  "page_size": 25,
  "cursor": null
}
```

Rules:

- name is required, normalized/trimmed by the backend, and 2–100 characters;
- UI applies the same obvious length/control-character guard for immediate feedback without claiming canonical normalization;
- type is absent, `household`, or `business`;
- page size is fixed by this UI at `25` and is not user-configurable;
- cursor is opaque and never parsed, displayed, logged, or persisted;
- changing either filter clears items, selection, and cursor;
- search never executes on mount or on every keystroke;
- no unfiltered request and no type-only request is emitted.

Accepted search-item fields parsed into typed in-memory state:

```text
employer_id, employer_type, display_name, lifecycle_status, version, received_at
```

After validating the accepted shape, project only `employer_id`, `employer_type`, `display_name`, and `lifecycle_status` into UI state. The UUID supports exact-detail selection; discard version/timestamp because this slice does not need them. The UI does not infer totals, relevance, or completeness.

#### Detail

```text
GET /api/staff/v1/employers/{employer_id}
```

The ID originates only from an accepted search/create response. Parse/pick only the approved detail shape:

```text
employer_id, employer_type, display_name, lifecycle_status, source_channel,
version, received_at, created_at
```

After validating the accepted shape, require detail response ID to equal the requested ID and require create response ID to be a valid UUID. Project only `employer_id`, `employer_type`, `display_name`, `lifecycle_status`, and `source_channel` into UI state. Render all but the UUID. Discard version/timestamps and do not render creator, receipts, audit events, raw response, or an edit/export action.

#### Create

```text
POST /api/staff/v1/employers
Idempotency-Key: <browser-generated UUID v4>
```

Request:

```json
{
  "employer_type": "household",
  "display_name": "Synthetic Household 001"
}
```

Create behavior:

- generate the command ID with `crypto.randomUUID()` at first valid submit;
- snapshot an immutable `{commandId, submittedPayload}` attempt separately from editable draft state, and retain it while the outcome is pending, unknown, or retryable;
- disable all create fields and duplicate submission while one request is pending so user interaction cannot replace the only retry-safe key/payload pair;
- reuse the same ID for explicit retry of the unchanged payload;
- clear the attempt only after authoritative success, a definitive no-commit response, or explicit abandonment; after an unknown outcome, input change must first confirm abandonment and complete the search-before-resubmit path for the prior submitted name;
- register a generic `beforeunload` warning while a request is pending or its outcome is unknown, remove it after resolution/abandonment, and never place Employer values in the warning;
- never expose the ID in the DOM, URL, logs, analytics, or translated copy;
- treat the existing `201` response as success for both first execution and replay; do not render the `Idempotency-Replayed` header;
- use the returned detail-shaped representation directly for success; do not issue an unnecessary detail read;
- do not add autosave, batch create, duplicate detection, update, delete, lifecycle transitions, contact/worksite/request fields, or browser-side receipt history.

### 1.5 Runtime response guard

Before data enters UI state, test and enforce all of the following without carrying unknown properties forward:

- accepted success responses declare an `application/json` media type; missing or different success content type is contract-invalid and the client never falls back to rendering text/HTML;
- every response/page/item is a non-null object and search `items` is an array of at most the requested 25 records;
- `employer_id` is a syntactically valid hyphenated UUID; detail IDs equal the requested ID;
- `employer_type` is exactly `household` or `business`, `lifecycle_status` is exactly `draft`, and detail/create `source_channel` is exactly `staff_entry`;
- `display_name` is an NFC-normalized nonblank string of at most 200 Unicode code points with no control characters;
- `version` is a positive safe integer;
- `received_at`/`created_at` are RFC 3339 strings with an explicit `Z` or numeric offset and a valid calendar/time value; they are then discarded rather than formatted/rendered;
- search `next_cursor` is `null` or a nonempty string no longer than the backend's 512-character cursor input bound; it remains opaque;
- extra properties are ignored at the parser boundary rather than spread into state, DOM, diagnostics, snapshots, or logs;
- every malformed case returns only `unexpected` for reads/search or `unknown_outcome` for create and never throws a formatter error or reflects raw data.

### 1.6 Error and create-attempt mapping

The API client converts transport/status/shape failures into a narrow internal union without preserving or reflecting submitted values or arbitrary backend detail:

```ts
type ApiFailureKind =
  | "validation"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "unavailable"
  | "unknown_outcome"
  | "unexpected";
```

- create `400` (invalid browser-generated idempotency key), `403`, and `422` are definitive pre-command failures: discard that attempt, preserve only safe editable draft values, and require a fresh UUID after correction/reauthorization; a client-generated invalid UUID is also recorded as implementation/contract drift;
- create `409` means the key is already bound to a different payload: never retry or silently regenerate it; require explicit abandonment plus search-before-resubmit because the conflicting prior command may identify another Employer;
- search/read `400`, `409`, and `422`: localized bounded correction guidance appropriate to the operation;
- `403`: localized access-denied state; do not imply the record exists.
- `404` detail: localized not-found state; clear stale detail.
- `500` and `503` during reads/search: localized unavailable/unexpected state; no raw detail.
- network failure, `500`/`503`, any unrecognized status, an unexpected 2xx status, or an unreadable/contract-invalid `201` body during create: `unknown_outcome`; the server may have committed, so retain the immutable attempt and offer retry of the exact unchanged payload;
- network failure during reads: unavailable; retry is allowed without idempotency semantics.
- malformed success JSON or a success body outside the narrow runtime guard during reads/search: unexpected.
- `response.statusText`, response body text, exception message, URL, headers, and submitted values are not rendered or logged.
- for every status not accepted by that operation—including recognized errors, create `200`, unexpected 2xx, and unrecognized statuses—cancel the unread response stream without parsing, retaining, logging, or reflecting it; cancellation failure is swallowed into the same bounded operation-specific classification and never exposes body data. For expected `200` read/search or `201` create success, validate the JSON media type before parsing and cancel the unread body if the media type is missing/wrong; otherwise consume only through the guarded JSON parser and immediately discard parsed contract-invalid data.

### 1.7 English/Spanish and accessibility contract

- English and Spanish are both complete from the first merge.
- A typed two-locale catalog makes missing keys a TypeScript error.
- Typed/catalog tests prove key completeness, not translation accuracy. Classify the initial operational labels/help/errors as Proposed; record a fluent English/Spanish review before the mandatory bilingual walkthrough and require client/counsel approval separately for any later legal/policy content.
- Language defaults to English for this synthetic tracer and is not persisted.
- This non-persistence is an explicit local/no-identity exception to the eventual changeable-preference requirement in `docs/governance/language-requirement-english-spanish.md`. Record the catalog version, Proposed review state, and review owner in source/review evidence; persist preference with provenance only after a separately approved identity/session design, and revisit before live use.
- The language toggle updates the document `lang` value and every affected label/state atomically.
- Store canonical enums/failure kinds in state, never pretranslated strings, so changing locale re-renders current loading/empty/error/success/detail states without another API request.
- Legal/policy translations and client terminology are not invented; this slice contains only ordinary interface copy.
- Every input has a persistent programmatic label and linked error message.
- Validation summary and async status use deliberate `role="alert"` / `aria-live` behavior without duplicate announcements.
- Focus moves to the first invalid input after failed submit, to the result summary after search completion, and to the detail heading after selection/detail completion.
- State is conveyed through text and structure, never color alone.
- Visible focus meets contrast expectations.
- CSS honors `prefers-reduced-motion: reduce`.
- Layout remains usable at 320 CSS px without two-dimensional scrolling for ordinary content.
- Automated semantic and `axe-core` checks are required, but do not replace the mandatory pre-merge keyboard/browser walkthrough in Task 13.
- API timestamps are validated at the client boundary and discarded; this slice renders no date/time value, so it makes no locale/time-zone formatting decision.

### 1.8 Visual boundary

No approved Golden Rose logo, palette, typography, or final brand system exists in the repository. Therefore:

- use system fonts;
- use a neutral, high-contrast operational palette through CSS custom properties;
- use restrained borders/surfaces and one non-status accent for interactive focus/actions;
- use no stock logo, rose graphic, gradients, animation flourish, icon package, Tailwind, component framework, or third-party font;
- label the visual system provisional in documentation;
- reserve success/warning/error colors for status and pair them with text;
- do not claim client brand approval.

## 2. Explicit non-scope and hard stops

This slice adds none of the following:

- real staff identity, login, logout, MFA, session/recovery UI, role editor, bearer-token handling, or permission decisions;
- public worker/employer routes or public/staff credential sharing;
- Employer update/delete/lifecycle transition/correction history;
- EmployerContact, Worksite, StaffingRequest, ShiftNeed, requirements, assignment, worker, referral, payment, document, message, map, dashboard, calendar, count, export, bulk action, or exact-location behavior;
- contacts, phone, email, exact address, free-text duties/requirements, worker data, protected traits, or live/client data;
- automatic matching, ranking, eligibility, suitability, referral, hiring, or prioritization;
- CORS widening, backend route/schema/database/index/migration changes beyond the explicit create-success `no-store` header hardening, audit events for reads, or new backend authorization semantics;
- production hosting, FastAPI static serving, CDN/object storage, Cloud Run, GCP configuration, domains, TLS, CSP deployment headers, secrets, monitoring, analytics, or public exposure;
- a service worker, offline mode, browser persistence, URL-carried search state, CSV/PDF/print export, or deep links to records;
- final brand approval, legal/policy copy, or client-approved translations.

Stop and return to planning if implementation appears to require any item above, any backend contract change beyond the explicit create-success `no-store` header hardening, a new third-party runtime data recipient, or real records.

## 3. Proposed file topology

```text
src/golden_rose/api/staff/employers.py
tests/integration/api/test_staff_employers.py
tests/unit/api/test_employer_schemas.py
apps/web/
  .npmrc
  .nvmrc
  package.json
  package-lock.json
  index.html
  tsconfig.json
  tsconfig.app.json
  tsconfig.node.json
  vite.config.ts
  eslint.config.js
  scripts/
    validate-lockfile.mjs
    validate-lockfile.test.mjs
  src/
    main.tsx
    styles.css
    app/
      App.tsx
      App.test.tsx
      AppShell.tsx
      AppShell.test.tsx
      NotFoundPage.tsx
    api/
      employerClient.ts
      employerClient.test.ts
      employerContracts.ts
    employers/
      EmployerWorkspace.tsx
      EmployerWorkspace.test.tsx
      EmployerSearch.tsx
      EmployerDetail.tsx
      EmployerCreateForm.tsx
    i18n/
      LanguageProvider.tsx
      LanguageProvider.test.tsx
      messages.ts
    test/
      axe.ts
      renderApp.tsx
      setup.ts
.github/workflows/application-quality.yml
README.md
SECURITY.md
TECHNICAL_REQUIREMENTS.md
ARCHITECTURE.md
TECHNOLOGY_DECISIONS.md
CURRENT_WORK.md
ROADMAP.md
NOTES.md
docs/adr/ADR-0005-phase-1-employer-workspace-frontend-boundary.md
docs/review-handoffs/YYYY-MM-DD-phase-1-employer-workspace-review-handoff.md
```

Do not create generic `components/`, `hooks/`, global state, generated API client, design-system package, or abstraction layer unless a concrete test in this slice requires it.

## 4. Dependency and build contract

### 4.1 Runtime dependencies

Pin exact versions in `apps/web/package.json` and lock them:

```json
{
  "react": "19.2.8",
  "react-dom": "19.2.8",
  "react-router-dom": "7.18.2"
}
```

### 4.2 Development dependencies

Pin a mutually compatible set rather than blindly selecting every latest package:

```text
@eslint/js 10.0.1
@testing-library/jest-dom 7.0.0
@testing-library/react 16.3.2
@testing-library/user-event 14.6.3
@types/node 22.20.1
@types/react 19.2.18
@types/react-dom 19.2.4
@vitejs/plugin-react 6.0.5
@vitest/coverage-v8 4.1.10
axe-core 4.13.0
eslint 10.8.0
eslint-plugin-react-hooks 7.1.1
eslint-plugin-react-refresh 0.5.3
jsdom 30.0.1
typescript 5.9.3
typescript-eslint 8.66.0
vite 8.2.1
vitest 4.1.10
```

Re-query and re-check engine/peer compatibility at implementation kickoff. A later version is not automatically authorized. Any version change from this packet must be recorded in `NOTES.md` with the compatibility reason and included in independent dependency review.

### 4.3 Scripts

`apps/web/package.json` exposes:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 127.0.0.1",
    "lint": "eslint . --max-warnings 0",
    "validate:lock": "node scripts/validate-lockfile.mjs package-lock.json",
    "test:lock": "node --test scripts/validate-lockfile.test.mjs",
    "test": "vitest run",
    "test:coverage": "vitest run --coverage",
    "typecheck": "tsc -b --pretty false",
    "verify": "npm run validate:lock && npm run test:lock && npm run lint && npm run typecheck && npm run test:coverage && npm run build"
  }
}
```

The implementation must contain a real `index.html` entry to `src/main.tsx`; tests/typecheck without a production build do not qualify the slice.

### 4.4 Coverage

Use V8 coverage with explicit `coverage.include: ["src/**/*.{ts,tsx}"]` so Vitest 4.1.10 includes matching unimported production files, plus deliberate exclusions only for `main.tsx`, test helpers, and declaration/type-only files. Do not use the removed historical `coverage.all` option. Enforce global floors of 90% statements, 90% lines, 90% functions, and 85% branches. Do not lower a floor or exclude a product file merely to pass; any proposed gate change requires a reviewed planning amendment with the uncovered behavior explained.

## 5. Exact TDD execution nodes

For every quoted frontend test name below, run the exact focused form `npm --prefix apps/web test -- <test-file> -t "<test name>"`; first observe the stated missing-behavior assertion/import failure, implement only the named minimal production boundary, rerun the same command to GREEN, then rerun that entire test file. A node is not complete from a later broad-suite pass alone. Static/configuration checks are explicitly classified when they cannot produce a behavior RED.

### Task 1: Re-baseline the coding lane and prove the inherited backend

**Objective:** Start from the reviewed merged planning tip with no historical branch drift.

**Files:** None.

1. Obtain explicit approval for repository operations.
2. Run `git status --short --branch`, `git fetch origin --prune`, `git switch develop`, and `git merge --ff-only origin/develop`.
3. Verify `git rev-parse HEAD` equals `git rev-parse origin/develop` and the worktree is clean.
4. Read `AGENTS.md`, this plan, ADR-0005, ADR-0002, ADR-0004, `CURRENT_WORK.md`, and the affected backend routes/schemas/tests.
5. Run `env -u PYTHONPATH uv run pytest tests/unit -q`.
6. Create `feat/staff-employer-workspace` from that exact tip.
7. Record observed baseline evidence in `NOTES.md` only after the branch exists.

Expected: no code changes, inherited tests green, no service started.

### Task 2: Close the create-success response-cache gap before browser consumption

**Objective:** Ensure the existing sensitive create representation is non-cacheable without changing its status, body, idempotency, or authority contract.

**Files:**

- Modify `tests/integration/api/test_staff_employers.py`
- Modify `tests/unit/api/test_employer_schemas.py`
- Modify `src/golden_rose/api/staff/employers.py`

1. Add `"accepts a normalized display name of exactly 200 Unicode code points"` beside the existing 201-character rejection in `tests/unit/api/test_employer_schemas.py`; require successful model construction and the exact retained 200-code-point value. Run both exact boundary nodes. This is an inherited-contract characterization expected to pass immediately, not a fabricated RED; if it fails, stop and return to planning rather than changing the accepted schema boundary.
2. Obtain explicit scoped approval, then start only the repository test database with `docker compose --env-file .env.test up -d postgres-test`; use the ignored approved test configuration, wait for health, set the required test/application environment without printing credentials, and run `env -u PYTHONPATH uv run alembic upgrade head` before the integration test.
3. RED: extend `test_post_staff_employers_returns_201_and_exact_body_for_permitted_request` and `test_post_staff_employers_identical_replay_returns_same_resource_with_replay_header` to require `Cache-Control: no-store` on both `201` responses while preserving the existing `Idempotency-Replayed: true` assertion on replay.
4. Run `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py::test_post_staff_employers_returns_201_and_exact_body_for_permitted_request tests/integration/api/test_staff_employers.py::test_post_staff_employers_identical_replay_returns_same_resource_with_replay_header -q`; confirm both fail only on the missing response header rather than service/setup drift, then retain `env -u PYTHONPATH uv run pytest tests/integration/api/test_staff_employers.py -q` as the file-level GREEN regression.
5. GREEN: set `response.headers["Cache-Control"] = "no-store"` on the existing create route before returning the unchanged `DraftEmployerResponse` for both fresh and replayed execution. Do not alter status code, body, error mapping, or replay semantics.
6. Rerun the exact 200/201 schema-boundary nodes, the focused integration tests, and then the existing create/read/search API regression subset. Stop/clean the test service with `docker compose --env-file .env.test down`, verify no repository container/process remains, and record cleanup evidence when finished.
7. Commit this bounded prerequisite separately as `fix(api): prevent caching employer create responses` so review can distinguish inherited API hardening from frontend implementation.

Stop if the regression exposes any wider cache/middleware contract change; return that finding to planning rather than broadening this node.

### Task 3: Add the smallest buildable frontend harness and force the first shell RED

**Objective:** Establish only enough runtime/test configuration to express a meaningful missing-shell test.

**Files:**

- Create `apps/web/.nvmrc`
- Create `apps/web/.npmrc`
- Create `apps/web/package.json`
- Create `apps/web/package-lock.json`
- Create `apps/web/index.html`
- Create `apps/web/tsconfig.json`
- Create `apps/web/tsconfig.app.json`
- Create `apps/web/tsconfig.node.json`
- Create `apps/web/vite.config.ts`
- Create `apps/web/eslint.config.js`
- Create `apps/web/scripts/validate-lockfile.mjs`
- Create `apps/web/scripts/validate-lockfile.test.mjs`
- Create `apps/web/src/test/setup.ts`
- Create `apps/web/src/app/AppShell.test.tsx`

1. Pin Node `22.22.3` in `.nvmrc`; set `packageManager` to `npm@10.9.8` and exact `engines.node`/`engines.npm` constraints in `package.json`. Use `.npmrc` with `engine-strict=true`, `save-exact=true`, `ignore-scripts=true`, `fund=false`, `audit=false`, and `registry=https://registry.npmjs.org/` so install behavior/source are explicit and the separately recorded audit command remains the gate. Assert exact `node --version` and `npm --version`, then use `npm --userconfig apps/web/.npmrc config get registry` and `npm --userconfig apps/web/.npmrc config get ignore-scripts` for the app-local values; a root-level `npm config get` does not prove that the future app-local `.npmrc` was selected. Stop on any drift rather than silently rewriting the lockfile. Pin exact package versions, ESM mode, scripts, strict TypeScript, jsdom, test setup, and coverage include/exclude. Configure Vite development at `127.0.0.1:5173` and preview at `127.0.0.1:4173`, both with strict ports and a fixed local-only `/api` proxy target of `http://127.0.0.1:8000`; keep proxy origin rewriting disabled. Set `build.sourcemap: false`. Do not add an environment-controlled arbitrary proxy target or non-loopback host in this slice; the built browser artifact uses relative paths and contains no embedded backend origin.
2. Write `validate-lockfile.test.mjs` first using only `node:test`/`node:assert`. Require lockfile version exactly 3; a root package entry whose dependency/devDependency maps exactly match `package.json` and contain exact SemVer literals rather than ranges/tags/aliases/protocols; and, for every non-root fetched package, no link/local/git source, an HTTPS URL with exact origin `https://registry.npmjs.org`, no credentials/port/query/fragment, a `.tgz` path, and a valid `sha512-...` SRI value decoding to 64 bytes. Include failing fixtures for root/package-manifest drift, ranged/URL/tag/alias specs, missing/wrong lock version, alternate host, HTTP, credentials, query/fragment, `file:`/git/link, missing integrity, and weak/malformed integrity. No exception exists in this slice; any future exception must be an exact package-entry/source allowlist with written rationale and independent review, never a wildcard/skip.
3. Run `node --test apps/web/scripts/validate-lockfile.test.mjs`; verify meaningful RED because the validator module is absent, not because Node/config cannot load. Implement the smallest stdlib-only fail-closed validator and rerun that exact command to GREEN.
4. Generate the lock with `npm --userconfig apps/web/.npmrc install --package-lock-only --ignore-scripts --prefix apps/web`, then run `node apps/web/scripts/validate-lockfile.mjs apps/web/package-lock.json` before any dependency install and inspect the dependency-spec/lock diff. Do not use caret/tilde/URL/git/file dependency specs or accept registry, lifecycle, source, integrity, or lockfile-version drift.
5. Write `"renders the staff workspace landmarks"` in `AppShell.test.tsx`, importing `AppShell` and requiring named banner/navigation/main landmarks plus the Employers current-link state.
6. Run `npm --prefix apps/web test -- AppShell.test.tsx -t "renders the staff workspace landmarks"`.
7. Verify meaningful RED because `AppShell` is missing, not because dependencies/configuration cannot load; Task 4's minimal `AppShell` markup is the GREEN boundary.
8. Commit only after the next task turns this node green; do not commit a knowingly red branch.

### Task 4: Implement the minimal shell, route, and production entry

**Objective:** Make the shell test green and prove `/` → `/employers` routing plus a real Vite build entry.

**Files:**

- Create `apps/web/src/main.tsx`
- Create `apps/web/src/app/App.tsx`
- Create `apps/web/src/app/App.test.tsx`
- Create `apps/web/src/app/AppShell.tsx`
- Create `apps/web/src/app/NotFoundPage.tsx`
- Create `apps/web/src/styles.css`
- Modify `apps/web/src/app/AppShell.test.tsx`

1. Implement only enough shell markup and nested routing to satisfy the first test.
2. Add `"routes root employers and unknown paths safely"` in `App.test.tsx` for `/`, `/employers`, and an unknown path; assert `aria-current="page"` exists only on `/employers` and is absent on the not-found route.
3. Run the exact focused command and verify RED because redirect/not-found/current-link behavior is absent.
4. Add explicit redirect, canonical route, `Outlet`, and localized-placeholder not-found structure without implementing Employer behavior.
5. Verify both shell and route tests green.
6. Run `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build`; verify `dist/` is produced and ignored.
7. Commit: `feat(web): add staff workspace shell`.

### Task 5: Add typed English/Spanish parity before product copy widens

**Objective:** Make every shell and future state consume one compile-time-complete two-locale catalog.

**Files:**

- Create `apps/web/src/i18n/messages.ts`
- Create `apps/web/src/i18n/LanguageProvider.tsx`
- Create `apps/web/src/i18n/LanguageProvider.test.tsx`
- Modify shell/app tests and components

1. Write `"switches all shell copy and document language"` in `LanguageProvider.test.tsx`, proving the toggle changes the shell heading, navigation label, toggle accessible name, and document `lang` from English to Spanish and back; verify RED because no provider/toggle exists.
2. Implement only the minimal in-memory provider/toggle and initial typed shell keys needed for that node; do not read/write browser storage or infer language from identity/location/name. Rerun the exact toggle node to GREEN.
3. Only after that GREEN, write `"keeps versioned English and Spanish catalogs complete"` to require a Proposed catalog version/review state, exact key parity, representative Spanish Unicode/diacritic copy, and no fallback key tokens; verify RED because version/review metadata and complete parity are absent.
4. Derive the complete Spanish catalog type from the English keys and add the minimal version/review metadata so a missing/extra key fails typecheck; rerun the exact parity node to GREEN.
5. Verify both focused locale tests, the entire locale test file, and typecheck green. Do not add the parity/fallback assertion only after implementation and misclassify it as RED evidence.
6. Commit: `feat(web): add bilingual interface catalog`.

### Task 6: Define and harden the narrow Employer API client

**Objective:** Prove exact request methods/paths/bodies/headers, defensive response guards, no-store fetch behavior, abort handling, and safe failure classification.

**Files:**

- Create `apps/web/src/api/employerContracts.ts`
- Create `apps/web/src/api/employerClient.ts`
- Create `apps/web/src/api/employerClient.test.ts`

Execute one RED→GREEN node at a time in `employerClient.test.ts`:

1. `"sends the bounded search contract"`: RED on absent `searchEmployers`; require POST `/api/staff/v1/employers/search`, exact body/fixed page size/optional type/opaque cursor, no-store/same-origin mode+credentials, redirect refusal, no-referrer policy, JSON headers, and caller abort signal. GREEN is `searchEmployers` request construction only.
2. `"rejects contract-invalid search responses"`: RED while malformed values are accepted; cover missing/wrong success content type, null/non-object pages/items, non-array or over-25 `items`, invalid UUID, enum/lifecycle literals, blank/over-200/control/non-NFC names, non-positive/non-integer versions, malformed/offset-free timestamps, and empty/over-512/non-string cursors. GREEN is a narrow parser satisfying Section 1.5, ignoring rather than retaining extra properties.
3. `"sends and validates exact detail"`: RED on absent detail client; require encoded UUID path, GET/no body, all Section 1.3 fetch defaults, complete value validation, and requested/returned ID equality. GREEN is `getEmployer` plus UUID rejection before fetch.
4. `"sends create with caller command identity"`: RED on absent create client; require exact POST body/headers, all Section 1.3 fetch defaults, and accept only a contract-valid `201` for fresh or replay. Explicitly prove `200` is unknown outcome. GREEN is `createEmployer` with caller-supplied UUID and no replay-header rendering.
5. `"maps failures and disposes unread bodies without reflection"`: RED while status/network/malformed-body data escapes or unread streams remain live; cover recognized error statuses, create `200`, unexpected 2xx, unrecognized statuses, and expected-status responses with missing/wrong media type using cancellable mock streams. GREEN cancels each unaccepted/unread body without parsing it, swallows cancellation failure into the same bounded classification, and proves no body text/JSON reader is called and no raw body/detail/status text, URL, headers, or submitted value enters returned/thrown objects or console mocks. Valid expected `200` read/search and `201` create responses use only the guarded JSON parser; parsed invalid data is discarded.
6. `"classifies aborted reads silently"`: RED while `AbortError` becomes user-visible failure. GREEN is a private abort sentinel handled silently by read callers.

For each node use `npm --prefix apps/web test -- employerClient.test.ts -t "<exact test name>"`, then rerun `npm --prefix apps/web test -- employerClient.test.ts`.

Commit: `feat(web): add bounded employer API client`.

### Task 7: Build explicit-search initial, validation, loading, empty, error, and result states

**Objective:** Add a bounded search UI that cannot issue unfiltered/type-only requests or leak filter state to URLs/storage.

**Files:**

- Create `apps/web/src/employers/EmployerWorkspace.tsx`
- Create `apps/web/src/employers/EmployerSearch.tsx`
- Create `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify `apps/web/src/app/App.tsx`

Execute these exact `EmployerWorkspace.test.tsx` nodes:

1. `"shows search instructions without fetching on mount"`: RED while the workspace/form is absent; GREEN is initial instructions/form with no request and no fake empty claim.
2. `"blocks invalid and type-only searches"`: RED while invalid input can fetch; cover blank, one-character, over-100, and control-character names, linked error/focus, and type-only submission. GREEN is client-side usability validation only.
3. `"submits one explicit bounded search"`: RED while no request/loading state exists; GREEN issues one request only on submit, prevents duplicate activation of the same submitted snapshot while keeping filters available to supersede/abort it, exposes bounded busy/status copy, and snapshots submitted filters in memory.
4. `"renders an accepted empty page safely"`: RED while empty success is not represented; GREEN is generic localized no-results copy/focus without interpolating submitted/backend text.
5. `"renders minimized accepted results"`: RED while results are absent; GREEN renders keyboard selection buttons with only name/translated type/lifecycle, retains UUID privately for detail, discards version/timestamp, focuses the result summary, and proves hostile-looking accepted names remain inert text with no injected element/event.
6. `"maps search failures to bounded localized states"`: RED while failure states collapse or reflect raw data; GREEN distinguishes validation/forbidden/unavailable/unexpected with safe focus/live behavior and bounded read retry.
7. `"invalidates pending base search on supersession edit and unmount"`: use deferred promises; RED while late resolve/reject can restore state. GREEN aborts/invalidates on second search, filter edit, or unmount and proves late completion cannot restore results, selection, cursor, errors, or focus announcements.
8. `"keeps search values out of browser side channels"`: RED while privacy/form attributes are absent; GREEN proves no filter/name/type/cursor in navigation URL, storage/console mocks, or DOM data attributes and sets autocomplete/spellcheck/autocorrect/autocapitalize protections.

The first privacy node also adds a focused test for the shared diagnostic redactor: the RED must show sentinel Employer/API values in an unsanitized custom Testing Library error; the minimal GREEN changes only test setup/helpers so the error contains `[REDACTED]` and no raw fixture/payload. Do not sanitize product behavior failures into false passes.

Use fictional synthetic names only, never client-derived values. Commit: `feat(web): add bounded employer search`.

### Task 8: Add filter-bound next-page loading without inventing totals

**Objective:** Consume the existing opaque cursor safely and preserve deterministic visible state.

**Files:**

- Modify `apps/web/src/employers/EmployerSearch.tsx`
- Modify `apps/web/src/employers/EmployerWorkspace.test.tsx`

Execute these exact `EmployerWorkspace.test.tsx` nodes:

1. `"loads the next page with the submitted filters"`: RED while no load-more behavior exists; GREEN stores the opaque cursor privately, renders localized load-more without totals/page numbers, and requests it with the snapshotted filters.
2. `"appends unique accepted results and retires a null cursor"`: RED while page replacement/duplication occurs; GREEN appends new IDs, preserves the first visible copy of duplicates, replaces the cursor, moves focus to the first newly appended result (or the results heading if no new ID survives deduplication), and removes the load-more control when cursor becomes null without leaving focus on a detached node.
3. `"invalidates pending pagination on filter edit new search and unmount"`: use deferred resolve and reject; RED while a late page can append/restore cursor/error. GREEN aborts/invalidates on either edit, a new base search, or unmount and proves late completion cannot alter items, selection, cursor, errors, or focus.
4. `"preserves results and cursor retry after page failure"`: RED while existing items disappear or retry drifts; GREEN adds a separate announced page error and focused retry control, retains the same cursor/filters for retry, and preserves existing results.

Commit: `feat(web): add employer search pagination`.

### Task 9: Add minimized exact-detail selection

**Objective:** Let staff inspect the approved detail contract without adding edit/export/history affordances.

**Files:**

- Create `apps/web/src/employers/EmployerDetail.tsx`
- Modify workspace tests/components

Execute these exact `EmployerWorkspace.test.tsx` nodes:

1. `"loads one exact detail for the selected result"`: RED while selection has no detail request/loading region; GREEN calls detail once from the privately retained accepted UUID.
2. `"renders only matching minimized detail"`: RED while safe detail view is absent; GREEN requires ID equality, renders semantic name/translated type/lifecycle/source as inert text, discards validated version/timestamps, rejects injected markup behavior, and focuses the heading.
3. `"invalidates pending detail on selection filter search and unmount"`: use deferred resolve/reject; RED while stale detail/error can return. GREEN aborts/invalidates on selection change, either filter edit, a new search, or unmount and proves late completion restores nothing.
4. `"maps detail failures without existence or data leakage"`: RED while stale detail remains/raw copy appears; GREEN clears detail and safely distinguishes not-found/forbidden/unavailable.
5. `"omits unapproved detail data and side effects"`: RED while absence/privacy contract is unproven; GREEN asserts no edit/delete/export/audit/contact/worksite/request controls, raw JSON, UUID, creator/cursor/command/event fields, or URL/history/storage change.

Commit: `feat(web): add employer detail panel`.

### Task 10: Add idempotent draft-Employer creation with unknown-outcome recovery

**Objective:** Expose the existing create command without turning retries or double-clicks into duplicate authority writes.

**Files:**

- Create `apps/web/src/employers/EmployerCreateForm.tsx`
- Modify workspace tests/components

Execute these exact `EmployerWorkspace.test.tsx` nodes:

1. `"renders only the bounded fictional create form"`: RED while the form is absent; GREEN adds labeled type/name, fictional-synthetic warning, submit, and no extra fields.
2. `"enforces the inclusive 200-code-point create boundary before fetch"`: RED while invalid data can submit or exact-boundary data is rejected; prove a normalized 200-code-point name is accepted and submitted unchanged, while a 201-code-point name, blank value, control characters, and unsupported/missing type are rejected with linked error/focus and no fetch. GREEN is create-specific validation and must not reuse the 100-character search limit.
3. `"freezes one immutable create attempt while pending"`: use a deferred promise; RED while fields remain editable, the key/payload can drift, or rapid activation sends twice. GREEN snapshots one `{commandId, submittedPayload}`, disables every create field/submit, and issues exactly one request with that UUID/body.
4. `"accepts only valid 201 create success"`: RED while replay/status/body rules drift; GREEN gives fresh/replay the same localized success, clears attempt/form state, renders validated minimized returned detail as inert text without GET, focuses its heading, ignores the informational replay header, and treats `200` as unknown outcome.
5. `"retries an unknown create outcome with the identical attempt"`: RED while network/500/503/unrecognized status/unexpected 2xx/invalid `201` regenerate identity or reflect raw data. GREEN preserves the immutable attempt, displays bounded warning, registers a generic value-free `beforeunload` warning, and proves explicit retry sends the identical key/body.
6. `"requires abandonment and search before changed resubmission"`: RED while editing an unknown attempt silently clears identity. GREEN requires confirmation, states the prior create may have succeeded, searches the prior submitted name before enabling a changed/new attempt, and removes the unload warning only after success or explicit abandonment. Record the accepted reload/crash limit: after the in-memory key is lost, the UI cannot know the outcome and instructs search before create.
7. `"disposes create identity by operation-specific status"`: RED while all statuses share retry behavior. GREEN proves `400`/`403`/`422` discard the definitive no-commit attempt and use a fresh UUID after correction, `409` blocks retry/regeneration until abandonment plus search, and unknown outcomes preserve key/payload exactly.
8. `"keeps create authority data out of browser side channels"`: RED while command/body values can escape; GREEN proves no command ID/submitted body in DOM, URL, history, storage, console, thrown diagnostics, or snapshots.
9. `"keeps created detail authoritative over stale reads"`: start deferred search/page/detail work before a valid create completion; RED while any late resolve/reject can overwrite the created detail or restore stale results/errors. GREEN invalidates/aborts every pending read generation on authoritative create success, clears prior items/cursor/selection, and proves late read completion changes no current state or focus.
10. `"does not restore Employer state from browser back-forward cache"`: populate editable create/search/result/detail state and pending reads, then dispatch `pagehide` followed by `pageshow` with `persisted === true`; RED while values or requests survive. GREEN aborts/invalidates reads on hide and calls an injected canonical-reload seam on persisted restore before state reuse, with no `keepalive` request. Prove an abandoned unknown create returns only to the documented fresh search-before-create guidance, never a reconstructed key or silent retry.

Commit: `feat(web): add draft employer creation`.

### Task 11: Apply provisional accessible styling and interaction hardening

**Objective:** Make the complete slice usable without inventing client branding.

**Files:**

- Modify `apps/web/src/styles.css`
- Create/modify `apps/web/src/test/axe.ts`
- Modify shell/workspace tests

Execute these exact workspace/shell test nodes:

1. `"exposes one ordered semantic workspace"`: RED on missing/incorrect landmarks, heading order, labels, status regions, or multiple mains; GREEN is semantic markup only.
2. `"has no automated axe violations in both locales"`: RED on the first reported violation across English initial/search/detail/create and Spanish core states; GREEN is the smallest semantic/accessibility fix, never a disabled rule without reviewed justification.
3. `"provides focus hooks for every interactive control"`: RED while links/buttons/selects/inputs lack the declared focusable classes/state; GREEN adds hooks and visible-focus CSS tokens.
4. `"uses text and structure for every status"`: RED while a status depends on class/color alone; GREEN adds bounded text/semantic structure.
5. `"honors reduced motion and narrow single-column structure"`: RED while the CSS marker/media rule or narrow-layout hooks are absent; GREEN adds only the reduced-motion query and ordered single-column responsive rules—no drawer.
6. Treat the final CSS token/remote-resource inspection as a configuration/source-review check, not behavior RED evidence: prove every color comes from custom properties, production source maps are absent, and no remote font/image/icon request exists. Task 13 supplies the mandatory visual/focus/contrast/reflow browser evidence that jsdom cannot prove.

Place nodes 1–3 in `App.test.tsx` against the routed complete workspace and nodes 4–5 in `EmployerWorkspace.test.tsx`; use the exact focused command convention above.

Commit: `feat(web): harden workspace accessibility`.

### Task 12: Extend the existing required `application` CI gate

**Objective:** Make frontend quality part of the already-owned required check without adding an unstable required context.

**Files:**

- Modify `.github/workflows/application-quality.yml`
- Modify `apps/web/package.json` if gate scripts require correction

1. Classify the workflow edit as a CI-configuration exception rather than inventing a brittle text-based unit test. Before editing, record the existing ordered backend steps and immutable action SHAs; after editing, review the YAML diff and execute every declared command locally in the same order. If an already-approved YAML/action validator is available, run it; otherwise record that GitHub workflow parsing remains PR evidence rather than claiming local syntax proof.
2. Add `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020` (`v7.0.0`, observed 2026-08-06 using the Node 24 action runtime) with exact Node `22.22.3` and npm cache keyed to `apps/web/package-lock.json`. Re-resolve that release/tag/`action.yml` at implementation time; any replacement SHA/version requires recorded compatibility/security rationale rather than a floating tag.
3. Retain PostgreSQL as the existing job-level service and state its lifecycle truthfully: GitHub provisions it before job steps. Add Node setup after the existing Python/uv setup, keep the existing health wait before the combined quality command, and put frontend checks first inside that command while the already-running healthy database remains idle. Do not claim that frontend checks run before PostgreSQL startup or that this avoids holding the service open. Preserve the existing relative order of every backend command.
4. Assert exact Node/npm values and the app-local registry/`ignore-scripts` values with `npm --userconfig apps/web/.npmrc config get ...`; run the stdlib lock-validator test and validate the real lockfile **before** `npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web`. Fail before install on any engine, lockfile-version, dependency spec, registry source, integrity, local/git/link source, or lifecycle drift.
5. Run `npm --prefix apps/web run verify`.
6. Run `npm --prefix apps/web ls --all` and fail on invalid/extraneous dependency-tree state; record every direct dependency's purpose and license, review transitive lock/SBOM licenses and deprecation notices, and stop for an unknown, incompatible, or newly copyleft license pending explicit repository-owner/legal disposition rather than silently accepting it.
7. Run `npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high` over the complete locked runtime and development tree; this explicit command overrides `.npmrc`'s install-time `audit=false`. Build/test tooling executes in developer and CI trust contexts, so High/Critical findings in dev dependencies are not silently omitted. A temporary registry outage must be reported as an unavailable gate, never as a clean audit.
8. Run `mkdir -p build && npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json`; parse it to require CycloneDX identity and spec version without printing the component inventory to ordinary logs. The generated SBOM stays ignored and is uploaded as CI evidence only.
9. With the job-level PostgreSQL service already healthy, install locked Python dependencies and retain the current exact backend order: lock check → Ruff format/check → mypy → Bandit → `alembic upgrade head` → complete pytest/coverage → `alembic downgrade base` → `alembic upgrade head` → `pip-audit` → backend CycloneDX generation/validation.
10. Upload backend and frontend SBOMs as separately named artifacts with immutable-SHA-pinned upload actions, `if-no-files-found: error`, and `retention-days: 14`; preserve `permissions: contents: read`.
11. Reproduce the same lifecycle/order locally after PostgreSQL service-start approval: start/wait for the database first (matching the job-level service), perform runtime setup, lock provenance validation before install, frontend gates, then the unchanged backend command sequence; run the downgrade/upgrade cycle, stop the service/processes, and record exact results. Without service approval, label the unit/static/frontend run partial rather than CI-equivalent.

Commit: `ci: require frontend quality and SBOM evidence`.

### Task 13: Prove cross-surface contract and complete the mandatory approved browser walkthrough

**Objective:** Qualify the UI against the merged backend without claiming mocked tests alone are a live end-to-end proof.

**Files:**

- Modify focused existing backend API tests only for the explicit create-success `no-store` assertion or if another missing contract assertion is discovered; do not otherwise change backend behavior.
- Create no Playwright dependency in this slice unless separately approved after a demonstrated coverage gap.

1. Obtain the required PostgreSQL service-start approval; start only `postgres-test` with the ignored approved `.env.test`, wait for health, migrate, run the existing backend create/detail/search API tests, then tear down/verify cleanup. If approval is unavailable, pause the implementation—this required contract evidence cannot be replaced by unit tests or later prose.
2. Run all frontend client/component tests against fictional fixtures copied exactly from those accepted contracts.
3. Verify the frontend parser rejects fields/types outside the accepted contract and does not render unapproved fields.
4. With separate required walkthrough approval, start only the disposable local PostgreSQL service, migrate, build the frontend, load the approved ignored test environment into the process without printing values, run `env -u PYTHONPATH uv run uvicorn golden_rose.main:app --host 127.0.0.1 --port 8000`, and run `npm --prefix apps/web run preview`. If approval is unavailable, pause before merge; browser evidence is a completion gate, not optional evidence.
5. Inspect live listeners before using the UI with `lsof -nP -iTCP:8000 -sTCP:LISTEN` and `lsof -nP -iTCP:4173 -sTCP:LISTEN`; both application processes must show only `127.0.0.1`/loopback. A wildcard/non-loopback listener is a stop condition because application code does not independently enforce the local network bind.
6. Use fictional synthetic records only to walk through create → search → load/select detail in English and Spanish. Validate keyboard-only order, focus placement/restoration, status announcements, visible focus/contrast, 200% and 400% zoom/reflow including 320 CSS px, no two-dimensional ordinary-content scrolling, reduced-motion behavior, and navigate-away/back behavior proving a BFCache restore does not recover Employer/form state; record browser/version and the separately named fluent language reviewer/catalog version.
7. Inspect browser console/network/application storage in place: no unexpected error, no URL-carried search value, no remote third-party request, no browser persistence, relative staff API calls only, and no production source map. Record a value-free textual checklist; do not export screenshots, HAR, traces, DOM, console, or storage captures.
8. Stop all started processes/services, verify the listeners/containers are gone, and record commands/results/provenance in `NOTES.md` and the review handoff.
9. Any unvalidated keyboard/focus/contrast/reflow/language item blocks completion; do not convert it to an “honestly unvalidated” merge caveat or claim production accessibility conformance from this bounded walkthrough.

### Task 14: Run complete pre-closeout quality/security verification and independent review

**Objective:** Prove the implemented tree, draft the evidence handoff, and clear independent pre-commit review before living-doc closeout. Final committed-head evidence is Task 16.

**Files:**

- Create the draft `docs/review-handoffs/YYYY-MM-DD-phase-1-employer-workspace-review-handoff.md`; Task 15 reconciles it and the living docs only after review clears.

After explicit approval for the required repository/test operations:

```text
# PostgreSQL was already started and reported healthy before this canonical gate block.
test "$(node --version)" = "v22.22.3"
test "$(npm --version)" = "10.9.8"
test "$(npm --userconfig apps/web/.npmrc config get registry)" = "https://registry.npmjs.org/"
test "$(npm --userconfig apps/web/.npmrc config get ignore-scripts)" = "true"
node --test apps/web/scripts/validate-lockfile.test.mjs
node apps/web/scripts/validate-lockfile.mjs apps/web/package-lock.json
npm --userconfig apps/web/.npmrc ci --ignore-scripts --prefix apps/web
npm --prefix apps/web ls --all
npm --prefix apps/web run verify
npm --userconfig apps/web/.npmrc --prefix apps/web audit --audit-level=high
mkdir -p build
npm --userconfig apps/web/.npmrc --prefix apps/web sbom --sbom-format cyclonedx --sbom-type application > build/frontend-sbom.cdx.json
# parse the generated JSON and require bomFormat == CycloneDX plus specVersion; print no inventory
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run pytest tests/unit -q
# run the complete PostgreSQL-backed suite/migration cycle after the required service approval
git diff --check
git status --short
```

The unit-only line is interim feedback, not completion evidence. The one canonical local/CI-parity sequence is: `docker compose --env-file .env.test up -d postgres-test` → wait healthy without printing credentials → runtime setup and exact Node/npm/app-local config assertions → stdlib validator test plus real lockfile provenance/integrity validation → script-disabled locked frontend install → frontend tree/verify/audit/SBOM checks → locked Python install and backend static/security checks → `alembic upgrade head` → complete pytest/coverage → `alembic downgrade base` → `alembic upgrade head` → Python dependency audit → backend SBOM generation/validation → `docker compose --env-file .env.test down` and listener/container verification. The GitHub job-level service is provisioned before steps and follows the same service-first lifecycle; do not claim CI parity from any reordered sequence. Absence of service approval pauses completion.

Also:

1. draft the review handoff with the observed RED/GREEN, complete PostgreSQL, browser/accessibility/language, dependency/license/audit/SBOM, cleanup, and limitation evidence; do not call it final-head evidence yet;
2. inspect `git diff --stat`, `git diff --name-status`, dependency lock diff, and generated build/SBOM handling;
3. verify no client/live data, secrets, `.env`, `dist`, `node_modules`, coverage output, or generated SBOM is tracked;
4. verify no backend/database/API contract changed beyond the reviewed create-success `no-store` header;
5. document remaining warnings/tool limitations honestly, but do not downgrade mandatory PostgreSQL/browser/accessibility evidence to optional;
6. dispatch independent spec-compliance and security/code-quality review against this exact implementation plus draft handoff;
7. block on every High/Blocker finding and record all severity dispositions;
8. rerun affected nodes after remediation and then repeat the complete pre-closeout gate whenever code, dependency, workflow, or test behavior changes; only a cleared tree proceeds to Task 15.

### Task 15: Align living documents after verified GREEN

**Objective:** Make rollout truth and trust-boundary status match the implemented branch.

**Files:**

- Modify `README.md`
- Modify `CURRENT_WORK.md`
- Modify `ROADMAP.md`
- Modify `NOTES.md`
- Modify `SECURITY.md`
- Modify `TECHNICAL_REQUIREMENTS.md`
- Modify `ARCHITECTURE.md`
- Modify `TECHNOLOGY_DECISIONS.md`
- Modify `AGENTS.md`
- Update and finalize the Task 14 review handoff

Record:

- React/TypeScript/Vite/npm accepted only for this local frontend boundary;
- exact commands/results and honest test counts;
- English/Spanish/accessibility evidence;
- browser privacy/no-persistence/no-third-party-request boundary;
- backend status/body/schema/authority unchanged and the reviewed create-success `no-store` hardening recorded;
- fictional-synthetic/local-only status and no client-derived fixture values;
- GCP/deployment/auth/contact/worksite/request/public/live-data non-scope;
- next gate is independent review and protected PR, not production readiness.

Do not mark Phase 1 complete or claim client acceptance, production accessibility conformance, legal translation approval, real staff authorization, or deployment readiness.

Commit the reconciled living-doc and handoff closeout through the approved workflow as `docs: record employer workspace verification` only after Task 14 review clears. Do not edit tracked files after that commit unless a finding forces a new reviewed commit and a repeat of Tasks 14–16.

### Task 16: Repeat the complete gate on the exact committed head, then use protected PR/CI

**Objective:** Ensure the committed branch presented for review is exactly the cleared tree and obtain final required-CI evidence without creating a post-verification documentation commit.

1. After Task 15 is committed, verify the worktree is clean and obtain the required PostgreSQL service-start approval. Against that immutable final HEAD, repeat the **exact canonical service-first sequence from Task 14**, not a reordered/no-service subset: database start/health → runtime/config assertions → lock-validator test and real lock provenance/integrity validation before install → locked script-disabled frontend install → dependency tree/frontend verify/audit/SBOM → locked Python install/static/security → migration up → complete pytest/coverage → migration down/up → Python dependency audit/backend SBOM → deterministic service teardown/listener/container cleanup. Any unavailable mandatory gate blocks progression.
2. Rerun `git diff --check origin/develop...HEAD`, `git diff --name-status origin/develop...HEAD`, `git diff --stat origin/develop...HEAD`, `git rev-list --count origin/develop..HEAD`, and a redacted local Gitleaks scan over exact `origin/develop..HEAD`; verify no ignored/generated/confidential file is tracked. The regenerated SBOMs remain ignored evidence and must not alter the committed tree.
3. Retain Task 13's browser/language/accessibility evidence only when Task 15 changed reviewed Markdown and no executable/config/lock/test behavior changed after that walkthrough. If any such behavior changed, repeat the affected browser evidence before proceeding; the complete machine gate in step 1 is mandatory on final HEAD regardless of a docs-only closeout commit.
4. Put final-head command results in the PR evidence rather than modifying the branch afterward. Dispatch one final read-only verification that the committed tree, handoff, range evidence, and Task 16 results agree; any finding that causes a commit requires repeating this task.
5. With explicit approval, push the exact branch and open the protected PR to `develop`.
6. Require repository-hygiene and the extended `application` job to pass on that exact remote head, including the complete PostgreSQL/migration/audit/SBOM path. A failed, cancelled, skipped, stale-head, or unavailable required check blocks merge.
7. If review or CI causes any commit, repeat this task—including the full local final-HEAD gate and exact-range Gitleaks—and verify CI against the new head. Do not merge, deploy, start production services, or admit live data in this plan.

## 6. Review checklist

### 6.1 Product/spec compliance

- [ ] Only `/employers` and not-found behavior exist.
- [ ] Search requires explicit bounded name input; no mount/keystroke/unfiltered/type-only search.
- [ ] Cursor remains opaque/filter-bound by server and private in browser memory.
- [ ] Detail/create render only accepted fields.
- [ ] Create validation accepts exactly 200 normalized Unicode code points and rejects 201.
- [ ] Create retry preserves one idempotency key for unchanged unknown outcome.
- [ ] No later domain entity or workflow appears.
- [ ] English/Spanish parity covers every state; catalog version/review state and the named fluent reviewer are recorded.

### 6.2 Security/privacy

- [ ] No authorization is inferred from UI visibility.
- [ ] No real identity/token handling.
- [ ] No browser-navigation/storage/log/analytics leakage; Employer UUID appears only in the required exact-detail staff API path.
- [ ] Browser back/forward-cache restoration forces a fresh value-free workspace; no request uses `keepalive`.
- [ ] Relative same-origin API calls, no-store fetch, no third-party runtime calls.
- [ ] Unaccepted/wrong-media-type response bodies are cancelled without parsing or reflection; accepted bodies use only guarded JSON parsing.
- [ ] Arbitrary problem details and malformed JSON are not reflected.
- [ ] Rapid/stale responses cannot replace current state.
- [ ] No live/client data or secrets.
- [ ] Dependency lock, audit, SBOM, immutable CI action pins, and Gitleaks evidence exist.
- [ ] Lockfile v3 provenance/integrity validation passes before every install; no unreviewed alternate/local/git/link source exists.

### 6.3 Accessibility/localization

- [ ] Landmarks, labels, heading order, focus, live regions, and keyboard paths are tested.
- [ ] `axe-core` automated checks pass for representative English/Spanish states.
- [ ] Document language changes correctly.
- [ ] Status is not color-only; visible focus and reduced motion are present.
- [ ] Mandatory approved browser evidence proves keyboard/focus/contrast plus 200%/400% zoom and 320-CSS-pixel reflow in both languages.

### 6.4 Engineering

- [ ] Every behavior node had an observed meaningful RED before GREEN.
- [ ] Frontend lint/typecheck/coverage/build pass.
- [ ] Backend regressions pass.
- [ ] `index.html` and production build are real.
- [ ] No backend migration/schema/route behavior changed beyond the reviewed create-success `no-store` header.
- [ ] Required `application` check retains backend gates and adds frontend gates.
- [ ] Diff/secret/dependency review is recorded.

## 7. Risks, trade-offs, and revisit triggers

### 7.1 Accepted trade-offs

- Manual narrow runtime parsers duplicate a small amount of Pydantic contract knowledge, but avoid premature code generation and ensure raw JSON is never spread into UI state. Revisit when a second frontend domain contract appears.
- Typed in-repo messages avoid a localization dependency for one route. Revisit when pluralization, server content, or more locales require a mature i18n library.
- Component-local state is sufficient for one workspace. Revisit only when multiple routes need shared cached authority—not before.
- Plain CSS avoids inventing a design-system/vendor dependency before client branding exists. Revisit after client visual review.
- Mocked fetch component tests plus existing backend contract tests are the automated baseline; the mandatory approved loopback browser walkthrough closes manual accessibility/privacy evidence but does not transform the tracer into deployment evidence or production conformance.

### 7.2 Revisit triggers

Return to planning before:

- adding a second domain route/entity or API contract;
- introducing authentication/session/token behavior;
- carrying any Employer value in URL or persistent browser storage;
- adding code generation, state management, i18n framework, UI kit, CSS framework, service worker, analytics, error reporter, or third-party font/icon/map;
- serving the build from FastAPI or selecting production frontend hosting;
- adding contacts, worksites, requests, exact locations, live data, legal/policy content, or client-approved branding;
- changing backend schemas, permissions, error contracts, cache rules beyond the explicit create-success `no-store` hardening, or CORS.

## 8. Completion definition

The implementation slice is complete only when:

1. the browser artifact builds and its tested Employer create/search/detail workflow is green;
2. required English/Spanish, accessibility, privacy, idempotency, error, stale-response, and no-persistence behaviors are proven, including the mandatory browser walkthrough and named fluent catalog review;
3. after the Task 15 closeout commit, the entire Task 14 frontend/audit/SBOM/Python/PostgreSQL/migration/dependency/SBOM gate is rerun green on the immutable final local HEAD;
4. the required CI job includes frontend verification, full locked-tree dependency audit, and SBOM evidence without losing backend gates, and passes on that same pushed head;
5. exact-branch Gitleaks/diff/dependency review and independent spec/security review clear all High/Blocker findings;
6. living docs and review handoff state the local/synthetic and non-deployment boundary honestly;
7. no service, commit, push, PR, merge, infrastructure, public route, or live-data action occurs without its explicit gate.
