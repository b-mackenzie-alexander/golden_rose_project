# FinOps Budget Ownership Separation Planning Review Handoff

**Status:** Accepted planning packet published in open PR #79; CI remediation reviewed CLEAN and locally green
**Base:** protected `develop@f41e2756c820abc736c52739c6a67390107afb7f`
**Authority:** Documentation/planning only; no implementation or cloud/state authority

## Trigger

A reviewed migration plan-generation run authenticated the named human and minted the provisioner token, then stopped during Terraform initialization before state read or plan generation. Explicit quota attribution requires `serviceusage.services.use` for the provisioner, which conflicts with the accepted prohibition on project-level provisioner authority. Both private approvals are consumed; no retry or mutation is authorized.

Beatrice selected separation of Billing Budget ownership into a billing-authorized control-plane/FinOps root.

## Review surface

Exact tracked modifications:

- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `ROADMAP.md`
- `README.md`
- `infra/gcp/README.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `docs/adr/README.md`

Exact new planning artifacts:

- `docs/adr/ADR-0015-finops-budget-ownership-separation.md`
- `.hermes/plans/2026-09-07_finops-budget-ownership-separation-plan.md`
- `docs/review-handoffs/2026-09-07-finops-budget-ownership-separation-plan-review-handoff.md`

## Required independent reviews

1. **Architecture/security:** no project-level workload-provisioner authority; exact billing-human/FinOps ownership; no ambient fallback or mixed-token path; explicit cross-root gate and privacy boundaries.
2. **Terraform/state transfer:** three distinct backends/locks/lineages; import-before-remove safety; one final state owner; no live replacement; complete failure/recovery handling.
3. **Plan executability/governance:** outcome-scale PR/gate sequence; exact files and TDD nodes; no implementation-before-planning-merge; normal downstream ADR-0013 continuation; material replanning triggers.

## Acceptance questions

- Does the packet preserve one staged workload root while separating only billing-account resource ownership?
- Can the exact existing budget move without replacement or live mutation?
- Is the dedicated state bucket's authoritative IAM exactly one `roles/storage.objectAdmin` binding with two distinct named-human members, with inherited access and prohibited identities proved separately?
- Is every billing-human collector/Terraform path forced through the same fail-before-call credential runner?
- Is temporary dual-state ownership bounded by a no-plan/no-apply freeze and deterministic cleanup?
- Is the signed FinOps receipt stored/published owner-only and atomically, and is nonce consumption cross-process atomic and permanently one-use?
- Are failure and rollback/recovery paths exact enough to prevent state repair improvisation?
- Does the plan avoid smuggling implementation or cloud approval into planning acceptance?

## Acceptance and hash transition

The fifth substantive review round (`deleg_e2f5fe26`) returned CLEAN in all three lanes:

- architecture/security: CLEAN
- Terraform/state transfer: CLEAN
- plan executability/governance: CLEAN

Beatrice then explicitly accepted the reviewed contract on 2026-09-07. The exact pre-acceptance reviewed artifact hashes were:

- ADR: `d058a90b0a6c47c61df79f67179ff9ddea82ed3765ad7e8de973b60796562d90`
- plan: `2fc25d8c4a71b7fc995ddcc090e4aa67661c393674938225b194a342e07c1f23`

The accepted-publication artifacts differ only because their status/approval prose now records that completed acceptance and publication remains pending; the technical contract is unchanged. Their current hashes are:

- ADR: `764b2e4b295b9685f1f966b4841faf0d062a487734a3b94674376c1971b03e91`
- plan: `65850c60eb7088df437b56138ba0334712562abe968600f4dc02aa0db393c34a`

The first focused status-delta review found stale Proposed wording and this missing hash transition; those Medium findings were remediated. Final focused review `deleg_c3a0cbd0` returned CLEAN. Beatrice explicitly confirmed the current accepted-publication hashes and authorized only the exact 16-file documentation branch/commit/push/PR publication; merge and every implementation/operational action remain unauthorized.

## PR #79 CI remediation

The first pushed head `94afcb33f94d981c853a8390834be7ee86a53284` failed two jobs at one shared assertion:

- Terraform static validation run `34149726459`
- Application quality run `34149726411`
- exact failing node: `tests/unit/test_terraform_hygiene.py::test_gcp_bootstrap_provisioner_local_operator_impersonation_is_exact_and_resource_scoped`

The accepted runbook rewrite changed the provisioner transition from future tense to completed PR #78 history but removed five literal phrases retained as a static contract. The narrow correction restores those phrases in a truthful completed-history paragraph. No Terraform/product source, test, workflow, accepted ADR/plan hash, or cloud authority changed. Local RED reproduced the exact assertion; local GREEN is `1 passed`, followed by `299 passed` for the complete Terraform hygiene file.

## Current stop

The remediation is committed at `1ca2041966a705b290683e29501a4b8d2c06ca15`, received CLEAN technical/governance and exact-head rereview except for this status-only Medium, and passed final-head Terraform hygiene (`299 passed`), range diff hygiene, unchanged ADR/plan hashes, and two-commit Gitleaks with no leaks. It may be pushed under the existing exact PR-publication authority. Do not merge, edit Terraform implementation, authenticate to GCP, initialize a backend, read/mutate state, generate/apply a plan, or run migration/downstream work without later separate authority.
