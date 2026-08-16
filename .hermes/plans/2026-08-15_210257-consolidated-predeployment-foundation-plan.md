# Consolidated Pre-Deployment Foundation Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. Component reviewers are agent/separate-session quality evidence, not independent human authorization.

**Goal:** Complete all remaining source-controlled work required before a reviewed Terraform plan and private fictional-synthetic GCP `develop` deployment can be separately authorized.

**Architecture:** Preserve ADR-0009's private same-origin Cloud Run + private Cloud SQL target and lifecycle-independent control plane. Implement bootstrap/state/WIF, least-privilege IAM, migration/database authority, budgets/observability, immutable build/deploy workflows, recovery/teardown procedures, and gate evidence in one ordered pre-deployment PR. Keep planning, implementation, read-only cloud qualification, Terraform plan, foundation apply, first deployment, and qualification as separate owner-controlled gates.

**Tech Stack:** Terraform 1.15.8, Google provider 6.50.0, GCP Cloud Run v2/Jobs, Cloud SQL PostgreSQL 16, Artifact Registry, Secret Manager, Cloud Logging/Monitoring, Billing Budgets, GitHub Actions OIDC/WIF, Python 3.12, uv 0.12.5, pytest, semantic HCL/YAML/JSON policy validation, Gitleaks, CycloneDX.

---

## Status and authority

- **Planning base:** protected `origin/develop@08fe3056e1637d3cab4d1f82ad3081a8a324948e`, the PR #29 merge.
- **Planning branch:** `docs/consolidated-predeployment-plan`.
- **Decision owner and sole maintainer:** Beatrice Alexander.
- **Controlling proposed decision:** `docs/adr/ADR-0012-solo-maintainer-consolidated-predeployment-boundary.md`.
- **Implementation status:** not authorized until this packet is reviewed, explicitly accepted, and merged.
- **Implementation shape after acceptance:** one larger source-controlled pre-deployment PR with ordered internal nodes and bounded commits.
- **Review truth:** agent and separate-session reviews are adversarial quality evidence, not independent human approval.
- **Current cloud truth:** no cloud authentication/inspection, backend migration, Terraform plan/apply, API enablement, provisioning, image push, secret injection, Cloud SQL use, service start, deployment, real identity, live/client data, or production action is authorized by this planning packet.

## Why consolidation is appropriate

The remaining work is one coupled authority chain:

```text
bootstrap/state → WIF trust → provisioner/image/deploy identities
→ private workload IAM → migration/database roles
→ immutable build/push/migrate/deploy workflows
→ budgets/logging/monitoring/recovery evidence
```

Splitting this chain across repeated planning PRs creates handoff overhead and partial contracts. Consolidation does not collapse operational gates. It puts all source-controlled pre-deployment definitions in one reviewable implementation surface while requiring separate explicit approval for read-only cloud inspection, Terraform plan, apply, and deployment.

## Permanent solo-maintainer protocol

The implementation must not request a second human reviewer, CODEOWNER, owner-controlled alternate account, or fictional independent approval. It must:

1. Keep the same-repository-CI finding High/open and explicitly accepted as residual risk.
2. Use required checks, local qualification, and agent/separate-session reviews as quality evidence only.
3. Require Beatrice's explicit disposition of every substantiated Blocker/High finding.
4. Preserve exact-head, exact-range, immutable-pin, locked-dependency, static-policy, secret-scan, and value-safe evidence.
5. Prevent one gate's success from authorizing the next gate implicitly.

## Non-goals and hard stops

This plan does not authorize:

- production, public access, real staff identity, live/client-derived data, or de-identified client data;
- Terraform plan/apply, backend migration, state import, cloud mutation, API enablement, or provisioning during the source implementation nodes;
- project creation, billing changes, domain/DNS changes, service-account key creation, or broad IAM;
- image push, secret-payload injection, migration execution, Cloud SQL workload use, or service start before their named gate;
- uploads, documents, mapping/geocoding, messaging, payments, signatures, screening, public workflows, or automated decisions;
- committing project IDs, billing IDs, domains, emails, principals, backend values, credentials, state, plans, passwords, tokens, or secret payloads.

## Gate model

### Gate 0 — Planning acceptance

Required:

- ADR-0012 and this plan reviewed for architecture, Terraform/IAM, CI/supply chain, database/migration, cost/recovery, and documentation consistency.
- Beatrice explicitly accepts the packet.
- Documentation-only PR passes protected checks and merges to `develop`.

Authority granted: create one implementation branch from the resulting exact merged tip and execute Tasks 1–16 below without cloud authentication or mutation.

### Gate 1 — Pre-deployment implementation PR

Required:

- Tasks 1–16 complete under RED → GREEN where behavior/policy changes.
- Exact component review evidence and owner finding dispositions.
- Full local no-cloud qualification, exact-range Gitleaks, and protected CI.
- No environment-specific or secret material in the committed range.

Authority granted by merge: request separate read-only GCP qualification approval. No cloud access is automatic.

### Gate 2 — Read-only GCP qualification

Requires a new explicit approval naming the allowed organization/projects and read-only commands. Inspect only:

- organization/folder/project relationship and lifecycle;
- candidate durable control-plane project and disposable workload project;
- billing attachment and budget-notification capability without changing either;
- inherited/effective IAM and current administrators;
- enabled services, quotas, region/service availability, existing state/storage conflicts;
- candidate non-overlapping RFC1918 subnet;
- domain/principal claims needed for exact WIF conditions;
- current resources that could collide with planned names.

Output: a redacted operator-held qualification record plus value-safe repository evidence. Any mutation or secret display is a stop.

### Gate 3 — Backend/bootstrap migration and Terraform plan

Requires a new explicit approval naming:

- control-plane and workload project boundaries;
- billing scope and maximum first-run exposure;
- state bucket/backend key, location, versioning, retention, IAM owners, recovery, emergency access, and handoff owner;
- exact non-secret inputs and approved operator-held backend configuration;
- plan command and where the sensitive plan artifact may exist.

Run bootstrap/backend work only in the approved order, then produce a saved plan whose detailed output is not committed or broadly logged. Review resource count, replacements/destruction, IAM, APIs, budgets, networking, database, secrets metadata, logs, and costs. Any unexpected mutation/destruction or broad authority blocks Gate 4.

### Gate 4 — Foundation apply

Requires explicit approval of the exact plan artifact and target. Apply only the reviewed non-production foundation. Verify effective IAM, no public invoker/database path, no service-account keys, budget routing, remote-state controls, API set, labels, deletion protection, and teardown inventory. Do not push the app image, inject secrets, run migrations, or start the workload.

### Gate 5 — First private synthetic deployment

Requires exact digest/provenance/SBOM/vulnerability disposition, secret custody, database-role evidence, migration compatibility/lock evidence, named private testers, rollback/forward-recovery authority, and synthetic cleanup procedure. Separately approve image push, secret version creation, migration, and service rollout.

### Gate 6 — Qualification and shared target acceptance

Verify private access, liveness/readiness, synthetic workflow, effective IAM/database grants, platform/application logs, alert delivery, observed cost, backup/restore or teardown/rebuild, rollback/forward recovery, browser/accessibility, and English/Spanish walkthroughs. This may establish only “private GCP develop target qualified with fictional synthetic data.”

## Planned implementation file map

Likely new or changed paths:

- `infra/gcp/bootstrap/versions.tf`
- `infra/gcp/bootstrap/providers.tf`
- `infra/gcp/bootstrap/variables.tf`
- `infra/gcp/bootstrap/state.tf`
- `infra/gcp/bootstrap/wif.tf`
- `infra/gcp/bootstrap/iam.tf`
- `infra/gcp/bootstrap/outputs.tf`
- `infra/gcp/backend.tf`
- `infra/gcp/develop/identities.tf`
- `infra/gcp/develop/iam.tf`
- `infra/gcp/develop/cloud_run.tf`
- `infra/gcp/develop/migration_job.tf`
- `infra/gcp/develop/cloud_sql.tf`
- `infra/gcp/develop/secrets.tf`
- `infra/gcp/develop/budgets.tf`
- `infra/gcp/develop/observability.tf`
- `infra/gcp/develop/variables.tf`
- `infra/gcp/develop/outputs.tf`
- `infra/gcp/variables.tf`
- `infra/gcp/outputs.tf`
- `.github/workflows/build-image.yml`
- `.github/workflows/deploy-develop.yml`
- `scripts/validate_terraform_static.py`
- `scripts/verify_image_provenance.py`
- `scripts/verify_gcp_foundation.py`
- `scripts/verify_database_authority.py`
- `scripts/qualify_develop_deployment.py`
- `scripts/terraform_gate.sh` or a narrower shell-safe gate wrapper if tests prove it necessary
- `deploy/gcp/README.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/first-deployment-runbook.md`
- `deploy/gcp/rollback-forward-recovery-runbook.md`
- `deploy/gcp/teardown-rebuild-runbook.md`
- `deploy/gcp/evidence-template.md`
- `tests/unit/test_terraform_hygiene.py`
- focused unit tests for each new verification script
- `.github/workflows/application-quality.yml`
- `.github/workflows/infrastructure-quality.yml`
- `pyproject.toml` and `uv.lock` only if a directly used locked validator dependency is required
- living architecture/security/status documents listed in Task 16

Exact paths may be narrowed after implementation-base inspection. No new dependency or file is added merely because it appears in this inventory.

## Task sequence

### Task 1: Rebaseline and freeze the implementation authority map

**Objective:** Start from the exact planning merge and make the large PR's scope machine-checkable.

**Files:**
- Create: `infra/policy/predeployment-authority-manifest.json`
- Modify: `scripts/validate_terraform_static.py`
- Test: `tests/unit/test_terraform_hygiene.py`

**Steps:**

1. Verify clean checkout, exact merged base, branch prefix, one worktree, and no inherited delta.
2. Add a duplicate-rejecting manifest that lists every allowed Terraform resource type/cardinality, workflow/job/step execution shape, script entrypoint, and protected deployment path for this plan.
3. Write RED fixtures proving an unlisted resource, workflow, cloud-auth step, broad IAM binding, or execution-bearing field fails closed.
4. Implement the minimum semantic-manifest extension.
5. Run focused tests, full Terraform hygiene, locked static validation, and diff hygiene.
6. Commit only the manifest/scanner/tests node.

**Expected boundary:** no Terraform command beyond existing fmt/validate/graph; no cloud authentication.

### Task 2: Model the durable bootstrap/state control plane

**Objective:** Define lifecycle-independent state infrastructure and an explicit one-time bootstrap ceremony without embedding environment identifiers.

**Files:**
- Create: `infra/gcp/bootstrap/*.tf`
- Create: `infra/gcp/backend.tf`
- Create: `deploy/gcp/bootstrap-state-runbook.md`
- Modify: `infra/gcp/README.md`
- Test: `tests/unit/test_terraform_hygiene.py`

**Required contracts:**

- separate bootstrap root from disposable workload root;
- operator-supplied project, location, bucket, and principal values with no committed defaults;
- versioning, uniform access, public-access prevention, retention/recovery posture, encryption decision, and lifecycle protection;
- no secret payloads in source/state by design;
- partial backend configuration with operator-held values;
- explicit local-bootstrap → remote-state migration → WIF handoff → bootstrap-authority retirement sequence;
- state access, emergency recovery, client handoff, and teardown exclusions.

**TDD:** add negative tests first for backend values in source, public bucket access, missing versioning/recovery controls, workload references that can destroy state, and unbounded bootstrap authority.

### Task 3: Define exact GitHub OIDC/WIF trust

**Objective:** Permit keyless, exact-repository/ref/environment impersonation after provisioning without granting PR workflows cloud authority.

**Files:**
- Create/Modify: `infra/gcp/bootstrap/wif.tf`
- Modify: `infra/gcp/bootstrap/iam.tf`
- Test: `tests/unit/test_terraform_hygiene.py`

**Required contracts:**

- exact GitHub repository owner/name claim;
- exact protected `develop` ref and named deployment environment claims;
- no pull-request event subject may impersonate deploy authority;
- no wildcard owner/repository/ref/environment conditions;
- no service-account keys;
- separate provisioner, image-publisher, and deployer identities;
- minimum token-creation/impersonation bindings.

Write adversarial RED fixtures for forks, tags, arbitrary refs, missing environments, wildcard claims, and principal-set broadening.

### Task 4: Complete workload service identities and IAM

**Objective:** Give runtime, migration, image publishing, deployment, and private invocation only their exact service-level permissions.

**Files:**
- Modify: `infra/gcp/develop/identities.tf`
- Create: `infra/gcp/develop/iam.tf`
- Modify: `infra/gcp/develop/secrets.tf`
- Test: `tests/unit/test_terraform_hygiene.py`

**Required contracts:**

- no owner/editor/basic roles;
- no service-account keys;
- runtime gets only Cloud SQL connection, exact secret-version access, and required logging/metrics emission;
- migration identity is separate and narrowly invocable;
- image publisher writes only to the managed repository;
- deployer updates only the reviewed Cloud Run service/job and may impersonate only required identities;
- service-level invoker grants only approved operator/group inputs;
- reject `allUsers`, `allAuthenticatedUsers`, project-wide secret access, and inherited business-data authority.

Principal identifiers remain required operator inputs with no committed values.

### Task 5: Add the serialized Cloud Run migration job

**Objective:** Define one-task migration execution using the exact application digest and separate identity.

**Files:**
- Create: `infra/gcp/develop/migration_job.tf`
- Modify: `infra/gcp/develop/cloud_run.tf`
- Modify: `infra/gcp/develop/variables.tf`
- Modify: application migration entrypoint only if existing behavior cannot enforce the accepted lock contract
- Test: Terraform hygiene plus focused application/migration tests

**Required contracts:**

- one task, bounded retry/timeout, separate migration service account;
- exact managed application digest shared with service deployment;
- Direct VPC/private SQL path;
- secret references only, no payloads;
- no automatic web-startup migration;
- database-level advisory lock held for the entire migration and fail-closed contention behavior;
- migration result is known before service rollout.

### Task 6: Implement PostgreSQL authority lifecycle and drift verification

**Objective:** Prove non-login schema ownership, bounded migration assumption, and non-owner runtime privileges.

**Files:**
- Create: migration(s) under `migrations/versions/`
- Create: `scripts/verify_database_authority.py`
- Add focused migration/integration tests
- Modify: deployment runbooks

**Required contracts:**

- non-login schema-owner owns schema, tables, sequences, functions, triggers, and Alembic objects;
- migration login may assume only the schema-owner role for reviewed migrations;
- runtime login has explicit required DML/sequence/function privileges only;
- runtime cannot DDL, `TRUNCATE`, alter triggers, manage roles, assume owner, or update/delete append-only authority;
- existing and newly migrated objects receive correct grants/default privileges;
- verification fails closed on drift.

No real password or principal enters source, test output, or migration text.

### Task 7: Complete database resources and recovery inputs

**Objective:** Model the database/schema metadata needed for deployment without inventing unresolved recovery policy.

**Files:**
- Modify: `infra/gcp/develop/cloud_sql.tf`
- Modify: module/root variables and outputs
- Test: `tests/unit/test_terraform_hygiene.py`

**Required contracts:**

- private IP only, PostgreSQL 16, approved develop tier/storage, deletion protection;
- database metadata and non-secret user/role identifiers only where safe;
- no passwords in Terraform;
- backup/PITR/retention/restore inputs remain explicit and cannot claim approved values until Gate 2 evidence supplies them;
- no HA/production-RTO claim;
- output minimization and sensitivity marking.

If provider behavior would place credentials in state, keep that creation out of Terraform and document the approved out-of-band procedure.

### Task 8: Add budgets, alert routing, logging, and monitoring

**Objective:** Make cost and value-safe runtime evidence prerequisites to workload startup.

**Files:**
- Create: `infra/gcp/develop/budgets.tf`
- Create: `infra/gcp/develop/observability.tf`
- Modify: variables/outputs
- Test: Terraform hygiene

**Required contracts:**

- accepted $50/$75/$100 thresholds with operator-supplied billing scope and recipients;
- alerts are explicitly not hard spending caps;
- liveness/readiness/error monitoring without business-record mutation;
- bounded log retention and access;
- no broad export sink or secret/request-body/SQL-value logging;
- Cloud Run UUID-bearing request-path minimization/access decision represented and later verified live;
- value-safe outputs only.

Write RED fixtures for missing routing, broad sinks, extended/unbounded retention, payload logging, and absent startup budget dependency.

### Task 9: Define immutable build, SBOM, scan, and provenance workflow

**Objective:** Build once and produce an approved digest without granting PR workflows push/deploy authority.

**Files:**
- Create: `.github/workflows/build-image.yml`
- Create: `scripts/verify_image_provenance.py`
- Add focused script/workflow tests
- Modify: semantic workflow manifest/policy

**Required contracts:**

- immutable action pins and reviewed tool versions/checksums;
- protected-source commit only for publication;
- PR path performs validation/build/scan only and receives no cloud credentials;
- publish path uses WIF and named environment after merge;
- Docker base digest, non-root/runtime contract, backend/frontend SBOM validation, vulnerability disposition, and provenance/attestation;
- push once, capture digest, never deploy by tag;
- logs omit tokens, identifiers outside approved value-safe fields, and application data.

### Task 10: Define migrate/deploy workflow with explicit gates

**Objective:** Serialize migration and deploy the reviewed digest only after owner-controlled environment approval.

**Files:**
- Create: `.github/workflows/deploy-develop.yml`
- Modify: workflow manifest/policy/tests

**Required contracts:**

- no pull-request trigger or PR cloud credentials;
- exact protected `develop` source and named environment;
- WIF only;
- explicit input accepts managed digest, never arbitrary registry reference;
- migration job execution precedes service rollout;
- database advisory lock plus workflow concurrency;
- old/candidate schema compatibility evidence;
- rollback only in a proven compatibility window, otherwise forward recovery;
- readiness and qualification are distinct;
- value-safe artifact/result evidence and deterministic failure behavior.

Adversarial tests must cover skipped migration, changed order, arbitrary digest host, mutable tag, broad OIDC claims, `continue-on-error`, environment removal, and concurrency removal.

### Task 11: Add foundation and effective-authority verification tools

**Objective:** Verify live foundation posture without trusting Terraform declarations alone.

**Files:**
- Create: `scripts/verify_gcp_foundation.py`
- Add unit tests with synthetic command/API fixtures
- Create: `deploy/gcp/evidence-template.md`

**Required checks:**

- expected project/environment labels and resource inventory;
- only approved APIs;
- no public Cloud Run invoker and approved named service-level invokers only;
- no public Cloud SQL path;
- no service-account keys;
- exact service-account role bindings and no basic roles;
- state versioning/access/recovery posture;
- budget/alert route existence;
- log sinks/retention/access posture;
- value-safe redaction and duplicate/malformed input failure.

The tool must default to read-only and require a separate explicit mode/approval for any future mutation; this plan adds no mutation mode.

### Task 12: Add private synthetic deployment qualification tooling

**Objective:** Separate health from bounded synthetic workflow qualification and record only minimized evidence.

**Files:**
- Create: `scripts/qualify_develop_deployment.py`
- Add focused tests
- Modify: deployment evidence template

**Required contracts:**

- approved authenticated private access only;
- `/health` and `/readiness` probes remain non-mutating;
- qualification creates newly generated fictional values only;
- bounded Employer create/read/search/revision/replay and EmployerContact create/query/read;
- no submitted names, UUIDs, command IDs, cursors, raw bodies, DSNs, tokens, or exceptions in output;
- explicit cleanup/rebuild disposition without inventing product delete semantics;
- deterministic nonzero exit on any failed boundary.

### Task 13: Write secret injection and private tester procedures

**Objective:** Define human/operator ceremonies that Terraform and CI cannot safely infer.

**Files:**
- Create/Modify: `deploy/gcp/first-deployment-runbook.md`
- Create: `deploy/gcp/private-tester-access.md`
- Modify: `infra/gcp/README.md`

**Required contracts:**

- Secret Manager payloads injected out of band; never in Terraform/Git/chat/artifacts/logs;
- named custodian, rotation, revocation, and recovery ownership recorded outside public evidence where necessary;
- database passwords generated and transmitted without display;
- private Cloud Run access method for named testers while synthetic auth remains;
- no `allUsers`/`allAuthenticatedUsers` convenience exception;
- exact stop/cleanup procedure for accidental exposure.

### Task 14: Write rollback, recovery, and teardown/rebuild runbooks

**Objective:** Make failure handling executable before first workload start.

**Files:**
- Create: `deploy/gcp/rollback-forward-recovery-runbook.md`
- Create: `deploy/gcp/teardown-rebuild-runbook.md`
- Modify: bootstrap/state runbook

**Required contracts:**

- schema/image compatibility matrix and rollback-versus-forward-recovery decision;
- migration lock/failure handling;
- backup/restore or rebuild evidence requirements without claiming untested RTO/RPO;
- control-plane/state survival across workload teardown;
- deletion protection and explicit break-glass steps;
- inventory, cost, secret, evidence, and orphan-resource checks;
- no automatic scheduled destroy.

### Task 15: Exercise clean-room local pre-deployment qualification

**Objective:** Prove the large PR is reproducible without developer-local caches or cloud access.

**Required commands/evidence:**

- `env -u PYTHONPATH uv lock --check`
- locked sync and Python quality/security/SBOM gates
- frontend lock validator, tests, coverage, audit, SBOM, and build
- Terraform fmt check
- clean-copy `terraform init -backend=false -input=false`, validate, providers, and graph
- semantic static validation and full Terraform hygiene
- migration upgrade/downgrade/upgrade plus database-authority tests against disposable local PostgreSQL only after separate local service approval
- container build/inspection/scan only after separate local image-build/service approval if required by the existing runtime contract
- exact-range Gitleaks and `git diff --check`

No cloud auth, plan, apply, backend migration, push, or service deployment occurs in Task 15.

### Task 16: Align living docs and prepare the solo-maintainer review handoff

**Objective:** Make the exact implementation surface, residual risks, evidence, and next operational gate unambiguous.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md` by appending at the bottom before its maintenance footer
- Modify: `SECURITY.md`
- Modify: `TECHNICAL_REQUIREMENTS.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`
- Modify: `GIT_WORKFLOW.md`
- Modify: `AGENTS.md`
- Modify: `infra/gcp/README.md`
- Create: `docs/review-handoffs/<date>-consolidated-predeployment-review-handoff.md`

The handoff must state:

- exact base/head and complete changed-path manifest;
- component review assignments and findings;
- all local/CI/secret-scan evidence;
- High/open same-repository-CI residual risk;
- agent review is not independent human authorization;
- no cloud operation occurred;
- next authority is Gate 2 read-only qualification only after merge and explicit approval.

## Component review strategy for the large PR

Use parallel or sequential agent/separate-session reviews for:

1. Terraform module graph, state/bootstrap lifecycle, provider behavior, and API dependencies.
2. IAM/WIF claim exactness, privilege escalation, and public-access prevention.
3. PostgreSQL migration lock, ownership, grants/default privileges, and drift tests.
4. GitHub workflow supply chain, OIDC authority, immutable artifacts, and gate ordering.
5. Cost, logging, monitoring, backup/recovery, teardown, and evidence minimization.
6. Documentation consistency, residual-risk honesty, and scope containment.

Every review report must identify itself as agent quality evidence. Beatrice dispositions all Blocker/High findings. No task requires an unavailable second human.

## Implementation-PR completion criteria

The consolidated implementation PR is ready to merge only when:

- all Tasks 1–16 are complete or explicitly removed through an accepted plan amendment;
- no environment-specific identifier or secret appears in the committed range;
- Terraform and workflow authority manifests match the complete intended surface;
- focused RED/GREEN and full local gates pass;
- agent component reviews report no undispositioned Blocker/High finding;
- exact-range Gitleaks and diff hygiene pass;
- protected required checks pass on the exact head;
- living docs state the High/open solo-maintainer residual risk and no-cloud truth;
- Beatrice explicitly approves merge under the solo-maintainer posture.

Merge authorizes only a request for Gate 2 read-only GCP qualification. It does not authorize backend migration, plan, apply, image push, secret injection, migration, deployment, public access, real identity, live/client data, or production.

## Risks and tradeoffs

- **Large PR review load:** mitigate with ordered commits, a machine-readable authority manifest, component-focused review, and no drive-by refactors.
- **Bootstrap/state durability:** keep it in a separate root/project boundary and test that workload teardown cannot target it.
- **WIF privilege escalation:** exact repository/ref/environment claims and separate service accounts; no wildcard principals or PR authority.
- **Credential/state leakage:** no secret payloads in Terraform; sensitive plan/state handling outside Git and ordinary logs.
- **Migration/runtime authority drift:** database catalog verification after every migration and before qualification.
- **Cost surprise:** budget routes and maximum exposure accepted before apply; Cloud SQL remains the fixed cost driver.
- **False readiness:** distinguish source merged, read-only qualification, plan reviewed, foundation applied, image published, deployment operational, qualification complete, and production/live-data gates.
- **Solo-maintainer concentration:** keep the risk explicit; use defense in depth and owner dispositions without pretending agent or CI evidence is independent approval.

## Planning-packet completion criteria

This planning packet is complete when:

- ADR-0012 and this plan are internally consistent;
- living docs record PR #29's merge and the new proposed lane;
- ADR-0011 is historical for the completed six-task remediation and is not left as a permanent unavailable-reviewer deadlock;
- all pre-deployment source-controlled tasks are represented once in this plan;
- plan, apply, deployment, and qualification remain separate explicit gates;
- no implementation or cloud action occurs on the planning branch;
- Beatrice reviews and explicitly accepts or amends the packet before publication/merge.
