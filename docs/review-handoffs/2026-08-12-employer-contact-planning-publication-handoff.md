# Review Handoff — EmployerContact planning publication

**Date:** 2026-08-12
**Target PR base:** `develop`
**Planning base:** `a4d8f90dc8272de2db5f75c3bf3b96017236aceb` (`develop == origin/develop` before publication preparation)
**Intended branch:** `docs/employer-contact-authority-plan`
**Review surface:** local uncommitted Markdown-only working tree
**PR status:** no commit, push, or PR yet

## 1. Purpose

Publish the formally accepted planning boundary for the next bounded Phase 1 slice. This handoff grants no implementation authority and contains no product code, migration, dependency, lockfile, frontend, service, deployment, real-identity, or live-data change.

Controlling artifacts:

- `docs/adr/ADR-0008-phase-1-employer-contact-authority-foundation.md`
- `.hermes/plans/2026-08-12_111500-phase-1-employer-contact-authority-foundation-plan.md`

ADR-0008 is an **Accepted planning boundary — publication pending**. EmployerContact implementation remains blocked until this packet merges through protected `develop`, a fresh coding lane rebaselines from the exact merge tip, and Beatrice separately authorizes implementation and any required PostgreSQL use.

## 2. Accepted technical boundary

In scope for the later implementation lane:

- nested idempotent EmployerContact creation under a draft Employer;
- required normalized `full_name` only;
- bounded parent-scoped POST collection query for authoritative rediscovery;
- parent-scoped exact read;
- `employer_contact:draft:create` and `employer_contact:read`, each preserving the parent Employer boundary;
- explicit EmployerContact entity authority;
- type-bound Employer/EmployerContact receipt and audit correspondence;
- synthetic/local-only fixtures and no-store/minimized responses.

Out of scope:

- browser/UI or public routes;
- global/name search, unbounded listing/counting, or export;
- phone, email, relationship/title, status, consent, communication, correction, lifecycle, or deletion;
- Worksite, StaffingRequest, ShiftNeed, queue, calendar, map, or broader persistence completion;
- production identity, deployment, client/live data, or legacy import.

## 3. Independent review evidence

The controlling exact-artifact closure batch returned two PASS verdicts with zero residual Blocker, High, or Medium findings against baseline `a4d8f90dc8272de2db5f75c3bf3b96017236aceb`.

Reviewed pre-acceptance hashes:

- ADR-0008: `c4e169fc2ac904f1da4b1394da41f1abb7a16a7c95f8a9f4b8e5a44f85c7df87`
- plan: `59ef6ea20be4311907471dba65ee05194e3f9a37fb9b4f5b51faeed3f8e29451`

Review closure covered:

- FastAPI transport validation versus transport-valid authorization precedence;
- bounded operation-specific no-store/error behavior and separate unmatched-route/method probes;
- application/access-log non-disclosure matrices for contact PII and authority markers;
- existing-writer compatibility before generalized rejecting constraints;
- write-conflicting migration locks, staged validation, rollback, and downgrade ordering;
- exact command/result entity and event schema/type/entity compatibility;
- truthful ordinary-row mutation guards versus lifecycle/downgrade authority mutation;
- deterministic two-session `READ COMMITTED` idempotency races;
- empty, predecessor-populated, and mixed-state upgrade/downgrade qualification;
- executable RED/GREEN ordering and final-head publication gates.

After PASS, Beatrice formally accepted ADR-0008. The current publication hashes changed only because governance/status and completed-gate language was updated across the ADR, plan, decision register, and living documents:

- accepted-status ADR-0008: `f0e35f5dbb4b9a7520eee870e6e4dc3ad96d2ab6a6ceeda884b43d348f43552b`
- accepted-status plan: `ee5dc68590b211e6f20a8efaf2be6d52ae25ed1f57cf22625e79ab2d92a575ae`

Publication review must verify that this acceptance delta does not alter the independently reviewed technical contract or relax any stop boundary.

## 4. Baseline technical evidence

The fresh 2026-08-12 baseline review recorded:

- local `develop == origin/develop == a4d8f90` before planning edits;
- 116 frontend tests passed;
- 238 backend tests passed at 96.14% coverage;
- frontend/backend lint, typing, build, Alembic round-trip, dependency audit, SBOM validation, and diff hygiene passed;
- exact-range Gitleaks over `1543248..a4d8f90` found no leaks;
- the isolated review database/role was removed;
- the healthy pre-existing PostgreSQL container was intentionally left unchanged.

These results qualify the merged baseline. They are not final-head evidence for an eventual publication commit.

## 5. Publication surface

Before this handoff was added, the live working tree contained 18 Markdown-only paths: 16 modified and two untracked. This handoff is the nineteenth Markdown path. The surface consists only of the accepted ADR/plan, decision/living-document alignment, historical status reconciliation, and this review handoff.

No source code, test code, migration, package manifest, lockfile, workflow, generated artifact, or secret-bearing file is in scope.

## 6. Required publication review

Review the complete uncommitted working-tree diff and report Blocker/High/Medium/Low findings. At minimum verify:

1. ADR-0008 and the plan retain the reviewed create + bounded parent query + exact-read contract.
2. Acceptance language never implies implementation, deployment, live-data, or broad-roadmap completion.
3. `ROADMAP.md` marks review/acceptance complete but leaves protected publication/merge and implementation incomplete.
4. `CURRENT_WORK.md`, `AGENTS.md`, the ADR/decision indexes, architecture/security/technical requirements, permission matrix, operational discovery register, and dated notes agree on the current gate.
5. Historical Proposed-state notes remain chronological evidence rather than being rewritten as though acceptance existed earlier.
6. Every changed/untracked path is Markdown and belongs to this planning publication.
7. Referenced paths and named existing tests in the implementation plan exist.
8. `git diff --check` passes.

## 7. Stop boundary

Do not implement EmployerContact, create migration `0004`, add permissions/routes/models/tests, start or alter services, use client/live data, commit, push, open a PR, or merge as part of this handoff review.

After independent publication-delta clearance, commit/push/PR creation still requires separate authorization. After protected merge, implementation requires a fresh exact-tip rebaseline and separate coding approval.
