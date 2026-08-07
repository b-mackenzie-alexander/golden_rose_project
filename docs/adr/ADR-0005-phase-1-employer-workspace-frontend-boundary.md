# ADR-0005: Phase 1 Employer Workspace Frontend Boundary

**Status:** Accepted
**Date:** 2026-08-06

## Context and evidence posture

PR #11 merged the synthetic/local staff Employer detail and bounded-search tracer into `develop`, completing the first backend path for draft-Employer creation, exact retrieval, and privacy-conscious bounded search. The repository still has no browser application, JavaScript manifest, frontend lockfile, or approved visual-brand specification. Phase 1 is intended to provide a browser-based staff workflow, but later EmployerContact, Worksite, and StaffingRequest implementation remains gated by field requiredness, precise-location treatment, household/general-labor extension decisions, and a deliberate expansion of the current audit/command persistence spine.

The next increment should add product feedback without collecting stronger personal/location data, changing backend authority, selecting production hosting, or coupling this lane to separate GCP planning. After independent architecture/TDD, security/supply-chain, and product/accessibility/localization review cleared all Blocker/High/Medium findings, Beatrice accepted this frontend-tracer product/architecture direction on 2026-08-06. Acceptance does not authorize implementation from this planning branch: the planning packet must first merge to protected `develop`, a fresh implementation session must rebaseline from that merged tip, and implementation repository/service operations remain separately approved.

## Decision

Add one standalone frontend under `apps/web/` for the existing staff Employer API only. Before browser consumption, close the observed response-cache gap by adding `Cache-Control: no-store` to both fresh and idempotently replayed create successes. This header-only hardening does not change create status, body, authorization, idempotency, persistence, schema, or route shape.

Use:

- Node.js 22.22.3, npm 10.9.8, exact engine/package-manager constraints, and an exact committed lockfile;
- React 19.2.8 and React DOM 19.2.8;
- React Router 8.3.0 with `/employers` as the sole product route and `/` redirecting to it;
- TypeScript 5.9.3 rather than TypeScript 7 because the selected `typescript-eslint` line declares support below TypeScript 6.1;
- Vite 8.2.1 and `@vitejs/plugin-react` 6.0.5 for local development and production build verification;
- Vitest, jsdom, Testing Library, `axe-core`, ESLint, and V8 coverage for focused frontend quality evidence;
- the browser `fetch` API with narrow manually guarded Employer request/response types;
- component-local state, one typed in-repository English/Spanish catalog, and plain CSS custom properties;
- relative `/api/staff/v1/...` requests and a loopback-only Vite development/production-preview proxy to the separately started local backend; the built browser artifact embeds no backend origin.

The workspace permits only:

1. explicit bounded Employer search with optional Employer type;
2. opaque-cursor next-page loading with the exact submitted filters;
3. selection and display of the merged minimized exact-detail contract;
4. draft-Employer creation with a browser-generated idempotency UUID retained for retry of an unchanged unknown outcome;
5. explicit, localized initial/loading/empty/validation/denied/not-found/unavailable/unknown/unexpected states.

The browser is not an authority boundary. Server authorization and validation remain controlling even when a control is hidden or disabled.

## Privacy, security, and accessibility constraints

- Keep search values, Employer names/types, cursors, command IDs, problem bodies, and response data out of browser navigation URLs, browser persistence, console output, analytics, telemetry, and arbitrary thrown/rendered text. A selected Employer UUID appears only in the required exact-detail staff API request path, never in the UI route/query/fragment or a link/referrer target.
- Render accepted values only as React text. Prohibit raw/string-to-markup DOM APIs, dynamic script/style injection, and Employer values in attributes/classes/URLs; hostile-looking fictional fixtures must remain inert.
- Use fictional sentinel test values, no snapshots/debug DOM dumps/raw-payload diagnostics, and redacted custom test errors; CI uploads SBOM evidence only, never Employer/API test artifacts.
- Record browser walkthrough evidence as value-free text only; no screenshots, video, DOM dumps, HAR/network exports, traces, or storage exports containing Employer/API values.
- Add no local/session storage, IndexedDB, Cache API, service worker, analytics, error-reporting SDK, remote font, icon service, image request, or third-party runtime recipient.
- Treat back/forward-cache restoration as browser persistence: abort/invalidate reads on page hide and force a canonical fresh reload on persisted page restore before Employer/form state is reused; no API request uses `keepalive`.
- Turn browser autocomplete off and disable spellcheck/autocorrect/autocapitalization on Employer-name inputs; validate actual managed-browser behavior separately before live use.
- Use `cache: "no-store"`, same-origin mode/credentials, redirect refusal, no-referrer policy, relative staff paths, and explicit JSON headers at the client boundary.
- Cancel every unread response stream whose status is not accepted for that operation—including recognized errors, create `200`, unexpected 2xx, and unrecognized statuses—without parsing, retaining, logging, or reflecting body data. For expected `200` read/search and `201` create responses, require the JSON media type before parsing; cancel wrong-media-type bodies and consume valid-media-type bodies only through the strict guarded JSON path.
- Never spread raw JSON into UI state or fall back to rendering response text/HTML. Runtime guards require an `application/json` success media type, non-null objects/arrays, exact enum literals, valid UUID/RFC 3339 values, positive integer versions, bounded opaque cursor shape, and normalized bounded names; they pick approved fields only and map failures to a narrow internal union without reflecting backend detail/status text.
- Abort or invalidate superseded search/detail requests so stale responses cannot replace current state.
- Any approved synthetic runtime walkthrough binds both FastAPI and Vite to loopback and verifies live listeners before use; a wildcard/non-loopback application listener is a stop condition.
- Generate create command IDs with `crypto.randomUUID()`, freeze all create fields while an immutable `{commandId, submittedPayload}` attempt is pending, and reuse that exact attempt after network/500/503/unrecognized-status failure, unexpected 2xx, or unreadable/invalid `201`. Definitive `400`/`403`/`422` responses discard the attempt; `409` blocks retry/regeneration until explicit abandonment plus search. Changing input after an unknown outcome requires confirmation and search-before-resubmit; a generic value-free unload warning remains while pending/unknown.
- The command ID is intentionally tab-memory-only. If a reload/crash loses it after an unknown outcome, the synthetic UI directs staff to search before another create. Durable live-use recovery requires a separately approved design.
- English and Spanish must be functionally complete from the first merge. Legal/policy translations remain separately approved content.
- Typed catalog parity does not prove linguistic accuracy. Initial operational copy remains Proposed pending a fluent English/Spanish review before the mandatory pre-merge bilingual walkthrough; legal/policy copy still requires its separate approval/versioning gate.
- Defaulting to English on reload is an explicit local/no-identity exception to the eventual persisted language-preference requirement. The catalog remains versioned with review ownership; preference persistence with provenance requires a separately approved identity/session design and must be revisited before live use.
- Use semantic landmarks/forms/lists/detail structures, deliberate focus and live-region behavior, visible focus, text-plus-structure status, reduced-motion support, and a 320-CSS-pixel usable layout.
- Automated semantic/`axe-core` checks supplement rather than replace a mandatory pre-merge keyboard/browser walkthrough covering focus, keyboard flow, zoom/reflow at 320 CSS px, contrast, and both languages.
- Use fictional synthetic Employer fixtures only; never copy, transform, hash, or derive values from client/live records.

## Build and CI boundary

The application must include a real Vite `index.html` and module entry and pass lint, TypeScript build/typecheck, component/client tests with coverage, and production build. The existing required `application` GitHub Actions job is extended rather than creating a new unstable required check. It must retain every backend/PostgreSQL/migration/security gate and add immutable-SHA-pinned Node setup, exact Node/npm/config assertions, a stdlib-only pre-install validator that requires lockfile version 3, exact manifest/root-lock dependency agreement, exact-version specs, canonical npm-registry tarball sources, and SHA-512 integrity for every fetched package, lifecycle-script-disabled deterministic install, dependency-tree validation, frontend verification, full locked-tree High/Critical dependency audit, CycloneDX SBOM generation/validation, and bounded SBOM upload. Local final-head qualification follows the workflow's actual service-first lifecycle: start and health-check the disposable PostgreSQL service before the canonical frontend-then-backend gate; the GitHub job-level service likewise exists before job steps.

Backend API/schema/database/migration behavior does not change beyond the explicit create-success `no-store` header. Existing PostgreSQL-backed create/read/search tests, including fresh/replayed create cache assertions, plus the frontend's exact request/response fixtures provide cross-surface contract evidence. A disposable loopback browser walkthrough requires separate service-start approval and is a mandatory pre-merge accessibility/privacy gate; it is not production/deployment evidence or production accessibility conformance.

## Explicit non-decision and non-scope

This ADR does not select or authorize:

- production frontend hosting, GCP resources, FastAPI static serving, CDN/object storage, domain/TLS/CSP deployment configuration, public exposure, secrets, or monitoring;
- real staff identity, login, MFA, sessions, token storage, permission administration, or public/staff credential sharing;
- Employer correction/update/delete/lifecycle transitions;
- EmployerContact, Worksite, StaffingRequest, ShiftNeed, worker, assignment, referral, document, messaging, payment, map, calendar, dashboard, count, export, or bulk behavior;
- phone, email, exact address, work requirements, worker/protected-trait data, client/live data, or legal/policy content;
- matching, ranking, eligibility, suitability, hiring, referral, or prioritization;
- final client branding, a design-system dependency, CSS framework, state-management library, i18n framework, generated API client, service worker, analytics, or external runtime data recipient;
- CORS widening or any backend contract change beyond the explicit create-success `no-store` header.

Any apparent need for those items stops implementation and returns to planning.

## Alternatives considered

- **Implement EmployerContact next:** deferred because contact requiredness/lifecycle remains an explicit pre-implementation discovery and introduces stronger PII plus a deliberate audit/command schema expansion.
- **Implement Worksite or StaffingRequest next:** deferred because exact-location treatment, request requiredness, household/general-labor extensions, and the complete parent-reference chain remain unresolved.
- **Implement Employer revision/correction next:** viable but lower immediate product-learning value than exposing the already-proven create/find path through a browser; correction remains separately planned.
- **Expose an Employer audit timeline next:** deferred because the current Employer has only its creation event, staff-facing actor/audit-field authorization remains separately bounded, and a timeline does not establish the first browser create/find/detail product loop.
- **Add only a read-only search UI:** rejected because the backend already proves safe creation and the smallest useful staff Employer workspace is create plus find/detail. The create behavior remains exactly bounded to two accepted fields and existing server authority.
- **Use Next.js or another server-rendered framework:** rejected because no server-rendering, SEO, public route, or frontend backend-for-frontend need is approved.
- **Keep React Router DOM 7.18.2 exactly as first planned:** rejected after Task 12 CI-parity qualification because the required locked-tree frontend audit surfaced `GHSA-qwww-vcr4-c8h2` on the `react-router-dom`/`react-router` chain while no published `react-router-dom` 8.3.0 package existed to satisfy the workflow's High-severity audit gate. The approved mitigation candidate keeps the single-route declarative browser surface but switches to `react-router` 8.3.0 directly, which exports the exact BrowserRouter/NavLink/Routes/Route/Navigate/Outlet/MemoryRouter surface this tracer uses and clears the required audit gate.
- **Use Tailwind/component library/global state/i18n framework/OpenAPI code generation:** deferred under YAGNI for one route and three existing operations. Revisit only after a concrete second-slice need.
- **Serve the frontend from FastAPI:** deferred because it would couple local UI work to deployment architecture and change the backend/runtime boundary owned by another lane.
- **Put search state in URL or browser storage:** rejected because Employer names may identify households/people and need not enter history, logs, referrers, persistence, or copied links.

## Consequences and constraints

- The repository becomes a small multi-application repository with separate Python and npm lockfiles but no monorepo orchestration tool.
- CI time and supply-chain surface increase; exact pins, lockfile/tree/license review, full runtime-and-development audit, SBOM, build, immutable workflow actions, and independent review become required.
- Manual narrow response guards duplicate a small amount of Pydantic contract knowledge. Revisit shared generation only when a second frontend domain contract makes drift materially likely.
- The typed two-locale catalog and plain CSS are intentionally small. Revisit mature i18n/design tooling only when pluralization, server-authored content, additional locales, or approved brand governance requires it.
- The UI is locally runnable through Vite but has no authorized production deployment path in this ADR.
- The frontend may display sensitive Employer names in-memory and on-screen to the synthetic staff principal; browser/device/screenshot/live-data controls remain unsatisfied and therefore live-data admission remains prohibited.
- Beatrice owns synthetic/local technical acceptance; a separately named fluent English/Spanish reviewer owns catalog review before the mandatory bilingual walkthrough. There is no production support, monitoring, training, or client-acceptance claim, and rollback uses reviewed commit reversion because no migration/live data is introduced.

## Approval and revisit trigger

Beatrice accepted this ADR's bounded product/architecture direction on 2026-08-06 after independent planning rereviews reported no remaining Blocker, High, or Medium finding. PR #12 merged this exact planning packet into `develop` at `b06923a`, so the ADR is now the implementation baseline for the active coding lane. Implementation repository operations are approved in that lane; all service starts remain separately approved.

Revisit before adding a second domain route/entity, identity/session handling, browser persistence, URL-carried record/search state, a new third-party runtime service, production serving/deployment, client branding, legal content, real data, or any backend contract/schema/permission change beyond the explicit create-success `no-store` hardening. The exact execution nodes and gates are controlled by `.hermes/plans/2026-08-06_115420-phase-1-employer-workspace-frontend-plan.md`.
