# Git Workflow — Golden Rose Operations Platform

**Status:** Accepted repository policy. GitHub enforcement/configuration is managed through reviewed infrastructure as code in `infra/github/`; `develop` and `main` protections have been exercised through real PRs.

## Core rules
- Protected integration/release branches are `develop` and `main`; never commit directly, force-push, or bypass review/checks.
- Work starts on a short-lived, purpose-named branch from the current approved base.
- Use focused, attributable commits. Do not mix unrelated refactors, secrets, client data, generated artifacts, or unreviewed configuration with a feature slice.
- A pull request records scope/non-scope, trust/data impact, validation evidence, migration/recovery posture, rollout plan, and approval dependencies.
- Use squash merge for ordinary feature branches to retain concise protected-branch history while preserving PR/CI/review evidence.
- `main` represents reviewed, releasable source. Production is promoted from the qualified immutable artifact only after recorded approval.

## Branch naming
Allowed branch prefixes:
```text
feat/<short-purpose>
fix/<short-purpose>
docs/<short-purpose>
chore/<short-purpose>
hotfix/<short-purpose>
security/<short-purpose>
ci/<short-purpose>
test/<short-purpose>
refactor/<short-purpose>
spike/<short-purpose>
```

Examples:
```text
docs/phase-0-living-doc-baseline
feat/staff-employer-request-entry
security/staff-plane-authorization-review
ci/repository-governance-checks
```

Branch naming will be validated in CI/ruleset policy; classic branch protection alone may not enforce it fully.

## Commit convention
Use Conventional Commit-style messages:
```text
feat(staff): add employer request entry
fix(auth): reject public token at staff API
docs: record dashboard KPI approval gate
security(upload): quarantine untrusted PDF before scan
ci: add dependency audit
chore: refresh development fixture
```

## Promotion constraint: `develop` → `main`
Only `develop` or `hotfix/*` may target `main`; required CI enforces the allowed source branches. `develop` and `main` are protected from deletion and force pushes.

GitHub repository settings do not natively enforce a different merge method by PR target. Since feature → `develop` PRs use squash merge, every `develop` → `main` promotion must manually select **Create a merge commit** and retain `develop`. This is an explicit release checklist gate, not a claimed automatic protection. ADR-0001 records the limitation and revisit trigger.

## Pull-request flow
```text
purpose branch → PR → CI + review → develop
release candidate → PR → CI + acceptance/release evidence → main
qualified immutable artifact → explicit protected production promotion
```

Required review escalation applies to authentication/authorization, staff/public boundaries, secrets, data access, migrations, documents/receipts, payments, exports, logging/audit, dependencies, infrastructure/IaC, and deployment controls.

### Solo-maintainer authority boundary
The solo-maintainer protocol preserves useful quality evidence but does not eliminate self-authorization: same-repository required contexts are emitted by files that a pull request may edit. This repository has no independently controlled reviewer/CODEOWNER. ADR-0012 makes the PR #24 High/open accepted residual risk a permanent operating constraint rather than fabricating an approval boundary.

The actual policy remains zero required approvals, no CODEOWNER review, and no last-push approval. PRs, owned required checks, strict update-before-merge, stale-review dismissal, conversation resolution, administrator enforcement, deletion/force-push prevention, exact-head local qualification, exact-range secret scanning, and documented owner merge rationale are quality controls—not independent authorization. Delegated or separate-session review evidence must be labeled accordingly.

`Terraform static validation` is required quality evidence after PR #29's qualified producer merged. It must never be described as immutable or independent. Under accepted ADR-0012 and ADR-0013, the open High remains accepted residual risk while Beatrice separately authorizes remediation implementation, read-only cloud qualification, each Terraform plan/apply, publication, migration, service activation, and qualification. No unavailable second-human approval is required, and no gate silently authorizes the next.

## Required checks (target state)
- Branch policy.
- Repository/documentation hygiene.
- Unit/integration/contract tests and lint/type checks.
- Migration compatibility checks when applicable.
- Secret scanning.
- Dependency/SBOM and vulnerability scanning.
- SAST and relevant configuration/IaC scanning.

Only stable, owned checks should be required. Optional/third-party checks must not silently become merge blockers without explicit policy.

## Repository governance as code
Target directory:
```text
infra/github/
  repo-policy.json
  apply-repo-policy.sh
  verify-repo-policy.sh
```

The policy should cover protected branches, required checks, review-count mode,
merge methods, conversation resolution, force-push/deletion rules, branch
deletion after merge, and drift verification. It must be exercised by a real PR
before it is considered operational. The current zero-approval policy is
historical residual risk, not the target state and not evidence that review or
validation may be skipped.

## Sensitive-data and artifact hygiene
Never commit credentials, `.env` files, client records, legacy exports, raw personal data, production backups, unapproved generated reports, or unmanaged cloud state. Commit only reviewed source, non-secret configuration/templates, tests with wholly fictional synthetic fixtures unless a separate test-data procedure explicitly approves otherwise, documentation, and approved infrastructure definitions.
