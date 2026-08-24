# Independent re-review handoff — post-PR33 authority-boundary remediation

**Date:** 2026-08-24 (post-second-rereview remediation)
**Branch:** `fix/post-pr33-deployment-path-remediation`
**Review base:** `origin/develop@fd7b89dd848a1eb12e2eb6ba082d2dcb3d3b8ea0`
**Historical committed head:** `6e11635b4168ee7827462a4a28ad85b509024890`
**Review surface:** current uncommitted working tree above `6e11635`; not pushed, committed, or otherwise promoted
**Cloud status:** no cloud authentication, plan/apply, publication, deployment, or live qualification

## Purpose

Review the remediation of the independent authority-boundary findings reported against the earlier `6e11635` packet. This supersedes `docs/review-handoffs/2026-08-21-post-pr33-remediation-authority-rereview-handoff.md`, which described the pre-remediation working tree.

## Independent rereview disposition

Focused independent rereview of the current uncommitted working tree returned **PASS** with no remaining Blocker, High, or Medium findings. The reviewer verified foundation-stage Job IAM count safety, migration-receipt contract validation before service activation, service projection ingress/IAM comparison, Cloud Run v2 readiness image extraction, tester authority derivation through signed receipt inputs, direct Cosign v3 DSSE provenance/SBOM semantics, and strict deploy command-body authority. This disposition clears the surface for closeout commit preparation only; exact-head rerun, exact-range secret scan, push/PR, protected CI, and merge remain separate gates.

## Findings remediated in this round

1. **Migration-success linkage:** service transitions now require a separately supplied, Cosign-verified migration-stage receipt and bind the migration-success receipt to that migration receipt SHA-256, not the selected service receipt.
2. **Configuration projection authority:** `scripts/verify_stage_receipt.py` strictly normalizes stage projections and compares them to the full described Terraform-owned Cloud Run job/service projection before migration execution or service readiness.
3. **Exact-resource foundation verification:** `scripts/verify_gcp_foundation.py` now models job/service IAM separately from project IAM, derives the Monitoring service agent from the workload project number, and verifies complete authenticated uptime-check shape.
4. **Direct OCI evidence:** `scripts/verify_deploy_image_authority.py` parses actual Cosign v3 in-toto DSSE payloads and validates provenance BuildKit/source/commit/platform semantics, SPDX package inventory, and application-SBOM checksums bound to the verified digest.
5. **Tester authority derivation:** service-stage Terraform uses the receipt verifier through its external data source and the live verifier independently derives the expected principal; neither accepts a caller-supplied principal/digest pair.
6. **Deploy command-body policy:** all deploy `run:` steps are SHA-256-pinned to the reviewed scripts. Mutation fixtures cover IAM, create/delete, Terraform, secret access, arbitrary `gcloud`, and Cloud Run update attempts.
7. **Foundation and migration-receipt safety:** migration Job IAM is stage-gated with the Job; a Terraform-native foundation count test proves no `[0]` dereference. Service activation validates the full signed migration receipt contract before accepting a hash-bound migration-success receipt.

## Review scope

```text
.github/workflows/deploy-develop.yml
.hermes/plans/2026-08-20_002931-post-pr33-deployment-path-remediation-plan.md
CURRENT_WORK.md
NOTES.md
ROADMAP.md
deploy/gcp/private-tester-access.md
docs/adr/ADR-0013-post-pr33-deployment-path-remediation.md
infra/gcp/develop.tf
infra/gcp/develop/iam.tf
infra/gcp/develop/observability.tf
infra/gcp/develop/variables.tf
infra/gcp/variables.tf
infra/gcp/versions.tf
infra/gcp/.terraform.lock.hcl
infra/gcp/bootstrap/.terraform.lock.hcl
infra/policy/predeployment-authority-manifest.json
docs/review-handoffs/2026-08-24-post-pr33-authority-rereview-handoff.md
scripts/validate_terraform_static.py
scripts/verify_deploy_image_authority.py
scripts/verify_gcp_foundation.py
scripts/verify_stage_receipt.py
scripts/verify_tester_authority_receipt.py
tests/unit/test_deploy_image_authority.py
tests/unit/test_stage_receipt.py
tests/unit/test_tester_authority_receipt.py
tests/unit/test_terraform_hygiene.py
tests/unit/test_verify_gcp_foundation.py
```

## Verified local evidence

- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` — passed.
- `terraform fmt -check -recursive infra/gcp` — passed.
- `terraform -chdir=infra/gcp validate` and `terraform -chdir=infra/gcp/bootstrap validate` — passed.
- `env -u PYTHONPATH uv run ruff format --check .` and `ruff check .` — passed.
- `env -u PYTHONPATH uv run mypy src tests` — `Success: no issues found in 80 source files`.
- `env -u PYTHONPATH uv run bandit -q -r src` — passed (existing scoped `# nosec` warning only).
- Focused authority/static suites — `288 passed`.
- Independent rereview focused authority bundle — `328 passed` during reviewer verification.
- Full service-backed no-cloud suite — `655 passed, 2 warnings in 63.43s` after a disposable loopback PostgreSQL startup and migration upgrade.
- `docker compose down` followed by `docker compose ps -a` — empty listing.

## Review focus

1. Confirm signed migration evidence is fully validated as the current migration-stage receipt before its hash binds service activation.
2. Confirm projection normalization compares every reviewed execution-affecting field before the selected transition.
3. Confirm tester receipt derivation is sufficient and no arbitrary principal/digest input can bypass it.
4. Confirm DSSE statement parsing is appropriate for real Cosign v3 output and checks the required provenance/SBOM semantics rather than synthetic workflow claims.
5. Confirm strict per-step run-body hashes reject arbitrary authority expansion, not only imperative deploy updates.
6. Confirm resource IAM and uptime-agent checks match ADR-0013 Amendment A.
7. Confirm current docs describe an uncommitted review surface and no cloud action.

## Requested verdict

Return **PASS** or **CHANGES REQUIRED** with severity, exact path/line, reproduction, and minimum remediation. Do not treat local test success as authorization to commit, push, create a PR, or proceed to any cloud gate.
