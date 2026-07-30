# ADR-0001: Protected `develop` Integration and `main` Promotion Branches

**Status:** Accepted
**Date:** 2026-07-30

## Context
The project needs a protected integration branch for normal work and a higher-control production-promotion branch. The user requires `main` to accept only promotions from `develop` or emergency `hotfix/*` branches. `develop` must not be accidentally deleted and ordinary work must pass branch/security checks before squash merge.

## Decision
- Create `develop` from the initial `main` baseline.
- Protect both `develop` and `main` against direct push, force push, deletion, unresolved conversations, and missing required checks; include administrators in enforcement.
- Use required GitHub Actions checks to enforce source/target policy:
  - only `develop` or `hotfix/*` may target `main`;
  - only approved purpose-named branches may target `develop`.
- Allow squash merge for feature branches into `develop`; retain merge commits at repository level for `develop` → `main` promotions.
- Store desired GitHub policy and apply/verify scripts in `infra/github/`.

## Consequences and constraints
GitHub’s normal branch-protection API does not natively enforce a different merge method by target branch. It can block the wrong source branch through a required check, but it cannot mechanically forbid selecting “Squash and merge” only for a `develop` → `main` PR while allowing it for feature → `develop` PRs in the same repository.

Therefore, until a separately reviewed merge-queue/release-automation design is adopted, every `develop` → `main` promotion must select **Create a merge commit** and retain `develop`; this is a documented manual release gate, not a falsely claimed technical enforcement. The branch itself is protected from deletion.

## Alternatives considered
- Disable squash merges globally: rejected because ordinary feature slices should squash merge into `develop`.
- Allow all PR sources to `main`: rejected because it bypasses integration/release evidence.
- Add a privileged promotion bot now: deferred; it introduces credentials, bypass authority, and more operational complexity before a need is proven.

## Approval and revisit trigger
Approved for repository bootstrap subject to successful PR/CI exercise. Revisit if GitHub merge queue, release automation, multiple maintainers, or a hard technical guarantee of promotion merge method becomes required.
