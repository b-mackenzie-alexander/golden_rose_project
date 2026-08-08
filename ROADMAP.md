# Golden Rose Operations Platform — Roadmap

**Status:** Living checklist. Discovery evidence and approved decisions control scope; unchecked items are not authorized merely because they appear below.

## Phase 0 — Discovery and planning baseline
- [x] Record source-material ledger and evidence notes for received client artifacts.
- [x] Identify fragmented paper, spreadsheet, calendar, Trello, messaging, and hosted-form workflows.
- [x] Establish the source-of-truth boundary: client artifacts are discovery evidence, not production legal/business content.
- [x] Establish English/Spanish functional-parity requirement.
- [x] Record the proposed public-plane / staff-plane security boundary.
- [x] Create repository living-document baseline.
- [x] Create and push `develop` from the initial `main` baseline.
- [x] Exercise the governance-as-code PR into `develop`, then apply and verify protections for both `develop` and `main`.
- [x] Confirm the protected promotion path: purpose branch → `develop` (squash) and `develop`/`hotfix/*` → `main` (merge commit only by release checklist).
- [ ] Complete client validation of current workflow, owners, source records, and exceptions.
- [ ] Obtain approved business model, legal statements, and production content/rule owners.
- [ ] Reconcile the client-provided DCWP checklist against current authoritative sources and counsel/client validation.
- [ ] Approve the preliminary PRD and seven-week delivery plan.

## Phase 0.5 — GCP governance and non-production readiness
**Goal:** Establish the approved management, cost, security, and recovery baseline for GCP without treating this checklist as permission to provision infrastructure or use live data.

- [x] Record GCP as the selected platform, with Cloud Run + Cloud SQL as the managed-container/database baseline.
- [x] Record the interim billing constraint: Beatrice funds approved infrastructure until final contract payment, then billing responsibility transfers to the client through a documented handoff.
- [ ] Select and validate the GCP region against required service availability, cost, latency, recovery, and data-location needs.
- [ ] Produce separate non-production and production cost estimates covering Cloud SQL compute/storage/backups/HA, Cloud Run, Artifact Registry, Secret Manager/KMS, logging/monitoring, identity/MFA, network/egress, support, and post-credit costs.
- [ ] Decide the GCP organization/project, billing-account, domain/DNS, support, emergency-access, and final-handoff topology that supports interim Beatrice billing and secure client transfer.
- [ ] Approve GCP human-access roles and service-account boundaries consistent with the accepted application staff/Platform Administrator, MFA/recovery, break-glass, and periodic-access-review contracts; qualify the selected identity-provider configuration.
- [ ] Define backup/PITR, restore-test cadence, RTO/RPO, log-retention, incident-alert, budget-alert, and cost-review expectations.
- [ ] Choose and review infrastructure-as-code and immutable-artifact promotion conventions; prohibit long-lived GCP service-account keys in CI/CD.
- [ ] Obtain separate scoped approval before creating any GCP project, billing linkage, cloud resource, service identity, or external integration.
- [ ] After scoped approval, establish and qualify the isolated GCP non-production environment with synthetic/approved data only: Artifact Registry, Secret Manager, Cloud Run, Cloud SQL, Logging/Monitoring, and GitHub Workload Identity Federation.
- [ ] Verify non-production deployment by immutable image digest, least-privilege runtime/deployment identities, budget/alert routing, migration/rollback, backup/restore, log redaction, and environment teardown/rebuild evidence.

## Phase 1 — Staff pilot foundation: employer demand workflow
**Goal:** Give authorized agency staff a reliable, browser-based place to create and find employer staffing requests without duplicating response stores.

- [x] Accept the production staff account-lifecycle, MFA, recovery, session, access-review, and support-ownership baseline in `docs/planning/phase-1-mfa-recovery-support-ownership.md`.
- [ ] Name production recovery/support personnel and contact paths, qualify the identity-provider configuration, rehearse the procedures, and approve the initial staff cohort/data classification before production activation.
- [x] Accept `docs/planning/phase-1-correction-audit-event-contract.md` as the source of truth for current-state versus history boundaries, draft revisions, material corrections, append-only events, atomic multi-record commands, optimistic concurrency/idempotency, restricted historical values, and disposable derived projections.
- [ ] Approve production retention/disposal periods, restricted-history recipients, reason terminology, and any stronger legal-record archival requirement before live-data admission.
- [x] Accept the canonical Phase 1 field-purpose inventory: neutral Employer, EmployerContact, Worksite, StaffingRequest, ShiftNeed, RequestRequirement, WorksiteZoneMembership, ServiceZone/Composition, pinned NYC MapArea/CDTA assignments, and AuditEvent with explicit data-purpose and prohibited-use boundaries.
- [x] Record client acceptance of the staff-plane permission matrix in `docs/planning/phase-1-staff-permission-matrix.md` for Owner, delegated Manager, interchangeable Operations Staff, and separately bounded Platform Administrator roles; deny Phase 1 exports and standing operational access for technical support, and require attributable time-bounded break-glass support.
- [x] Accept a flat adaptive Owner-managed service-zone taxonomy composed from pinned NYC CDTAs, with optional late assignment, overlapping worksite memberships, one primary/default membership, visible unassigned work, and no automatic service-zone/proximity inference.
- [x] Record client acceptance of the authorized-staff Phase 1 NYC job-demand map contract: pinned official DCP 2020 CDTAs, Owner-composed zones, transparent demand/coverage measures, provider-neutral server-side address derivation, accessible list parity, and no worker/ranking layer.
- [ ] Discover and validate Owner-led map/catalog usability, delegation, out-of-area policy, exact-address reveal permissions, and renderer/tile/geocoder provider posture during implementation and client pilot preparation; final zone names are not an implementation prerequisite, while live provider/address use remains gated.
- [x] Accept guarded request and shift/coverage states, reversible coverage for no-shows, completed/unfulfilled/cancelled shift outcomes, request close reasons, and exceptional audited reopening.
- [x] Accept separate queue clocks, hybrid time accounting, shared accountable ownership, provisional configurable review triggers, three-attempt no-response safeguard, and deterministic queue lanes.
- [ ] Validate provisional business hours, thresholds, escalation ownership, and no-response procedure with the client before production policy or SLA claims.
- [x] Accept calendar/coverage semantics for request milestones, explicit shift occurrences, state visibility, timezone/overnight behavior, aggregate counts, address reveal, corrections, overlap, and audited rescheduling.
- [x] Create `docs/planning/phase-1-operational-discovery-register.md` to distinguish slice blockers from implementation-time discoveries, live-data gates, and public/legal release gates.
- [x] Accept the first-slice shape, stack/toolchain, and minimal draft-Employer requiredness in ADR-0002 and ADR-0003: client supplies only employer type/display name; the server controls draft state, source, actor, identifiers, timestamps, and version.
- [x] Review and merge `.hermes/plans/2026-08-04_phase-1-first-slice-plan.md`, including synthetic data classification, TDD acceptance evidence, PostgreSQL service approval, recovery posture, independent review handoff, and explicit stop boundaries.
- [x] Implement and locally verify the first synthetic/local staff tracer: synthetic authorization for `employer:draft:create`, atomic `CommandReceipt` + draft `Employer` + append-only `AuditEvent`, replay/conflict-safe `POST /api/staff/v1/employers`, and the PR `application` CI quality gate with SBOM evidence. Review remediation validates prohibited production/synthetic startup configuration before traffic, runs migration before pytest on a fresh PostgreSQL service, pins third-party CI actions to immutable SHAs, and excludes the unrelated client-PDF generator from backend formatting enforcement.
- [x] Require the qualified `application` check on protected `develop` and `main` through reviewed solo-maintainer governance as code, then apply and verify the merged policy under separate approval.
- [x] Review and merge ADR-0004 plus `.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md` for exact Employer detail and privacy-conscious bounded search using one `employer:read` permission, a POST body, filter-bound keyset pagination, no counts/exports, and no read-side audit events. PR #10 merged this planning packet into `develop` at `bde9143`.
- [x] Implement and locally verify the approved Employer detail and bounded-search tracer on `feat/staff-employer-read-search`: `employer:read`, exact UUID detail, privacy-conscious POST search, filter-bound keyset cursoring, preserved create-route behavior, focused API regressions, and Task 6 quality/security evidence (`97 passed`, `96.67%` coverage, no known vulnerabilities, CycloneDX SBOM generated).
- [x] Complete independent code/security review on the local `feat/staff-employer-read-search` working tree, remediate the reported High/Medium findings, and merge PR #11 into protected `develop` at `b9eaee6`. Independent rereview verified create-path NFC normalization, detail-route no-store coverage, employer-specific 404 behavior, and read-side minimization.
- [x] Independently audit and remediate ADR-0005 plus `.hermes/plans/2026-08-06_115420-phase-1-employer-workspace-frontend-plan.md` for architecture/TDD, security/privacy/supply chain, and product/accessibility/localization; final focused rereviews reported no remaining Blocker/High/Medium findings.
- [x] Obtain Beatrice's explicit direction approval and update ADR-0005 from Proposed to Accepted locally after independent review cleared the first local/synthetic staff browser workspace packet.
- [x] Commit, push, open, review, and merge the Accepted planning packet through protected `develop`; PR #12 merged this planning-only gate at `b06923a`, and implementation now proceeds only from a fresh merged-tip coding branch.
- [x] Implement the approved Employer workspace under strict RED → GREEN nodes through Task 10: fresh/replayed create success is no-store; the browser workspace now has English/Spanish parity, bounded create/search/detail flows, browser privacy/no-persistence controls, idempotent unknown-outcome retry/abandon handling, authoritative read invalidation, and BFCache reset protection, with local focused test/typecheck/diff evidence recorded in `NOTES.md`.
- [x] Apply provisional accessible styling and interaction hardening for the routed employer workspace (Task 11): semantic workspace order, automated axe parity, focus hooks, bounded status structure, and reduced-motion/narrow-layout support without inventing branding.
- [x] Merge the first local/synthetic Employer workspace implementation into protected `develop`; PR #13 merged this bounded create/search/detail browser slice at `f8236e6`.
- [x] Review and merge `.hermes/plans/2026-08-07_145911-phase-1-employer-workspace-closeout-plan.md` as the post-merge closeout authorization; PR #14 merged that plan alone into `develop` at `b0a459b`. ADR-0006 is accepted in the implementation-closeout candidate and remains pending durable merge with that closeout PR.
- [ ] Complete the post-merge closeout lane on `fix/employer-workspace-closeout`: reconcile project truth, remediate the evidence-backed browser/privacy/runtime/database/CI defects, independently rereview the exact remediation surface, and requalify the merged workspace before any draft-Employer revision planning or implementation begins.
  - Observed 2026-08-08: the first independent review found one frontend High plus frontend/backend Mediums. All findings and Lows were remediated with focused RED → GREEN/PostgreSQL evidence, and frontend/backend/CI/docs/final-delta rereviews returned ACCEPT with no residual findings. Commit, exact committed-head qualification, exact-range Gitleaks, and protected-`develop` promotion remain outstanding.
- [ ] Define household and general-labor request extensions without creating separate workflows or data stores.
- [ ] Use fictional synthetic fixtures only for the current tracers—never copy, transform, hash, or derive them from client/live records; any later de-identified-data procedure requires separate approval.
- [ ] Implement staff authentication and authorization boundary.
- [ ] Implement employer/contact/worksite/request/shift persistence with migration-managed schema.
- [ ] Implement staff request entry, detail, correction, and an authorized demand work queue as a mandatory service-time capability.
- [ ] Implement the accepted NYC CDTA map foundation and transparent job-demand/coverage layer with deterministic synthetic geocoder fixtures; do not enable a live geocoder or worker layer without its separate gate.
- [ ] Implement the accepted derived calendar/coverage view from authoritative request milestones and explicit shift occurrences; keep worker assignment/availability enrichment deferred and do not create a parallel calendar store.
- [ ] Implement the accepted append-only audit-event envelope, atomic domain/event command boundary, protected changed-field evidence, correction-of-correction behavior, and safe separate operational logging.
- [ ] Test accessibility and English/Spanish behavior for the released staff workflow.
- [ ] Complete staff-pilot acceptance, support, rollback/forward-recovery, and training evidence.

## Phase 2 — Staff dashboard and governed comparison aid
**Goal:** Replace manual statistics collection with an agency-only dashboard derived from authoritative workflow records, then support transparent staff comparison.

- [ ] Approve staff roles, decision questions, KPIs, source records, calculation definitions, and refresh/export rules.
- [ ] Implement role-scoped operational dashboard projections; no extra metric-entry forms.
- [ ] Extend the accepted Phase 1 demand map with the separately approved worker-supply overlay and privacy-preserving aggregation; geographic overlap must not become automatic matching/ranking.
- [ ] Validate graph totals and empty/error states against source records.
- [ ] Approve job-relevant worker/employer comparison criteria, display language, and human-review process.
- [ ] Implement explainable comparison aid that shows supported signals, missing data, and staff notes.
- [ ] Block automated ranking, eligibility, hiring, or referral decisions.
- [ ] Test authorization, aggregation/redaction, accessibility, and auditability.

## Phase 3 — Worker profile and controlled documents
**Goal:** Add a staged, inclusive worker profile for agency review and controlled referral preparation.

- [ ] Approve worker field inventory, field purpose, visibility, retention, and correction process.
- [ ] Implement staged worker onboarding with agency review; do not imply automatic eligibility or employment.
- [ ] Achieve English/Spanish functional and accessibility parity across the workflow.
- [ ] Approve document-upload scope, consent, retention, and staff-access rules.
- [ ] Implement and qualify a PDF-first secure document-ingestion boundary before enabling uploads.
- [ ] Implement agency-controlled worker profile management and referral-readiness state.

## Phase 4 — Controlled referral, delivery, and operational records
- [ ] Approve legal/business templates, receipt/agreement rules, and role-scoped delivery views.
- [ ] Implement agency-reviewed referral/placement workflow and immutable referral snapshot.
- [ ] Implement attributable corrections, cancellations, replacements, and delivery events.
- [ ] Validate record retrieval, audit, retention, and export requirements with client/counsel.

## Phase 5 — Production qualification and rollout
- [ ] Record the interim billing arrangement: Beatrice pays approved infrastructure charges until final contract payment, after which billing responsibility transfers to the client through a documented handoff.
- [ ] Approve client-owned account/project, billing, domain/DNS, support, recovery, and emergency-access ownership at handoff; identify an effective transfer date and confirm service continuity.
- [ ] Qualify isolated environments, secrets, backups/restore, monitoring, and incident response.
- [ ] Complete security/privacy review and production-data gate for each rollout increment.
- [ ] Promote the qualified immutable release artifact through recorded approval.
- [ ] Capture client acceptance and post-release follow-up.

## Explicitly deferred unless separately approved
- AI-assisted ranking, screening, or decision-making.
- Public job publication, public or individual-level mapping, precise-location features, third-party mapping/geocoding, and automated geographic ranking.
- Payment, e-signature, background/identity/credit screening, messaging, and calendar vendors.
- Legacy-response migration or unrestricted production-data collection.
