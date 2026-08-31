# A1 live-remediation review handoff

**Date:** 2026-08-31
**Branch:** `docs/a1-post-merge-disposition`
**PR base:** `develop`
**Exact base:** `origin/develop@72c56c471ee015d731adcf5ce38dbf2f5fa4b1e8` (PR #56 merge)
**Review surface:** uncommitted local working tree; zero commits ahead of `origin/develop`
**Private evidence:** operator-held Obsidian A1 records, including `2026-08-31-a1-final-current-source-disposition.md`

## Purpose

Review the source and living-document closeout for the completed A1 private fictional-synthetic foundation reconciliation. The final current-source foundation verifier passed with zero violations using private evidence. This packet does not authorize A2 provenance/import, Terraform backend/state operations, plan/apply, publication, service activation, tester access, client/live data, or production.

## Changed review surface

### Verifier and tests
- `scripts/verify_gcp_foundation.py`
- `tests/unit/test_verify_gcp_foundation.py`

### Living documents
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`

### Existing untracked item, deliberately excluded
- `.hermes/plans/2026-08-31_161200-workload-project-establishment-decision-plan.md` is a pre-existing decision artifact and is not part of this remediation packet unless explicitly added at closeout.

## Implemented contract

1. Normalize the actual `gcloud storage buckets describe` snake-case schema before evaluating versioning, uniform access, public-access prevention, and retention.
2. Derive WIF pool/provider IDs from the CLI resource-name shape while preserving exact mapping and whitespace-normalized condition checks.
3. Exclude provider-managed service accounts from the user-managed workload identity inventory without excluding custom identities.
4. Permit exactly two well-formed retained sinks only when every destination remains inside Cloud Logging; reject another count, malformed metadata, and external exports.
5. Allow the documented active-bootstrap exception only when expected workload IAM remains exact, the enumerated temporary roles belong only to the supplied bootstrap principal, and provider service-agent roles contain service accounts only.
6. Keep ordinary/basic-role rejection active outside that exact `bootstrap-active` exception.

## Live reconciliation evidence

Private readback reconciled the approved labels, WIF, source-defined registry writer/reader boundary, state-bucket protection and temporary bounded bootstrap authority, service-account inventory, and retained logging posture. An empty erroneous registry repository was removed. The final read-only foundation run passed with zero violations. No workload image, Cloud Run service/job, secret payload, database operation, Terraform backend/state operation, plan, apply, tester access, client/live data, or production action occurred.

The master bootstrap exception is bounded technical debt and must be replaced by dedicated state/recovery/operator identities with effective resource-level custody readback before handoff or production.

## Rereview remediation — sink-boundary hardening

The first rereview returned **CHANGES REQUIRED** because retained-sink validation accepted foreign-project and malformed Cloud Logging destinations. That finding is remediated: destinations now require the exact same-project Cloud Logging bucket grammar, names are normalized from the CLI resource path and validated as nonempty sink IDs, and foreign-project, prefix-only, empty-name, and non-Logging destinations have negative regressions.

The second rereview returned **CHANGES REQUIRED** because two copies of one valid sink still met the count-only posture. That finding is remediated: normalized sink IDs are tracked per evaluation and a duplicate emits a logging-sink violation. The new duplicate regression is GREEN.

A fresh rereview is required on this updated exact working-tree surface.

## Verification evidence

```text
env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py tests/unit/test_terraform_hygiene.py -q
```
Observed: `338 passed` after the sink-boundary and duplicate-ID remediations.

```text
env -u PYTHONPATH uv run ruff format --check scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py
env -u PYTHONPATH uv run ruff check scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py
env -u PYTHONPATH uv run mypy --explicit-package-bases scripts/verify_gcp_foundation.py tests/unit/test_verify_gcp_foundation.py
terraform fmt -check -recursive infra/gcp
terraform -chdir=infra/gcp init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp validate
terraform -chdir=infra/gcp/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/gcp/bootstrap validate
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
git diff --check
gitleaks dir . --redact --no-banner
```
Observed: formatter, lint, mypy, both backend-free Terraform validations, static validation, diff hygiene, and working-tree Gitleaks passed.

## Reviewer focus

1. Verify the bootstrap exception remains narrow: active status, exact bootstrap principal, enumerated temporary roles, service-account-only provider roles, and ordinary behavior unchanged otherwise.
2. Verify the GCS and WIF CLI schema adaptations are exact and do not weaken malformed/unknown output handling.
3. Verify the retained-sink rule preserves the no-external-export boundary.
4. Verify provider-managed service-account filtering does not hide custom identities.
5. Verify all living docs accurately state A1 closure, temporary-debt retirement, and A2's separate approval boundary.
6. Verify the packet contains no private identifiers, principals, raw cloud payloads, credentials, or unapproved operational claims.

## Review-surface caveats and stop boundary

- This is an uncommitted working-tree review, not a committed PR range.
- The exact PR-range Gitleaks scan has not run because there is no new commit yet; the passing `gitleaks dir` result covers the current working tree only.
- Review/remediate first. After review clearance: explicitly select tracked files, commit the reviewed surface, run exact-head checks and exact-range Gitleaks, then push and open the PR to `develop`.
- Do not commit the excluded untracked plan without a separate scope decision.

## Requested verdict

Return **PASS** or **CHANGES REQUIRED** with severity, exact path/line, reproduction, and minimum remediation. This review does not authorize commit, push, PR creation, A2, backend/state operations, deployment, or any other later gate.
