# GCP Develop Deployment Foundation Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task only after this planning packet is independently reviewed, accepted, merged to `develop`, and Beatrice separately authorizes the applicable implementation or provisioning slice.

**Goal:** Establish a safe, reviewable path from merged Golden Rose source to an isolated GCP `develop` environment that runs only fictional synthetic data and creates no production-readiness claim.

**Architecture:** Package the existing modular staff application as one same-origin Cloud Run deployable for the first non-production target, backed by Cloud SQL for PostgreSQL and a separately invoked migration job. Keep the Cloud Run service private to named GCP test operators while synthetic application authentication remains in use; Cloud Run IAM is an outer test-access boundary, not a substitute for future staff identity or server-enforced business authorization. Manage resources as reviewed Terraform, build immutable images into Artifact Registry, use Secret Manager and distinct runtime/migration/deployment identities, and use GitHub Workload Identity Federation rather than service-account keys.

**Tech Stack:** Python 3.12, FastAPI, React/TypeScript/Vite, PostgreSQL 16, Alembic, Docker/OCI, GCP Cloud Run, Cloud Run Jobs, Cloud SQL, Artifact Registry, Secret Manager, Cloud Logging/Monitoring, Terraform, GitHub Actions with Workload Identity Federation.

---

## Status and authority

- **Planning status:** Accepted and merged by PR #21 at `9e27f80`; later implementation remains slice-gated. This document authorizes no cloud resource, billing linkage, service identity, deployment, service start, or external exposure by itself.
- **Base:** PR #20 merged into protected `develop` at `6eb05d5af3bcceed3d05b1eb2e91676ce4e1bf10`.
- **Target:** One isolated, disposable/rebuildable GCP `develop` environment using fictional synthetic data only.
- **Acceptance owner:** Beatrice for technical planning and each separately approved implementation/provisioning action. Client production acceptance is not part of this plan.
- **Controlling decision:** Accepted `docs/adr/ADR-0009-gcp-develop-deployment-boundary.md`.
- **Prior rollout context:** `.hermes/plans/2026-08-03_gcp-rollout-management-plan.md` remains the broad staged rollout strategy. This plan narrows its Stage 0–3 non-production work into reviewable slices.

## Non-goals and hard stops

This plan does not authorize or claim:

- production projects, production promotion, live/client-derived data, de-identified client data, or legacy imports;
- unauthenticated public internet access while the application uses a synthetic principal;
- a public worker/employer plane, public job publication, uploads, documents, payments, signatures, messaging, screening, mapping/geocoding, or automated decisions;
- real staff identity, MFA, business-role administration, or production support readiness;
- production HA, production SLOs, production RTO/RPO, production retention policy, or production incident readiness;
- completion of Worksite, StaffingRequest, ShiftNeed, queue, calendar, map, or broader Phase 1 product scope;
- direct Terraform apply, billing linkage, API enablement, resource creation, image push, migration execution, deployment, or service start without a new explicit scoped approval.

## Decision summary

| Concern | Accepted develop decision | Boundary / rationale |
|---|---|---|
| Environment | Dedicated GCP non-production project | No shared production project or credentials; designed for teardown/rebuild and later ownership transfer. |
| Region | Use `us-east4` for the `develop` Cloud Run, Cloud SQL, and Artifact Registry baseline | Production and any secondary/backup location remain separate decisions. |
| Deployable | One same-origin staff-app Cloud Run service | Preserves the existing relative `/api/staff/v1/...` browser contract and avoids introducing a premature gateway, load balancer, or cross-origin token design. Revisit before public/staff-plane expansion. |
| Test access | Cloud Run IAM only; neither `allUsers` nor `allAuthenticatedUsers` may invoke while synthetic auth remains | Service-level `roles/run.invoker` is limited to the approved group or named managed principals. Named operators may use an authenticated local proxy or another separately approved private access method. Cloud IAM identifies the outer caller but does not become application business authorization. |
| Application auth | Synthetic principal remains develop-only for the first deployment | `develop` must be explicit in validated configuration and visibly labeled. Real identity remains a separate planned gate. |
| Database | Cloud SQL PostgreSQL 16, smallest qualified develop shape, no HA by default | PostgreSQL compatibility is already required. Fixed cost means sizing and budget review precede provisioning. |
| Database authority | Separate runtime and migration database roles | Runtime role must not own schema or bypass audit/receipt immutability through DDL/TRUNCATE/trigger management. Migration job owns bounded schema evolution. |
| Migrations | Explicit Cloud Run Job or equivalent one-shot job using the immutable application image | Never run migration concurrently in every web instance startup. Promotion waits for migration result and compatibility evidence. |
| Images | Artifact Registry; deploy by immutable digest | Tags may aid discovery but never constitute deployment authority. Backend/frontend SBOM evidence remains associated with the source/image. |
| Secrets | Secret Manager and runtime identity access | No `.env`, plaintext Terraform variables/state, GitHub secrets containing GCP keys, or secret values in logs/artifacts. |
| IaC | Terraform with remote-state design decided before apply | Project/billing bootstrap exceptions must be documented; routine resources remain reviewed and reproducible. |
| CI/CD | GitHub Actions + GCP Workload Identity Federation | No long-lived service-account keys. Separate build, provision, and deploy identities/workflows with environment approval gates. |
| Health | Cheap liveness, authoritative readiness, separate qualification workflow | Readiness checks database connectivity/schema compatibility; synthetic create/read/replay is qualification, not a health probe. |
| Visibility | Value-safe deployment evidence packet | Provide facilitator-visible status, architecture, image digest, migration/readiness result, synthetic walkthrough outcome, cost/budget posture, and open gates without exposing secrets or synthetic record values. |

## Develop environment acceptance boundary

The first environment is acceptable for **cloud deployment testing** only when all of the following are true:

1. The service is private to approved named test operators; both `allUsers` and `allAuthenticatedUsers` invocation are denied and effective IAM has been inspected for inherited access.
2. Only wholly fictional synthetic records are admitted, and the UI clearly identifies the environment as non-production/synthetic.
3. The deployed image is referenced by digest and traceable to a protected-branch commit and passing CI.
4. The migration job and runtime service use separate identities and database roles.
5. The runtime database role cannot perform DDL, truncate authority tables, alter triggers, or update/delete append-only command/audit authority.
6. Readiness proves required configuration, database reachability, and a declared compatible schema capability/range without executing a business mutation or making an old serving revision unready merely because an expand-compatible migration ran.
7. Qualification separately proves a bounded synthetic create → read/search → revision/replay → contact create/query/read path.
8. Application and platform logs/evidence omit or strictly minimize and access-restrict database URLs, secrets, tokens, names, UUID-bearing request paths, cursors, command IDs, raw request bodies, SQL values, and raw exception details; all configured sinks are inspected.
9. A budget and alert route exist before workload startup; observed cost is recorded as evidence, not an SLO.
10. The approved develop recovery path is exercised with real evidence: database backup/restore and environment teardown/rebuild where both are required by the accepted recovery decision. An unmet recovery exercise leaves the environment deployed but explicitly unqualified for cloud deployment testing.

## Slice structure and approval boundaries

### Slice A — Planning publication and independent review

**Objective:** Publish only ADR-0009, this exact plan, and aligned living documents.

**Files:**
- Create: `docs/adr/ADR-0009-gcp-develop-deployment-boundary.md`
- Create: `.hermes/plans/2026-08-13_145234-gcp-develop-deployment-foundation-plan.md`
- Modify: `docs/adr/README.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`
- Modify: `SECURITY.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `README.md`
- Modify: `NOTES.md`
- Modify: `AGENTS.md`
- Modify: `docs/review-handoffs/2026-08-12-employer-contact-authority-foundation-review-handoff.md`

**Steps:**
1. Confirm the planning branch is based exactly on merged `origin/develop` commit `6eb05d5` and has no inherited product delta.
2. Independently review architecture, cloud security/IAM, database/migration/recovery, cost/governance, CI/supply chain, and documentation consistency.
3. Remediate findings in planning artifacts only.
4. Run Markdown/diff hygiene and exact-range secret scanning after commit.
5. Open a planning-only PR to `develop`; require protected checks and record that merge grants no provisioning authority.

**Exit gate:** Accepted/merged planning packet and a separately approved coding slice. Do not begin Slice B from an unmerged planning branch.

### Slice B — Runtime and container contract, local verification only

**Objective:** Make the existing staff tracer packageable and observable without creating cloud resources or starting cloud services.

**Likely files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `deploy/container/README.md`
- Create: `scripts/container-entrypoint.sh` or a narrower reviewed equivalent
- Create: `src/golden_rose/api/health.py`
- Create: `src/golden_rose/static_app.py` or a narrowly named same-origin static-serving module
- Modify: `src/golden_rose/main.py`
- Modify: `src/golden_rose/config.py`
- Modify: `apps/web/vite.config.ts` only if production base/output behavior requires it
- Test: `tests/unit/test_config.py`
- Test: `tests/unit/test_main.py`
- Test: new focused health/static/deployment contract tests
- Modify: `.github/workflows/application-quality.yml` only after exact local parity is defined

**Exact TDD nodes to specify in the Slice B implementation plan:**
1. RED: configuration accepts explicit `develop` but rejects synthetic auth in `production` and rejects unlabeled/ambiguous cloud posture.
2. GREEN: minimal validated develop configuration and a non-production UI marker contract.
3. RED/GREEN: `/health` is cheap and database-independent.
4. RED/GREEN: `/readiness` performs only bounded authoritative database/schema checks and returns static value-safe failure bodies.
5. RED/GREEN: qualification remains a separate command and does not run through health probes.
6. RED/GREEN: built Vite assets are served same-origin without turning arbitrary filesystem paths into public content.
7. RED/GREEN: unknown frontend paths and `/api` paths preserve the intended routing/error boundary.
8. RED/GREEN: the executable entrypoint binds the application to `0.0.0.0:$PORT`, validates the deployment port posture and fails deterministically on invalid configuration, forwards signals, and returns the application process exit status.
9. RED/GREEN: `SIGTERM` initiates graceful FastAPI shutdown and database-engine disposal within the approved Cloud Run termination window; tests prove bounded termination rather than relying on shell behavior.
10. RED/GREEN: container runs as a fixed non-root user, has a read-only-compatible filesystem posture except explicitly approved writable temporary paths, receives configuration only at runtime, and contains no `.env`, source credential, test data, coverage, or local build evidence.
11. GREEN verification: locally build the image, inspect metadata/user/layers/entrypoint, run it only after separate local service-start approval with a non-default valid `PORT`, prove external-interface reachability and approved writable paths, probe liveness/readiness, send `SIGTERM`, and verify graceful deterministic exit.

**Verification:**
- Existing full application-quality workflow remains green.
- Image build is reproducible enough to identify the exact image digest.
- Container vulnerability scan policy is proposed and reviewed before becoming required.
- No cloud push/deploy occurs in this slice.

**Hard stop:** No Terraform, GCP API, Artifact Registry push, Cloud SQL connection, or public listener.

### Slice C — Terraform and policy scaffold, validate without apply

**Objective:** Create reviewable GCP develop IaC and policy tests without provisioning anything.

**Likely files:**
- Create: `infra/gcp/README.md`
- Create: `infra/gcp/versions.tf`
- Create: `infra/gcp/providers.tf`
- Create: `infra/gcp/variables.tf`
- Create: `infra/gcp/outputs.tf`
- Create: `infra/gcp/develop/` modules/configuration for APIs, Artifact Registry, service accounts/IAM, Secret Manager metadata, Cloud SQL, Cloud Run service/job, logging/monitoring, and budgets
- Create: `infra/gcp/tests/` policy/contract fixtures
- Create: `.github/workflows/infrastructure-quality.yml` or extend a reviewed stable gate
- Modify: `.gitignore` only if additional local Terraform artifacts need exclusion

**Required design constraints:**
- Region variable has no silent default until region approval is recorded.
- Project ID, billing account, organization/folder, domain, users, and secret values are never committed.
- Terraform state design is explicit; no apply occurs while state ownership/access/backup is unresolved.
- Runtime, migration, deploy, and human administration identities are distinct.
- No basic roles (`roles/owner`, `roles/editor`) are granted by routine modules.
- Runtime identity receives only Cloud SQL connection, required secret-version access, logging/metrics emission, and its own service needs.
- Migration identity is separately invocable and receives the minimum database migration capability; it is not the web runtime identity. Job execution is one task and only narrowly approved principals may invoke it.
- PostgreSQL uses a non-login schema-owner role; the migration login may assume it only for reviewed migrations; runtime receives explicit least-privilege grants. Bootstrap, ownership transfer, revocations, existing-object grants, default privileges for future tables/sequences/functions, trigger/function ownership, and `alembic_version` access are declared.
- Cloud Run grants neither `allUsers` nor `allAuthenticatedUsers` invoker; service-level `roles/run.invoker` is limited to the approved group or named principals and approved ingress settings are used.
- Cloud SQL has deletion protection/backups appropriate to the approved develop recovery decision; no public database exposure by default.
- Budget alerts are configured before workload start, with the limitation that budgets are alerts rather than hard caps.
- Artifact Registry, images, logs, secrets, database storage/backups, and Terraform state each have an explicit retention/cleanup owner.

**Validation:**
- `terraform fmt -check -recursive`
- `terraform init -backend=false`
- `terraform validate`
- pinned IaC lint/security tooling with reviewed suppressions only
- policy tests that fail on either `allUsers` or `allAuthenticatedUsers` invoker, broad IAM, service-account keys, unpinned image tags, public database exposure, missing budget, and secret-like variable defaults; qualification also checks effective IAM rather than declarations alone
- `git diff --check`

**Hard stop:** No `terraform apply`, API enablement, project creation, billing linkage, identity creation, or secret version creation.

### Slice D — Build provenance and WIF deployment workflow definitions

**Objective:** Define reviewable image-build and deployment workflows without authenticating to or changing GCP.

**Likely files:**
- Create: `.github/workflows/build-image.yml`
- Create: `.github/workflows/deploy-develop.yml`
- Create: `scripts/verify-image-provenance.py` or a minimal reviewed equivalent
- Modify: repository-governance policy if new stable checks/environments are accepted
- Modify: `docs/security/dependency-purpose-license-review.md` if container/build dependencies are introduced

**Required workflow boundaries:**
- Immutable-SHA-pinned GitHub Actions.
- Exact protected source/ref and environment checks.
- OIDC/WIF only; fail if a JSON service-account key path/value is configured.
- Build once, scan and attest, push once, deploy by digest.
- Separate build/push, migration, and service rollout steps.
- GitHub `develop` environment approval required before migration/deployment.
- No pull-request workflow receives deploy credentials or mutates cloud resources.
- Workflow concurrency reduces overlapping migrations/deployments but is defense in depth. The migration runner also holds one reviewed PostgreSQL advisory lock for the entire migration, fails closed if it cannot acquire the lock, and has a test proving a second independent invocation cannot migrate concurrently.
- Each migration declares its supported old/candidate image-to-schema compatibility range and proves expand compatibility before rollout; rollback is allowed only within a proven range, otherwise forward recovery is required.
- Evidence records commit, image digest, SBOM/provenance validation, migration job result, Cloud Run revision, readiness result, and rollback target without logging secrets or operational values.

**Hard stop:** Workflows remain non-runnable placeholders or validation-only until WIF/provider/project identifiers are separately approved and provisioned.

### Decision Gate 1 — Pre-provisioning evidence and explicit approval

Before any resource is created, produce and review:

- cited region comparison and accepted region;
- non-production monthly cost estimate and budget/alert thresholds;
- interim Beatrice billing topology plus transfer/continuity design;
- organization/folder/project and domain/DNS ownership plan;
- named human cloud administrators, emergency-access owners, and support/alert recipients;
- managed individual human identities, phishing-resistant MFA for privileged/recovery access, group-scoped grants, time-bounded reviewed break-glass, and periodic access-review evidence;
- named owners for secret custody/rotation/revocation, emergency access, IAM review, and eventual client handoff continuity;
- service-account and database-role matrix;
- PostgreSQL schema-owner/migration/runtime ownership, grant, default-privilege, bootstrap, and drift-verification design;
- Cloud SQL sizing, backup/PITR, restore cadence, develop RTO/RPO targets, and deletion/teardown posture;
- application and Cloud Run platform request-log retention/minimization/access/sink contract, including UUID-bearing request paths, plus alert routing;
- Terraform state location, access, backup, and handoff owner;
- access method for facilitator/tester visibility while synthetic auth remains;
- reviewed Terraform plan from non-secret inputs;
- documented maximum first-run cost exposure and teardown command.

**Required user action:** Beatrice gives a new explicit, scoped approval naming the project/billing/resource boundary. Planning approval is not sufficient.

### Slice E — Controlled GCP foundation provisioning

**Objective:** Provision only the reviewed non-production foundation.

**Sequence:**
1. Confirm active GCP account/project/billing context without printing tokens or secrets.
2. Create/attach only the approved project and billing relationship.
3. Establish budget/alerts and emergency ownership before workload resources.
4. Establish Terraform state and least-privilege human/deployment identities.
5. Apply the reviewed Terraform plan; stop on drift.
6. Verify APIs, Artifact Registry, service identities, Secret Manager metadata, Cloud SQL, Cloud Run service/job definitions, Logging/Monitoring, and WIF.
7. Inspect effective project and service IAM, including inherited policy; confirm neither `allUsers` nor `allAuthenticatedUsers` can invoke, only the approved group/named principals have service-level `roles/run.invoker`, and there is no public database path, service-account key, or production/live-data resource.
8. Record resource identifiers in value-safe deployment evidence; never record secret values.

**Hard stop:** Do not push/deploy the application or start Cloud SQL workload use until foundation verification and a separate first-deployment approval.

### Decision Gate 2 — First deployment approval

Require:

- foundation verification green;
- budget alerts confirmed to named recipients;
- secret values supplied out of band and access tested without disclosure;
- runtime/migration DB users and grants reviewed;
- database-level migration advisory-lock behavior and second-invocation fail-closed test reviewed;
- exact image digest and vulnerability/provenance disposition approved;
- migration compatibility range, old/candidate image proofs, and rollback-versus-forward-recovery plan approved;
- named deployment operator and rollback authority;
- private tester access procedure approved;
- synthetic fixture and cleanup procedure approved.

### Slice F — First private synthetic deployment

**Objective:** Deploy the immutable staff tracer privately and qualify the deployment boundary.

**Sequence:**
1. Push the already qualified image and capture its digest.
2. Configure secrets by reference only.
3. Run the one-task migration job under its narrowly restricted invoker; acquire the PostgreSQL advisory lock for the full migration, record revision/result, and stop on lock or migration failure.
4. Prove the old image remains compatible/readiness-healthy after expansion, then deploy the service by digest with neither `allUsers` nor `allAuthenticatedUsers` invoker.
5. Probe liveness and readiness through the approved authenticated access path.
6. Run the bounded synthetic qualification flow; use newly generated fictional values and remove them through the approved environment cleanup/restore approach rather than inventing production delete semantics.
7. Generate representative exact-detail traffic, then inspect application logs, Cloud Run platform request logs, access controls, retention, and every configured sink for secrets, request values, UUID-bearing paths/cursors, SQL/DSNs, and raw exceptions; application output alone is insufficient.
8. Verify effective runtime/migration IAM and database ownership/grants/default privileges from observed configuration, including newly created migration objects and absence of drift.
9. Verify budget/monitoring signals and record initial observed cost posture.
10. Exercise rollback or forward recovery and an approved backup/restore or teardown/rebuild path.
11. Stop or scale down resources according to the approved cost posture after evidence capture.

**Qualification outcome:** This may establish “GCP develop deployment operational with synthetic data.” It must not be described as production-ready, live-data-ready, identity-qualified, or staff-pilot accepted.

### Slice G — Shared human qualification and facilitator visibility

**Objective:** Use the private deployed target for the human checks previously deferred by ADR-0006 without weakening access controls.

**Evidence packet:**
- one-page scope/status/non-scope summary;
- architecture and trust-boundary diagram;
- commit and image digest;
- private-access method and named tester list (no credentials);
- liveness/readiness/migration result;
- English/Spanish functional walkthrough results;
- manual keyboard, focus, zoom/reflow, contrast, reduced-motion, and supported-browser results;
- synthetic workflow outcomes without record values/screenshots containing sensitive-looking fixtures;
- observed defects, owners, severity, and remediation status;
- budget/cost and recovery evidence;
- explicit remaining blockers for real identity, live data, production, and incomplete Phase 1 features.

**Hard stop:** Facilitator visibility does not authorize public exposure, live data, production promotion, or broader product scope.

## Verification matrix

| Layer | Required proof |
|---|---|
| Source | Protected `develop` commit; clean exact review range; independent review evidence |
| Backend/frontend | Existing quality gate plus deployment-specific tests/build |
| Container | Non-root, minimized context, no embedded secrets, pinned base digest, scan/provenance/SBOM disposition |
| Health | Cheap liveness; DB/schema readiness; separate synthetic qualification |
| Database | Migration job, schema revision, runtime/migration role separation, append-only authority under non-owner runtime role |
| IaC | fmt/init/validate/lint/security/policy tests; reviewed plan; no apply before approval |
| CI/CD | immutable actions, WIF, environment approval, concurrency, digest deployment, no PR deploy credentials |
| Access | neither `allUsers` nor `allAuthenticatedUsers`; effective IAM inspection; approved group/named operator access; synthetic auth clearly non-production |
| Data | fictional synthetic only; no client-derived values; bounded cleanup |
| Logs/evidence | value-safe, no secrets/PII-like values/DSNs/raw exceptions |
| Cost | estimate before provision; budget before startup; observed cost after qualification |
| Recovery | migration failure/rollback posture plus backup/restore or teardown/rebuild proof |
| Teardown | exact resources/state retained or removed intentionally; no orphaned billable resources |

## Risks and mitigations

- **Synthetic principal behind accidental public access:** block unauthenticated invocation in IaC/policy tests and verify live IAM before every qualification run.
- **Cloud Run IAM mistaken for application authorization:** state explicitly in UI/docs/evidence that it is only an outer non-production access perimeter; keep real staff auth as a separate gate.
- **Single combined deployable becomes permanent architecture by inertia:** document it as the first same-origin staff-plane deployment choice and require ADR revisit before public-plane or independent scaling needs.
- **Runtime database owner bypasses append-only controls:** create and qualify a non-owner runtime role; isolate migration authority.
- **Migration performed on web startup:** prohibit it; run a serialized explicit migration job.
- **Terraform state or output leaks secrets:** mark values sensitive, prohibit secret material in Terraform, review plans/artifacts, and restrict state access.
- **WIF overprivilege:** separate build/deploy/runtime/migration identities and use attribute conditions bound to the exact repository/branch/environment.
- **Cloud SQL fixed cost surprises:** accepted estimate, smallest qualified shape, budgets before startup, and teardown/scale-down procedure.
- **Deployment work displaces Phase 1 product work:** maintain deployment as a parallel bounded lane with explicit exits; do not treat deployed tracer visibility as workflow completeness.
- **Evidence overclaims readiness:** every report must distinguish source merged, image built, foundation provisioned, service deployed, synthetic workflow qualified, human review complete, and production/live-data gates.

## Remaining decisions before Slices D-G can be accepted

Slice B merged through PR #22, and Slice C's validate-without-apply scaffold merged through PR #24. PR #24's final-head findings require a separate remediation before later slices proceed.

1. Does read-only qualification clear the existing non-workload project as the durable bootstrap/state/WIF control plane, and what exact billing/folder/handoff topology supports eventual client transfer without sharing credentials?
2. Who receives budget, incident, deployment, database, and break-glass alerts during develop testing?
3. What monthly develop budget and maximum first-run exposure are acceptable?
4. What Cloud SQL develop size, storage, backup/PITR, deletion protection, restore cadence, and develop RTO/RPO are approved?
5. Which named users require private facilitator/test access, and is authenticated local proxy access acceptable for the first walkthrough?
6. What exact bucket, access, versioning, retention, recovery, emergency-access, state-partitioning, migration, and transfer contract implements the accepted lifecycle-independent control plane?
7. Which container vulnerability severity and exception process blocks deployment?
8. Which qualification artifacts may be retained, for how long, and who may access them?

## Completion criteria

This plan is complete only when:

- the planning packet is independently reviewed, accepted, and merged;
- each code/IaC/provision/deploy slice has its own explicit authorization and exact implementation plan;
- the first deployment remains private and synthetic-only;
- image, migration, readiness, IAM, budget, logging, recovery, and teardown evidence is real and reviewable;
- facilitator visibility is delivered without weakening access or overstating product/production readiness;
- living documents name the next remaining product and deployment gates honestly.
