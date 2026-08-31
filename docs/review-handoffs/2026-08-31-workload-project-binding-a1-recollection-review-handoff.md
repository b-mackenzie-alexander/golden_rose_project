# Workload-project binding / A1 recollection review handoff

**Date:** 2026-08-31
**Branch:** `docs/workload-project-binding-a1-recollection`
**PR base:** `develop`
**Exact base:** `origin/develop@de15b267fa8b379444f83352b9ec114c1dcc19bb` (PR #57 merge)
**Review surface:** uncommitted local working tree; zero commits ahead of `origin/develop`
**Private evidence:** operator-held custody, billing, and A1 records; no private identifiers belong in this review surface.

## Purpose

Review the documentation-only binding/A1-recollection packet and living-document realignment after PR #57. The existing dedicated workload project is the accepted disposable target. This slice prohibits another project-creation transaction and preserves every later cloud, state, Terraform, deployment, tester, qualification, live-data, and production gate.

## Changed review surface

### Decision packet
- `.hermes/plans/2026-08-31_161200-workload-project-binding-a1-recollection-decision-plan.md`

### Living and operational documents
- `docs/review-handoffs/2026-08-31-workload-project-binding-a1-recollection-review-handoff.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `README.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `infra/gcp/README.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`

## Reviewed contract

1. The existing dedicated workload project is the sole disposable workload target; its identifier, billing details, and private evidence stay outside tracked source.
2. The duplicate project under deletion is excluded from binding, inventory, Terraform, and lifecycle decisions.
3. The packet prohibits project creation, billing or label mutation, API enablement, IAM changes, resource creation, state/backend activity, Terraform, and runtime activity.
4. WP-1 is source-only independent review and protected publication.
5. WP-2 remains a separately approved, private, read-only custody/billing/parent/label readback; it has no mutation authority.
6. WP-3 is a separately approved full A1 recollection against exactly the control-plane and confirmed workload projects.
7. A2 provenance/import, bootstrap-root adoption, workload-root adoption, augmentation, saved plans, applies, publication, migration, service activation, tester access, qualification, live/client data, and production remain distinct gates.

## Independent-review remediation

The first independent review returned **CHANGES REQUIRED**: the original header could be read as allowing packet acceptance plus private inputs to substitute for the separate WP-2/WP-3 approvals. The packet now states that acceptance/merge authorizes **only WP-1**, and that each of WP-2 and WP-3 requires its own explicit, separately recorded approval before any cloud readback or collection command. A fresh independent rereview returned **PASS** with no Blocker, High, or Medium finding.

## Living-document alignment

`CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `SECURITY.md`, `TECHNOLOGY_DECISIONS.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `README.md`, the repository instruction file, and active GCP runbooks now record PR #57's A1 closure and the binding → A1 recollection → A2/adoption order. Historical PR #57 handoff material and earlier dated Notes entries retain their original historical wording; the later dated direction is the active authority.

## Verification evidence

```text
env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q
```

Observed: `264 passed in 59.48s`.

```text
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
terraform fmt -check -recursive infra/gcp
git diff --check
```

Observed: Terraform static validation and formatting checks passed; diff hygiene passed. `gitleaks dir --no-banner --redact --report-format json --report-path /tmp/golden-rose-binding-working-tree-gitleaks.json .` also completed with zero findings.

## Reviewer focus

1. Confirm the existing-target decision contains no residual project-creation or candidate-substitution authority.
2. Confirm WP-2 is strictly read-only and that WP-3, A2, state adoption, and later gates remain explicitly separate.
3. Confirm all active status surfaces agree on the sequence and do not disclose project IDs, billing IDs, principals, credentials, raw evidence, or other private values.
4. Distinguish deliberately preserved historical evidence from active status claims.
5. Confirm no Markdown/runbook wording implies an approved cloud operation or production readiness.

## Review-surface caveats and stop boundary

- This is an uncommitted working-tree review, not a committed PR range.
- The exact PR-range Gitleaks scan has not run because no new commit exists yet.
- Review/remediate first. After review clearance: stage the decision packet, this handoff, and every other file listed above; commit the exact reviewed surface, run final-head checks and exact-range Gitleaks, then push and open a docs-only PR to `develop`.
- No cloud operation, project selection/mutation, state operation, Terraform plan/apply, deployment, tester access, live-data action, or production action is authorized.

## Requested verdict

Return **PASS** or **CHANGES REQUIRED** with severity, exact path/line, rationale, and minimum remediation. This review does not authorize commit, push, PR creation, or any operational gate.
