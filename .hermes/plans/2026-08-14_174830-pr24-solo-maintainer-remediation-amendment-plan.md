# PR #24 solo-maintainer remediation amendment plan

> **For Hermes:** This is a planning-only amendment. Do not edit Terraform, workflows, policy scripts, dependencies, tests, branch protection, or cloud resources from this plan. Publish and accept the replacement decision/plan before creating any implementation branch.

**Goal:** Replace ADR-0010’s impossible independent-review prerequisite with a truthful solo-maintainer control model while preserving the required-CI finding as an accepted, explicitly bounded residual risk and retaining the six implementable static-remediation tasks.

**Architecture:** The repository remains a personal, single-maintainer repository with classic GitHub branch protection. Required same-repository CI contexts remain useful qualification signals but cannot be represented as independent authorization because the pull request may edit their producers. The revised boundary therefore separates (1) local/static quality controls that can be strengthened now from (2) independent-authorization controls that are unavailable and remain open for every future cloud-mutating or deployment action.

**Tech stack:** Markdown ADR/plan/living-doc governance, GitHub classic branch protection, GitHub Actions, Python/pytest static policy harness, Terraform validate-without-apply.

---

## Current evidence and non-negotiable facts

- Live `develop` is clean and equals `origin/develop` at `c5a1380` (merged PR #26).
- The repository has one collaborator/administrator: Beatrice. There is no independent reviewer or CODEOWNER candidate.
- Current committed and live branch-protection posture is truthful for a solo repository: zero required approvals, no CODEOWNER review, no last-push approval, and required contexts `enforce`, `check`, and `application`.
- ADR-0010 section 1 and the original remediation plan make independent reviewer/CODEOWNER evidence a hard prerequisite. That requirement cannot be satisfied in this operating model.
- A same-repository required status (including a new `Terraform static validation` context) remains PR-editable and is therefore a quality gate, not an independent authorization boundary.
- Nothing in this amendment authorizes GCP authentication, project inspection, Terraform plan/apply, API enablement, provisioning, IAM mutation, image push, Cloud SQL use, deployment, service start, public access, real identity, live/client data, or production work.

## Decision to publish

Create a successor ADR and successor implementation plan rather than silently weakening ADR-0010 in place.

1. **Status of finding 1:** Retain the required-CI self-authorization issue as **High / open / accepted residual risk**. Do not call it remediated, mitigated to closure, independently reviewed, or operationally validated.
2. **Solo-maintainer protocol:** Preserve PRs, protected branches, required owned checks, stale-review dismissal, conversation resolution, force-push/deletion prevention, clean branch topology, exact-head local qualification, exact-range secret scanning, and an explicit owner merge rationale. These are defense-in-depth quality controls, not independent approval.
3. **Static validation context:** Add `Terraform static validation` to the committed required-check policy only if its workflow is qualified on the exact implementation PR and the live policy is later applied/read back under a separately authorized action. Describe the context as required quality evidence, never as unmodifiable or independently authoritative.
4. **No CODEOWNERS theater:** Do not create `.github/CODEOWNERS`, set review count to one, require CODEOWNER review, or enable last-push approval while no independent eligible actor exists. Those settings would deadlock or create bypass theater.
5. **Permitted remediation scope:** Re-plan and implement only original Tasks 2–7: semantic parser-based policy validation, deterministic `uv`, Direct VPC/private-SQL static definition, API ordering, backup baseline, and managed Artifact Registry digest authority. Each remains validate-without-apply.
6. **Future cloud boundary:** The open High blocks any future cloud-mutating, deployment, credential, remote-state, WIF/bootstrap, or production gate until an external independently controlled authority becomes available and is separately approved. A later organization-level required workflow/ruleset or independently controlled GitHub App may replace the human reviewer only through another reviewed amendment.

## Task 1: Author the replacement governance ADR

**Objective:** Create a durable decision that makes the solo-maintainer limitation explicit and supersedes only the unattainable independent-review portion of ADR-0010.

**Files:**
- Create: `docs/adr/ADR-0011-pr24-solo-maintainer-remediation-boundary.md`
- Modify: `docs/adr/ADR-0010-pr24-terraform-remediation-boundary.md`
- Modify: `docs/adr/README.md`

**Steps:**
1. Write ADR-0011 with status `Proposed` and identify ADR-0010 section 1 as superseded only after ADR-0011 is accepted and merged.
2. Record the observed single-maintainer/no-independent-authority fact without naming credentials, tokens, emails, or unverified account details.
3. State the residual risk precisely: required same-repository CI is mutable by a PR and does not provide independent authorization.
4. Define the allowed solo-maintainer qualification protocol and the explicit cloud/deployment hard stop.
5. State that Tasks 2–7 are permitted only after documented separate-session/delegated review evidence, but no review is described as an independent GitHub approval or authority boundary.
6. Preserve ADR-0010’s decisions for semantic policy, `uv`, Direct VPC egress, API ordering, backups, and image authority unless a later scoped decision changes them.

**Verification:**
- Review cross-references and statuses across both ADRs.
- Confirm no text says Task 1 is closed, independently authorized, or operationally validated.
- `git diff --check`

## Task 2: Publish a successor exact-node implementation plan

**Objective:** Replace the seven-node plan with a six-task solo-maintainer implementation plan that begins only after the successor ADR/plan merge.

**Files:**
- Create: `.hermes/plans/YYYY-MM-DD_HHMMSS-pr24-solo-maintainer-remediation-implementation-plan.md`
- Modify: `.hermes/plans/2026-08-14_164545-pr24-terraform-remediation-plan.md`

**Steps:**
1. Mark the original plan as superseded for execution after the successor plan is accepted; retain it as historical evidence.
2. Carry forward Tasks 2–7 exactly in their approved sequence, renumbered as implementation Tasks 1–6.
3. Remove all impossible CODEOWNERS/reviewer/bootstrap approval nodes from the executable ledger.
4. Add a first governance test node that asserts the committed policy remains explicitly solo-maintainer (`0` approving reviews; no CODEOWNER/last-push claims) and that the documentation declares required contexts as quality evidence only.
5. Retain exact RED → GREEN requirements for the semantic-policy task; it remains first substantive implementation work.
6. Retain final-head qualification and secret scanning, but label review evidence accurately as solo-maintainer separate-session/delegated review rather than independent GitHub review.
7. Add an explicit stop: after Tasks 1–6 merge, the required-CI High remains open and blocks the bootstrap/state/WIF and all cloud-mutating/deployment lanes.

**Verification:**
- Every executable test selector has an honest expected RED/GREEN classification and minimal GREEN boundary.
- No task depends on an unavailable collaborator, CODEOWNER, or independent approval.
- The plan prohibits cloud authentication and Terraform plan/apply.

## Task 3: Reconcile governance-as-code without false claims

**Objective:** Adjust the intended policy contract to the real solo-maintainer posture while strengthening reliable quality checks where technically valid.

**Files:**
- Modify: `infra/github/repo-policy.json`
- Modify: `infra/github/apply-repo-policy.sh` only if the successor policy schema needs a non-enforceable documentation field removed or test coverage exposes drift
- Modify: `infra/github/verify-repo-policy.sh` only if it must verify the revised factual policy
- Modify: `tests/unit/test_repo_policy_apply_script.py`
- Modify: `tests/unit/test_repo_policy_verify_script.py`
- Modify: `.github/workflows/infrastructure-quality.yml`

**Exact TDD boundary:**
1. Add a failing test that the policy does not claim required approval/CODEOWNER/last-push controls in a solo-maintainer configuration.
2. Add a failing test that the committed quality policy includes `Terraform static validation` once its unconditional workflow producer is implemented and qualified.
3. Make the smallest policy/workflow change that makes the context schedule on every `develop`/`main` pull request.
4. Add/adjust verifier tests so it confirms only live, enforceable fields and never claims workflow immutability or independent authority.
5. Do not apply live GitHub policy from the branch. After merge, require a separately scoped authorization for apply/read-back from protected `develop`.

**Verification:**
```text
env -u PYTHONPATH uv run pytest \
  tests/unit/test_repo_policy_apply_script.py \
  tests/unit/test_repo_policy_verify_script.py -q
```

## Task 4: Execute semantic static-policy remediation first

**Objective:** Retain the original Task 2 as the first substantive implementation task because later CI evidence depends on it.

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `.github/workflows/infrastructure-quality.yml`
- Create: `infra/policy/static-validation-manifest.json`
- Modify: `scripts/validate_terraform_static.py`
- Modify: `tests/unit/test_terraform_hygiene.py`
- Create only when needed: `tests/fixtures/terraform_policy/**`

**Exact TDD boundary:** Carry forward every original Task 2 RED selector and the locked dependency decision (`python-hcl2==8.1.2`, `ruamel.yaml==0.19.1`). Do not begin deterministic `uv` or Terraform resource changes until semantic parsing, duplicate-key rejection, structural workflow allowlisting, and redacted failures have focused GREEN evidence.

**Verification:**
```text
env -u PYTHONPATH uv lock --check
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py
```

## Task 5: Execute the remaining static Terraform tasks vertically

**Objective:** Complete the original Tasks 3–7 one exact node at a time without altering their security boundaries.

**Files:**
- Original Task 3: `.github/workflows/application-quality.yml`, `.github/workflows/infrastructure-quality.yml`, manifest, policy tests
- Original Task 4: `infra/gcp/variables.tf`, `infra/gcp/develop.tf`, `infra/gcp/develop/variables.tf`, `infra/gcp/develop/network.tf`, `infra/gcp/develop/cloud_run.tf`, manifest, policy tests, `infra/gcp/README.md`
- Original Task 5: `infra/gcp/develop/artifact_registry.tf`, `cloud_run.tf`, `cloud_sql.tf`, `identities.tf`, `network.tf`, `secrets.tf`, manifest, policy tests
- Original Task 6: `infra/gcp/develop/cloud_sql.tf`, manifest, policy tests, `infra/gcp/README.md`, `SECURITY.md`
- Original Task 7: `infra/gcp/variables.tf`, `infra/gcp/locals.tf`, `infra/gcp/develop.tf`, `infra/gcp/develop/variables.tf`, `infra/gcp/develop/locals.tf`, `infra/gcp/develop/cloud_run.tf`, manifest, policy tests, `infra/gcp/README.md`

**Exact TDD boundary:**
1. Deterministic `uv`: preserve `0.12.5`, reviewed checksum, identical workflow setup, and pre-use version reporting.
2. Direct VPC: retain a required, non-secret, uncommitted RFC1918 `/26`-or-broader input; add no connector/NAT/public route/public SQL.
3. API ordering: use only exact service dependencies; no sleeps/provisioners/blanket dependency edges.
4. Backups: add only `backup_configuration.enabled = true`; do not claim RTO/RPO, retention, PITR, or restore evidence.
5. Image authority: accept only the prescribed digest syntax and derive the managed Artifact Registry image reference; do not accept arbitrary image references.

**Verification after each task:**
```text
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp graph
env -u PYTHONPATH uv run --locked python scripts/validate_terraform_static.py
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
```

## Task 6: Align every living status surface and publish a planning-only PR

**Objective:** Ensure the repository describes the revised risk and authorization boundary consistently before any implementation branch is created.

**Files:**
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md` (append under the bottom-most current date section)
- Modify: `GIT_WORKFLOW.md`
- Modify: `SECURITY.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify where status claims require it: `README.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `AGENTS.md`, `infra/gcp/README.md`
- Create: `docs/review-handoffs/YYYY-MM-DD-pr24-solo-maintainer-remediation-plan-review-handoff.md`

**Steps:**
1. State that PR #26 merged the original planning packet but that its independent-review prerequisite is unavailable and its execution path is superseded pending this successor packet.
2. Mark the required-CI finding High/open/accepted residual risk. Do not use “remediated,” “cleared,” or “closed.”
3. Mark Tasks 2–7 as planned, not implemented.
4. Restate the no-cloud/no-plan/no-apply/no-deployment hard stop.
5. Replace stale phrases claiming a future real reviewer will be supplied with the selected solo-maintainer protocol and its revisit trigger.
6. Create a review handoff stating that review evidence is advisory/separate-session only and cannot provide the independent GitHub authority missing from the repository.
7. Use a `docs/` branch, publish a planning-only PR to `develop`, run the existing required checks, and record the exact PR/head/check evidence. This PR does not apply GitHub policy or start implementation.

**Verification:**
```text
git diff --check
env -u PYTHONPATH uv run pytest \
  tests/unit/test_repo_policy_apply_script.py \
  tests/unit/test_repo_policy_verify_script.py \
  tests/unit/test_terraform_hygiene.py -q
```

## Post-merge implementation gate

Only after the successor ADR, successor plan, living-doc reconciliation, and planning-only PR merge:

1. fetch/prune and rebaseline exactly from protected `origin/develop`;
2. create a fresh `security/pr24-solo-maintainer-terraform-remediation` branch;
3. update `CURRENT_WORK.md` and `NOTES.md` to name the active implementation lane;
4. begin the exact governance-policy RED node, then semantic-policy RED nodes;
5. preserve the residual High as open in every handoff and review;
6. stop after static remediation/qualification. Do not create or execute a bootstrap/state/WIF implementation packet, cloud credential path, plan/apply, or deployment lane without a later separately accepted decision that resolves the missing independent authority.

## Risks and acceptance criteria

**Residual risk accepted by this amendment:** A repository owner can modify a same-repository required workflow and merge through a zero-approval policy. Required contexts, tests, review artifacts, and clean-head evidence reduce accidental defects but do not create a trust boundary against the repository owner.

**This planning amendment is acceptable only if:**
- it labels the High as open and accepted rather than resolved;
- it never uses CODEOWNERS/required-review configuration as theater;
- it retains all validate-without-apply and no-cloud boundaries;
- it preserves the parser/security remediation order;
- it defines the six static remediation tasks with exact TDD evidence;
- it blocks cloud-mutating/deployment/bootstrap progression pending an independently controlled authority or a separately approved external-control design.
