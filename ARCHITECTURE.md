# Architecture — Golden Rose Operations Platform

## 2026-09-16 — Current private develop architecture status

Protected `develop@dd6697871986fa5677e722b2805a21a8a7776b64` is deployed to the existing private fictional-synthetic Cloud Run/Cloud SQL `develop` service for stakeholder review. The architecture remains one private staff service behind the temporary expiring Basic gate, with private Cloud SQL, one-instance service bounds, immutable image promotion, and fictional/synthetic data controls. The latest rollout changed only image references for the service, migration job and database-authority job; it did not run migrations, execute database verification, alter Terraform topology, change ingress/authentication, rotate credentials, or promote production authority.

The visible dashboard now contains a static NYC map, calendar and work-queue experience. Architecturally, these are review surfaces over static or placeholder data until separately wired to authoritative request, shift, zone/map-area, follow-up and audit records. Dashboard, calendar, queues, search and maps remain disposable derived projections/queries; PostgreSQL domain rows and append-only audit history remain the authoritative current/history boundary.

## 2026-09-15 — PR D canonical correction source candidate

PR #104 merged PR C at `develop@50f2ac86621329f12680e706bd8d224e76833c22`. PR D proceeds on `feat/staff-intake-corrections` under accepted ADR-0017. The source adds nine explicit section correction commands with current field permissions, expected versions, required reasons, immutable retries, same-target correction references, and protected before/after evidence. Separate current-facts review binds the original output identities/dispositions to current row versions; original intake reviews and finalizations remain immutable.

Migrations `0009_canonical_corrections` and `0009a_canonical_reviews` retain applied predecessors, narrow runtime column grants, invoker-only guards, exact typed receipt/result/audit authority and downgrade refusal with protected history. Current-purpose address and structured schedule/availability checks apply in both application and SQL authority. Browser buffers retain later edits and exact unknown retries, serialize shared-row commands, and block router history traversal while unresolved; the router's optional transition cache uses inert storage. No default permission activation, cloud inspection/mutation, deployment, live/client data or production authority follows. See [the intake contract](docs/planning/staff-intake-contract.md) and [the PR D handoff](docs/review-handoffs/2026-09-15-staff-intake-pr-d-handoff.md) for qualification and publication status.


## 2026-09-14 — PR B source implementation

PR #102 merged durable intake drafts at `develop@2783415dd19027428bf2036730b6c0d83f23ab3c`. The owner completed the bounded local browser-verification step and authorized PR B on `feat/staff-intake-review`. Review/follow-up, protected history and governed bilingual work interests are now implemented in the source candidate. Fresh specification/quality and final integration reviews approved source publication; local qualification passed 1,253 backend tests (95.64% coverage) and 202 frontend tests. Required CI and protected merge remain; this is not deployed functionality. The browser evidence remains separately preserved in `ee82615` on `test/staff-intake-browser-ux`, and the requested minor-polish note is reserved for the next docs PR.

Migration `0007_intake_review_follow_up` extends exact receipt/result/audit authority and append-only protected payloads. Review binds the saved content/catalog versions; follow-up changes aggregate version without changing reviewed facts. Owner choices come only from an injected trusted directory; no user administration or develop permission grant is introduced. Contract §6 clarifies the bounded owner query and structured protected follow-up context. PR C linking/finalization and PR D corrections remain later work under the accepted plan. No cloud inspection/mutation, deployment, live/client data or production authority follows. The historical v28 packet remains consumed and its formal status remains `not_qualified`.

See the [PR B handoff](docs/review-handoffs/2026-09-14-staff-intake-pr-b-handoff.md) for the current evidence and next action. Older PR A-only and planning-only activation statements below are historical.

## 2026-09-14 — PR A source activation

PR #100 merged this intake planning contract at `ce38fb0`; PR #101 merged the Wave 1 UX predecessor at `9a6b66735f7261ca705f7e8ba5b7c2afcd815f92`. The owner subsequently authorized PR A implementation and disposable local PostgreSQL tests. The active branch is `feat/staff-intake-drafts` from that exact integration tip. Older docs-only/unmerged-predecessor statements below describe the planning snapshot and are superseded for this source lane. Browser UX verification is deferred until PR A is finished at the owner's request.

PR A adds only durable candidate drafts, separately authorized address sections, bounded shared recovery and typed atomic receipt/result/audit authority. Review/follow-up, links, canonical finalization and corrections remain PRs B–D. The v28 runtime is historical and remains `not_qualified`; no deployment, cloud inspection/mutation, live data or production is authorized or claimed.


**Status:** Docs-only staff-intake planning, not implemented or deployed. Wave 1 UI is a separate preserved predecessor with no new backend authority; intake explicitly proposes bounded new persistence, permissions, API, and finalization authority. V28 is historical deployment evidence, not a runtime check performed by this audit.

## 2026-09-14 — Staff intake planning boundary

Accepted conversational direction is durable shared worker/employer intake with explicit save/resume, version-bound review and follow-up, restricted addresses, deliberate existing-party links without overwrite, and atomic finalization only after complete current review. Technical details remain proposed source contracts, not deployed functionality or new client/counsel policy. See [Staff intake contract](docs/planning/staff-intake-contract.md), [outcome-scale plan](.hermes/plans/2026-09-14-staff-intake-workflows-plan.md), and proposed [ADR-0017](docs/adr/ADR-0017-staff-intake-workflows.md).

The improved Wave 1 UI is the preserved uncommitted predecessor in `/Users/genie/Desktop/golden_rose_project` on `feat/staff-intake-workflows`; do not reset, stash, copy over, or mix it into this docs-only planning worktree. Complete and merge that predecessor and the accepted planning packet before intake coding. V28 deployment/browser evidence is historical and its packet consumed; this audit did not recheck runtime availability or access expiry. The last recorded formal status remains `not_qualified`. No cloud, live-data, public-plane, implementation, or service-start authority is granted here.

## Architectural posture
Start with one modular product and a relational operational core. Preserve explicit trust boundaries and auditability without prematurely splitting into microservices.

## Logical components
```text
Agency Staff Web App ──┐
                       ├─ Staff API / domain service ─┐
Public Worker/Employer ┤                               ├─ PostgreSQL operational records
Apps (later, separate) └─ Public API / domain service ─┤
                                                       ├─ Private document store (later, qualified)
                                                       ├─ Audit-event / reporting projections
                                                       └─ Observability, backup, secret-management services
```

## Security-plane boundary
- **Staff plane:** separate hostname/application/API route set, identity client, session/token audience, credentials, authorization policies, and deployment secrets. Staff actions are attributable and MFA is required before live use.
- **Public plane:** future worker/employer experience. It does not receive generic administrative APIs or access to staff-plane credentials/data.
- **Controlled crossing:** staff can take defined, audited actions on public-workflow records. Public identities cannot self-promote into staff roles.

The logical split does not require independent products or microservices in V1. It requires deliberate identity, endpoint, credential, deployment, and data-access separation.

## Staff authorization and support boundary
- The accepted business roles are Owner, delegated Manager, and interchangeable Operations Staff. Their named permissions, field restrictions, delegations, exact-location controls, export denial, and verification obligations are controlled by `docs/planning/phase-1-staff-permission-matrix.md`; permissions must be server-enforced, attributable, and limited to approved operational records/actions.
- Platform Administrator is a distinct technical-support role, not a business-superuser role. It uses a separate privileged identity/access path for health, cache/job remediation, and approved troubleshooting; it has no standing access to operational personal data, documents, raw database records, or business-role administration.
- Exceptional production support access requires time bounds, approval, attribution, logging, automatic expiry/revocation, and Owner review. Owner authority over agency operations does not imply routine cloud-console, secret, backup, or database access.
- `docs/planning/phase-1-mfa-recovery-support-ownership.md` controls individual staff/privileged identities, required MFA factors, step-up actions, staff/privileged session limits, independent recovery, access reviews, and support ownership. The identity provider must be qualified against that contract and cannot silently weaken application authorization or combine public/staff identity audiences.

## Authoritative data and derived views
PostgreSQL is the accepted transactional system of record for approved operational entities. Domain rows are authoritative current truth; append-only `AuditEvent` records are authoritative material history, not a full event-sourcing/replay store. `docs/planning/phase-1-correction-audit-event-contract.md` controls draft revisions, material corrections, atomic domain/event commands, concurrency/idempotency, protected prior/new values, correction-of-correction, and projection failure behavior. The dashboard, calendar/month views, work queues, map, search, reporting, and metrics are disposable derived projections/queries, not independent manual response stores.

The accepted employer-demand predecessor structural source of truth is `Employer → EmployerContact / Worksite / StaffingRequest → ShiftNeed / RequestRequirement`, supported by `WorksiteZoneMembership`, `ServiceZone`, `ServiceZoneComposition`, `MapAreaDatasetVersion`, `MapArea`, `WorksiteMapAreaAssignment`, and `AuditEvent`. Worksite-to-zone and worksite-to-map-area relationships use explicit versioned association records; they are not collapsed into a direct service-zone foreign key. `Employer` is neutral across household and business hiring parties; employer type enables governed extensions without separate forms or response stores. `docs/planning/phase-1-canonical-field-purpose-inventory.md` controls the purpose, classification, visibility boundary, prohibited uses, and exclusions for these fields.

`docs/planning/phase-1-request-shift-state-model.md` controls guarded lifecycle transitions. Active shift coverage is represented in the shift state and may reverse with attributable count/source evidence, including reported no-shows. Terminal shift outcomes remain authoritative when the parent request closes. State transitions and audit events must be committed consistently; dashboards and calendars derive from those records rather than maintaining separate status.

`docs/planning/phase-1-work-queue-aging-follow-up-model.md` controls derived queue timing, ownership, follow-up, provisional review triggers, and deterministic lanes. Request record age, agency-controlled review time, explicit follow-up deadlines, and continuous shift urgency remain separate measures. Queue escalation increases authorized visibility/priority only; it does not mutate domain state, reassign work, or send external messages automatically.

`docs/planning/phase-1-calendar-coverage-semantics.md` controls the derived staff calendar. Date-only request milestones and timed shift occurrences remain distinct projections over authoritative records. No executable recurrence or worker-conflict inference exists in Phase 1. Calendar drag issues governed commands: active-shift rescheduling atomically creates a linked replacement and cancels the prior shift without transferring coverage.

`docs/planning/phase-1-service-zone-taxonomy.md` controls broad operational geography. The Owner may evolve labels and group pinned NYC CDTAs into zones during pilot use without engineering changes. A worksite may have overlapping effective memberships with one primary/default; requests and shifts may remain visibly unassigned until later classification. Zone catalog/composition, membership, workflow-record classification, CDTA derivation, and exact address remain separate authorities.

`docs/planning/phase-1-nyc-job-demand-map-contract.md` controls the Phase 1 authorized-staff NYC map. A pinned/checksummed DCP 2020 CDTA release supplies fixed geometry. A provider-neutral server-side geocoder yields a transient point for local point-in-polygon assignment; exact coordinates are discarded by default. The map derives transparent demand/coverage measures and an accessible equivalent table. Renderer, tile, and geocoder providers remain replaceable and separately gated. No worker layer exists until its location/availability contract is approved.

Material operational changes preserve the accepted event envelope, changed-field evidence, actor, server time, reason where applicable, source/reference, and relationship to prior record/event. Required domain changes and audit inserts commit atomically through one reviewed authority boundary; stale writes are rejected. Corrections, cancellations, replacements, and supersessions are linked actions rather than silent overwrites. Projection failure never rolls back committed truth or becomes a false empty result.

## Proposed intake authority extension

The outcome is ordered PRs A–D, including §9 canonical correction/current-facts review, not read-only outputs as the completed outcome. Expected target/dependency versions, delegated correction rights, independent restricted read/write, reason and protected atomic before/after history govern corrections. Original finalized intake/review/output links remain immutable. Section-local saves isolate command keys, status and unsaved buffers across version refresh; no aggregate saved claim during another section's unknown outcome. Planning publication is independent of UI merge; both accepted planning and preserved UI merges gate coding.

The intake contract adds durable candidate aggregates and separately protected addresses/review history, not a second editable customer master. Atomic expected-version/idempotent finalization creates or explicitly reuses the listed Worker/contact/residence/preferences or Employer/contact/details/address/worksite/draft-request records. Existing linked rows are never silently overwritten; finalized intake snapshots remain immutable. No ShiftNeed, open demand, coverage, map assignment, worker verification, referral or placement is created. Existing Employer/contact DTOs and permissions remain unchanged; new output reads and typed receipt/event/FK extensions are explicit proposed exceptions to predecessor-only scope.

## Accepted and proposed technology direction
- ADR-0005 accepts React 19, TypeScript 5.9, Vite 8, npm, Vitest/Testing Library, plain CSS, and a typed English/Spanish catalog for the first local/synthetic staff browser slice. PR #12 merged that planning packet into `develop`, and PR #13 merged the first implementation.
- ADR-0006 governed the closeout merged by PR #15. ADR-0007 governed draft-Employer revision merged by PR #17 and remediated by PR #18. PR #20 merged ADR-0008's independently reviewed EmployerContact authority implementation at `6eb05d5`. PR #22 merged ADR-0009 Slice B's local runtime/container contract at `f3cac4d`; v28 later completed the private synthetic Cloud Run/Cloud SQL deployment and first browser handoff. Manual accessibility/fluent-language evidence and production identity remain future gates.
- ADR-0003 accepts Python 3.12, uv, FastAPI/Pydantic v2, synchronous SQLAlchemy 2/psycopg 3, Alembic, and PostgreSQL 16 for the first backend slice.
- GCP is the selected platform. Cloud Run + private Cloud SQL is the managed-container/database baseline; Secret Manager, Artifact Registry, Cloud Logging/Monitoring, and GitHub Actions with Workload Identity Federation are supporting services. `us-east4` is the single `develop` location. ADR-0015 FinOps separation is deferred until production/handoff or a concrete billing trigger; the existing workload budget remains authoritative.
- ADR-0009 accepts one private same-origin staff-app Cloud Run service for the first shared tracer, an explicit one-shot migration job, Cloud SQL PostgreSQL 16, distinct runtime/migration/deploy identities and database roles, Terraform, digest promotion, Secret Manager, and value-safe observability. PR #22 implemented only the local package/runtime contract for that future target; Cloud Run IAM remains only an outer test-access perimeter while synthetic application authentication remains and is not staff business authorization.
- ADR-0013 requires one no-default staged workload root: `foundation` creates no executable Cloud Run workload, `migration` adds but does not execute the configured job, and `service` adds the staff service only after migration evidence. Terraform alone owns configuration. The deploy executor receives exact job execution/view authority only; direct-workflow `workflow_ref` separates publisher/deploy WIF trust; the provisioner has no GitHub WIF binding and no GitHub apply workflow is authorized.
- The human-visible `develop` service uses `INGRESS_TRAFFIC_ALL` with exactly `allUsers` → `roles/run.invoker`; application middleware protects every route except minimized `/health` and `/readiness` using fixed username `golden-rose-demo`, a canonical unpadded base64url password representing at least 32 random bytes, constant-time comparison, and strict UTC expiry no later than seven days after revision creation. Production rejects this configuration. This is temporary synthetic access, not production staff identity.
- Develop mutation commands additionally enforce bounded generated fictional Employer/EmployerContact name shapes below HTTP schema handling and before all persistence authority. The Basic gate alone never authorizes arbitrary or client-derived data admission.
- Terraform owns the one-instance service cap, immutable image, synthetic markers, runtime-only demo-secret reference, private Cloud SQL path, and exact custom quota role `goldenRoseProvisionerQuotaUser` with only `serviceusage.services.use` and one workload-provisioner member. Terraform manages secret metadata/references, never payloads. Static/live admission rejects broader IAM, extra invokers, user-managed keys, budget mutation, public database exposure, or weakened access/scale constraints.
- GitHub-based CI/CD and repository governance as code; exact provider/account configuration remains unapproved.

See `TECHNOLOGY_DECISIONS.md` for rationale and `docs/adr/` for durable decisions.

## Data boundaries
- Minimize personal, household, location, document, and free-text data.
- Keep exact worksite/household address internal by default; use least-precise location outside approved workflows.
- Store documents outside database rows with private, controlled access only after document-ingestion qualification.
- Keep secrets out of Git, logs, client builds, and ordinary operational records.
- Use wholly fictional synthetic data in development until a separately approved test-data procedure exists; de-identified, transformed, hashed, or otherwise client/live-derived values are not allowed by default.

## Environment and promotion model
```text
feat/*    → PR/CI → develop (isolated non-production; wholly fictional synthetic data under ADR-0009)
develop   → PR/release evidence → main (immutable production candidate)
main artifact → protected explicit production promotion
```

`develop` and production require isolated projects/accounts/resources, identity clients, secrets, databases, buckets, and budgets. Production is a deliberate promotion of the qualified immutable artifact, not an automatic side effect of a merge.

The first implementation slice is narrower than this eventual environment model. ADR-0002 permits one local/test-only staff route, synthetic configuration-supplied principal, security-internal transactional `CommandReceipt`, draft `Employer` insert, and atomic creation `AuditEvent`; it creates no deployment, public plane, real identity, or live-data path.

ADR-0004 controls the implemented second bounded local/test slice: one `employer:read` permission, exact current-Employer detail, and privacy-conscious POST search over accepted Employer fields. Search remains a bounded query over authoritative PostgreSQL rows—not a second store or durable projection—and ordinary reads append no domain audit event. Filter-required literal matching, deterministic keyset pagination, minimized responses, no-store caching, and authorization before lookup/result derivation define the boundary.

ADR-0005 accepts the first standalone staff browser application boundary under `apps/web/`. Before browser consumption it adds `Cache-Control: no-store` to fresh and replayed create successes without changing status, body, authority, idempotency, persistence, route, or schema. It then consumes the Employer create/search/detail contracts through relative staff API paths, keeps Employer/search/command state in memory rather than URLs or browser persistence, and requires English/Spanish parity plus accessibility and frontend quality/security evidence. PR #13 merged that bounded implementation to `develop`.

ADR-0006 controlled the closeout merged by PR #15. ADR-0007 controlled draft-Employer revision merged by PR #17 and remediated by PR #18. ADR-0008's implementation merged through PR #20 at `6eb05d5`. PR #22 merged ADR-0009 Slice B's local runtime/container implementation at `f3cac4d`; PR #24 merged the local validate-without-apply Terraform scaffold at `50451b3`; PR #29 merged the six static remediation tasks at `08fe305`; PR #30 merged accepted ADR-0012's consolidated pre-deployment implementation authority at `f9b7903`; PR #37 merged the ADR-0013 no-cloud remediation at `caf96a7`; PR #42 scoped tester verification to service stage at `b2d79b5`; PR #46 stage-gated deferred network/database resources at `58aed28`; and PR #48 aligned foundation verification at `5f265d8`. The completed source contracts preserve the High/open same-repository-CI residual risk and do not authorize cloud inspection, Terraform plan/apply, backend migration, provisioning, image push, secret injection, deployment, service start, live data, or production.

## Interim infrastructure billing and handoff
- **Accepted contractual constraint:** Beatrice is responsible for paying approved cloud-infrastructure charges until the final payment for the engagement has been rendered. Billing responsibility then transfers to the client through a documented handoff.
- The current starting account shape is reported as one Beatrice-owned GCP organization with two projects, including one project dedicated exclusively to cloud deployment/testing. Exact billing topology, project identifiers, domain/DNS, remote state, support, and transfer details remain controlled operational inputs; they must support least-privilege access, cost visibility, continuity, and an orderly transfer without exposing secrets or interrupting the staff workflow.
- The handoff record must identify the billing owner, account/project ownership, budget-alert recipients, support/incident contacts, recovery access, and effective transfer date. It does not itself authorize production provisioning, production-data use, or feature expansion.

## Deferred architecture decisions
Identity provider; billing/state/domain/support topology; named cloud/support roles and alert recipients; develop recovery targets and log-retention details; production topology; document/malware-scanning services; background workers; messaging/signature/payment/screening integrations; production RTO/RPO; WAF/CDN/network design; and exact dashboard/reporting technology.
