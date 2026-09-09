# Human-visible develop acceleration source ledger

**Status:** Proposed. This ledger grants no implementation or cloud authority.

**Base:** exact protected `develop@3dca8101141e31e3d5b22739dabeaa4bc61dd15f`.

## Planning packet — 9 paths

| Path | Disposition |
|---|---|
| `AGENTS.md` | MODIFY |
| `GIT_WORKFLOW.md` | MODIFY |
| `CURRENT_WORK.md` | MODIFY |
| `ROADMAP.md` | MODIFY |
| `NOTES.md` | MODIFY |
| `docs/adr/ADR-0016-signed-finops-approval-authority.md` | MODIFY |
| `.hermes/plans/2026-09-09_005924-finops-post-execution-result-authority-amendment-plan.md` | CREATE |
| `docs/planning/finops-result-authority-replay-disposition.md` | CREATE |
| `docs/review-handoffs/2026-09-09-human-visible-develop-continuity-handoff.md` | CREATE |

## Single source PR — 40 paths

| Path | Disposition |
|---|---|
| `AGENTS.md` | MODIFY |
| `GIT_WORKFLOW.md` | MODIFY |
| `ARCHITECTURE.md` | MODIFY |
| `CURRENT_WORK.md` | MODIFY |
| `NOTES.md` | MODIFY |
| `ROADMAP.md` | MODIFY |
| `SECURITY.md` | MODIFY |
| `TECHNICAL_REQUIREMENTS.md` | MODIFY |
| `TECHNOLOGY_DECISIONS.md` | MODIFY |
| `.hermes/plans/2026-09-09_005924-finops-post-execution-result-authority-amendment-plan.md` | MODIFY |
| `docs/planning/finops-result-authority-replay-disposition.md` | MODIFY |
| `src/golden_rose/config.py` | MODIFY |
| `src/golden_rose/demo_access.py` | CREATE |
| `src/golden_rose/main.py` | MODIFY |
| `tests/unit/test_config.py` | MODIFY |
| `tests/unit/test_demo_access.py` | CREATE |
| `infra/gcp/develop/cloud_run.tf` | MODIFY |
| `infra/gcp/develop/iam.tf` | MODIFY |
| `infra/gcp/develop/secrets.tf` | MODIFY |
| `infra/gcp/develop/variables.tf` | MODIFY |
| `infra/gcp/develop/outputs.tf` | MODIFY |
| `infra/gcp/develop.tf` | MODIFY |
| `infra/gcp/variables.tf` | MODIFY |
| `infra/gcp/outputs.tf` | MODIFY |
| `infra/policy/predeployment-authority-manifest.json` | MODIFY |
| `scripts/validate_terraform_static.py` | MODIFY |
| `scripts/verify_gcp_foundation.py` | MODIFY |
| `scripts/qualify_develop_deployment.py` | MODIFY |
| `tests/unit/test_terraform_hygiene.py` | MODIFY |
| `tests/unit/test_verify_gcp_foundation.py` | MODIFY |
| `tests/unit/test_qualify_develop_deployment.py` | MODIFY |
| `.github/workflows/infrastructure-quality.yml` | MODIFY |
| `.github/workflows/application-quality.yml` | MODIFY |
| `.github/workflows/deploy-develop.yml` | MODIFY |
| `deploy/gcp/first-deployment-runbook.md` | MODIFY |
| `deploy/gcp/private-tester-access.md` | MODIFY |
| `deploy/gcp/evidence-template.md` | MODIFY |
| `deploy/gcp/qualification-status-contract.md` | MODIFY |
| `deploy/gcp/human-qualification-checklist.md` | MODIFY |
| `docs/review-handoffs/2026-09-09-human-visible-develop-continuity-handoff.md` | MODIFY |

Count assertion: exactly **40** source paths. Any implementation need outside this list requires an explicit same-plan scope amendment, not a new outcome plan, unless it changes the trust/data/schema/cloud architecture.

## Required implementation outcomes

1. Exact workload-project custom role with sole permission `serviceusage.services.use`, bound only to the workload provisioner.
2. Existing workload-owned budget remains unchanged.
3. High-entropy expiring HTTP Basic middleware protects every route except `/health` and `/readiness`.
4. Service-stage `allUsers` invoker exists only with synthetic mode, expiring shared gate, one-instance cap, and no-live-data marker.
5. Demo password exists only as Secret Manager payload and owner-held private file; Terraform manages metadata/reference, not payload.
6. Cloud SQL remains private and synthetic database recovery is teardown/rebuild.
7. Qualification proves unauthenticated/wrong denial, authorized browser/API access, synthetic workflows, scale/cost bounds, and log redaction.
8. One bundled operational packet controls precheck through qualification.

## Explicitly deferred/absent

- FinOps state root/bucket/import/remove and workload budget extraction.
- Four result-attestor workflows, WIF identities, HMAC keys, result ledger, and receipt v2.
- Human reviewer/CODEOWNER quorum or repository migration.
- Live/client data, production staff identity, production backup/restore, production support/handoff.

## Mechanical checks

Before source review:

- changed/untracked paths match the 40-path allowlist bidirectionally;
- `infra/gcp/develop/budgets.tf` is byte-identical to the planning merge base;
- custom role permission/member cardinality is exact;
- no second public route or database public-IP path appears;
- Basic secret values never appear in source, plans, test output, logs, or argv;
- all deferred result-authority paths remain absent;
- Terraform 1.15.8, application quality, static policy, qualification tests, Gitleaks, and diff hygiene pass.
