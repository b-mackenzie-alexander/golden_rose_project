# Bootstrap plan no-op convergence review handoff

## Objective

Review the source-only correction prompted by the withheld bootstrap one-create plan so a later fresh plan can contain only `google_service_account_iam_member.provisioner_operator_token_creator` and every existing managed address remains no-op.

## Source of truth

- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md`
- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`

## Branch topology

- Branch: `fix/bootstrap-plan-noop-convergence`
- Base: protected `develop@436b6e13bae653ef78062299586008777f7718d5`
- Surface: uncommitted source-only working tree
- The withheld bootstrap binary plan and all raw provider/state evidence remain private and outside Git

## Observed operational trigger

The approved bootstrap plan-generation packet completed initialization, state readback, and binary/JSON plan generation, then stopped before apply. Mechanical admission found the permitted IAM-member create plus two prohibited in-place updates:

1. the WIF provider condition differed only by whitespace representation—the reviewed Boolean contract was semantically identical, but source rendered multiline text while the provider retained one canonical line;
2. the artifact-verifier service-account description differed from observed live metadata.

The plan is withheld and non-reusable. Its one-use generation approval is consumed. No apply, IAM mutation, token mint, migration action, or downstream action occurred.

## Implemented correction

- `infra/gcp/bootstrap/wif.tf` renders the same exact repository/owner/ref/environment/event/workflow trust condition in provider-canonical single-line form.
- `infra/gcp/bootstrap/iam.tf` preserves the observed non-sensitive artifact-verifier description so metadata remains no-op.
- `scripts/validate_terraform_static.py` parses exactly one effective HCL provider resource, rejects duplicate attributes and decoded-equivalent mapping keys from the pre-collapse syntax tree, and exact-binds its complete field set, target references, provider identity metadata, OIDC issuer, seven-entry attribute mapping, and decoded canonical condition; comments, decoys, and escaped-key aliases cannot satisfy the boundary.
- `tests/unit/test_terraform_hygiene.py` adds the provider/live no-op representation regression, updates adversarial WIF mutations to modify decoded effective values rather than relying on the retired heredoc shape, and proves canonical comment decoys, literal duplicate keys, escaped-key aliases, or anomalous computed keys cannot hide condition, issuer, or workflow-ref mapping substitution.
- Living docs record the consumed approval, withheld plan, source-only correction, and fresh-merge/rebind requirement.

## Exact review surface — 10 files

- `CURRENT_WORK.md`
- `NOTES.md`
- `ROADMAP.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `docs/review-handoffs/2026-09-04-bootstrap-plan-noop-convergence-review-handoff.md`
- `infra/gcp/bootstrap/iam.tf`
- `infra/gcp/bootstrap/wif.tf`
- `scripts/validate_terraform_static.py`
- `tests/unit/test_terraform_hygiene.py`

## Validation already run

- Focused provider-canonical/no-op plus WIF negative matrix: passed.
- Focused parsed-effective-resource/comment-decoy matrix: `7 passed`.
- Focused duplicate/anomalous authority-field matrix: `5 passed`.
- Combined foundation-verifier/Terraform-hygiene suite: `385 passed`.
- Full unit suite: `667 passed, 1 existing deprecation warning`.
- Terraform static validation: passed.
- Backend-free bootstrap initialization/validation: passed.
- `terraform fmt -check -recursive infra/gcp`: passed.
- Focused Ruff format/check: passed.
- `mypy src tests`: passed for 83 source files.
- `uv lock --check`: passed.
- Working-tree Gitleaks: no leaks.
- `git diff --check`: passed.

## Independent review history

The first source/IAM and documentation/security reviews independently found the same High: the initial validator used a first-match raw-text regex, so a canonical condition in a preceding comment could hide a computed or heredoc effective condition. Focused RED evidence reproduced both bypasses. After condition parsing was remediated, fresh source/IAM rereview found the same class remained for raw-substring OIDC issuer and workflow-ref mapping checks. Two additional RED cases reproduced those decoys. After complete effective-resource parsing was added, the next source/IAM rereview found that `python-hcl2` collapses duplicate authority-bearing keys to their final value; duplicate `attribute_condition`, OIDC issuer, and workflow-ref mapping fixtures reproduced the bypass. Pre-parse syntax-tree duplicate detection closed those literal-key cases. The next rereview found escaped HCL object keys were compared lexically; one RED reproduced the semantically duplicate escaped workflow-ref key and key decoding closed it. Final rereview then found the duplicate/anomalous flag could be reset after a non-decodable computed object key; one RED reproduced that path and the reduction now preserves any earlier fail-closed result. The validator exact-binds the complete provider field set, OIDC issuer, attribute mapping, target references, metadata, and decoded literal condition. All nine adversarial bypass cases are GREEN. Fresh final rereview must assess the complete remediated 10-file surface.

## Primary review focus

1. The single-line condition is byte-compatible with the provider-observed representation while preserving the exact accepted WIF trust semantics.
2. Static validation parses the effective value and cannot be bypassed by escaped strings, comments, heredocs, wildcards, additive clauses, or decoys.
3. Preserving the observed artifact-verifier description changes no IAM or identity authority.
4. The correction does not conceal or authorize the intended IAM create; it only removes two unrelated plan actions.
5. Status surfaces do not imply plan retry, apply, token mint, migration, or downstream authority.

## Final independent rereview

Fresh source/IAM and documentation/security rereviews of the complete remediated 10-file surface returned CLEAN with zero Blocker, High, Medium, or Low findings. Reviewers made no edits and ran no cloud, backend, state, plan, apply, or private-evidence operation.

## Hard constraints

- Review is source-only and cloud-blind.
- Do not authenticate to GCP, initialize a backend, access remote state, generate/retry a plan, apply Terraform, mutate IAM, or mint a token during review.
- Do not copy private principals, project/backend/state identifiers, tfvars, plan values, or raw provider output into Git, review comments, or ordinary evidence.
- Any Blocker/High or substantiated Medium requires remediation and fresh rereview before commit/push/PR.
- After protected merge, invalidate all current private packet hashes and prepare a fresh separately reviewed/approved one-create plan-generation request.
