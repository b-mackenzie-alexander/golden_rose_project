# Current Work — Golden Rose Operations Platform

**Updated:** 2026-08-04
**Lane:** Planning / Phase 1 coding-readiness closeout
**Overall status:** Phase 0 discovery is moving into implementation planning. The client has accepted the Phase 1 authorized-staff demand map and staff role model. A bounded synthetic/local coding slice may begin only after its implementation plan, stack, field-requiredness scope, and data classification are approved. Infrastructure provisioning, public release, live integrations, and production-data use remain unauthorized.

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
1. Complete and review this coding-readiness documentation closeout against the preliminary PRD.
2. Approve the application stack and a narrow first synthetic/local implementation slice, including its field-requiredness boundary, data classification, acceptance tests, recovery posture, and explicit non-scope.
3. Convert the accepted field-purpose, workflow, access, audit, map, and operational-discovery contracts into a concrete implementation plan.
4. After the documentation plan is reviewed and merged, re-baseline live Git state and create a purpose-named implementation branch from `develop`.
5. Record implementation and pilot findings in the operational-discovery register and `NOTES.md`; escalate only changes to accepted behavior, data purpose, authorization, legal posture, or trust boundaries into reviewed contract/ADR updates.

## Gate classification

### Required before the affected synthetic/local implementation slice
- Approved narrow implementation plan and accepted application stack/toolchain.
- Slice-specific field-by-state requiredness and validation rules; do not invent fields, transitions, or nullability policy.
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
- `develop` and `main` are now protected: pull requests, required `enforce` (Branch policy) and `check` (Repository hygiene) statuses, up-to-date branches, resolved conversations, administrator enforcement, and deletion/force-push prevention.
- Repository policy was applied from `infra/github/repo-policy.json` and verified by `infra/github/verify-repo-policy.sh`.
- PR #3 qualified the permitted `develop` → `main` source path: both required checks passed; it was then closed without merge because it was a synthetic governance test, not a release.
- PR #5 merged the reviewed Phase 1 discovery, compliance, governance, planning, and PDF-generation documentation into `develop`. The active follow-up is this coding-readiness drift closeout and first-slice implementation plan.

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
