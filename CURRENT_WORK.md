# Current Work — Golden Rose Operations Platform

**Updated:** 2026-08-04
**Lane:** Planning / discovery
**Overall status:** Phase 0 is in progress. No implementation, infrastructure provisioning, public release, or production-data use is authorized by this file.

## Active objective
Turn the completed initial discovery baseline into an approved, narrow first delivery: an agency-staff pilot for employer demand entry and retrieval, followed by a governed dashboard and transparent worker/employer comparison aid.

## Current evidence-backed direction
- The agency’s current operation is paper-first and fragmented across workbooks, hosted forms, Trello, calendars, messaging, and manual follow-up.
- Multiple legacy employer and worker forms overlap. The proposed replacement is one canonical staged workflow, not duplicate forms or response stores.
- The first usable product should serve agency members: enter employer demand, find/review requests, work an authorized demand queue, and replace manual metric collection with governed operational data.
- The staff calendar/shift-coverage view must be derived from authoritative operational records, not maintained as a parallel manual store.
- Proposed location direction: organize routine operations and reporting by approved broad service zones; precise worksite and worker/home location remain sensitive, restricted, and separately governed.
- Accepted staff-plane roles are Owner, delegated Manager, interchangeable Operations Staff, and a separately bounded Platform Administrator. `docs/planning/phase-1-staff-permission-matrix.md` controls command, field, delegation, exact-address, export-denial, and break-glass boundaries; platform maintenance must not create standing access to operational personal data.
- Employer demand is the proposed first entry workflow because current demand exceeds available worker supply.
- Worker profiles should follow quickly, but self-reported preferences/skills are not verified credentials and must not drive automatic ranking, eligibility, hiring, or referral.
- Public worker/employer access and higher-trust staff administration require materially separate security boundaries.
- Accepted Phase 1 canonical structure: neutral `Employer` → `EmployerContact` / `Worksite` / `StaffingRequest` → `ShiftNeed` / `RequestRequirement`, supported by `WorksiteZoneMembership`, `ServiceZoneComposition`, pinned `MapArea`/`WorksiteMapAreaAssignment`, and `AuditEvent`. Field purposes and exclusions are controlled by `docs/planning/phase-1-canonical-field-purpose-inventory.md`.
- Accepted request/shift lifecycle: guarded request review/open/close states and combined shift/coverage states with reversible coverage, explicit completed/unfulfilled/cancelled outcomes, and exceptional audited reopening to pending review. `docs/planning/phase-1-request-shift-state-model.md` is authoritative.
- Accepted work-queue model: separate review/follow-up/coverage clocks, hybrid business/continuous time, shared accountable ownership, provisional configurable triggers, three-attempt no-response safeguard, and deterministic lanes. `docs/planning/phase-1-work-queue-aging-follow-up-model.md` is authoritative; provisional values are not SLAs and require client validation before production.
- Accepted calendar/coverage model: distinct request milestones and explicit timed shift occurrences; pending/active/historical visibility; timezone-safe intervals; aggregate coverage; permission-gated day/week address reveal; current truth with audit history; and governed drag/rescheduling. `docs/planning/phase-1-calendar-coverage-semantics.md` is authoritative.
- Accepted service-zone model: flat adaptive Owner-managed catalog; optional late assignment; overlapping worksite memberships with one primary/default; visible unassigned work; no double counting; and audited historical correction. `docs/planning/phase-1-service-zone-taxonomy.md` is authoritative; exact names/conventions may emerge through pilot use and do not block implementation.
- Accepted NYC map model: mandatory authorized-staff Phase 1 job-demand/coverage map over pinned official DCP 2020 CDTAs; Owner-created zones group fixed cells; automatic provider-neutral server-side address-to-CDTA derivation discards precise coordinates by default; worker supply follows its own contract. `docs/planning/phase-1-nyc-job-demand-map-contract.md` is authoritative.
- Accepted permission model: server-enforced named permissions distinguish Owner, delegated Manager, Operations Staff, and separately bounded Platform Administrator; exact worksite reveal is distinct from calendar/map access, exports are disabled, and exceptional support is time-bounded break-glass only. `docs/planning/phase-1-staff-permission-matrix.md` is authoritative.
- Accepted production identity/support baseline: individual staff identities, mandatory MFA, phishing-resistant factors for privileged/recovery roles, controlled independent recovery, session expiry/revocation, monthly pilot access review, and separated business/technical support ownership. `docs/planning/phase-1-mfa-recovery-support-ownership.md` is authoritative; provider selection, named personnel, rehearsal evidence, and live-data/production activation remain gated.
- Accepted correction/audit baseline: PostgreSQL domain rows hold current operational truth; append-only `AuditEvent` records preserve material history through atomic expected-version/idempotent commands; restricted prior/new values remain field-authorized; and derived projections are disposable rather than competing record stores. `docs/planning/phase-1-correction-audit-event-contract.md` is authoritative.

## Immediate next steps
1. Review this document set against the preliminary PRD with Beatrice and the client.
2. Obtain the outstanding business-model/legal-content and operational-policy decisions needed to define the staff pilot safely.
3. Validate client terminology, provisional queue business-calendar/thresholds, Owner-led zone/map usability, out-of-area policy, named exact-address recipients, map provider/data-processing posture, field-by-state requiredness, staff access/delegation owners, and correction/audit retention and restricted-history recipients against the accepted planning contracts.
4. Convert the accepted field-purpose inventory and approved workflow/access contracts into a concrete implementation plan.
5. Before any coding, re-baseline live Git state and create a purpose-named branch from the approved integration branch.

## Required decision gates before implementation
- Client/counsel-approved source and owner for public, legal, fee, retention, consent, and receipt/agreement content.
- Name staff-role assignments/delegations, recovery approvers/executors, support contacts/hours, client technical successor, dormant-account threshold, and the qualified identity-provider configuration under the accepted identity/support baseline.
- Field-by-state requiredness, client terminology, and operational validation for the accepted canonical field-purpose inventory and state model; do not add fields or transitions without documented purpose and owner.
- Owner-led zone/map controls, delegation, out-of-area policy, exact-address reveal permissions, and live renderer/tile/geocoder provider approval; final zone naming is not an implementation gate and synthetic geocoder/map fixtures remain sufficient for bounded local testing.
- Record individual Owners/Managers, delegated elevated capabilities, exact-address recipients, and break-glass approvers/review owner under the accepted staff permission matrix.
- Approval of which legacy fields are excluded, staff-only, controlled extensions, or require neutral/counsel-reviewed treatment.
- Data classification, environment, synthetic-fixture, backup/recovery, and production-data pilot gate.
- Client/counsel-approved retention/disposal periods for audit envelopes and restricted prior/new values, named restricted-history recipients, and any stronger legal-record archival requirements.
- Interim cloud-billing and final-payment handoff procedure: Beatrice funds approved infrastructure until final payment; then client billing/account/support ownership transfers through a documented continuity check.

## Hard stop boundaries
- Do not collect or import unrestricted live personal data.
- Do not enable public workflows, uploads, payment, signatures, screening, or vendor integrations.
- Do not encode legacy language, protected-trait/proxy criteria, legal text, fee policy, retention rules, or business terms as production behavior.
- Do not implement automated matching, ranking, eligibility, hiring, or referral decisions.
- Do not start cloud services, provision accounts, or change client systems without explicit scoped approval.
- Do not present provisional queue business hours, thresholds, escalation behavior, or no-response procedure as production policy, an SLA, compliance rule, or staff-performance standard before client validation.

## Repository-governance closeout
- `develop` and `main` are now protected: pull requests, required `enforce` (Branch policy) and `check` (Repository hygiene) statuses, up-to-date branches, resolved conversations, administrator enforcement, and deletion/force-push prevention.
- Repository policy was applied from `infra/github/repo-policy.json` and verified by `infra/github/verify-repo-policy.sh`.
- PR #3 qualified the permitted `develop` → `main` source path: both required checks passed; it was then closed without merge because it was a synthetic governance test, not a release.
- The next slice is a confidentiality/content review of the currently local discovery/compliance/governance Markdown and PDF-generation script before any future documentation-tracking PR.

## Repository bootstrap state
- The initial tracked baseline contains the living documents, ADR convention, and a protective `.gitignore`.
- Client-source artifacts, generated client PDFs, existing discovery/compliance/governance notes, and the PDF-generation script remain intentionally untracked pending a separate confidentiality/content review.
- The remote is `origin` at `https://github.com/b-mackenzie-alexander/golden_rose_project.git`; the initial `main` push establishes the default branch before governance-as-code work begins.

## Continuity sources
- Discovery and detailed evidence: currently local `docs/discovery/` and `docs/compliance/`; review and sanitize before a future tracked-documentation commit.
- Governance baseline: currently local `docs/governance/`; review and sanitize before a future tracked-documentation commit.
- Engagement evidence index: Obsidian note `Golden Rose Employment Agency - Engagement Index`.
- Stable project decisions: `TECHNOLOGY_DECISIONS.md` and `docs/adr/`.
- Execution checklist: `ROADMAP.md`.
