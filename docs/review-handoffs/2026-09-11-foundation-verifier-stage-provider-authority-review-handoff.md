# Foundation verifier stage/provider authority remediation review handoff

## Delivery lock
- Golden Rose has one independent developer; agent reviews are quality evidence, not human-quorum authorization.
- The mandatory next outcome remains a durable fictional-synthetic GCP `develop` environment Beatrice can exercise in a browser.
- Source must merge through protected `develop`; cloud work resumes only under one fresh exact eight-hour packet.
- Do not restore Gate E0, per-command approvals, signer/attestor machinery, immediate FinOps separation, named-IAM-only access, human quorum, or production backup/recovery gates.

## Objective
Review the bounded source correction for the first packet's A02 live-foundation-verifier stop. No new implementation plan was created; the existing outcome plan and Beatrice's explicit source-remediation authorization control this slice.

## Source of truth and topology
- Review base: protected `develop@58ea1cfe3b88ac9580971ed44b9cf0814824abf8`, merged by PR #86.
- Active branch: `fix/foundation-verifier-stage-provider-authority`.
- Governing procedure: `deploy/gcp/first-deployment-runbook.md`.
- Private raw evidence remains outside Git; this handoff is value-safe.

## Observed packet stop
- A00 packet admission passed.
- A01 named-human active/ADC equality, exact quota-bootstrap permission checks, and non-echoing provisioner-token mint passed.
- A02 created and exact-read back only the exact one-permission quota custom role and its sole provisioner binding.
- The mandatory post-quota verifier then reported five stage/provider-authority contradictions and stopped the packet before A03.
- The one-use approval is consumed. No backend initialization/import/state access, Terraform plan/apply, image publication, Secret payload, database, migration, Cloud Run job/service, public access, qualification, live/client-data, or production action followed.

## Scope and implemented behavior
1. `foundation` mode now expects only the already-established runtime and migration workload identities and key inventories; the live collector does not manufacture a database-verifier entry. The database-verifier identity remains mandatory in `migration` and `service` modes.
2. `foundation` project IAM expects runtime/migration Cloud SQL Client members without prematurely requiring the database verifier.
3. `foundation` Secret IAM exact-checks the existing migration/runtime consumers while rejecting missing, extra, or database-verifier members before migration stage.
4. `--provider-operator-principal` is required and separately modeled from `--provisioner-operator-principal`.
5. A direct `roles/owner` binding is tolerated only when its complete membership equals that exact named `user:` provider operator. Other basic roles, wrong users, extra members, and nonhuman principals still fail closed.
6. Runbooks and current continuity surfaces record the stopped/consumed packet, exact sole mutation, remediation lane, and fresh-packet boundary.

## TDD evidence
- RED: `test_foundation_mode_accepts_database_verifier_absence_and_existing_secret_consumers` failed on premature service-account, Secret-IAM, and Cloud-SQL-member expectations.
- GREEN: the focused stage test passed after stage-aware expectations.
- RED: `test_foundation_mode_accepts_exact_named_human_provider_owner` failed on basic-role/project-IAM rejection.
- GREEN: the focused provider test passed after the exact named-human exception.
- Four wrong/extra/nonhuman provider cases passed immediately as negative regressions and remain fail-closed coverage.
- RED→GREEN: the runbook contract test required the new explicit `--provider-operator-principal` handoff.

## First rereview findings and remediation
- Architecture/security found one Medium because foundation key collection/evaluation still used service-mode defaults and manufactured a deferred database-verifier key entry. `test_foundation_mode_key_inventory_omits_deferred_database_verifier` observed RED. Mode now flows through the live runner and key/IAM expectations; the node is GREEN.
- Architecture/security found one Medium because exact foundation Secret-IAM behavior lacked negative regressions. Missing policy, extra member, and premature database-verifier membership now have explicit foundation-mode coverage and passed immediately against the existing fail-closed implementation.
- The first Terraform/deployment reviewer timed out without a verdict and is not counted. A fresh replacement Terraform/deployment rereview returned `PASS` with no findings.
- A second architecture/security rereview found one Medium because the corrected live-runner mode forwarding was not directly regression-pinned. The foundation main-path test now asserts the runner receives `foundation`, and a fake-gcloud live-runner regression proves key/IAM collection does not query or manufacture the deferred database-verifier identity. Both nodes passed immediately against the corrected code.
- Fresh final architecture/security rereview returned `PASS` with no Blocker, High, or Medium. The replacement Terraform/deployment rereview had already returned `PASS`; a later test/docs-only confirmation attempt was blocked by missing terminal consent, asserted no defect, and is not counted.

## Validation already run
- `env -u PYTHONPATH uv run pytest tests/unit/test_verify_gcp_foundation.py -q` — `123 passed`.
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q` — `303 passed`.
- `env -u PYTHONPATH uv run pytest tests/unit -q` — `733 passed`, one inherited Starlette deprecation warning.
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` — passed.
- Both Terraform roots initialized backend-free with readonly lockfiles and validated; recursive `terraform fmt -check` passed.
- Repository-wide Ruff format/check passed.
- `env -u PYTHONPATH uv run mypy src tests scripts/verify_gcp_foundation.py` — passed for `88` source files.
- Bandit over `src` passed with the existing acknowledged `B104` nosec warning.
- `git diff --check` — passed.

## Review surface
1. `AGENTS.md`
2. `ARCHITECTURE.md`
3. `CURRENT_WORK.md`
4. `GIT_WORKFLOW.md`
5. `NOTES.md`
6. `README.md`
7. `ROADMAP.md`
8. `SECURITY.md`
9. `TECHNICAL_REQUIREMENTS.md`
10. `TECHNOLOGY_DECISIONS.md`
11. `deploy/gcp/bootstrap-state-runbook.md`
12. `deploy/gcp/first-deployment-runbook.md`
13. `deploy/gcp/private-tester-access.md`
14. `deploy/gcp/staged-plan-approval.md`
15. `docs/adr/README.md`
16. `infra/gcp/README.md`
17. `scripts/verify_gcp_foundation.py`
18. `tests/unit/test_terraform_hygiene.py`
19. `tests/unit/test_verify_gcp_foundation.py`
20. `docs/review-handoffs/2026-09-11-foundation-verifier-stage-provider-authority-review-handoff.md`

## Primary review focus
- Stage-aware identity, key, project-IAM, and Secret-IAM semantics remain internally consistent.
- The provider-owner exception is exact and cannot admit a wrong/extra member, another basic role, a group, or a service account.
- Provider authority does not broaden or replace backend-only provisioner impersonation.
- Historical packet evidence remains preserved and non-reusable.
- No wording splits a future fresh packet into command-level approvals or implies cloud work may resume before a new approval.

## Hard stop
Do not authenticate to GCP, touch backend/state, plan/apply/import, publish an image, create Secret payloads/users/database roles, run migration or Cloud Run jobs/services, grant access, or qualify the target from this branch. After clean rereview and protected merge, rebaseline and prepare one fresh exact packet; stop for new explicit one-use approval.
