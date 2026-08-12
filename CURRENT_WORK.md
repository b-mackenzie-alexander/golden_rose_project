# Current Work — Golden Rose Operations Platform

**Updated:** 2026-08-12
**Lane:** Phase 1 planning publication — accepted EmployerContact authority foundation
**Verification:** PR #18 merged the bounded draft-Employer revision remediation into protected `develop` at `a4d8f90`; all required checks passed. A fresh 2026-08-12 review rebaselined local `develop` to that exact tip and reran the complete application-quality sequence on an isolated synthetic review database: 116 frontend tests, 238 backend tests at 96.14% coverage, frontend/backend lint, type, build, migration, audit, and SBOM validation all passed. Exact-range Gitleaks over `1543248..a4d8f90` found no leaks.
**Overall status:** The merged Employer create/search/detail/revision tracer is technically healthy for its bounded synthetic/local scope. No adjacent Phase 1 entity is implemented, no real staff identity or deployment is authorized, and the broad roadmap epics remain incomplete. ADR-0008 and `.hermes/plans/2026-08-12_111500-phase-1-employer-contact-authority-foundation-plan.md` now form the formally accepted backend-only EmployerContact create + bounded parent collection-query + exact-read planning boundary. Exact-hash API/security plus persistence/migration/TDD closure rereviews returned PASS with no Blocker, High, or Medium findings. Protected planning-only publication/merge and a separate exact-tip coding authorization remain outstanding.

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
1. Prepare the accepted ADR-0008 packet as an uncommitted planning-only publication surface on a valid `docs/` branch; add no product code.
2. Under separate approval, commit, rerun committed-range/final-head hygiene and exact-range secret scanning, then push/open the planning-only PR to protected `develop`.
3. Only after merge, rebaseline a separately authorized coding lane from that exact protected integration tip and execute the reviewed plan under exact-node TDD.
4. Keep the implementation scope to synthetic/local backend contact create + bounded parent collection-query + parent-scoped exact read; preserve the separate approval gates for Git mutation, PostgreSQL service use, deployment, real identity, and live/client data.
5. Keep broad roadmap items unchecked until their full contracts and acceptance evidence exist; this candidate advances one coherent prerequisite rather than claiming several epics complete.

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
- PR #17 merged the bounded synthetic/local draft-Employer revision implementation into protected `develop` at `1543248`; PR #18 merged its independently rereviewed remediation at `a4d8f90`, and both feature branches are historical. The current lane is the reviewed and formally accepted ADR-0008 planning packet; implementation remains blocked on protected planning-only merge, exact-tip rebaseline, and separate coding authorization.

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
