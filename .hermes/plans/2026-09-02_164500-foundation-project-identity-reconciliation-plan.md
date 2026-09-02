# Foundation ownership-alignment outcome plan

> **For Hermes:** This is one outcome-scale plan. After protected merge and exact-`develop` rebaseline, it authorizes the bounded source-only reconciliation implementation/PR sequence only under the separately approved read-only and implementation command records. It does **not** authorize a Terraform apply, an arbitrary state repair, or a new general inventory/reconciliation program.

**Goal:** Turn the already generated foundation saved-plan evidence into one reviewed, non-destructive foundation plan that retains the verified E2/E3/A5 outcome, treats the four known absent Secret-access IAM bindings as explicit desired-state creates, and removes or truthfully escalates the five unexplained project-identity replacements.

**Architecture:** Reuse the completed A1, E2, E3, and A5 evidence as fixed inputs. The sole remaining ownership question is whether the imported parent representation for one logging bucket configuration and four metadata-only Secrets denotes the same approved workload project as the reviewed Terraform input. Resolve that one identity-normalization seam through bounded private evidence; then make one narrow source/import-representation correction if—and only if—the exact evidence proves a false replacement. The next saved plan remains a new artifact and apply remains a separate approval.

**Tech stack:** Terraform and the locked Google provider, the existing `infra/gcp` workload root, `tests/unit/test_terraform_hygiene.py`, `scripts/validate_terraform_static.py`, and private Obsidian evidence.

---

## What is already complete — do not repeat it

| Closed result | Evidence to reuse | Explicit non-action |
| --- | --- | --- |
| A1 source/live foundation inventory and disposition | Private A1 records and current-source verifier closeout | Do not recollect a general project/IAM/API inventory. |
| E2 bootstrap state establishment | Verified bootstrap lineage, serial, and 11-address state readback | Do not adopt/recreate bootstrap state or generate an empty augmentation plan. |
| E3 workload state establishment | Verified workload lineage/serial and 37 imported resource addresses plus the expected `google_project` data source | Do not re-import, state-rm, state-push, or manually edit workload state. |
| A5 artifact verifier outcome | Existing bootstrap/workload addresses and live IAM exact-binding readbacks | Do not create or apply an empty A5 augmentation. |
| Foundation root evaluation safety | PR #63 and PR #64 merged to `develop@c78ba18` | Do not re-plan source guards or use placeholder service/image values. |

## The exact current plan result

The private plan generated from `develop@c78ba18` is valid as a review artifact and has **zero executable Cloud Run service/job changes**. It has:

- 29 no-ops;
- 3 updates;
- 4 creates for the known, previously absent Secret-access IAM addresses; and
- 5 delete/create replacements: one `google_logging_project_bucket_config` and four `google_secret_manager_secret` metadata-only resources.

All five replacements are `project`-ForceNew changes. The plan’s after-values use the reviewed workload input; each state before-value differs from that input. The five state values are not all the control-plane input, so this is not yet proven to be a simple control-plane/workload mix-up.

## Decisions already answered

### 1. Is this another broad reconciliation phase?

**No.** This is a bounded ownership-alignment disposition for exactly five replacement candidates and four already-known IAM creates. It must not re-open A1/E2/E3/A5 or begin a new discovery loop.

### 2. Should the current saved plan be applied?

**No.** Apply is withheld. A replacement of an imported logging bucket configuration or a metadata-only Secret is still a destructive identity transition and needs a separate explicit destructive/replacement decision if it cannot be removed by proven source/state representation convergence.

### 3. What should happen to the four Secret-access IAM creates?

**Suggested disposition: retain them as expected foundation desired-state creates.** They were deliberately excluded from E3 imports because they were absent live, not because they were unknown. They are not a state-repair issue and should not cause another global reconciliation. Before the final plan request, make one bounded confirmation that the exact source tuples still match the accepted source contract and no equivalent binding has appeared under another Terraform address. If unchanged, they remain visible, expected `create` actions in the next plan review and require explicit apply approval with the rest of the plan.

### 4. What must be proven about the five replacements?

One precise answer only: whether each state parent representation resolves to the same approved workload project as the Terraform source value.

- **Same live project, representation-only drift:** make the smallest source/import-representation correction that eliminates the replacements; do not replace resources.
- **Different live project:** stop and classify a true ownership/custody mismatch. This is a material replanning trigger because moving these resources would change cloud authority and lifecycle ownership.
- **Inconclusive:** stop. Do not guess from string shape, select a likely project, or use a state operation as a diagnostic tool.

## Plan sequence

### Phase 1 — one bounded private identity comparison (separate read-only authorization)

**Objective:** Classify the five `project` ForceNew changes without collecting unrelated inventory or mutating state/cloud resources.

**Private inputs:**
- current saved plan and JSON inventory;
- final E3 workload state readback;
- approved workload input binding and recovery record;
- the five exact resource addresses already named by the plan.

**Allowed procedure:**
1. Bind the exact current source SHA, provider lock digest, plan digest, workload state lineage/serial reference, and the five-address scope in a private request record.
2. Prove active account/ADC acquisition without printing either identity or token.
3. For the logging bucket configuration and each metadata-only Secret, read only the exact existing live resource using the approved workload binding.
4. Compare three facts privately: source workload project, Terraform state parent representation, and provider-read canonical parent/resource name.
5. Produce a five-row private decision matrix with exactly one classification per row: `same_project_representation_drift`, `true_cross_project_ownership_mismatch`, or `inconclusive`.

**Stop conditions:** Any non-workload parent, inaccessible candidate, unexpected missing resource, public/broad authority, or inconsistent canonical identity stops the phase. Do not broaden to list/search nearby resources.

**Acceptance:** The five rows are all `same_project_representation_drift`, or the result is a truthful bounded stop requiring a material new decision.

### Phase 2 — preserve the known Secret IAM decision (same read-only authorization)

**Objective:** Confirm the known four desired creates remain exactly the previously accepted absent bindings—nothing more.

**Files and source contract:** `infra/gcp/develop/iam.tf:64-89`.

**Allowed procedure:**
1. Compare the four source tuples (secret, role, member) to the existing private E3 deferred-address disposition.
2. Read the exact affected policies only if the original evidence is stale or a Phase 1 result indicates parent drift.
3. Confirm no binding is already represented by a different Terraform state address.

**Suggested outcome:** Keep all four as `expected_absent_desired_create` in the next foundation plan review. This preserves the accepted least-privilege source contract while making the later apply decision explicit.

**Stop conditions:** An equivalent binding under another state address, a changed identity/role/parent tuple, or an unapproved access expansion requires a narrow source decision; do not import duplicates or grant access during this phase.

### Phase 3 — one source-only correction PR if Phase 1 proves representation drift

**Objective:** Eliminate only false replacement churn while preserving the reviewed resource identity and authority.

**Likely files (evidence-dependent):**
- `infra/gcp/develop/observability.tf:24-30` for the logging bucket configuration;
- `infra/gcp/develop/secrets.tf:10-21` for metadata-only Secrets;
- the smallest applicable root/module variable or private import-binding artifact if that is the proven representation boundary;
- `tests/unit/test_terraform_hygiene.py`;
- `scripts/validate_terraform_static.py` only if a static policy contract must change;
- `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `infra/gcp/README.md`, and `deploy/gcp/staged-plan-approval.md` only for an actual value-safe outcome.

**TDD contract:**
1. Add one focused regression per resource family that fails when the corrected source representation would force a project-parent replacement for the same canonical workload project.
2. Run the focused node and record an honest RED.
3. Change only the representation proven by Phase 1. Do not use `ignore_changes`, `-target`, a lifecycle replacement escape hatch, a provider upgrade, a placeholder project, or a state command to suppress the plan.
4. Run focused GREEN, then `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q`, `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py`, `terraform fmt -check -recursive infra/gcp`, and `git diff --check`.
5. Independently review the complete uncommitted slice. Address every Blocker/High and every unaccepted Medium before the source-only PR.

**PR boundary:** One coherent source-only PR may include the representation fix, exact regressions, and living-document truth repair. It must not include a plan/apply, state mutation, secret version, database, image, service, or tester change.

### Phase 4 — regenerated plan review (separate plan-generation approval)

**Preconditions:** Phase 1 is conclusive, any Phase 3 source PR is merged, and private plan inputs/backend/recovery/state bindings are rebound to the exact merged tip.

**Procedure:**
1. Generate a new binary foundation plan and JSON inventory from the rebounded source/lock/input/backend bundle.
2. Require zero Cloud Run service/job changes.
3. Require zero delete/create replacements for the five reconciled existing controls.
4. Expect only the four `google_secret_manager_secret_iam_member` creates, plus any separately reviewed non-destructive updates whose exact cause is recorded.
5. If the replacement set remains, stop and classify it—do not apply a more recent plan just because the old one was reviewed.

**Apply boundary:** A reviewed plan is still not apply authority. The final apply request must explicitly enumerate expected creates/updates, confirm no deletion/replacement, and retain every later migration/service/tester/data/production gate.

## Evidence and review requirements

- Raw provider responses, canonical project identities, plan JSON, state snapshots, backend values, and principal values stay private in Obsidian.
- Tracked docs may record only the bounded classification, whether a replacement was removed or remains withheld, and the next gate.
- The review handoff must list every changed tracked file from the actual diff and distinguish historical E2/E3/A5 evidence from the current source-only reconciliation.
- Run exact-range Gitleaks after the source-only closeout commit and before PR creation.
- Do not commit, push, open a PR, generate a new plan, or apply anything merely because this plan exists; each hazardous gate remains separately approved.

## Anti-replanning completion contract

These additions deliberately make the plan self-closing for the normal same-project representation outcome. They prevent a reviewer from discovering ordinary plan-readiness gaps one at a time after the source-only PR is open.

### Whole-root deferred-reference sweep

PR #63 and PR #64 exposed two different eagerly evaluated locals. Before the reconciliation PR is reviewed, perform one bounded source sweep of the entire workload root for references to stage-counted resources or deferred inputs from locals, outputs, data sources, and unconditional expressions. Classify each as:

- safe in `foundation` because it has no deferred reference;
- protected by the same explicit stage condition as its consumer and returns `null` outside that stage; or
- a source defect to remediate inside the same PR.

Add or extend a focused source-contract regression so an unguarded `[0]` access to a service/job/count-zero resource cannot return in another local. This is a root-evaluation audit of current source, not a new inventory gate or plan cycle.

### Plan action allowlist

The regenerated plan review must use a written private action contract, not a qualitative "looks safe" judgment:

| Action class | Acceptance rule |
| --- | --- |
| `google_cloud_run_v2_service` / `google_cloud_run_v2_job` | Exactly zero changes in `foundation`. |
| Existing logging bucket configuration and metadata-only Secrets | Exactly zero `delete,create` replacement actions. Any remaining replacement rejects the plan. |
| Four known Secret-access IAM members | Exactly four `create` actions only if Phase 2 retains their existing absent-and-approved disposition. No delete/replacement and no additional Secret IAM address. |
| All other action types | Must be no-op or appear in a private, resource-family-specific expected-update ledger with a stated source/live reason. Any undeclared create/delete/replacement rejects the plan. |
| Public/broad IAM, secret payload/version, service/tester/migration resources | Exactly zero changes. |

Preserve the action ledger with the binary plan/JSON inventory and compare it mechanically before requesting apply. This converts the present discovery into a repeatable approval control rather than another review discussion.

### Canonical-parent proof and test seam

If Phase 1 proves same-project representation drift, the source-only PR must encode the chosen canonical parent form in one named helper, variable normalization boundary, or exact resource-shape contract rather than repeating ad-hoc project expressions across the five resources. Add a regression that models the observed alternative state representation without private identifiers and proves the corrected source selects the canonical workload parent.

If canonicalization requires a provider-specific import format rather than source HCL, retain the source unchanged and add a private import-binding regression/checkpoint. Do not use source churn merely to make a one-off plan green.

### Single review/PR package

The source-only PR must contain every normal-case closure artifact in one coherent review surface:

1. project-representation correction, if proved necessary;
2. four-IAM disposition test/contract, if its source outcome changes;
3. whole-root deferred-reference sweep/regression;
4. plan action allowlist/check script or reviewable private-record schema; and
5. current value-safe status/docs plus one review handoff whose file inventory is derived from the actual diff.

Routine test/validator/runbook corrections discovered during that sequence remain in this PR. Do not create another planning PR for them. Only a true cross-project result, changed authority boundary, provider/state migration, or unavoidable destructive transition escapes this plan.

### Exact exit criteria

This plan is complete—and the next step is a separately approved new foundation plan generation, not more planning—when all of the following are true:

- each of the five replacements has a conclusive same-project disposition and no replacement remains in a regenerated plan;
- the four IAM rows have one accepted disposition each, with no duplicate Terraform owner;
- the root sweep finds no unguarded foundation-evaluated deferred reference;
- the new binary plan/JSON inventory passes the action allowlist and has zero workload changes; and
- exact source/lock/input/backend/state/recovery bindings are recorded for that new plan.

## Downstream continuation package — no normal replanning after foundation

This plan deliberately carries the verified foundation outcome into the already accepted private-synthetic activation sequence. The following are **predeclared execution gates**, not invitations to start a new planning cycle after the reconciliation PR. Each still requires its own hazardous operational approval and exact artifacts; none authorizes another gate by implication.

### Gate F — foundation apply and verification

After the regenerated plan satisfies the action allowlist:

1. obtain explicit approval to apply that exact binary foundation plan only;
2. apply only the reviewed saved artifact;
3. immediately run the foundation verifier and private state/IAM/cost/logging readback;
4. record the non-executable foundation outcome and stop.

**Exit contract:** no Cloud Run service/job, no Secret version, no database, no image publication, no tester access, and no unexplained replacement/deletion.

### Gate P — immutable image publication and verification

After verified foundation completion, use the existing reviewed build/publish contract rather than designing another publishing workflow.

1. select the exact merged application commit and run its existing local/CI build, SBOM, provenance, and signature prerequisites;
2. obtain separate approval to publish one immutable `linux/amd64` image through the exact protected workflow/identity path;
3. capture the immutable digest plus keyless Cosign/SLSA/image-SBOM/application-SBOM evidence privately;
4. verify the artifact-verifier/deployer authority separation already established by A5; stop before any deployment.

**Exit contract:** one verified digest, no mutable-tag deployment authority, no service rollout, and no secret/database action.

### Gate S — out-of-band Secret version preparation

After the immutable digest is verified, prepare only the approved Secret versions under a separate custody approval.

1. bind the exact Secret metadata parents, payload custody method, named operator, and evidence location privately;
2. create/read back only the approved payload versions; never place payloads in Terraform source, state, plan JSON, GitHub logs, chat, or ordinary docs;
3. confirm the foundation-approved Secret IAM surface remains exact and that version creation has not created a database login, migration execution, or service deployment.

**Exit contract:** approved private versions exist with no payload disclosure; no Cloud SQL login, migration, or service change has occurred.

### Gate M — migration-stage plan, database authority, and one migration execution

After Gate P and Gate S, follow the existing migration source contract without replanning its workflow.

1. generate and review a distinct `migration` saved plan bound to the verified image digest and private Secret references; it must contain the migration job and no Cloud Run service;
2. obtain separate migration-plan apply approval and apply only that exact artifact;
3. under a separate database-authority approval, prepare/read back the reviewed non-login role chain and verify it through the non-echoing authority verifier;
4. obtain a separate one-time migration execution approval; execute once, then record advisory-lock, schema-version, compatibility, and migration-success receipt evidence;
5. stop before service-plan generation.

**Exit contract:** migration job configuration, private network/database authority, digest, and Secret references are verified; successful migration evidence exists; no Cloud Run service or tester access is activated.

### Gate SV — service plan, named tester access, and qualification

The next predeclared stage after successful migration is a separate `service` plan/apply gate, followed by named IAM-private tester access and bounded fictional-synthetic qualification. It retains independent approvals for service apply, tester grant, qualification, human browser/accessibility/language review, and any production decision.

### Continuity rule

A source-only fix, validator adjustment, runbook correction, evidence-schema refinement, or review remediation discovered inside Gates F/P/S/M/SV stays inside this outcome plan and its ordered implementation PR sequence. Do not start a new planning PR merely because a routine implementation detail needs correction.

Return to planning only for an actual architecture/trust/data/identity/vendor/schema/cloud-authority change, infeasible execution path, destructive transition not already reviewed, or user/client feedback that changes the target workflow.

## Material replanning triggers

Create a new outcome plan only if the bounded comparison proves cross-project ownership, requires a new trust/identity model, changes the Secret-access authority boundary, requires state migration/provider upgrade, or requires any destructive transition. A routine representation correction and its review PR stay inside this plan.
