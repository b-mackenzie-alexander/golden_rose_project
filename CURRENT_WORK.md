# Current Work — Golden Rose Operations Platform

**Updated:** 2026-08-11
**Lane:** Phase 1 post-merge remediation — bounded draft Employer revision
**Verification:** Full local CI-parity verification completed successfully on 2026-08-11: Node/npm/lockfile constraints, locked `uv`/npm installation, frontend verify/audit/SBOM validation, Ruff, mypy, Bandit, Alembic upgrade→downgrade→upgrade, 238 backend tests at 96.14% coverage, pip-audit, backend SBOM validation, and `git diff --check` all passed. Fresh independent rereview then passed with no Blocker/High/Medium findings. The exact uncommitted surface is cleared for a closeout commit, but commit/push/PR/final-head verification require separate execution and authorization.
**Overall status:** PR #17 merged the synthetic/local draft-Employer revision slice into protected `develop` at `1543248`; required checks passed. A fresh post-merge audit found no Blocker/High issues but identified two Medium correctness defects: revision success was not bound to the requested Employer ID in the browser client, and fresh-command no-op/audit-field calculation could race a future-version catch-up under PostgreSQL `READ COMMITTED`. The active `fix/draft-employer-revision-post-merge` branch was created from exact `origin/develop` at `1543248`; both Medium paths are remediated under focused regression coverage, known revision persistence failures are now translated to safe persistence errors, full local verification passed, and independent rereview cleared the exact working tree. The surface is ready for a separately authorized closeout commit, followed by final-head verification and exact-range secret scanning before any push/PR.
**Historical pre-PR #17 status (superseded):** PR #15 merged the independently rereviewed and exact-head-qualified Employer workspace closeout into protected `develop` at `7ae448e`, and PR #16 then merged the accepted ADR-0007 draft-revision planning packet into protected `develop` at `1c66eeb`; required protected checks passed on both promotions. The planning packet is now durable merged authority on `origin/develop`, the merged tip has been reverified in the repository, and Beatrice has explicitly authorized coding from a fresh implementation branch. The active branch is now `feat/staff-draft-employer-revision`, created from exact merged `origin/develop` at `1c66eeb`. Task 1 authority rebaseline is complete. Task 2 cycle 5 remains GREEN, the orphan timing gap remains closed, populated-state downgrade refusal is in place, Task 3 permission hardening is complete, Task 4 create replay authority is fully classified, Task 5 cycles 1-22 are now GREEN or honest GREEN regressions, Task 6 is GREEN locally through the exact OpenAPI route-surface compatibility node, Task 7 client cycles 1-10 are GREEN through the exact revision transport/contract boundary plus routine-browser actor-attribution rejection, Task 8 cycles 1-16 are GREEN through the standalone revision form recovery/accessibility matrix, Task 9 cycles 1-20 are now GREEN through revision side-channel instrumentation across URL/history/storage/console/diagnostic surfaces, Task 10.1 `LANG(keeps exact English and Spanish revision keys in parity)` is an honest GREEN regression, Task 10.2 `FORM(passes axe in both locales across every revision and recovery state)` is GREEN, Task 10.3 `FORM(announces and focuses every revision transition with reduced-motion-safe behavior)` is GREEN, Task 10.4 `WORKSPACE(revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels)` is an honest GREEN regression, Task 10.5 `DIAG(revision controls preserve value-independent Testing Library diagnostics)` is an honest GREEN regression, Task 10.6 `API(test_revision_error_and_exception_diagnostics_are_value_safe)` is now an honest GREEN regression after one setup repair, and Task 10.7 `CLIENT(rejects actor attribution fields from routine revision and detail browser responses)` is GREEN after tightening routine browser detail/revision response parsing to reject leaked actor-attribution fields. The approved Task 10 closeout verification command set has now passed in full: the focused revision/privacy client and workspace files passed with `84 passed` plus the known non-failing jsdom `HTMLCanvasElement.getContext()` warnings during axe coverage, the catalog/client file pair passed with `25 passed`, `npm --prefix apps/web run typecheck` passed, and `git diff --check` passed. A durable pre-PR handoff packet now exists at `docs/review-handoffs/2026-08-11-draft-employer-revision-review-handoff.md`, and the branch is ready for independent review of the local working-tree surface. Human browser/manual accessibility/fluent-language qualification remains deferred until a shared deployed `develop` environment exists. Runtime-role immutability, connection-pool/load qualification, GCP work, public release, live integrations, real identity, and client/production-data use remain unauthorized.

## Active objective
Turn the completed initial discovery baseline into an approved, narrow first delivery: an agency-staff pilot for employer demand entry and retrieval, followed by a governed dashboard and transparent worker/employer comparison aid.

## Current evidence-backed direction
- The agency’s current operation is paper-first and fragmented across workbooks, hosted forms, Trello, calendars, messaging, and manual follow-up.
- Multiple legacy employer and worker forms overlap. The proposed replacement is one canonical staged workflow, not duplicate forms or response stores.
- The first usable product should serve agency members: enter employer demand, find/review requests, work an authorized demand queue, and replace manual metric collection with governed operational data.
- The staff calendar/shift-coverage view must be derived from authoritative operational records, not maintained as a parallel manual store.
- Client-accepted location direction: organize routine operations and reporting through the authorized-staff NYC demand map and broad client-managed service zones; precise worksite and worker/home location remain sensitive, restricted, and separately governed.
- Client-accepted staff-plane roles are Owner, delegated Manager, interchangeable Operations Staff, and a separately bounded Platform Administrator. `docs/planning/phase-1-staff-permission-matrix.md` controls command, field, delegation, exact-address, export-denial, and break-glass boundaries; platform maintenance must not create standing access to operational personal data.
- Employer demand is the proposed first entry workflow because current demand exceeds available worker supply.
- Worker profiles should follow quickly, but self-reported preferences/skills are not verified credentials and must not drive automatic ranking, eligibility, hiring, or referral.
- Public worker/employer access and higher-trust staff administration require materially separate security boundaries.
- Accepted Phase 1 canonical structure: neutral `Employer` → `EmployerContact` / `Worksite` / `StaffingRequest` → `ShiftNeed` / `RequestRequirement`, supported by `WorksiteZoneMembership`, `ServiceZoneComposition`, pinned `MapArea`/`WorksiteMapAreaAssignment`, and `AuditEvent`. Field purposes and exclusions are controlled by `docs/planning/phase-1-canonical-field-purpose-inventory.md`.
- Accepted request/shift lifecycle: guarded request review/open/close states and combined shift/coverage states with reversible coverage, explicit completed/unfulfilled/cancelled outcomes, and exceptional audited reopening to pending review. `docs/planning/phase-1-request-shift-state-model.md` is authoritative.
- Accepted work-queue model: separate review/follow-up/coverage clocks, hybrid business/continuous time, shared accountable ownership, provisional configurable triggers, three-attempt no-response safeguard, and deterministic lanes. `docs/planning/phase-1-work-queue-aging-follow-up-model.md` is authoritative; provisional values are not SLAs and require client validation before production.
- Accepted calendar/coverage model: distinct request milestones and explicit timed shift occurrences; pending/active/historical visibility; timezone-safe intervals; aggregate coverage; permission-gated day/week address reveal; current truth with audit history; and governed drag/rescheduling. `docs/planning/phase-1-calendar-coverage-semantics.md` is authoritative.
- Accepted service-zone model: flat adaptive Owner-managed catalog; optional late assignment; overlapping worksite memberships with one primary/default; visible unassigned work; no double counting; and audited historical correction. `docs/planning/phase-1-service-zone-taxonomy.md` is authoritative; exact names/conventions may emerge through pilot use and do not block implementation.
- Client-accepted NYC map model: mandatory authorized-staff Phase 1 job-demand/coverage map over pinned official DCP 2020 CDTAs; Owner-created zones group fixed cells; automatic provider-neutral server-side address-to-CDTA derivation discards precise coordinates by default; worker supply follows its own contract. `docs/planning/phase-1-nyc-job-demand-map-contract.md` is authoritative.
- Client-accepted permission model: server-enforced named permissions distinguish Owner, delegated Manager, Operations Staff, and separately bounded Platform Administrator; exact worksite reveal is distinct from calendar/map access, exports are disabled, and exceptional support is time-bounded break-glass only. `docs/planning/phase-1-staff-permission-matrix.md` is authoritative.
- Operational questions expected to be answered through implementation, staff walkthroughs, and pilot preparation are tracked in `docs/planning/phase-1-operational-discovery-register.md`. A discovery is not an implementation blocker unless its gate class says the affected slice would otherwise invent durable policy, authorization, schema, or trust-boundary behavior.
- Accepted production identity/support baseline: individual staff identities, mandatory MFA, phishing-resistant factors for privileged/recovery roles, controlled independent recovery, session expiry/revocation, monthly pilot access review, and separated business/technical support ownership. `docs/planning/phase-1-mfa-recovery-support-ownership.md` is authoritative; provider selection, named personnel, rehearsal evidence, and live-data/production activation remain gated.
- Accepted correction/audit baseline: PostgreSQL domain rows hold current operational truth; append-only `AuditEvent` records preserve material history through atomic expected-version/idempotent commands; restricted prior/new values remain field-authorized; and derived projections are disposable rather than competing record stores. `docs/planning/phase-1-correction-audit-event-contract.md` is authoritative.

## Immediate next steps
1. Obtain explicit approval before creating the closeout commit for the exact independently rereviewed working-tree surface.
2. The next coding-session planning artifact now exists at `.hermes/plans/2026-08-11_203958-phase-1-employer-contact-next-session-plan.md`. It names the recommended backend-only `EmployerContact` tracer and its hard decision gates; do not treat it as coding authority until the remediation PR merges and those gates are satisfied.
3. After the closeout commit, run final-head quality verification and exact-range secret scanning on `origin/develop..HEAD`; obtain approval again before push/PR actions.
4. Preserve the deferred-gate truth: human browser/manual accessibility/fluent-language review still waits for a shared deployed `develop` target, and runtime-role immutability/pool-load/GCP/live-data work remain out of scope.

## Gate classification

### Required before the affected synthetic/local implementation slice
- Explicitly accepted, reviewed, and merged narrow implementation plan. PR #10 satisfied this gate for the implemented Employer detail/search tracer. PR #12 now satisfies this gate for the Employer workspace frontend slice, and this fresh session has rebaselined from exact merged `origin/develop` before coding began.
- For this tracer, only `employer_type` and bounded `display_name` are client supplied; the server controls draft state, staff-entry source, identifiers, timestamps, actor, and version. Do not generalize these values into later lifecycle/intake policy.
- Slice-specific data classification, synthetic-fixture procedure, acceptance owner, test/CI evidence, and rollback/forward-recovery posture.

### Discover during implementation; validate before affected live use
- Client terminology, queue business calendar/thresholds, zone/map usability and names, out-of-area handling, correction reasons, office constraints, support/training, and named operational exceptions.
- Named staff assignments/delegations, recovery approvers/executors, support contacts/hours, exact-address recipients, access-review owner, and qualified identity-provider configuration.
- Live renderer/tile/geocoder provider and address-processing posture; synthetic deterministic fixtures remain sufficient for bounded local map implementation.
- Legacy-field treatment, production retention/disposal, restricted-history recipients, production backup/recovery, and production-data admission.
- Public/legal/fee/retention/consent/receipt/agreement behavior requires counsel documentation and client acceptance before the affected software is validated or released. Public-source research remains suggested guidance and does not block unrelated internal staff-workflow implementation.
- Interim cloud-billing and final-payment handoff procedure: Beatrice funds approved infrastructure until final payment; then client billing/account/support ownership transfers through a documented continuity check.

The complete discovery inventory and evidence rules are in `docs/planning/phase-1-operational-discovery-register.md`.

## Hard stop boundaries
- Do not collect or import unrestricted live personal data.
- Do not enable public workflows, uploads, payment, signatures, screening, or vendor integrations.
- Do not encode legacy language, protected-trait/proxy criteria, suggested legal research, fee policy, retention rules, or business terms as validated or production behavior before the applicable approval gate.
- Do not implement automated matching, ranking, eligibility, hiring, or referral decisions.
- Do not start cloud services, provision accounts, or change client systems without explicit scoped approval.
- Do not present provisional queue business hours, thresholds, escalation behavior, or no-response procedure as production policy, an SLA, compliance rule, or staff-performance standard before client validation.

## Repository-governance closeout
- `develop` and `main` are now protected: pull requests, required `enforce` (Branch policy), `check` (Repository hygiene), and `application` (Application quality) statuses, up-to-date branches, resolved conversations, administrator enforcement, and deletion/force-push prevention.
- Repository policy was applied from `infra/github/repo-policy.json` and verified by `infra/github/verify-repo-policy.sh`.
- PR #3 qualified the permitted `develop` → `main` source path: both required checks passed; it was then closed without merge because it was a synthetic governance test, not a release.
- PR #5 merged the reviewed Phase 1 discovery, compliance, governance, planning, and PDF-generation documentation into `develop`.
- PR #6 merged the coding-readiness closeout into `develop`.
- PR #7 merged the reviewed first-slice planning packet into `develop`.
- PR #8 merged the reviewed draft-employer tracer into `develop` at `0938c17`; its remote feature branch is retired.
- PR #9 merged the reviewed solo-maintainer governance and required-`application` policy at `80f4505`. The committed policy was then applied under explicit approval; `infra/github/verify-repo-policy.sh` reported no drift and direct GitHub queries confirmed all three required contexts on both protected branches.
- PR #11 merged the independently reviewed and remediated Employer detail/bounded-search tracer into `develop` at `b9eaee6`; its feature branch is historical and not a base for later work.
- PR #12 merged the independently reviewed Employer workspace frontend planning packet into `develop` at `b06923a`; its documentation branch is historical and not a base for implementation.
- PR #13 merged the first local/synthetic Employer workspace implementation into `develop` at `f8236e6`.
- PR #14 merged the independently reviewed closeout plan into `develop` at `b0a459b`.
- PR #15 merged the independently rereviewed and exact-head-qualified closeout plus ADR-0006 into `develop` at `7ae448e`; the retired closeout branch is historical.
- PR #16 merged the accepted ADR-0007 draft-revision planning packet into `develop` at `1c66eeb`.
- PR #17 merged the bounded synthetic/local draft-Employer revision implementation into protected `develop` at `1543248`; its feature branch is retired. The current lane is a fresh post-merge remediation branch from that exact merged tip.

## Repository bootstrap state
- The initial tracked baseline contains the living documents, ADR convention, and a protective `.gitignore`.
- Reviewed discovery/compliance/governance/planning Markdown and the PDF-generation source are tracked. Client-source artifacts and generated client PDFs remain ignored and outside the repository.
- The remote is `origin` at `https://github.com/b-mackenzie-alexander/golden_rose_project.git`; `develop` is the protected integration branch and `main` is the protected release branch.

## Continuity sources
- Discovery and detailed evidence: tracked, reviewed material in `docs/discovery/` and `docs/compliance/`; raw/client-source artifacts remain excluded.
- Governance baseline: tracked material in `docs/governance/`.
- Implementation and pilot discoveries: `docs/planning/phase-1-operational-discovery-register.md` plus dated evidence in `NOTES.md`.
- Engagement evidence index: Obsidian note `Golden Rose Employment Agency - Engagement Index`.
- Stable project decisions: `TECHNOLOGY_DECISIONS.md` and `docs/adr/`.
- Execution checklist: `ROADMAP.md`.
