# Current Work — Golden Rose Operations Platform

**Updated:** 2026-08-14
**Lane:** Phase 0.5 PR #24 remediation planning — independently qualify the seven-finding validate-without-apply packet before any remediation implementation or bootstrap/state/WIF planning
**Verification:** PR #25 merged the documentation-only PR #24 disposition into protected `develop` at `8dc1198c0eb571ca39e9f4814bb3af5e33079890`. The fresh planning branch was created from that exact tip. `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md` and ADR-0010 specify the required order and hard stops for two High and five Medium defects. Three independent review rounds remediated all Medium-or-higher planning findings; final Terraform/documentation, semantic-manifest, and staged-governance rereviews returned `ACCEPT`. The first High cannot be closed by another PR-editable status name: an eligible independently controlled GitHub reviewer/CODEOWNER must still be nominated and verified before implementation begins.
**Overall status:** The current tracer includes backend EmployerContact create, bounded parent query, exact read, typed receipt/audit authority, PR #22's local runtime/container contract, and PR #24's merged repo-local Terraform scaffold, provider lockfile, static validation harness, and pull-request infrastructure-quality workflow. No Terraform plan/apply, cloud authentication, API enablement, provisioning, remote-state migration, image push, Cloud SQL use, service start, deployment, public access, real identity, live/client data, or production work has occurred. Beatrice accepted a durable bootstrap/state control plane that remains separate from the disposable `develop` workload and survives repeated teardown/redeployment. The existing non-workload GCP project is the candidate control-plane project pending read-only qualification; identifiers, billing details, principals, credentials, and secret payloads remain outside tracked source and ordinary docs.

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
1. Publish the independently accepted planning-only packet to protected `develop` with exact documentation-scope and secret-scan evidence. Do not modify Terraform, CI, scanner, tests, dependencies, lockfiles, or live GitHub policy on this branch.
2. Merge only after PR checks and review evidence remain consistent with the exact published head.
3. Before any implementation branch starts, nominate and verify a real non-author GitHub reviewer/CODEOWNER. If that prerequisite is unavailable, keep required-CI authority High open and stop.
4. After the planning packet is accepted and merged, obtain separate authorization, rebaseline exact `origin/develop`, and execute the seven remediation nodes in the mandated governance → semantic policy → `uv` → networking → API ordering → backup → image-authority order.
5. Only after remediation is independently cleared and merged and repository policy is applied/read back from protected `develop`, prepare the separate bootstrap/state/WIF contract packet.

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
- No cloud authentication, GCP API call, backend migration, Terraform plan/apply, API enablement, provisioning, image push, Cloud SQL use, service start, deployment, or client-system change is currently authorized. Fresh scoped authorization may be considered only after the PR #24 remediation merges and the bootstrap/state/WIF packet is reviewed and accepted.
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
- PR #17 merged the bounded synthetic/local draft-Employer revision implementation into protected `develop` at `1543248`; PR #18 merged its independently rereviewed remediation at `a4d8f90`. PR #19 merged the accepted ADR-0008 planning packet at `745f9e8`, PR #20 merged its independently reviewed EmployerContact authority implementation at `6eb05d5`, PR #21 merged the accepted ADR-0009 GCP develop deployment foundation planning packet at `9e27f80`, PR #22 merged the local runtime/container contract at `f3cac4d`, PR #23 merged the Terraform preparation planning packet at `c27e1ee`, PR #24 merged the validate-without-apply Terraform scaffold at `50451b3`, and PR #25 merged its documentation-only disposition at `8dc1198`. Those branches are historical; the active branch is the planning-only PR #24 remediation packet from exact `origin/develop@8dc1198`.

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
