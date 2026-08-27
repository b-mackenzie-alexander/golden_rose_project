# Private Develop Activation and Human Feedback Master Plan

> **For Hermes:** Execute this plan through separate coding, operator, review, and PR lanes. Use small RED → GREEN nodes inside each implementation PR, but do not return to planning between predeclared PRs unless a material replanning trigger in this packet fires.

- **Status:** Accepted by Beatrice on 2026-08-27 after review-clean final rereview; unmerged and not implementation or operational authority until protected publication
- **Date:** 2026-08-27
- **Owner:** Beatrice Alexander
- **Exact planning base:** `origin/develop@5f265d8d1c1044915638d1399d8ba62c159b70c9` (PR #48 merge)
- **Controls:** ADR-0009, ADR-0012, ADR-0013, ADR-0014
- **Prior detailed ceremony:** `.hermes/plans/2026-08-26_210433-gate3-source-live-adoption-ceremony-plan.md`

**Goal:** Move Golden Rose from its current partial non-executable foundation to a private fictional-synthetic shared `develop` environment where approved named humans can exercise the current Employer/EmployerContact product, record structured feedback, and produce an honest qualified/not-qualified disposition.

**Architecture:** Preserve the two Terraform state roots and ADR-0013's `foundation → migration → service` authority model. Run source-readiness work and private state-adoption preparation as parallel tracks after this plan is accepted; join them before the exact foundation plan. Promote one immutable `linux/amd64` image through signed provenance/SBOM evidence, a separately approved migration transition, a separately approved service transition, automated qualification, then bounded human browser/accessibility/language/feedback review.

**Tech stack:** Terraform `>=1.9,<2.0`; pinned Google provider; GCS remote state; GCP Cloud Run, private Cloud SQL, Artifact Registry, Secret Manager metadata/IAM, Logging/Monitoring/Budgets; GitHub Actions WIF; Cosign v3/Sigstore; Docker Buildx; Python 3.12/uv/FastAPI/SQLAlchemy/Alembic/pytest; React/TypeScript/Vite/Vitest/axe.

---

## 1. Outcome and definition of done

This tranche is complete only when all of the following are true:

1. The accepted private inventory and both Terraform roots have independently reviewed, separate state custody with no mixed addresses, backend identity, state object/prefix, lock scope, or lineage.
2. An exact `foundation` saved plan was reviewed, explicitly approved, applied without executable workload or deferred network/database resources, and re-verified.
3. The reviewed image was published once by immutable digest and its direct signature, SLSA provenance, image SBOM, and application-SBOM checksum attestations were verified against the exact workflow identity.
4. Secret payload and database login-role preparation occurred only through approved out-of-band custody; database authority was verified without exposing connection material.
5. Exact `migration` and `service` saved plans were separately reviewed and approved; migration executed once under the advisory lock; service activation used the same reviewed digest and successful migration evidence.
6. Named tester access is exact, IAM-private, non-public, time-bounded, and proven to deny unauthenticated/unapproved access.
7. Automated qualification passes the current Employer create/read/search/revision/replay and EmployerContact create/query/read flows with newly generated fictional values, or writes a minimized failure artifact and stops.
8. A real human browser walkthrough is completed on the shared target for keyboard, focus, responsive/reflow, reduced-motion, cache/reload/BFCache, error/recovery, and English/Spanish functional parity.
9. Manual accessibility and fluent-language evidence are classified honestly. Missing a qualified fluent-language reviewer blocks a full bilingual/client-acceptance claim but does not erase separately labeled technical-feedback evidence.
10. Structured human feedback and every Blocker/High or pilot-blocking defect have an owner/disposition; the final status is exactly one of the statuses in section 11.
11. Value-safe repo docs and richer private/Obsidian records are reconciled; raw identifiers, endpoints, principals, plans, state, tokens, passwords, receipts, and outputs remain outside tracked source.
12. All temporary tester access and local secret/token material are removed or explicitly retained under an approved review date, and cleanup/readback evidence exists.

Merged source alone is not completion.

---

## 2. Current truthful baseline

### Implemented and merged

- Local/synthetic Employer create, detail/search, revision/replay, and browser workspace.
- Backend EmployerContact create, bounded parent query, and exact read.
- Container/runtime, health/readiness, migration entrypoint, and same-origin static serving.
- Terraform bootstrap and workload roots, stage-aware source contracts, least-privilege identities/IAM, budgets/observability, secret metadata/IAM, private-network/Cloud SQL declarations, migration job, service, tester IAM, and monitoring resources.
- Build/deploy workflows plus verifier scripts for foundation, image authority, stage receipts, tester authority, database authority, and bounded deployment qualification.
- PR #48's stage-correct foundation verifier: `foundation` is workload-free and Cloud-SQL-free; later stages retain fail-closed Cloud SQL checks.
- Initial Gate 2 evidence and partial non-executable foundation work recorded privately.

### Not yet complete

- Private source/live adoption inventory for this ceremony.
- Proven bootstrap local-state provenance/import representation and adopted bootstrap/workload remote state.
- Any saved Terraform plan or Terraform apply under this tranche.
- Verified real registry/Cosign/Buildx interoperability for the exact signed image-SBOM/provenance contract.
- Image publication, secret payload injection, database login roles, migration/service activation, tester access, automated deployment qualification, or human qualification.
- Real identity, live/client data, public access, or production.

### Open accepted risks

- Same-repository CI remains High/open accepted residual risk; required checks and agent review are quality evidence, not independent authorization.
- Provider/import/state behavior and OCI/Sigstore interoperability require exact-version evidence; uncertainty is a stop, not permission broadening.
- Recovery objectives and fully tested backup/restore remain incomplete; fictional-synthetic teardown/rebuild may be the only qualified recovery path.
- Synthetic application authentication is suitable only for this bounded private technical target and is not staff-pilot identity.

---

## 3. Master-plan authority and supersession

After protected merge into `develop`, this independently reviewed and explicitly accepted packet:

- authorizes the source-only implementation PRs in section 5;
- predefines the operational requests in sections 6-10;
- permits those separately approved gates to execute without publishing a new planning document for every gate;
- once accepted and merged, supersedes Task 6 and the prior Gate 3 packet's final one-plan-per-action sentence only for the predeclared foundation, publication, migration, service, qualification, and recovery gates in this master plan; no new standalone planning document is required between them;
- retains all detailed inventory, provenance, backend fingerprint, state readback, mismatch, and custody rules from the prior Gate 3 plan;
- does not itself approve any cloud command, private inventory, state/backend/import operation, Terraform plan/apply, registry/Sigstore spike, publication, secret/database action, migration, service, tester access, qualification, live/client data, or production.

Every operational gate still needs an exact approval bundle and readback. Passing one never grants the next.

All Terraform plan/apply operations in this tranche are operator-run from the exact approved checkout using operator-held backend configuration and keyless, short-lived impersonation of the exact provisioner authority. No service-account key or GitHub Terraform-apply workflow is authorized. If the approved local impersonation path cannot execute the reviewed plan without broader authority, stop and replan rather than adding an ambient credential or silently creating a workflow.

---

## 4. Parallel tracks and join points

After this plan merges, source implementation and private operator preparation may proceed in bounded parallel where their inputs do not conflict. No inventory collection, adoption, or saved plan may use a source revision that predates a required source-readiness PR.

### Track A — source and evidence readiness

- Implementation PR 0: bootstrap remote-state adoption readiness.
- Implementation PR A: artifact/transition authority interoperability closure.
- Implementation PR B: qualification, human review, and feedback evidence closure.

### Track B — private adoption readiness

- Prepare the read-only approval/custody bundle while source PRs are reviewed.
- Collect the private source/live inventory only after PR 0 and PR A merge and the approved source revision is exact.
- Perform the bootstrap provenance/import decision only against that same source revision.
- Bootstrap-root adoption is blocked until PR 0 is merged and the bootstrap partial backend contract is independently verified.
- Workload-root adoption remains blocked on cleared bootstrap adoption/readback.

### Join J1 — before foundation-plan generation

Require:

- PR 0, PR A, and PR B merged into protected `develop`, followed by exact-tip rebaseline before the approval-bound inventory run;
- both roots adopted and read back without unresolved mismatch;
- when Proposed Amendment B is accepted, A5's exact bootstrap augmentation plan/apply and post-apply identity/WIF readback completed before the workload foundation plan;
- source PRs required for foundation receipt/evidence generation merged;
- exact source SHA, provider lock, non-secret input digest, backend fingerprints, state readbacks, and inventory digest current;
- no material replanning trigger open.

### Join J2 — before image publication

Require:

- foundation apply and foundation-mode verification complete;
- artifact interoperability PR merged;
- exact build commit selected and locally/CI qualified;
- registry/Sigstore compatibility evidence accepted;
- vulnerability disposition current.

### Join J3 — before human testing

Require:

- migration and service gates complete;
- named tester authority exact and non-public;
- automated pre-human qualification passed;
- monitoring/incident and cleanup owners identified privately;
- human qualification/feedback packet merged.

---

## 5. Predeclared implementation PR sequence

### Planning PR P — methodology, truthful rebaseline, and this master plan

**Branch:** `docs/post-pr48-truthful-state-rebaseline`
**Scope:** ADR-0014; workflow-scale governance; post-PR #48 status reconciliation; Obsidian continuity; this master plan and review handoff.
**No executable authority:** No cloud/runtime actions or behavior changes.
**Exit:** Independent planning/security/executability review, Beatrice acceptance, protected checks, merge, exact-tip rebaseline.

### Implementation PR 0 — bootstrap remote-state adoption readiness

**Suggested branch:** `fix/bootstrap-state-adoption-readiness`
**Objective:** Make the bootstrap root capable of the already-planned remote-state adoption without mixing it with the workload backend or relying on a nonexistent partial backend declaration.

**Likely files:**

- Create: `infra/gcp/bootstrap/backend.tf`
- Modify: `deploy/gcp/bootstrap-state-runbook.md`
- Modify if needed: `scripts/validate_terraform_static.py`
- Test: `tests/unit/test_terraform_hygiene.py`

**Required RED → GREEN families:**

1. Prove the bootstrap root declares its own partial `backend "gcs" {}` block and the workload root retains its distinct partial backend declaration.
2. Prove no backend bucket/object/prefix/credential value is committed in either root.
3. Prove bootstrap and workload approvals require distinct opaque resolved-backend/state-object-or-prefix/lock-scope fingerprints before initialization.
4. Reconcile the runbook's local-bootstrap-to-remote-state migration sequence with the now-existing bootstrap backend declaration and the already-existing live bucket; preserve private pre-action recovery and exact readback.
5. Preserve backend-free local `init`/`validate` behavior for both roots and reject accidental shared-state configuration.

**Verification:**

```text
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
git diff --check
```

**Stop boundary:** No private inventory, backend initialization/migration, import, state read/write, Terraform plan/apply, or cloud mutation. Merge PR 0 before PR A so the shared static-policy/test surface and bootstrap-root contract have one clear base.

### Implementation PR A — artifact and transition authority interoperability

**Suggested branch:** `fix/develop-artifact-transition-authority`
**Objective:** Make the real Buildx/Cosign/registry output and stage-receipt path satisfy ADR-0013 end to end instead of relying only on hand-shaped local fixtures.

**Accepted authority design:** The deployer cannot read a private OCI image under ADR-0013's exact Cloud Run-only roles. The accepted correction is a separate `golden-rose-artifact-verifier` control-plane identity with only exact-repository `roles/artifactregistry.reader` authority and WIF trust limited to the protected direct `deploy-develop.yml@refs/heads/develop` workflow. The workflow must authenticate as that verifier only for direct OCI verification using a dedicated temporary `DOCKER_CONFIG`/Google credential directory, then log out, remove and prove absence of registry and Google credential files/environment, and authenticate separately as the Cloud Run deployer. The verifier receives no publish, Cloud Run, Terraform, IAM-mutation, secret, database, or application-invocation authority; the deployer receives no Artifact Registry read/write authority or reusable verifier token. This design remains unimplementable until the accepted packet merges and PR A begins from that exact tip.

**Likely files:**

- Modify: `.github/workflows/build-image.yml`
- Modify if required: `.github/workflows/deploy-develop.yml`
- Modify: `infra/gcp/bootstrap/iam.tf`
- Modify: `infra/gcp/bootstrap/wif.tf`
- Modify if needed: `infra/gcp/bootstrap/outputs.tf`
- Modify: `infra/gcp/develop/iam.tf`
- Modify: `scripts/verify_image_provenance.py`
- Modify: `scripts/verify_deploy_image_authority.py`
- Modify: `scripts/verify_stage_receipt.py`
- Create: `scripts/write_migration_success_receipt.py`
- Modify if needed: `scripts/validate_terraform_static.py`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify: `deploy/gcp/first-deployment-runbook.md`
- Modify: `deploy/gcp/receipts/README.md`
- Modify/create bounded example templates under `deploy/gcp/receipts/templates/`
- Test: `tests/unit/test_image_provenance.py`
- Test: `tests/unit/test_deploy_image_authority.py`
- Test: `tests/unit/test_stage_receipt.py`
- Create: `tests/unit/test_write_migration_success_receipt.py`
- Test: `tests/unit/test_terraform_hygiene.py`

**Required RED → GREEN families:**

1. Reproduce the exact mismatch, if any, between Buildx `--provenance=mode=max --sbom=true`, publication attestations, and deploy-time `cosign verify-attestation` expectations.
2. Prove the final-image SBOM is generated by the accepted tool/BuildKit output, attached or attested to the exact `linux/amd64` digest, schema-valid, and nonempty; reject a workflow-authored placeholder inventory.
3. Prove SLSA predicate type, subject digest, source commit, builder identity, certificate identity, OIDC issuer, and transparency inclusion from actual-shaped Cosign v3 output.
4. Prove application SBOM checksums bind the schema-validated backend/frontend SBOMs to the same digest.
5. Prove foundation receipt content permits no workload image/configuration while migration/service receipts require the exact image and projection.
6. Preserve workflow hash/static-policy allowlists and reject any new imperative cloud mutation or broadened IAM path.
7. Reconcile the runbook sequence so secret versions may precede the migration plan, but database login-role creation and live database-authority verification occur only after migration-stage Cloud SQL exists and before migration execution.
8. Prove the artifact-verifier/deployer credential handoff: verifier can read only the exact private repository for Cosign verification through a dedicated temporary registry/Google credential context; logout and deletion/unset checks run before deployer authentication; deployer can inspect/execute only the exact Cloud Run resources; neither can assume the other's authority, and stale verifier tokens/configuration are unavailable during deployer operations.
9. After a successful waited migration job, write a minimized migration-success receipt bound to the exact migration-receipt SHA-256, source SHA, immutable image digest, and successful execution reference; mark `deploy-result.json` successful only on that path, sign the receipt as a separate blob, and upload the receipt/bundle for operator-held custody. Failure, cancellation, or unknown outcome must not emit success authority.
10. Require the later service gate to verify the migration-success signature before cloud authentication and to accept it only after separate database/schema/authority readback is approved.
11. Test OCI index/child digest substitution, extra runnable platforms, unsupported SLSA v0.2 predicates, wrong OCI subjects, wrong media/predicate types, and attestations attached to another digest using actual-shaped Cosign v3 output.

**Compatibility spike gate:**

- Before production workflow logic is finalized, obtain separate approval for an isolated non-production registry/Sigstore compatibility spike.
- Bind it to exact Docker Buildx, Cosign, platform, workflow/source revision, and disposable image inputs.
- Store raw output only in private/ephemeral custody; track only value-safe findings.
- Stop on incompatible media type/predicate/attachment/retrieval behavior; do not fabricate an attestation or weaken verification.

**Verification:**

```text
env -u PYTHONPATH uv run pytest tests/unit/test_image_provenance.py tests/unit/test_deploy_image_authority.py tests/unit/test_stage_receipt.py tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run ruff format --check scripts tests
env -u PYTHONPATH uv run ruff check scripts tests
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
terraform fmt -check -recursive infra/gcp
git diff --check
```

**Stop boundary:** No target GCP publication, secret/database action, Terraform plan/apply, migration, or service activation.

### Implementation PR B — automated qualification and human-feedback readiness

**Suggested branch:** `feat/develop-human-qualification`
**Objective:** Make the controlled shared target testable by approved humans and ensure automated/manual evidence cannot overclaim qualification.

**Likely files:**

- Modify: `scripts/qualify_develop_deployment.py`
- Modify: `scripts/verify_database_authority.py`
- Modify: `infra/policy/predeployment-authority-manifest.json`
- Modify if needed: `scripts/validate_terraform_static.py`
- Modify: `deploy/gcp/evidence-template.md`
- Modify: `deploy/gcp/private-tester-access.md`
- Create: `deploy/gcp/human-qualification-checklist.md`
- Create: `deploy/gcp/human-feedback-template.md`
- Create: `deploy/gcp/qualification-status-contract.md`
- Test: `tests/unit/test_qualify_develop_deployment.py`
- Test: `tests/unit/test_verify_database_authority.py`
- Test: `tests/integration/test_database_authority.py`
- Frontend regression evidence: `apps/web/src/app/*.test.tsx`, `apps/web/src/employers/*.test.tsx`, `apps/web/src/i18n/LanguageProvider.test.tsx`, `apps/web/src/test/valueSafeDiagnostics.test.ts`

**Required RED → GREEN families:**

1. Add two distinct minimized denial probes before approved qualification: one unauthenticated request with no token, and one request using a separately sourced Google identity token for an authenticated-but-unapproved principal. Before the second probe, fail closed unless the token's signature, Google issuer, exact service audience, expiry/not-before, and privately approved expected subject are valid and a fresh live IAM/effective-authority read proves that subject has no direct, inherited, group/domain, public, or broad invocation path. Both probes transmit no business body and store no token, endpoint, identity, subject, or raw response in tracked evidence. The approved and unapproved tokens must use separate non-argv stdin/file/environment handoffs and may never be substituted for one another.
2. Keep authenticated health/readiness and synthetic-write qualification separate; require explicit `--allow-synthetic-writes` for mutations.
3. Bind qualification to the exact reviewed service authority, image digest, schema revision, and deployment target.
4. Emit one schema-stable result with explicit automated, manual-browser, accessibility, fluent-language, tester-access, monitoring, recovery, cleanup, and feedback fields; unperformed fields must be `not_run`/`not_evidenced`, never silently omitted or passed.
5. Preserve descriptor-anchored, symlink-safe, atomic evidence writes and value-independent failure output.
6. Define structured issue fields: synthetic scenario, role/language/browser/viewport, expected/observed behavior, severity, workflow blocker, accessibility impact, privacy/security impact, reproduction, evidence reference, owner, disposition, and retest result.
7. Define the manual checklist in section 10 without storing submitted names, UUIDs, commands, cursors, tester identities, endpoints, tokens, screenshots containing sensitive values, or raw bodies in tracked evidence.
8. Register `scripts/verify_database_authority.py` as an approved entrypoint and prove its main path fails with bounded nonzero output on connection/SQLAlchemy errors without reflecting connection material.
9. Retain controlled-PostgreSQL integration coverage for migrated-schema acceptance, runtime DDL/role/trigger/`TRUNCATE` denial, migration owner-role assumption, login identity separation, and drift rejection.
10. Require a named browser/OS/device-or-viewport/assistive-technology/network matrix before human testing; every required entry records pass/fail/not-run, tester role, language, evidence reference, and disposition.
11. Parse response headers case-insensitively and require `Cache-Control: no-store` across every exercised Employer create/replay/detail/search/revision/replay and EmployerContact create/query/read success. Add representative denied, validation, not-found, conflict, and unavailable outcomes where the accepted API contract requires no-store; any missing or cache-permissive value blocks a passing artifact.
12. Add negative tests proving the authenticated-but-unapproved probe rejects expired/not-yet-valid tokens, wrong issuer/audience/signature/subject, a subject that appears through any effective invoker binding, and reuse of the approved tester token; only a cryptographically valid token for a currently non-authorized subject may establish the IAM-denial result.

**Required no-store evidence matrix:**

| Boundary | Required live outcome | Required controlled service-backed/static outcomes |
| --- | --- | --- |
| Employer create | fresh `201`, replayed `201` | validation `422`, actor/payload idempotency conflict `409`, denied `403`, persistence unavailable `503`, unexpected failure `500` |
| Employer detail | current `200`, synthetic random-UUID not-found `404` | denied `403`, persistence unavailable `503`, unexpected failure `500` |
| Employer search | bounded `200`, malformed-cursor `422` | body validation `422`, denied `403`, persistence unavailable `503`, unexpected failure `500` |
| Employer revision | fresh `200`, replayed `200`, safely induced stale expected-version `412`, changed-key idempotency conflict `409` | validation/no-op `422`, denied `403`, not-found `404`, persistence unavailable `503`, unexpected failure `500` |
| EmployerContact create | fresh `201`, replayed `201` | validation `422`, idempotency conflict `409`, denied `403`, parent not-found `404`, persistence unavailable `503`, unexpected failure `500` |
| EmployerContact query | bounded `200`, malformed/overlength cursor `422` | body validation `422`, denied `403`, parent not-found `404`, persistence unavailable `503`, unexpected failure `500` |
| EmployerContact exact read | current `200`, synthetic random-UUID or parent/contact mismatch not-found `404` | denied `403`, persistence unavailable `503`, unexpected failure `500` |

The shared target exercises only outcomes safe to induce with newly generated fictional values and no infrastructure mutation. Application authorization and unavailable outcomes remain controlled service-backed/static evidence and must bind to the exact source candidate. Cloud Run IAM rejections are platform evidence only and must not be treated as FastAPI problem/cache evidence. Header names are case-insensitive; the parsed directive set must contain `no-store`, and any contradictory cache-permissive directive fails the row.

**Verification:**

```text
env -u PYTHONPATH uv run pytest tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_database_authority.py -q
# With the approved disposable PostgreSQL test service configured:
env -u PYTHONPATH uv run pytest tests/integration/test_database_authority.py -q
npm --userconfig apps/web/.npmrc --prefix apps/web run verify
env -u PYTHONPATH uv run ruff format --check scripts/qualify_develop_deployment.py scripts/verify_database_authority.py tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_database_authority.py tests/integration/test_database_authority.py
env -u PYTHONPATH uv run ruff check scripts/qualify_develop_deployment.py scripts/verify_database_authority.py tests/unit/test_qualify_develop_deployment.py tests/unit/test_verify_database_authority.py tests/integration/test_database_authority.py
env -u PYTHONPATH uv run mypy src tests
git diff --check
```

**Stop boundary:** No cloud access, tester grant, service start, or human walkthrough from this PR.

### Conditional implementation PR C — contract-preserving source/live remediation

**Suggested branch:** `fix/develop-activation-remediation`
**Activation condition:** A private inventory, exact plan, compatibility spike, or pre-human qualification reveals a source defect that remains inside ADR-0009/0013 and this plan's existing trust/data/identity/stage contracts.

Allowed examples:

- provider normalization or receipt rendering correction;
- value-safe evidence-parser compatibility;
- contract-preserving Terraform source correction;
- qualification harness defect;
- workflow integration bug that does not broaden authority.

Not allowed without replanning:

- broader IAM or public access;
- new resource class or stage;
- new vendor/identity/data class;
- destructive schema redesign;
- bypassing signature, receipt, state, migration, or qualification controls.

If no qualifying defect exists, skip PR C. Every fix is test-first, independently rereviewed, and merged before the affected operational gate is retried.

**Mandatory invalidation and replay matrix after any PR C merge:**

1. Rebaseline from the exact new protected `develop` tip and classify every changed path as Terraform/state-contract, workflow/receipt, application/image, qualification-only, or documentation-only.
2. Invalidate every saved plan, signed stage/tester/migration-success receipt, non-secret-input digest, source-bound approval, image/provenance set, or configuration projection whose bound source/artifact may have changed; never reuse an artifact merely because the behavioral fix seems unrelated.
3. Recompare private inventory/state readback to the new Terraform source when infrastructure or verifier contracts changed; request a new plan and explicit approval for every affected stage.
4. Republish and re-verify a new immutable image when application, migration, container, build, dependency, or source-bound provenance content changed.
5. Regenerate/reapprove migration and service plans in order when their source, image, configuration projection, secret references, network/database posture, tester authority, or prior migration evidence changed.
6. Rerun all affected automated, access, browser, accessibility, language, monitoring, recovery, cleanup, and feedback-retest evidence before closeout.
7. A documentation-only correction may avoid runtime replay only when independent review proves it changes no bound source/artifact/receipt/approval semantics; record that disposition explicitly.

### Closeout PR D — qualification and feedback disposition

**Suggested branch:** `docs/private-develop-qualification-closeout`
**Scope:** Value-safe result only: exact source/digest references, pass/fail status, blocker categories, cleanup disposition, feedback issue counts by severity/category, and next accepted tranche. No raw private evidence.

**Exit:** Living docs, ADR/decision status if changed, `ROADMAP.md`, `NOTES.md`, GCP README/runbooks, and Obsidian records agree on the final target status. This PR does not itself fix product defects; qualifying defects use PR C or trigger replanning.

---

## 6. Operational Gate A — private inventory and adoption

Retain Tasks 2-5 of the prior Gate 3 ceremony plan as the exact operating procedure.

### A0 — source-readiness activation

- Merge PR 0, PR A, and PR B through protected `develop`; re-fetch and prove the operator checkout equals the exact merged tip. PR B may be developed in parallel after the plan merge, but it must rebase onto the current protected tip before merge.
- Rerun local Terraform/static/unit/source-policy gates and confirm the bootstrap partial backend, proposed accepted artifact-verifier source contract, and receipt tooling are present.
- Invalidate any pre-merge inventory draft, candidate-address set, source/lock digest, or approval bundle. Only private custody/reader planning that contains no collected target facts may be carried forward.
- Obtain the A1 approval against the new exact source/lock/candidate universe. No collection or adoption may race the source PRs.

### A1 — read-only private inventory approval

Approval must bind privately:

- operator identity and exact project scopes;
- source SHA, Terraform/provider versions, and provider-lock digest;
- allowed read-only command families;
- candidate/deferred resource universe;
- evidence custody, authorized readers, disposal, and run ID;
- no-import/no-backend/no-state/no-plan/no-apply/no-mutation boundary;
- stop conditions and mismatch owner.

Acceptance: every in-scope candidate is classified exactly once; deferred network/Cloud SQL/database/workload classes remain absent; independent private review clears the inventory.

### A2 — bootstrap provenance/import decision

- Prove or block on authentic prior local-state provenance.
- Prove exact pinned-version import representation through documentation or separately approved isolated probe.
- Prove the intended bootstrap backend identity/fingerprint is distinct from workload state.

Acceptance: safe bootstrap adoption request or an honest blocker; no target trial-and-error.

### A3 — bootstrap-root adoption approval and execution

- Bind source/lock/input/backend digest/fingerprint/address/recovery evidence.
- Adopt bootstrap resources only.
- Read back after each action; confirm bootstrap-only lineage, lock scope, address set, and recovery access.
- Do not retire bootstrap authority here.

### A4 — workload-root adoption approval and execution

- Require cleared bootstrap readback.
- Bind a distinct workload backend and exact partial-foundation address set.
- Adopt only reviewed existing workload candidates.
- Confirm deferred network/Cloud SQL/database/workload classes remain absent.
- Do not run `terraform plan` in adoption.

Any mismatch is `blocked` or `unknown`, not repair authority.

### A5 — bootstrap-root augmentation plan/apply for accepted new control-plane identity

This gate is required by accepted ADR-0013 Amendment B. Adoption records existing bootstrap resources; it does not create the new artifact-verifier identity/WIF binding introduced by PR A.

1. Generate a bootstrap-root saved plan from the exact adopted bootstrap state and approved PR A source. Its reviewed JSON inventory may create only the accepted artifact-verifier service account and exact deploy-workflow WIF impersonation binding plus any value-safe bootstrap outputs required by the workload root.
2. Reject any state-bucket replacement, state IAM broadening, publisher/deployer/provisioner authority change, service-account key, Token Creator role, wildcard claim, or unrelated control-plane action.
3. Independently review and explicitly approve the exact bootstrap saved plan, source/lock/input/backend/state/inventory evidence, operator, expiry, and recovery posture.
4. Apply only that saved bootstrap plan through the approved keyless local provisioner path; read back bootstrap state, effective WIF/IAM, key absence, root separation, and recovery access.
5. Stop before workload foundation planning if the artifact-verifier identity, workflow claim, or effective authority differs from Proposed Amendment B as accepted.

The later workload `foundation` plan must separately create the exact-repository reader binding for this already-existing control-plane identity. Passing A5 does not grant the workload foundation plan/apply or publication.

---

## 7. Operational Gate B — exact foundation plan and apply

### B1 — plan-generation approval

Bind privately:

- exact source SHA and Terraform/provider versions;
- provider-lock and non-secret-input digests;
- both backend/state readbacks and inventory digest;
- `deployment_stage=foundation` with no image and null deferred network/database/tester inputs;
- saved binary plan destination and JSON inventory custody;
- invalidation conditions.
- exact keyless local provisioner impersonation and backend-config handoff; no GitHub apply workflow or service-account key.

### B2 — generate and review

- Generate one saved binary `foundation` plan and JSON representation privately.
- Prove no Cloud Run job/service, network, private-service access, Cloud SQL, application database, image, tester, monitoring uptime, secret payload, or database login action.
- Review every create/change/delete/replace, IAM/API/state/budget/observability/label/recovery implication, and current cost assumption.
- Produce a value-safe signed/approved foundation receipt and artifact hashes.

### B3 — explicit apply approval

Approval binds the exact saved plan bytes/hash, reviewed JSON inventory, source/lock/input/backend/state evidence, expiry, operator, keyless local provisioner impersonation path, and recovery disposition.

### B4 — apply and verify

- Apply only the approved saved plan; no regeneration.
- Run `scripts/verify_gcp_foundation.py --mode foundation` with operator-held inputs.
- Confirm no executable workload, Cloud SQL, keys, broad IAM, or state-control drift.
- Record value-safe pass/fail and cleanup; stop before publication.

---

## 8. Operational Gate C — publication, secrets, and database preparation

### C0 — protected `develop` environment and WIF configuration approval

- Review the private GitHub `develop` environment protection/approval posture and exact non-secret variables for project scope, WIF provider, publisher/deployer identities, and certificate identities.
- Verify effective workflow impersonation remains bound to the exact repository, owner, protected ref, environment, `workflow_dispatch`, and direct `workflow_ref` claims.
- Keep identifiers and certificate/configuration values out of tracked docs and ordinary evidence; record only private references/digests and pass/fail.
- Stop on missing environment protection, substituted workflow identity, broader principal set, service-account key, or publisher/deployer overlap.

### C1 — immutable publication approval

Require Join J2, exact protected `develop` source, merged PR A, accepted compatibility spike, current vulnerability disposition, and named publication owner.

- Dispatch `.github/workflows/build-image.yml` from protected `develop`.
- Publish one `linux/amd64` digest.
- Independently verify signature, transparency inclusion, SLSA provenance, final-image SBOM, and backend/frontend SBOM checksum attestation.
- Keep raw bundles and registry details in bounded private evidence.

### C2 — secret-version preparation approval

Follow `deploy/gcp/first-deployment-runbook.md`:

- name custodians, rotation/revocation/recovery owners privately;
- inject only approved secret versions through non-echoing channels;
- stop on payload exposure or authority drift.

The migration-stage Cloud SQL instance does not exist yet. Do not create database login roles or claim database-authority verification in this gate. Publication does not grant secret preparation; secret preparation does not grant the migration plan/apply.

---

## 9. Operational Gate D — migration and service activation

### D1 — exact migration plan

- Generate and review `deployment_stage=migration` against the exact published digest.
- Require network/private-service access/Cloud SQL/application database and configured migration job; require no staff service or tester access.
- Verify secret references, migration identity, Direct VPC/private database path, command, timeout, retries, task count, and exact configuration projection.
- Sign/approve the operator-held migration receipt.
- Use the same exact approved local provisioner path; the deploy workflow does not plan/apply or mutate Terraform-managed configuration.

### D2 — migration apply and execution

- Explicitly approve and apply the exact migration saved plan.
- Verify live job projection before execution.
- After the migration-stage Cloud SQL/database exists, obtain the separately scoped database-login preparation approval; create runtime/migration login roles out of band, grant only the reviewed group-role chains, and run `scripts/verify_database_authority.py` through non-echoing connection-material handoffs.
- Stop before migration execution if database authority, secret references, connectivity, or schema-owner assumption differs from the reviewed contract.
- Explicitly authorize one `.github/workflows/deploy-develop.yml` migration transition.
- Capture advisory-lock, exit, schema revision, database authority, and compatibility evidence.
- Unknown/cancelled execution blocks retry and service activation pending database inspection.
- Produce separately signed migration-success evidence bound to the migration receipt and digest.

### D3 — exact service plan

- Generate/review `deployment_stage=service` only after migration success.
- Obtain the separately scoped named-tester approval, create and sign the operator-held tester-authority receipt, verify its detached bundle, and derive exactly one approved `user:` principal plus immutable receipt digest for the plan; do not accept caller-supplied substitutes.
- Require exact service image/configuration, named tester and monitoring invokers, IAM-private internet-reachable ingress, service-stage alerting/uptime checks, and no broad principal.
- Sign/approve a distinct service receipt.
- Use the same exact approved local provisioner path; the deploy workflow remains limited to receipt/image/live-projection verification, migration-job execution, and readiness inspection.

### D4 — service apply and readiness

- Explicitly approve and apply the exact service saved plan.
- Run the service transition through `.github/workflows/deploy-develop.yml` with signed service, migration, and migration-success receipts.
- Verify typed Cloud Run `Ready=True`, exact immutable digest, configuration projection, IAM policy, and monitoring service-agent path.
- Record deployment-readiness separately from Gate 6 qualification.

---

## 10. Operational Gate E — automated and human qualification

### E1 — pre-human automated qualification

Before granting a human window:

1. Run service-mode foundation verification with the signed tester-authority receipt.
2. Run database-authority verification.
3. Prove unauthenticated invocation and authenticated-but-unapproved invocation fail through two independent probes without transmitting business data or reusing the approved tester token. Bind the second result to privately verified token claims and a fresh effective-IAM absence proof so an invalid token cannot masquerade as authorization denial.
4. Prove approved named invocation succeeds.
5. Run `scripts/qualify_develop_deployment.py` with a non-argv token handoff, exact service URL, exact digest/schema, and explicit fictional-synthetic write acknowledgement.
6. Verify Employer and EmployerContact flows, no-store/readiness posture, minimized evidence, logs, alerts, cost markers, and cleanup disposition.
7. Stop and remove/withhold the human window on any Blocker/High, public/broad invocation, identity mismatch, secret exposure, wrong digest/schema, or failed core workflow.

### E2 — bounded named-human technical feedback window

Private operator record must name the tester, owner, start/end or review time, service scope, incident path, and removal owner. The tracked record contains no identity or endpoint.

The tester uses newly generated fictional values only and is told explicitly:

- this is private non-production technical testing;
- synthetic application auth is not production identity;
- no client/live-derived data, screenshots with sensitive values, uploads, or production claims;
- report problems through the structured feedback artifact.

### E3 — human browser checklist

Exercise on the shared target:

- open/load, refresh, back/forward/BFCache, and no stale-state restoration;
- English and Spanish functional completeness for visible current workflows;
- create, replay/retry guidance, search, detail, revision, and error/recovery paths;
- keyboard-only operation, visible focus, focus ownership after async transitions, and live-region announcements;
- 200% zoom, 320 CSS-pixel reflow, narrow viewport, reduced-motion preference, text spacing, contrast, and non-color status meaning;
- no workflow values in URL query/hash, local/session storage, console, analytics, or third-party requests;
- responsive/loading/empty/success/error/conflict/unknown-outcome behavior that can be safely induced without cloud/IAM mutation;
- exact current limitation: EmployerContact remains backend-qualified unless a product UI exists; do not pretend it is a browser workflow.

**Minimum required manual matrix before any qualified or technical-feedback status:**

- current macOS Safari and current supported Chromium desktop entries;
- English and Spanish functional walkthroughs of every current Employer browser path in at least the primary browser, with a parity smoke pass in the second browser;
- keyboard-only navigation, visible focus, async focus ownership, and live-region behavior;
- 200% zoom, 320-CSS-pixel reflow, approved text-spacing override, reduced-motion preference, contrast, and non-color status meaning;
- refresh/back/forward/BFCache, constrained-network/loading, and safe error/recovery behavior;
- for each row: browser/OS/version, viewport/device class, assistive-technology or keyboard mode, network posture, language, tester role, pass/fail/not-run, private evidence reference/digest, defect links, disposition, and retest result.

Every required browser/manual-accessibility row must run and pass before status 1 or 2. A failed or unrun row produces `not_qualified`. The only evidence allowed to remain open for `operational_private_develop_technical_feedback_only` is a specifically named fluent-language content-quality review—normally fluent Spanish—when functional Spanish parity, all security/automated criteria, and every required browser/manual-accessibility row have passed. Legal/policy translation approval remains out of scope rather than a technical-feedback exception.

### E4 — language and accessibility evidence

Classify separately:

- automated axe/catalog parity;
- human keyboard/focus/reflow/zoom/reduced-motion/contrast review;
- fluent English review;
- fluent Spanish review;
- legal/policy translation approval (still out of scope).

A non-fluent tester may validate functional parity and discover obvious defects but cannot close the fluent-language gate. Record `not_evidenced` and the missing reviewer rather than inflating the result.

### E5 — feedback triage

Every feedback item receives:

- value-safe scenario and reproducibility;
- severity and workflow-blocking classification;
- accessibility, privacy, security, and language impact;
- expected/observed behavior;
- owner, disposition, and retest result;
- link to private evidence where needed without copying sensitive content.

Blocker/High and pilot-blocking items close through PR C or trigger replanning. Medium/Low items must be fixed, accepted with rationale for this technical window, or scheduled before staff-pilot promotion.

### E6 — access removal and cleanup

- Remove or explicitly review-date tester IAM.
- Prove removed principals have no inherited/broad invocation.
- Clear local token files/environment/clipboard material.
- Preserve only approved fictional data or use teardown/rebuild; do not invent delete semantics.
- Confirm monitoring/alert disposition and no public exposure.

### Conditional Operational Gate F — failed-activation recovery or teardown

A failed apply, migration, activation, or qualification does not grant cleanup, reverse-stage, destroy, IAM, secret, or deletion-protection mutation authority.

1. Immediately remove/withhold tester access and stop further migration/service/qualification attempts; preserve current state and private evidence.
2. Refresh private inventory and both state readbacks. Classify the failure and choose reviewed forward recovery, exact rollback, or workload teardown/rebuild under `deploy/gcp/rollback-forward-recovery-runbook.md` and `deploy/gcp/teardown-rebuild-runbook.md`.
3. For any Terraform reverse/destroy path, generate a separate exact saved plan and JSON action inventory. Review every delete/replace, deletion-protection change, IAM effect, secret-version disposition, monitoring/budget/log effect, orphan risk, cost implication, and recovery prerequisite.
4. Prove the durable bootstrap/state control plane, remote-state custody, recovery evidence, and excluded operator-held records are outside the disposable workload destruction set.
5. Obtain a distinct explicit recovery/teardown approval bound to the exact plan hash, source/lock/input/backend/state/inventory evidence, operator, expiry, and post-action verification.
6. Apply only the approved recovery/teardown plan; do not regenerate it. Read back state/live inventory, verify no unauthorized orphan/public access remains, and preserve or revoke secret versions according to the approved custody decision.
7. Re-entry after recovery follows the PR C invalidation/replay matrix and the normal forward gates from the earliest invalidated authority. A torn-down target requires fresh reviewed plans; it does not resume at service activation.

If Gate F is not approved, leave the target blocked/quarantined with human access removed and record the unresolved cleanup owner; do not improvise destruction.

---

## 11. Final status contract

The tranche ends with exactly one status:

1. **`qualified_private_develop_for_human_feedback`** — all automated, access, browser, manual accessibility, fluent English/Spanish, monitoring, recovery/cleanup, and feedback-blocker criteria pass. This is still non-production, synthetic-only, and not staff-pilot identity.
2. **`operational_private_develop_technical_feedback_only`** — service, security/automated qualification, and every required browser/manual-accessibility row pass, but the specifically named fluent-language content-quality review allowed above remains `not_evidenced`. No other missing/failed row qualifies for this status. Do not call this fully qualified or client-accepted.
3. **`not_qualified`** — a core automated, security, privacy, migration, service, browser, accessibility, language, monitoring, recovery, or cleanup criterion fails; record blockers and stop/cleanup disposition.
4. **`torn_down_after_failed_activation`** — activation cannot be safely retained; workload cleanup/rebuild disposition is executed while preserving the control-plane/state evidence required by approved recovery policy.

None of these statuses authorizes live/client data or production.

---

## 12. Material replanning triggers

Return to planning only if evidence requires:

- a new Terraform root, deployment stage, resource class, provider, region, identity model, vendor, or public access path;
- broader IAM than ADR-0013 permits;
- a different state topology or inability to prove bootstrap/workload separation;
- destructive/non-forward-compatible schema behavior outside accepted migration/recovery contracts;
- a new sensitive/live data class;
- weakening signature, receipt, digest, tester, database, or qualification authority;
- a Blocker/High that invalidates this architecture rather than exposing an implementation defect;
- client/user feedback that changes the target workflow rather than requesting a bounded defect fix;
- inability to deliver the outcome through the predeclared PR/gate sequence.

Do not replan for ordinary test failures, fixture/harness fixes, provider normalization within the accepted contract, helper extraction, review remediation, or splitting a predeclared PR for reviewability.

---

## 13. Full verification and review gates

### Source PR checks

Run the relevant focused suites plus the complete repository gate where behavior changes:

```text
env -u PYTHONPATH uv run ruff format --check .
env -u PYTHONPATH uv run ruff check .
env -u PYTHONPATH uv run mypy src tests
env -u PYTHONPATH uv run pytest -q
npm --userconfig apps/web/.npmrc --prefix apps/web run verify
env -u PYTHONPATH uv run bandit -q -r src
env -u PYTHONPATH uv run pip-audit --skip-editable
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
git diff --check
```

Use a disposable approved PostgreSQL service for integration/migration tests and prove teardown with an empty service listing. Run exact-range Gitleaks after each commit range exists.

### Independent review lenses

For the planning PR and each source PR, independently review:

1. state/adoption and Terraform stage authority;
2. IAM/WIF/tester/database authority;
3. OCI/Sigstore/SBOM and workflow execution authority;
4. qualification evidence, privacy, accessibility, and language truth;
5. documentation, private-custody, cleanup, and schedule/executability.

Blocker/High findings stop progression. Medium findings require remediation or explicit owner disposition appropriate to the technical non-production target.

### Operational readback

Every approved operator gate records privately:

- approved scope and operator;
- source/lock/input/artifact digests;
- start/end time;
- exact result status;
- private evidence references/digests;
- mismatch/incident/recovery disposition;
- next gate requested, never inferred.

Tracked docs receive only value-safe status, date, digest/reference where safe, and blocker category.

---

## 14. Hard stop boundaries

This plan never authorizes:

- public access or broad authenticated-user invocation;
- real staff identity claims, live/client-derived data, unrestricted uploads, integrations, or production;
- automatic matching, ranking, eligibility, hiring, or referral decisions;
- secret payloads, credentials, private endpoints, principals, plans, state, raw outputs, receipts, or tester identities in Git/chat/ordinary evidence;
- plan regeneration after approval, unreviewed `-target`, imperative Cloud Run configuration mutation, IAM broadening, or state repair by guess;
- concurrent/unknown migration retry, schema rollback by assumption, or service activation without signed migration evidence;
- treating human technical feedback as client acceptance, fluent-language approval, or production qualification;
- moving to the next operational gate because the prior one passed.

---

## 15. Planning packet acceptance checklist

Before this plan is accepted and merged:

- [x] Verify every named file/symbol exists or is explicitly marked `Create`.
- [x] Independently review and explicitly accept ADR-0013 Amendment B.
- [x] Confirm the plan preserves the prior Gate 3 inventory/adoption detail while replacing only the redundant future-plan document requirement.
- [x] Confirm the PR sequence is large enough to deliver the outcome but each PR remains reviewable.
- [x] Confirm source and operator tracks may run in parallel without one granting the other's authority.
- [x] Confirm exact operational approvals remain separate.
- [x] Confirm the final status contract cannot overclaim fluent-language, client acceptance, live-data, or production readiness.
- [x] Confirm all private evidence stays outside tracked source.
- [x] Complete independent architecture/security/executability review and remediate all findings.
- [x] Record Beatrice's explicit acceptance and perform an acceptance-delta audit.
- [ ] Publish through protected `develop`; then rebaseline every implementation branch from the exact merged tip.
