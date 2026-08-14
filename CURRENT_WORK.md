# Current Work — Golden Rose Operations Platform

**Updated:** 2026-08-13
**Lane:** Phase 0.5 planning — Terraform preparation after PR #22 closeout
**Verification:** PR #22 merged the local runtime/container contract into protected `develop` at `f3cac4de839bf4172754a0bee7f84dd8ab26b622`; GitHub reported `application`, `check`, `enforce`, and CodeRabbit successful. After fetch/prune, local `develop` was fast-forwarded to that exact `origin/develop` tip, the retired `feat/gcp-develop-runtime-container` branch was verified tree-equivalent to the merge result, and fresh branch `docs/pr22-closeout-terraform-prep` was created from the merged tip.
**Overall status:** The current tracer now includes backend EmployerContact create, bounded parent query, exact read, typed receipt/audit authority, and the PR #22 local runtime/container contract: explicit private-synthetic `develop` posture, value-safe environment marker, cheap `/health`, bounded no-store `/readiness`, same-origin static serving, entrypoint/runtime behavior, and non-root local image build/inspection evidence. Task 11 image evidence remains local-only; `/readiness` correctly returned static 503 in the image-only probe because no database was wired. The active lane is now Terraform preparation planning in `.hermes/plans/2026-08-13_181005-terraform-preparation-plan.md`. Beatrice has accepted the 14-decision private synthetic-only GCP `develop` IaC posture: `us-east4`; Terraform-managed API enablement; bootstrap-to-WIF Terraform provisioner identity; separate runtime/migration identities; private Artifact Registry digest deployment and cleanup; Terraform-managed $50/$75/$100 budget alerts; Secret Manager metadata/IAM only; private `db-f1-micro` Cloud SQL PostgreSQL 16; dedicated VPC/private service access; private Cloud Run invoker IAM only for approved principals; protected GitHub WIF apply/deploy gates; value-safe Logging/Monitoring; standard labels/tags; intentional teardown runbook support; and local state only until remote state is approved before shared apply. This lane still does not authorize Terraform implementation, Terraform apply, GCP project/billing/resource/service-identity provisioning, credentials, image push, cloud deployment, Cloud SQL use, public access, real identity, live/client data, production work, or merge approval.

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
1. Complete the PR #22 post-merge living-doc closeout on `docs/pr22-closeout-terraform-prep`, then run `git diff --check` and inspect the resulting diff before any commit/PR.
2. Use `.hermes/plans/2026-08-13_181005-terraform-preparation-plan.md` to prepare the next reviewed Terraform/IaC implementation plan around the accepted 14-decision develop posture; keep it planning-only until independently reviewed, accepted, and merged.
3. Keep PR #22's local-image evidence explicit: the image builds and serves `/health`/SPA shell locally; `/readiness` correctly returns static 503 without a wired local database during the image-only probe.
4. Do not create Terraform implementation files, run Terraform, authenticate to GCP, push images, or convert local Docker evidence into cloud deployment evidence; migration-job, non-owner database-role, WIF/digest promotion, Artifact Registry, Cloud SQL, provisioning, and deployment work remain separately gated. Treat API enablement as approved planning/provisioning scope only when the later provisioning gate is explicitly opened, not as permission to create workload resources now.

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
- Do not start cloud services, provision accounts, push images, call GCP APIs beyond explicitly approved API-enablement/provisioning scope, use Cloud SQL, or change client systems without explicit scoped approval.
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
- PR #17 merged the bounded synthetic/local draft-Employer revision implementation into protected `develop` at `1543248`; PR #18 merged its independently rereviewed remediation at `a4d8f90`. PR #19 merged the accepted ADR-0008 planning packet at `745f9e8`, PR #20 merged its independently reviewed EmployerContact authority implementation at `6eb05d5`, PR #21 merged the accepted ADR-0009 GCP develop deployment foundation planning packet at `9e27f80`, and PR #22 merged the local runtime/container contract at `f3cac4d`. Those feature/docs branches are historical; the active Terraform preparation planning branch starts exactly from the PR #22 merged tip.

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
