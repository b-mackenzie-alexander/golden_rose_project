# Git Workflow — Golden Rose Operations Platform

**Status:** Accepted repository policy. GitHub enforcement/configuration is managed through reviewed infrastructure as code in `infra/github/`; `develop` and `main` protections have been exercised through real PRs.

## Core rules
- Protected integration/release branches are `develop` and `main`; never commit directly, force-push, or bypass review/checks.
- Work starts on a short-lived, purpose-named branch from the current approved base.
- Use focused, attributable commits. Do not mix unrelated refactors, secrets, client data, generated artifacts, or unreviewed configuration with a feature slice.
- A pull request records scope/non-scope, trust/data impact, validation evidence, migration/recovery posture, rollout plan, and approval dependencies.
- Use squash merge for ordinary feature branches to retain concise protected-branch history while preserving PR/CI/review evidence.
- `main` represents reviewed, releasable source. Production is promoted from the qualified immutable artifact only after recorded approval.

## Plan, PR, and TDD granularity

- Planning is outcome-scale: a reviewed plan should normally cover multiple roadmap items and may define several ordered implementation PRs.
- PRs remain coherent review surfaces. A predeclared follow-on PR does not need another planning PR merely because its predecessor merged.
- RED → GREEN tests remain small implementation steps inside the accepted plan; normal failures and review remediation do not reopen planning.
- Replanning is reserved for material architecture/trust/data/identity/vendor/schema/cloud-authority changes, assumption-invalidating Blocker/High findings, infeasible decomposition, or user/client feedback that changes the target workflow.
- Splitting one predeclared PR into two for reviewability does not require replanning when scope, contracts, dependencies, and completion evidence remain unchanged.
- Hazardous authority remains explicit. For a private fictional-synthetic `develop` deployment, one reviewed time-bounded packet may authorize its complete ordered precheck → plans/applies → secret preparation → migration → service activation → access → qualification transaction, with internal stop/readback conditions. Do not split those ordinary steps into separate approval days. Separate approval remains mandatory for live-data admission, production, destructive recovery/state editing, or actions outside the packet.
- A tranche closes on its declared observable integration or qualification result—not merely when its source PRs merge.

ADR-0014 records this workflow-scale delivery policy. It changes planning granularity, not the protected-branch, review, evidence, or operational-authority controls below.

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

`Terraform static validation` is required quality evidence after PR #29's qualified producer merged. It must never be described as immutable or independent. The open solo-maintainer High remains accepted residual risk. ADR-0016's 2026-09-09 addendum supersedes the older per-transaction Gate E0/signing sequence for fictional-synthetic `develop`: Beatrice authorizes one exact eight-hour deployment packet, and internal plans/applies/publication/migration/service/qualification do not silently authorize anything outside that packet. No unavailable second-human approval is required.

PR #83 merged the reviewed 52-path source contract from `feat/human-visible-develop` head `cc48b9ffe74eaa7abd90488ba37baf8502eac4af` into protected `develop@9a04b274d9e0132e5a0b409314ba53170b43e303`; PR #84 merged its continuity closeout at `develop@63ac29b20314f03381d4a71e901a68ee51e913aa`; PR #85 merged bounded executability remediation at `develop@7a9e7c00de82842040f34080f6c529e688a6d445`; and PR #86 merged its status closeout at `develop@58ea1cfe3b88ac9580971ed44b9cf0814824abf8`. The first approved eight-hour packet created/read back only the exact quota role and sole provisioner binding, then stopped at the mandatory verifier before A03; its approval is consumed. Bounded source remediation now proceeds through the same protected PR workflow, and any successor cloud packet remains a distinct action requiring final-tip binding and explicit one-use approval.

PR #37 merged the `fix/post-pr33-deployment-path-remediation` source-controlled no-cloud remediation into protected `develop` at `caf96a72df87cd98114025627ad9f467f846f3a9`; its feature branch is retired. That merge cleared only the source-controlled remediation and opened the separate request for Gate 2 read-only qualification. It did not authorize cloud execution, plan/apply, publication, migration, activation, or qualification.

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
