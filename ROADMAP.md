# Golden Rose Operations Platform — Roadmap

**Status:** Living checklist. Discovery evidence and approved decisions control scope; unchecked items are not authorized merely because they appear below.

## Delivery-method governance

- [x] Adopt ADR-0014 workflow-scale planning: each implementation plan normally covers multiple checklist items or one meaningful user-observable, operational, or risk-bounded outcome and may authorize several ordered implementation PRs.
- [x] Keep RED → GREEN nodes small inside implementation without returning to planning for routine test failures, harness fixes, helper extraction, review remediation, or contract-preserving PR splits.
- [x] Preserve separate explicit approvals for cloud inventory, backend/state adoption, each Terraform plan/apply, publication, secret/database preparation, migration, service activation, tester access, qualification, live/client data, and production.
- [x] Draft `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md` as the first outcome-scale multi-PR master plan.
- [x] Independently review and explicitly accept ADR-0013 Amendment B plus the private-develop activation and human-feedback master plan.
- [x] Merge the accepted packet through protected `develop` before its source implementation PRs or operational gates begin. PR #49 merged the accepted ADR-0014 / ADR-0013 Amendment B / master-plan packet into protected `develop` at `fa8334c`.
- [ ] Complete the next outcome-scale tranche: a qualified private fictional-synthetic `develop` environment where approved humans can exercise the current Employer/EmployerContact product and provide structured feedback.
- [x] Complete, qualify, and merge PR A artifact/transition-authority remediation. PR #51 merged into protected `develop` at `a7f0649`; the source-only branch is retired, and no later operational gate is authorized until PR B and the remaining source-readiness requirements merge.
- [x] Complete, qualify, and merge PR B qualification/human-feedback readiness. PR #52 merged the source-only readiness contract into protected `develop` at `7272907`; no cloud, service, tester, human, live-data, or production authority was granted.
- [x] Complete conditional PR C contract-preserving remediation. PR #53 merged the absent-Cloud-Run verifier correction at `673f6d5`; the Cloud-SQL absence follow-up merged at `9663480`; and PR #56 merged the live-proven absent-future-identity and logging-exclusions fallback collection at `72c56c4`. The subsequent private A1 remediation aligned project labels/WIF, established the source-defined Artifact Registry writer/reader boundary, restored effective state-bucket custody and exact temporary bootstrap object authority, removed the empty erroneous registry repository, and reconciled the observed two logging-to-logging sinks through a bounded verifier contract. Final current-source private A1 verification passed with zero violations. WP-2/WP-3 and A2 subsequently selected the bootstrap-only new-lineage path; E2/E3 state establishment/readback, A5, ownership alignment, Gate F apply, and workload-free verification are complete.
- [ ] Publish and execute the accepted ADR-0015 FinOps budget-ownership separation tranche: add one billing-authorized FinOps root, transfer the existing budget to a third distinct state without replacement, remove old workload-state ownership, produce a no-op FinOps/readback receipt, and restore provisioner-owned migration planning without project-level provisioner authority. The accepted planning packet is published in open PR #79, remains unmerged, and grants no implementation or cloud/state authority before protected merge.

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
- [x] Select the GCP `develop` region against required service availability, cost, latency, recovery, and data-location needs: use `us-east4` / Northern Virginia as the single location for Cloud Run, Cloud SQL, and Artifact Registry. Production region/topology remains separately gated.
- [ ] Produce separate non-production and production cost estimates covering Cloud SQL compute/storage/backups/HA, Cloud Run, Artifact Registry, Secret Manager/KMS, logging/monitoring, identity/MFA, network/egress, support, and post-credit costs. Initial non-production planning estimate is about $15-$20/month with Cloud SQL as the fixed cost driver, private `db-f1-micro`/10 GiB SSD/no-public-IP as the accepted develop database baseline, Artifact Registry cleanup required, and budget alerts at $50, $75, and $100; recheck pricing before provisioning.
- [ ] Complete the remaining GCP billing-account, domain/DNS, support, emergency-access, and final-handoff topology. The durable bootstrap/state control plane, source/live adoption, state readbacks, and workload-free foundation are established; recovery/handoff completion and all private identifiers remain separately controlled. The deployment/testing project remains the disposable workload boundary.
- [ ] Approve GCP human-access roles and service-account boundaries consistent with the accepted application staff/Platform Administrator, MFA/recovery, break-glass, and periodic-access-review contracts; qualify the selected identity-provider configuration. The named-human provisioner Token Creator bridge, exact state-bucket authority, and provisioner-owned workload-backend proof are complete. Fresh migration planning then exposed an explicit quota-project requirement for project-level provisioner `serviceusage.services.use`, which the accepted boundary prohibits. Accepted ADR-0015, published in open PR #79 with protected merge pending, separates Billing Budget ownership into a billing-authorized FinOps root; planning acceptance grants no implementation, state transfer, retry, IAM change, or plan authority before protected merge.
- [ ] Define backup/PITR, restore-test cadence, RTO/RPO, log-retention, incident-alert, budget-alert, and cost-review expectations. Budget alert thresholds for develop are accepted at $50, $75, and $100, but alert recipients/routing and recovery objectives remain open.
- [x] Choose infrastructure-as-code and immutable-artifact promotion conventions: Terraform is the accepted IaC direction for reviewable GCP definitions, immutable image digest deployment is required, and long-lived GCP service-account keys in CI/CD are prohibited in favor of GitHub OIDC/WIF.
- [x] Independently review, accept, and merge ADR-0009 plus `.hermes/plans/2026-08-13_145234-gcp-develop-deployment-foundation-plan.md` as the private synthetic-only `develop` deployment boundary; PR #21 merged the planning packet at `9e27f80`, and planning merge does not imply provisioning approval.
- [x] Implement, independently review, qualify, and merge Slice B runtime/container packageability, liveness/readiness, same-origin serving, entrypoint behavior, local image contract, and local image build/inspection from `.hermes/plans/2026-08-13_160852-slice-b-runtime-container-contract-plan.md`; PR #22 merged the local-only contract at `f3cac4d`. Explicit migration-job, non-owner database-role, Terraform validation, and WIF/digest-promotion contracts remain later separately gated slices without cloud changes.
- [x] Prepare, independently review, accept, and merge the Terraform/IaC validate-without-apply implementation plan from `.hermes/plans/2026-08-13_181005-terraform-preparation-plan.md`; PR #23 merged the planning packet into protected `develop` at `c27e1ee`. This does not authorize Terraform apply, GCP authentication/API calls, API enablement, provisioning, resources, image push, or deployment.
- [x] Implement, remediate, and merge the Terraform validate-without-apply scaffold and policy/static tests. PR #24 merged the repo-local Terraform scaffold, provider lockfile, static scanner, infrastructure-quality workflow, and clean-checkout backend-free Terraform initialization into protected `develop` at `50451b3`; all PR checks passed. No Terraform plan/apply, GCP authentication, API enablement, provisioning, image push, deployment, Cloud SQL use, or secret configuration occurred.
- [x] Complete the PR #24 post-merge closeout: PR #25 merged the documentation-only disposition, actual CodeRabbit skipped-review status, and independent final-head review's two High and five Medium findings into protected `develop` at `8dc1198`. It modified no implementation or governance and granted no cloud authority.
- [x] Prepare, review, accept, and merge the bounded original PR #24 remediation planning packet in `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md` and ADR-0010. PR #26 merged it into protected `develop` at `c5a1380`, but its real non-author reviewer/CODEOWNER prerequisite is unavailable in this single-maintainer repository; its execution path is therefore retired pending the successor amendment.
- [x] Prepare, review, accept, and merge ADR-0011 plus `.hermes/plans/2026-08-14_174830-pr24-solo-maintainer-remediation-amendment-plan.md`. PR #27 merged the accepted successor packet into protected `develop` at `23f97cc7e5a0137da942e4f7aa69c77c56e24210`; it retains the self-authorizing-CI finding as High/open accepted residual risk, prohibits review/CODEOWNER theater, and grants no cloud authority.
- [x] Implement, qualify, and merge the six static remediation tasks: semantic Terraform/workflow policy; deterministic `uv`; Direct VPC private-SQL declaration; API ordering; Cloud SQL automated backups; and managed-registry digest authority. PR #29 merged into protected `develop` at `08fe305`; all required statuses passed. The same-repository-CI High remains open accepted residual risk and required checks remain quality evidence rather than independent authorization.
- [x] Review, accept, and merge proposed ADR-0012 plus `.hermes/plans/2026-08-15_210257-consolidated-predeployment-foundation-plan.md`. PR #30 merged the packet into protected `develop` at `f9b7903`; it adopts the permanent solo-maintainer posture, consolidates bootstrap/state/WIF, remaining IAM/runtime/database authority, budgets/observability, immutable workflows, recovery/teardown, and gate evidence into one later pre-deployment implementation PR, and grants no cloud authority by itself.
- [x] Close out and merge the consolidated source-controlled pre-deployment PR. PR #33 merged into protected `develop` at `3c0118a`; its source contracts and local/CI evidence are historical, and its branch is retired. No cloud action occurred.
- [x] Review, accept, and merge the initial ADR-0013 planning packet as PR #34 at `63caa40`. The post-merge audit found F1-F17 deployment-path defects, including four Blockers; the accepted decisions cover staged `foundation → migration → service` authority, Terraform-only configuration ownership, IAM-private internet-reachable named testers, viewer/exact-job deploy execution, direct-workflow `workflow_ref` WIF separation, digest-bound Cosign/SLSA/SBOM evidence, and authenticated `/readiness` uptime monitoring. Initial planning merge grants no implementation or cloud authority.
- [x] Amend, independently rereview, and merge the post-PR34 ADR-0013 planning packet so evaluated-stage proof, stage-safe image inputs, per-secret IAM, staged-plan receipts, tester authority, attestation matrices, service-stage monitoring, qualification-failure evidence, and living-doc status are executable before any implementation branch is created. PR #35 merged the amended packet into protected `develop` at `db1f293`; the packet is historical planning context and grants no cloud authority.
- [x] Implement, independently rereview, qualify, and merge the bounded F1-F17 no-cloud remediation from the exact ADR-0013 planning merge. PR #37 merged the independently rereviewed remediation into protected `develop` at `caf96a72df87cd98114025627ad9f467f846f3a9`; its feature branch was retired after exact rebaseline and patch-equivalence evidence. The same-repository-CI High remains open accepted residual risk. The merged source contract clears only the no-cloud remediation and grants no Gate 2 or later cloud authority.
- [x] Publish and merge the private-SQL foundation / verifier reconciliation planning packet. PR #39 merged `.hermes/plans/2026-08-25_195726-private-sql-foundation-verifier-reconciliation-plan.md` plus receipt scaffolding into protected `develop` at `1c1a7b6`; it authorizes only the later bounded source reconciliation and grants no cloud mutation authority.
- [x] Merge the bounded revise-draft-employer receipt-lookup follow-up. PR #40 merged into protected `develop` at `fabb78a`; it is historical context only and not a base for continued coding.
- [x] Merge the observability / verifier API policy reconciliation. PR #41 merged into protected `develop` at `6ef2452`; local implementation of the next verifier slice must rebaseline from this exact tip rather than from the retired planning branch.
- [x] Implement, independently rereview, and merge the accepted private-SQL foundation / verifier reconciliation. PR #42 merged the source-only, no-cloud slice into protected `develop` at `b2d79b5`; it makes tester-authority verification service-stage-only while retaining private Cloud SQL as a required lower-layer foundation contract. The separate private-network / Cloud SQL authority gate remains later and unapproved.
- [ ] Establish and qualify the isolated GCP non-production environment with wholly fictional synthetic data only: Artifact Registry, Secret Manager metadata and out-of-band payload injection, Cloud Run, Cloud SQL, Logging/Monitoring, and GitHub Workload Identity Federation. Any client/live-derived data admission requires a new reviewed decision and is prohibited under ADR-0009.
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
- [x] Review and merge `.hermes/plans/2026-08-07_145911-phase-1-employer-workspace-closeout-plan.md` as the post-merge closeout authorization; PR #14 merged that plan alone into `develop` at `b0a459b`.
- [x] Complete the post-merge closeout lane on `fix/employer-workspace-closeout`: all findings were remediated, independent frontend/backend/CI/docs/final-delta rereviews returned ACCEPT with no residual findings, exact committed-head application and migration gates passed, exact-range Gitleaks found no leaks, all protected checks passed, and PR #15 merged ADR-0006 plus the bounded closeout into `develop` at `7ae448e`.
- [x] Publish accepted ADR-0007 plus `.hermes/plans/2026-08-08_111916-phase-1-draft-employer-revision-plan.md` through an independently reviewed planning-only PR from exact merged closeout tip `7ae448e`; reconcile replay semantics and living documents, but add no product code and grant no implementation authority. PR #16 merged this planning packet into `develop` at `1c66eeb`.
- [x] Historical implementation record — completed the bounded draft-Employer revision coding lane on `feat/staff-draft-employer-revision`: Tasks 5-10 are GREEN or honest GREEN regressions through the approved Task 10 closeout verification set, the independent-review blocker/high remediation round is complete, and the stale OpenAPI route-surface guard has now been reconciled to the approved revision route. The branch enforces shared create/revise `display_name` validation parity, safe-fails malformed existing-receipt replay authority in `revise_draft_employer`, and carries revision-era migration/test reconciliation plus additional check-constraint coverage. Focused rereview evidence is GREEN: `tests/integration/api/test_staff_employer_reads.py -q` passed with `16 passed`; `tests/integration/test_initial_migration.py` passed with `27 passed`; `tests/unit/application/test_employer_text.py` + `tests/unit/api/test_employer_schemas.py` + `tests/integration/application/test_revise_draft_employer.py` + `tests/integration/api/test_staff_employers.py` passed with `110 passed`; the recommended backend rereview bundle `tests/integration/test_initial_migration.py tests/integration/application/test_revise_draft_employer.py tests/integration/api/test_staff_employers.py tests/unit/api/test_employer_schemas.py -q` passed with `134 passed`; the previously flaky same-key changed-actor/payload concurrency node passed focused with `1 passed`; and `git diff --check` passed. That historical branch was subsequently cleared, committed, pushed, and merged by PR #17 at `1543248`; the separate post-merge remediation item below now controls current work.
- [x] Complete and merge the PR #17 post-merge remediation lane: PR #18 merged the independently rereviewed target-binding, locked-row concurrency/no-op authority, safe persistence, and documentation closeout into protected `develop` at `a4d8f90`; all required checks passed.
- [x] Complete local remediation verification: focused regression evidence, exact CI-parity application-quality verification, migration round-trip, dependency audits, SBOM validation, and `git diff --check` passed before the closeout commit.
- [x] Complete fresh independent rereview and final-head closeout of the remediation: no Blocker, High, or Medium findings remained, exact-range secret scanning passed, all protected checks passed, and PR #18 merged at `a4d8f90`.
- [x] Write the preliminary next-session artifact `.hermes/plans/2026-08-11_203958-phase-1-employer-contact-next-session-plan.md`; it is superseded as the active candidate by the more exact ADR-0008 planning packet below.
- [x] Independently review and formally accept ADR-0008 plus `.hermes/plans/2026-08-12_111500-phase-1-employer-contact-authority-foundation-plan.md`: after remediation, exact-artifact API/security and persistence/migration/TDD closure rereviews passed with no Blocker, High, or Medium findings; Beatrice accepted the planning boundary on 2026-08-12.
- [x] Publish the accepted ADR-0008 packet through a protected planning-only PR and merge it to `develop` before any EmployerContact implementation branch begins from the resulting exact tip. PR #19 merged the packet into protected `develop` at `745f9e8`, and the separately authorized coding lane rebaselined from that exact tip onto `feat/employer-contact-authority-foundation`.
- [x] Complete, independently review, qualify, and merge the EmployerContact authority foundation. PR #20 merged the backend-only nested create, bounded parent query, exact read, and typed receipt/audit authority implementation into protected `develop` at `6eb05d5`; its prior handoff is now historical evidence.
- [ ] Define household and general-labor request extensions without creating separate workflows or data stores.
- [ ] Use fictional synthetic fixtures only for the current tracers—never copy, transform, hash, or derive them from client/live records; any later de-identified-data procedure requires separate approval.
- [ ] Implement staff authentication and authorization boundary.
- [ ] Implement employer/contact/worksite/request/shift persistence with migration-managed schema.
- [ ] Implement staff request entry, detail, correction, and an authorized demand work queue as a mandatory service-time capability.
- [ ] Plan and implement a staff-only paper-form scan/OCR-assisted intake path for employer and worker forms: parse into reviewable drafts only, require attributable staff validation/correction before database writes, preserve safe provenance, and qualify secure document-ingestion controls before any live scanned form is admitted.
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
- [ ] Implement staged worker onboarding with agency review, including staff-operated paper-form scan/OCR-assisted draft creation once the secure ingestion and validation boundary is approved; do not imply automatic eligibility or employment.
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

## Delivery date tracker — August 20 to September 7, 2026

**Purpose:** At-a-glance schedule control for the private fictional-synthetic cloud `develop` target, controlled staff-pilot decision, and production-activation backstop. A checked item means the named evidence exists; elapsed time or partial effort is not completion.

**Schedule rule:** The project is on track at the end of a date only when every item marked **Critical checkpoint** for that date is checked. If a critical item remains open, record the blocker in `NOTES.md`, carry it forward explicitly, and reduce feature scope before reducing security, governance, or qualification depth.

**Authority rule:** This tracker records schedule evidence; it does not grant cloud, Terraform, secret, migration, deployment, live-data, or production authority. Every ADR-0013 gate still requires its separate explicit approval.

### Thursday, August 20 — lock the remediation planning packet

- [x] Accept the seven ADR-0013 deployment-path decisions.
- [x] Accept mandatory keyless digest-bound Cosign/SLSA/SBOM evidence and limited Sigstore transparency metadata.
- [x] Create accepted ADR-0013 and amend the F1-F17 remediation plan.
- [x] Reconcile `CURRENT_WORK.md`, this roadmap, security/architecture/technical/decision docs, `AGENTS.md`, and the planning-review handoff.
- [x] Merge the initial documentation-only ADR-0013 packet through protected `develop` as PR #34 at `63caa40`; re-fetch/prune and verify the clean exact planning-merge tip.
- [x] Complete independent planning review across Terraform/gates, IAM/WIF, workflow/supply chain, monitoring, and documentation; it found plan-executability Blocker/High findings requiring this follow-up documentation amendment.
- [x] Amend ADR-0013, the remediation plan, handoff, and living docs to remediate or explicitly disposition every planning Blocker/High finding; independently rereview the amended packet. The final independent working-tree review returned CLEAN, retaining only the accepted same-repository-CI High residual risk.
- [x] Publish and merge the amended documentation-only planning packet through protected `develop` as PR #35 at `db1f293`.

**Critical checkpoint:** PR #34 and PR #35 are historical merged planning context; the amended ADR-0013 packet is independently rereviewed and merged, and implementation has not begun from an unmerged planning surface.

### Friday, August 21 — close the deployment Blockers first

- [x] Create `fix/post-pr33-deployment-path-remediation` from the exact ADR-0013 planning merge.
- [x] Complete exact-node RED → GREEN coverage for required `foundation → migration → service` staging.
- [x] Prove the foundation graph contains no executable Cloud Run job or service.
- [x] Wire exact runtime and migration configuration plus distinct Secret Manager references without payloads in Terraform.
- [x] Remove imperative Cloud Run configuration mutation from the deploy workflow.
- [x] Replace broad deploy authority with exact-job `roles/run.jobsExecutor` and exact job/service `roles/run.viewer`.
- [x] Enforce direct-workflow `workflow_ref` separation for publisher and deploy executor; remove dormant GitHub provisioner WIF and unnecessary Token Creator authority.
- [x] Run focused no-cloud tests, locked static validation, both Terraform root validations, and diff hygiene for the day’s nodes.

**Critical checkpoint:** F1-F3 and F7 have source-level GREEN evidence; no cloud command or service start has occurred.

### Saturday, August 22 — finish the no-cloud remediation surface

- [x] Implement the accepted IAM-private internet-reachable named-tester ingress contract without public/broad invocation.
- [x] Add Billing Budgets API management/dependency and provider-valid Cloud SQL recovery bounds.
- [x] Correct stage-aware foundation-verifier API, IAM, budget-channel, and live-response representations.
- [x] Make deploy evidence failure-safe, non-mutating, typed-Ready-aware, and explicit that Gate 6 qualification has not run.
- [x] Add bootstrap provider-schema CI validation and stage-aware Terraform expansion/cardinality policy.
- [x] Implement keyless exact-digest Cosign signature and signed SLSA v1, image-SBOM, and checksum-bound application-SBOM verification at publish and deploy boundaries.
- [x] Enforce the reviewed request-log minimization posture or record a narrow truthful disposition.
- [x] Add authenticated Cloud Monitoring `/readiness` uptime evidence with exact monitoring-service-agent invocation and provisional repeated-failure routing.
- [x] Reconcile remediation docs and prepare the exact implementation review handoff.
- [x] Run the complete local no-cloud qualification bundle.

**Critical checkpoint:** F1-F17 have implemented evidence or an explicit accepted residual-risk disposition; no undispositioned Blocker/High remains in the working tree.

### Sunday, August 23 — review, merge, and qualify cloud facts read-only

- [x] Complete independent Terraform/gate, IAM/WIF, database/runtime, workflow/supply-chain, monitoring, and documentation reviews.
- [x] Remediate every substantiated Blocker/High and all unaccepted Medium findings.
- [x] Pass exact-head quality/security checks, exact-range Gitleaks, `git diff --check`, and final cross-lane rereview.
- [x] Push the exact reviewed head, pass protected CI, and merge the remediation PR. PR #37 merged into protected `develop` at `caf96a72df87cd98114025627ad9f467f846f3a9`; its remote and local feature branches were retired after patch-equivalence and clean-worktree rebaseline evidence.
- [x] Rebaseline from the exact remediation merge and confirm a clean worktree.
- [x] Obtain and execute the initial bounded Gate 2 read-only GCP qualification; identifiers, commands, and raw outputs remain in private operator-held evidence.
- [x] Record the observed project, billing, IAM, API, quota, region, CIDR, and resource-collision findings privately; do not commit identifiers or sensitive output.
- [x] Reconcile the observed Gate 2 evidence with the separately approved partial foundation work and freeze the remaining operator-held decision/input dispositions: Terraform will become the future sole desired-state authority through a later reviewed adoption/reconciliation plan; recovery controls remain provisional; plan artifacts remain operator-held; monitoring-delivery confirmation, private-network/Cloud SQL inputs, and tester authority remain separate later-gate evidence.

**Critical checkpoint:** Gate 2 is closed with its value-safe findings and decision dispositions recorded privately. The next transition remains blocked until a separate reviewed source/live adoption/reconciliation plan is accepted; no import, Terraform plan/apply, or cloud mutation is implied by this closure.

### Monday, August 24 — bootstrap, plan, and apply foundation only

- [x] Complete separately approved partial control-plane/bootstrap and non-executable foundation work; its identifiers, commands, and raw evidence remain private, and it does not constitute a Terraform apply or a completed foundation gate.
- [x] Prepare, review, accept, and merge the source/live adoption/reconciliation plan that will make Terraform the future sole desired-state authority for the partial foundation. PR #45 merged `.hermes/plans/2026-08-26_164654-source-live-adoption-reconciliation-plan.md` into protected `develop` at `3c897e4`; it prohibits import, backend/state actions, Terraform plan/apply, and cloud mutation until later separate approval, and it blocks every foundation saved plan until a separately accepted source amendment stage-gates/removes the currently unconditional network, private-service-access, Cloud SQL, and application-database actions from the evaluated foundation root.
- [x] Implement, review, and merge the separate source amendment that makes `deployment_stage=foundation` omit network, private-service-access, Cloud SQL, and application-database resources plus their operator-held inputs before any adoption or foundation saved plan is attempted. PR #46 merged the independently rereviewed, protected-CI-qualified no-cloud source amendment into `develop` at `58aed28`; it does not authorize source/live inventory collection, backend/state actions, Terraform plan/apply, or cloud mutation.
- [x] Publish and merge the Gate 3 source/live adoption-ceremony planning packet. PR #47 merged `.hermes/plans/2026-08-26_210433-gate3-source-live-adoption-ceremony-plan.md` into protected `develop` at `d7952b4`; it preserves separate approvals for private inventory, bootstrap-root adoption, workload-root adoption, and the later exact foundation-plan request, and it recorded the then-open foundation-stage verifier contradiction that PR #48 subsequently closed.
- [x] Implement, independently rereview, and merge the separate source-only foundation-stage verifier reconciliation. PR #48 merged the bounded no-cloud correction into protected `develop` at `5f265d8`; `foundation` mode now permits absent Cloud SQL and rejects unexpected Cloud SQL/workload presence, while `migration` and `service` continue to fail closed on the required private Cloud SQL posture. The merge grants no source/live inventory, backend/state, plan/apply, or cloud authority.
- [x] Merge the accepted master plan's remaining PR B through protected `develop`; rebaseline from the exact tip and invalidate any pre-merge inventory/source approval bundle before target collection or adoption. PR #50 merged PR 0 at `d142bba`, PR #51 merged PR A at `a7f0649`, and PR #52 merged PR B at `7272907`.
- [x] Merge the binding/A1-recollection packet as PR #58 at `a8e091a`; it correctly prohibits project creation and separates WP-2/WP-3 approvals, but its full-A1-recollection language is superseded before execution to preserve PR #57's closed A1 record.
- [x] Merge PR #58's workload binding packet and PR #59's bounded scope-delta amendment; complete separately approved WP-2 binding/readback and WP-3 delta without mutation, preserving PR #57's closed A1 record.
- [x] Complete separately approved A2 provenance decision: the durable bootstrap bucket was manually established before Terraform state, so empty state/no local state retire prior-state adoption/import.
- [x] Merge PR #60's E1 bootstrap-state establishment/reconciliation decision packet and PR #61's source-only bootstrap IAM-address reconciliation plan.
- [x] Implement, independently review, and merge the bounded deduplicated bootstrap bucket-IAM representation from `.hermes/plans/2026-09-01_001500-bootstrap-iam-address-reconciliation-plan.md`; PR #62 merged it into protected `develop@0d13ebc` with no cloud action.
- [x] Rebind the private E2 backend/input/inventory/recovery material to the merged IAM-reconciliation source SHA, complete the bounded command allowlist/readback record, and establish/bootstrap-read back the new bootstrap-only state lineage. The final private readback contained only the expected bootstrap addresses; no plan/apply or cloud resource/IAM/API mutation occurred.
- [x] Obtain and execute the separate explicit bootstrap-state establishment/reconciliation approval, then independently verify bootstrap-only lineage, serial, recovery binding, and address set before stopping.
- [x] Complete the separately approved workload-state-path preparation: distinct backend target/lock scope, exact foundation-only inputs, current read-only inventory, recovery binding, and reviewed workload addresses. The private allowlist covers 37 present foundation addresses and separately records four absent source IAM bindings for later plan disposition.
- [x] Review, merge, and rebind the minimal foundation-stage null-image interpolation correction discovered by the first workload import. PR #63 merged the guarded local at `2fb7d2f`; the resumed E3 imports completed with all 37 approved resource addresses independently read back in distinct workload state, plus one expected evaluated data-source address.
- [x] Complete the ADR-0013 Amendment B A5 augmentation disposition. Fresh bootstrap/workload state and live IAM readbacks confirmed the artifact-verifier identity, exact deploy-workflow WIF binding, and exact repository-reader binding already converge; no empty bootstrap augmentation plan/apply was manufactured.
- [x] Review, merge, and rebind the foundation-stage readiness-host local correction. PR #64 merged the guard at `c78ba18`; the rebound private foundation plan has zero Cloud Run service/job changes.
- [x] Complete the accepted foundation ownership-alignment outcome through separate saved-plan generation, apply, and post-apply verification: all five replacements were removed; the exact approved foundation apply verified 41 managed addresses plus one expected data source, with no executable workload, Secret version, database, migration, service, tester, live-data, or production action.
- [x] Complete Gate P immutable image publication. PR #74 merged the canonical Cosign v3 signature-admission correction at protected `develop@92b104e`. Approved run `33882394981` completed immutable `linux/amd64` build/push/scan, keyless signing, SLSA v1/SPDX/embedded application-SBOM attestations, certificate/issuer/transparency verification, final repository semantic admission, and the verifier-approved immutable image-reference artifact. All eight evidence files and their integrity manifest are preserved privately. The approval is consumed. At Gate P closeout, Gate S and every downstream gate remained separately unapproved; Gate S has since completed only the bounded `synthetic-staff-id` version and private custody record, while both database-URL versions and every downstream gate remain deferred.
- [x] Review the foundation-scope resource inventory, IAM, APIs, budgets, Secret metadata, logs, recovery controls, costs, and destruction/replacement actions; private network and Cloud SQL remain correctly deferred to later stages.
- [x] Obtain explicit Gate 4 approval for the exact replacement-free saved foundation plan.
- [x] Apply only the approved foundation plan; the result contains 41 managed addresses plus one expected data source and no executable workload.
- [x] Run corrected foundation-mode verification for effective IAM, no executable workload, no service-account keys, state controls, budgets, alerts, logging, labels, deletion protection, and teardown inventory. Private-network / Cloud SQL posture remains deferred to the later stage where those resources are in scope.
- [x] Stop after foundation verification and before image publication, Secret payloads, database logins, migration job, service, or tester access.

**Critical checkpoint:** The verified foundation exists with no executable workload and no unresolved foundation Blocker/High.

### Tuesday, August 25 — activate and qualify private cloud develop

- [x] Publish the reviewed `linux/amd64` image once and capture its immutable digest. Approved run `33882394981` completed this Gate P operation from exact protected `develop@92b104e`; its one-use approval is consumed.
- [x] Verify exact-workflow keyless signature, transparency inclusion, SLSA v1 provenance, SPDX image SBOM, and backend/frontend SBOM bindings. Final repository semantic admission and verifier-approved immutable-reference emission passed in run `33882394981`.
- [ ] Complete staged out-of-band Secret-version preparation without exposing payloads. The early Gate S custody record is established and the sole `synthetic-staff-id` version was generated non-echoingly and verified by metadata-only readback. Runtime/migration database-URL versions remain deferred until migration-stage Cloud SQL/database creation and separately approved login-role preparation provide real connection material; do not create placeholders.
- [ ] Produce, review, approve, and apply the exact `migration` plan only after accepted ADR-0015 is published/merged and its interleaved FinOps sequence completes: PR A, isolated FinOps state-bucket plan/apply/readback, exact budget import, old workload-state removal under continuous freeze, PR B workload extraction, FinOps no-op convergence, and fresh signed receipt. The subsequent provisioner plan must be quota-free, bind/consume that receipt, and remain separately approved; no historical packet or approval is reusable.
- [ ] After migration-stage Cloud SQL/database exists, separately approve database login-role preparation, grant only reviewed non-login group-role chains, and verify database authority through non-echoing connection-material handoffs.
- [ ] Verify the configured migration job identity, digest, environment, secret references, network, and database authority before execution.
- [ ] Explicitly authorize and execute the migration once; capture advisory-lock, schema-version, and compatibility evidence.
- [ ] Produce, review, approve, and apply the exact `service` plan only after successful migration evidence.
- [ ] Verify exact named invokers, runtime configuration, ready revision/digest, and typed Cloud Run `Ready` condition.
- [ ] Verify approved tester access succeeds and unauthenticated/unapproved access fails.
- [ ] Run Gate 6 foundation, database, bounded synthetic application, log, alert, cost, recovery, browser, accessibility, and English/Spanish qualification.
- [ ] Record exactly one master-plan status: `qualified_private_develop_for_human_feedback`, `operational_private_develop_technical_feedback_only` (only the allowlisted fluent-language review may remain open), `not_qualified`, or `torn_down_after_failed_activation`; include blocker, tester-access removal/review date, recovery/cleanup, and feedback disposition without private values.
- [ ] Do not describe the target as production-ready or admit live/client-derived data.

**Critical checkpoint:** A functioning private synthetic `develop` target is qualified by evidence, or the project has a truthful blocker record and recovery plan without weakening controls.

### August 26–30 — stabilize the staff-pilot candidate

- [ ] Freeze the narrow agency-facing pilot scope; defer public and unrelated feature work.
- [ ] Define the exact staff cohort, data classification, support owner, incident path, manual fallback, and client acceptance owner.
- [ ] Implement and qualify real staff identity, MFA, session, recovery, deprovisioning, and server-enforced authorization before live use.
- [ ] Complete only the minimum end-to-end employer-demand workflow required for the pilot; do not represent unimplemented dashboard/request/shift behavior as available.
- [ ] Polish the released staff workflow’s loading, empty, success, error, conflict, unknown-outcome, recovery, keyboard, responsive, and bilingual states.
- [ ] Complete human browser, manual accessibility, and fluent English/Spanish review on the controlled shared target.
- [ ] Verify monitoring/alert delivery, backup/restore or teardown/rebuild, rollback/forward recovery, support documentation, and staff training material.
- [ ] Complete a client walkthrough and disposition every pilot-blocking finding.
- [ ] Decide whether August 31 production activation criteria are actually satisfied.

**Critical checkpoint:** The staff-pilot candidate has real identity and operational-readiness evidence; cosmetic polish has not displaced security, workflow correctness, or recovery work.

### Monday, August 31 — ideal production go/no-go

- [ ] Confirm the production release is the qualified immutable artifact, not an unreviewed rebuild.
- [ ] Confirm production data purpose/minimization, access, retention/disposal, audit-history recipients, backups, incident handling, support, and client acceptance are explicitly approved.
- [ ] Confirm no unresolved Blocker/High security, privacy, authorization, migration, recovery, accessibility, language, or operational finding remains.
- [ ] Record an explicit Beatrice/client production go decision for the narrow staff-only workflow.
- [ ] If every production gate passes, activate only the approved narrow staff workflow and record rollback/support evidence.
- [ ] If any production gate fails, keep the target non-production, record the blocker, and activate the September 7 backstop plan without relabeling the pilot as production.

**Critical checkpoint:** Production status is evidence-based and explicitly approved; schedule pressure does not convert a test target into production.

### September 1–6 — backstop remediation and production qualification

- [ ] Resolve every August 31 production blocker through reviewed, test-first work.
- [ ] Re-run security/privacy, authorization, migration, dependency, secret, backup/recovery, monitoring, accessibility, and language gates on the final candidate.
- [ ] Complete client acceptance, named support coverage, staff training, manual fallback, and incident/recovery rehearsal.
- [ ] Promote only the qualified immutable candidate through the protected `develop → main` release path.
- [ ] Freeze nonessential feature work until production activation and initial stability evidence are complete.

**Critical checkpoint:** The September 7 candidate is fully qualified with no schedule-based control exceptions.

### Monday, September 7 — production activation backstop

- [ ] Reconfirm the exact artifact, production configuration, identity/IAM, secrets, database migration, monitoring, backup/recovery, support, and acceptance evidence.
- [ ] Obtain explicit final production activation approval.
- [ ] Activate only the approved narrow agency-facing workflow.
- [ ] Verify post-activation health/readiness, access, logs, alerts, core staff workflow, and rollback/forward-recovery posture.
- [ ] Record client acceptance, known limitations, deferred public/worker features, support ownership, and next review date.

**Critical checkpoint:** The narrow staff workflow is operating under approved production controls, or activation remains blocked with a truthful documented reason.

### Schedule protection — first work to defer

If any critical checkpoint is at risk, defer these before compressing a security or governance gate:

- [ ] Public worker/employer portals and public job publication remain deferred.
- [ ] Worker-facing onboarding/profile expansion remains deferred unless required by the accepted narrow pilot.
- [ ] OCR/uploads, maps/geocoding, worker-supply overlays, automated comparison, broad reporting/export, and external integrations remain deferred.
- [ ] Decorative animation, marketing polish, and other nonessential visual enhancements remain deferred.
- [ ] No deferred item is silently reintroduced without an accepted plan and updated schedule impact.
