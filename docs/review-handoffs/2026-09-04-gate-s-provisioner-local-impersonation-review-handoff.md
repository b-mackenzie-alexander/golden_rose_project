# Gate S / provisioner local-impersonation review handoff

## Objective

Review the combined value-safe Gate P/Gate S/migration-preflight closeout and the contract-preserving source correction that makes the accepted local provisioner path executable without widening project, WIF, key, or workload authority.

## Source of truth

- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `SECURITY.md`
- `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`

## Branch topology

- Branch: `fix/provisioner-local-impersonation-authority`
- Review base: protected `develop@375038efdc28b544dbd0dde09a27def812679af3`
- Surface: uncommitted working tree; no closeout commit, push, or PR exists yet
- Executable source was unchanged during the approved Gate S and migration-input operator actions; the current source correction remains unapplied desired state

## Scope and observed operational evidence

- Gate P remains complete through PR #74 and successful run `33882394981`; PR #75 merged its documentation closeout.
- Gate S was corrected to three executable Secret Manager references. Private custody was established and exactly one `synthetic-staff-id` version was generated non-echoingly and confirmed through metadata-only readback.
- Runtime/migration database-URL versions remain absent until migration-stage Cloud SQL/database and separately approved login roles provide real connection material.
- Approved read-only migration preflight found one unused auto-mode default network. A separately approved exact cleanup removed its four firewall rules and the network after zero-dependency proof; readback confirmed zero remaining networks, subnets, routes, or firewall rules.
- The independently reviewed migration saved-plan request stopped before Terraform initialization because short-lived provisioner impersonation lacked `iam.serviceAccounts.getAccessToken`.
- Exact read-only IAM inspection confirmed no direct provisioner operator Token Creator member. Policy Troubleshooter stayed disabled; no API was enabled.

## Implemented source remediation

- `infra/gcp/bootstrap/variables.tf` adds one required operator-held named `user:` principal with no default.
- `infra/gcp/bootstrap/iam.tf` grants that principal `roles/iam.serviceAccountTokenCreator` only on `google_service_account.provisioner`.
- `infra/policy/predeployment-authority-manifest.json` raises the reviewed service-account IAM-member cardinality from three to four.
- `scripts/validate_terraform_static.py` semantically parses the effective HCL variable/resource and rejects missing/duplicate/drifted fields, decoy comments, WIF substitution, and additional Token Creator authority.
- `scripts/verify_gcp_foundation.py` requires the operator-held principal and verifies exactly one named-user Token Creator member on the provisioner separately from the three WIF identities.
- The verifier tests cover valid, missing, wrong-user, extra-role/member, WIF-substituted, project-wide, malformed, group, and service-account alternatives.
- Runbooks define one bootstrap exception: the existing bootstrap operator may separately plan/apply only a bootstrap plan whose sole create is this exact member; every workload-root Terraform action uses short-lived provisioner impersonation after readback.

## Primary review focus

1. Exact resource-level scope and user-only validation.
2. No project-wide Token Creator, provisioner WIF, service-account key, or ambient-user workload Terraform fallback.
3. No comment/lexical bypass in the new static boundary.
4. Live verifier parity with desired Terraform IAM.
5. Bootstrap plan/apply sequencing is not circular and does not imply approval.
6. Historical PR #49 plan changes are clearly labeled as a 2026-09-04 post-merge disposition candidate.
7. Repo docs contain no private identifiers, payloads, state, plans, or raw provider output.

## Exact review surface — 25 files

- `.hermes/plans/2026-08-27_124046-private-develop-activation-human-feedback-plan.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `NOTES.md`
- `README.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/first-deployment-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md`
- `docs/adr/README.md`
- `docs/review-handoffs/2026-08-27-private-develop-activation-human-feedback-plan-review-handoff.md`
- `docs/review-handoffs/2026-09-04-gate-s-provisioner-local-impersonation-review-handoff.md`
- `infra/gcp/README.md`
- `infra/gcp/bootstrap/iam.tf`
- `infra/gcp/bootstrap/variables.tf`
- `infra/policy/predeployment-authority-manifest.json`
- `scripts/validate_terraform_static.py`
- `scripts/verify_gcp_foundation.py`
- `tests/unit/test_terraform_hygiene.py`
- `tests/unit/test_verify_gcp_foundation.py`

## Validation already run

- Focused new verifier/static matrix: passed.
- `env -u PYTHONPATH uv run pytest tests/unit -q` → `657 passed, 1 warning` after deleting only an accumulated 4.6 GiB pytest temp tree that caused an environment-only no-space setup failure on the first attempt.
- `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py tests/unit/test_terraform_hygiene.py -q` → `375 passed`.
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` → passed.
- Backend-free locked bootstrap and workload Terraform initialization/validation → passed.
- `terraform fmt -check -recursive infra/gcp` → passed.
- Focused Ruff format/check → passed.
- `env -u PYTHONPATH uv run mypy --explicit-package-bases scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py` → passed.
- `env -u PYTHONPATH uv run mypy src tests` → passed for 83 source files.
- Working-tree Gitleaks 8.30.1 → no leaks.
- `git diff --check` → passed.

## Final independent review

The exact 25-file working tree received CLEAN source/IAM and CLEAN documentation/security verdicts after all findings were remediated. This review authorizes no IAM or Terraform operation.

## Hard constraints

- No IAM mutation, bootstrap plan/apply, backend-enabled or cloud-connected workload Terraform initialization, remote state access, workload plan/apply, database login role, database-URL Secret version, migration execution, service activation, tester access, qualification, live/client data, or production action is authorized by this branch. Backend-free local initialization used only for static validation remains permitted.
- High/Blocker findings require remediation and fresh rereview before commit/push/PR.
- After merge, invalidate and rebind private source/input/request artifacts before requesting the separate bootstrap saved-plan generation gate.
