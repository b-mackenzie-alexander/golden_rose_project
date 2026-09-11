# Foundation verifier managed-IAM reconciliation review handoff

## Delivery lock
- One independent developer; agent reviews are quality evidence, not human authorization.
- The mandatory next outcome remains a browser-visible fictional-synthetic GCP `develop` environment.
- Cloud work resumes only from a protected final tip under one fresh exact eight-hour packet.
- Do not restore per-command approvals, Gate E0, signer/attestor machinery, immediate FinOps separation, named-IAM-only access, human quorum, or production recovery gates.

## Objective
Review the bounded source correction for the successor packet's read-only A02 project-IAM stop. The existing outcome plan and Beatrice's explicit source-remediation authorization govern this slice; no new implementation plan was created.

## Base and observed stop
- Base: protected `develop@4b678d1c2b6b5eb13c1031bd2cd4be16a2da5302`, merged by PR #88.
- Branch: `fix/foundation-verifier-managed-iam`.
- Successor A00/A01 and exact A02 quota-role/binding readback passed.
- The verifier then rejected three legitimate Google-managed service-agent roles and three redundant bootstrap roles held by the same exact named-human Owner.
- The packet stopped read-only and is consumed. It made no mutation and performed no A03+ action.

## Implemented behavior
1. Exact project-number-derived identities are recognized for Compute Service Agent, Compute Instance Group Manager Service Agent, and Logging Service Agent.
2. Baseline project IAM accepts only exact reviewed application roles plus exact Google-managed roles.
3. The provider-owner exception may additionally contain only `roles/artifactregistry.admin`, `roles/iam.serviceAccountCreator`, and `roles/resourcemanager.projectIamAdmin`, each with complete membership equal to the same exact named-human Owner.
4. Wrong managed identities, additional members, another user, or any unapproved same-user role remain fail closed.
5. Retaining redundant labels does not increase effective authority while exact Owner remains; retirement stays required before handoff and is not a new current-target mutation gate.

## TDD and verification
- RED: exact current managed-service-agent acceptance test failed on project-IAM inventory.
- RED: exact same-provider redundant-role acceptance test failed on basic-role/project-IAM inventory.
- GREEN: both pass after exact managed-role and provider-role modeling.
- Six wrong-member, extra-member, and unapproved-role variants passed immediately as fail-closed regressions.
- Verifier suite: `131 passed`.
- Full unit suite: `741 passed`, one inherited Starlette warning.
- Terraform hygiene: `303 passed`; static validation passed.
- Ruff and mypy pass after formatter reconciliation; Bandit and diff hygiene pass.
- Final architecture/security rereview: `PASS`, no current-target Blocker, High, or Medium.
- Final Terraform/deployment rereview: `PASS`, no Blocker, High, Medium, or Low.

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
18. `tests/unit/test_verify_gcp_foundation.py`
19. `docs/review-handoffs/2026-09-11-foundation-verifier-managed-iam-review-handoff.md`

## Primary review focus
- Google-managed role identities are exact, project-number-derived, and not suffix-based.
- Same-provider redundant roles cannot admit another member, group, service account, or broader role.
- The baseline path still rejects every unreviewed project role.
- No wording revives command-level approvals or treats the consumed packet as reusable.

## Hard stop
Do not authenticate to cloud or perform any backend/state/image/Secret/database/migration/service/access/qualification action from this branch. After clean review and protected merge, prepare one fresh exact packet and obtain new one-use approval.
