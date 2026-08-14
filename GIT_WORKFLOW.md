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

### Independent authority prerequisite
The historical solo-maintainer protocol preserved review evidence but did not
eliminate self-authorization: same-repository workflow status contexts are
emitted by files that a pull request may edit. ADR-0010 therefore requires a real
non-author GitHub reviewer/CODEOWNER before PR #24 remediation implementation.
The reviewer must be another accountable person with an independently
controlled account, not the author, last pusher, an author-controlled alternate
account, or an agent using the author's credentials. Protected branches will
require one approval, stale-review dismissal, CODEOWNER review, and approval
after the latest push. Until an eligible reviewer is nominated, implementation
stops and the required-CI High remains open.

With one independent reviewer, the author pushes review corrections and the
reviewer approves the resulting head. If the reviewer becomes the latest
pusher, a second eligible non-last-pusher approver is required; do not weaken or
bypass last-push approval to avoid that result.

The bootstrap remediation PR must receive that independent review. After merge,
repository policy is applied from protected `develop` only under separate
explicit authorization and read back before the control is called operational.

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
