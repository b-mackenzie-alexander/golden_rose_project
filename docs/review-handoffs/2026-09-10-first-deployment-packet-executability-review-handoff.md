# First-deployment packet executability review handoff

## Delivery lock
- Golden Rose has one independent developer. Agent reviews are quality evidence, not human-quorum authorization.
- The mandatory outcome remains a durable fictional-synthetic GCP `develop` environment Beatrice can exercise in a browser.
- Delivery remains one merged remediation source PR followed by one separately approved, exact, eight-hour deployment packet.
- Do not restore Gate E0, per-command approvals, signed receipt/attestor machinery, immediate FinOps separation, named-IAM-only tester access, human quorum, or production backup/recovery gates.
- This review authorizes no cloud authentication or operation.

## Objective
Audit the bounded remediation that makes the first-deployment packet executable without widening its accepted trust, data, cost, exposure, or approval boundaries.

## Source of truth
- Current base: protected `develop@63ac29b20314f03381d4a71e901a68ee51e913aa`, merged by PR #84.
- Active branch: `fix/first-deployment-packet-executability`.
- Governing decisions: ADR-0013, ADR-0014, and ADR-0016's 2026-09-09 human-visible addendum.
- Operator procedure: `deploy/gcp/first-deployment-runbook.md`.

## Implemented behavior
- Separates GCS backend-only provisioner impersonation from prechecked named-human Google provider authority.
- Makes privileged database role bootstrap a one-time clean-database transition; initialized databases skip it and partial authority state fails closed.
- Adds one private, no-ingress, one-task `verify-database-authority` Cloud Run job using a dedicated service account.
- Limits that verifier identity to Cloud SQL Client and exact reads of migration/runtime database URL Secrets; it receives no log-writer or metric-writer project roles.
- Executes and reads back the exact verifier job through a distinct deployment-workflow stage before service activation.
- Constrains all three Terraform database role inputs to exact application contracts.
- Accepts both canonical Cloud Run service URL forms while retaining exact expected-URL equality and all existing scheme/authority/path/query/fragment restrictions.
- Reconciles Terraform/static-policy/verifier resource inventories and living status/runbook surfaces.

## Primary review focus
### Architecture/security
- Does backend/provider separation give the named human only the already-required provider path without broadening the provisioner?
- Is the clean/initialized/partial database authority state machine fail-closed and recurrence-safe?
- Is the verifier job private, immutable-image-bound, VPC-connected, no-override, and least-privilege?
- Can either database URL payload leak through argv, logs, Terraform, workflow output, or ordinary evidence?
- Did any historical FinOps, named-IAM-only tester, human-quorum, or per-command gate silently return?

### Terraform/deployment authority
- Are both jobs stage-gated and exactly inventoried in source, workflow, static policy, and live verifier?
- Does the workflow inspect exact image, identity, command, task/retry/timeout, VPC, environment/Secret bindings, and waited execution before accepting authority verification?
- Are manifest ceilings exact rather than broad?
- Does the runbook remain one packet with internal stop/readback boundaries and no cloud authority before explicit approval?
- Are both canonical Cloud Run URL grammars accepted without accepting adjacent authorities?

## Validation already run
- Full backend: `893 passed`, 96.03% coverage, four inherited warnings.
- Full integration: `176 passed`; exact initialized-database restricted-login regression passed.
- Frontend verify: `116 passed`; lockfile, lint, typecheck, coverage, and build passed.
- Ruff format/check and focused mypy: passed.
- Terraform formatting, backend-free initialization/validation for workload and bootstrap roots, and static policy: passed.
- Bandit over `src`, pip-audit, npm audit, frontend/backend SBOM generation and validation: passed.
- Disposable PostgreSQL service/network: removed; Docker Desktop restored to stopped state after DB qualification.
- Local no-push image build/inspection: passed. The `amd64` deployment image retained `golden-rose-run`, ran as `goldenrose`/UID 10001, contained `/app/scripts/verify_database_authority.py`, and failed closed with bounded output when verifier credentials were absent. The run-owned image was removed and Docker Desktop returned to stopped; the ARM64 host emitted the expected cross-platform warning.

## First review and remediation
- Architecture/security: `CHANGES REQUIRED` — one High (live verifier omission) and one Medium (name-only initialized-role inference).
- Terraform/deployment: `CHANGES REQUIRED` — two High (live verifier omission; incomplete workflow readback) and one Medium (non-exact manifest ceilings).
- Remediation now exact-inventories both jobs, verifier job/IAM/Secret IAM, workflow labels/args/duplicate env/project-qualified VPC fields, initialized PostgreSQL role attributes/memberships, and actual manifest maxima.
- Reviewer reproductions were observed RED before the fixes. Post-remediation unit tests passed with `720 passed`; Terraform hygiene passed with `303 passed`; the affected live PostgreSQL suite ultimately passed with `16 passed`; Terraform/static/Ruff/mypy/diff checks passed.
- Second architecture/security rereview: prior High closed; one Medium remained because outgoing grants to governed roles/current login were not inventoried. A real PostgreSQL RED accepted `pg_read_all_data` grants to schema-owner, runtime, and migration-login before Alembic.
- Second remediation exact-binds the complete outgoing membership set to only owner→migrator and migrator→current login. The expanded database-authority suite passed with `16 passed`.
- Next rereview: architecture/security `PASS`; Terraform/deployment found one High because the runbook retired temporary bootstrap membership after, rather than before, the restricted rerun.
- Final sequence remediation moves temporary Secret/user/membership retirement and exact readback before the restricted rerun. A focused runbook-order test observed RED then passed. A production-shaped PostgreSQL regression proved the rerun fails with `78` before retirement and succeeds afterward. Full backend qualification passed with `901 passed` and 96.03% coverage.
- Following rereview: architecture/security `PASS`; Terraform/deployment found one High in migration-job VPC/args readback and one Medium in disabled-versus-absent Secret wording/test coverage. New unit nodes observed RED. Live/workflow migration checks now exact-bind container count, absent args, project-qualified VPC identities, duplicate-free environment, and exact labels; the workflow hash was refreshed. Runbook/tests now bind Secret disablement, user/membership absence, readback, and one-packet ordering.
- Next architecture/security rereview found one Medium: ancestor-policy evaluation did not reject direct inherited authority for the database-verifier identity. A negative node observed RED; ancestor evaluation now rejects direct inherited bindings to all three workload identities. The paired Terraform/deployment review was command-timeout blocked after source inspection, so it issued no verdict.
- Final architecture/security rereview: `PASS`; no current-target Blocker/High/Medium.
- Final Terraform/deployment-authority rereview: `PASS`; both workflow hashes, both Terraform roots, static policy, all prior findings, and the exact 35-path inventory were independently verified. No current-target Blocker/High/Medium remains.

## Exact review surface
1. `.github/workflows/deploy-develop.yml`
2. `AGENTS.md`
3. `ARCHITECTURE.md`
4. `CURRENT_WORK.md`
5. `Dockerfile`
6. `GIT_WORKFLOW.md`
7. `NOTES.md`
8. `README.md`
9. `ROADMAP.md`
10. `SECURITY.md`
11. `TECHNICAL_REQUIREMENTS.md`
12. `TECHNOLOGY_DECISIONS.md`
13. `deploy/gcp/bootstrap-state-runbook.md`
14. `deploy/gcp/evidence-template.md`
15. `deploy/gcp/first-deployment-runbook.md`
16. `deploy/gcp/private-tester-access.md`
17. `deploy/gcp/staged-plan-approval.md`
18. `docs/adr/README.md`
19. `docs/review-handoffs/2026-09-10-first-deployment-packet-executability-review-handoff.md`
20. `infra/gcp/README.md`
21. `infra/gcp/develop/database_authority_job.tf`
22. `infra/gcp/develop/iam.tf`
23. `infra/gcp/develop/identities.tf`
24. `infra/gcp/develop/variables.tf`
25. `infra/gcp/variables.tf`
26. `infra/policy/predeployment-authority-manifest.json`
27. `scripts/qualify_develop_deployment.py`
28. `scripts/validate_terraform_static.py`
29. `scripts/verify_gcp_foundation.py`
30. `src/golden_rose/migration_runtime.py`
31. `tests/integration/test_database_authority.py`
32. `tests/unit/test_migration_runtime.py`
33. `tests/unit/test_qualify_develop_deployment.py`
34. `tests/unit/test_terraform_hygiene.py`
35. `tests/unit/test_verify_gcp_foundation.py`

## Hard stop
Do not authenticate to GCP; inspect or mutate backend/state; plan/apply/import; publish an image; create cloud users, roles, or Secret payloads; run cloud database/migration/jobs/services; deliver access; or qualify the cloud environment. After this source merges, rebaseline from the exact protected tip, prepare the private packet, and request Beatrice's explicit one-use eight-hour approval.
