# AGENTS.md — Golden Rose Operations Platform

## Mission and scope
Golden Rose is a seven-week, evidence-led, compliance-conscious operations-platform engagement for an employment agency. The immediate goal is a safe staff-facing employer-demand workflow; the product must not be treated as a finished public portal, legal/compliance system, or automated hiring/matching system.

## Authoritative working surfaces
1. `CURRENT_WORK.md` — active lane, current objective, next steps, and stop boundaries.
2. `ROADMAP.md` — phase checklist and rollout truth.
3. `NOTES.md` — concise dated evidence, verification, and handoff log.
4. `SECURITY.md` — security posture, risks, mitigations, and gates.
5. `TECHNICAL_REQUIREMENTS.md` and `ARCHITECTURE.md` — proposed product/technical baseline.
6. `TECHNOLOGY_DECISIONS.md` and `docs/adr/` — decision register and durable decision records.
7. `GIT_WORKFLOW.md` — branch, PR, review, and delivery policy.
8. Obsidian engagement notes — detailed client evidence and planning narrative. Honcho supports semantic continuity but is not an authoritative operational database.

## Evidence posture
Classify claims as Observed, Reported, Proposed, or Validated. Client documents, photographed paperwork, Google Forms, workbooks, and web material are discovery evidence—not automatic requirements, legal sources, or production templates. Approved legal documents control legal wording/rules; the client’s approved business plan controls commercial/operational policy.

## Non-negotiable product guardrails
- Do not make automatic matching, ranking, eligibility, hiring, or referral decisions.
- Do not use protected traits or proxy data as default filters/comparison controls.
- Treat self-reported worker preferences/skills as unverified unless a separately approved process says otherwise.
- Keep precise household/worksite locations internal by default; use least-precise information outside approved need-to-know workflows.
- Maintain English/Spanish functional and accessibility parity for affected surfaces; legal/policy translations require separate approval and versioning.
- Keep public worker/employer and staff administration materially separate: identity/session/token audiences, endpoints, credentials, authorization, deployments, and data access.
- Do not collect live/production data, provision infrastructure, start services, enable uploads/integrations, or modify client systems without explicit scoped approval.

## Engineering workflow
- Plan → approval → coding → independent review → PR/CI → protected promotion.
- Before coding, read the living docs and re-baseline Git state with explicit approval for terminal/Git actions.
- Use a valid branch prefix: `feat/`, `fix/`, `docs/`, `chore/`, `hotfix/`, `security/`, `ci/`, `test/`, `refactor/`, or `spike/`.
- Implement narrowly, with tests first where code is introduced. Run relevant quality/security checks and `git diff --check` after changes when terminal approval is granted.
- Update `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md` after material planning/implementation/review milestones; update technical/security/decision docs when their contracts change.
- Never commit secrets, client personal data, raw exports, production data/backups, or unreviewed generated artifacts.

## Current implementation boundaries
The completed first implementation slice is the synthetic/local staff-only create tracer in ADR-0002 and `.hermes/plans/2026-08-04_phase-1-first-slice-plan.md`: the approved backend toolchain accepts only `employer_type` and `display_name` for one draft `Employer`, authorizes a synthetic staff principal through `employer:draft:create`, and atomically appends `employer.created` audit history.

The completed second implementation slice is the synthetic/local Employer detail and bounded-search tracer in ADR-0004 and `.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md`, merged by PR #11. It adds one `employer:read` permission, exact UUID detail, and privacy-conscious POST search requiring a bounded name fragment with optional employer type, filter-bound keyset pagination, minimized no-store responses, and no read-side domain/audit writes.

ADR-0005 and `.hermes/plans/2026-08-06_115420-phase-1-employer-workspace-frontend-plan.md` authorized the first local/synthetic staff Employer workspace frontend; PR #13 merged that implementation into `develop`.

ADR-0006 and its paired plan controlled the closeout merged by PR #15. ADR-0007 controlled draft-Employer revision merged by PR #17 and remediated by PR #18. PR #20 merged ADR-0008's EmployerContact authority implementation into protected `develop` at `6eb05d5`: backend-only contact create, bounded parent query, exact read, and typed receipt/audit authority. PR #22 merged ADR-0009 Slice B's local runtime/container contract at `f3cac4d`. PR #24 merged the validate-without-apply Terraform scaffold at `50451b3`, PR #29 merged its six-task static remediation at `08fe305`, and PR #33 merged ADR-0012's consolidated source-controlled pre-deployment implementation at `3c0118a`. A post-merge audit found F1-F17 deployment-path defects, including four Blockers. PR #37 merged the ADR-0013 no-cloud remediation at `caf96a7`; PR #42 then merged the bounded source-only reconciliation that makes tester-authority verification service-stage-only while retaining private Cloud SQL as a foundation requirement. Initial read-only qualification and partial foundation work are privately recorded; remaining decision freezes, source/live reconciliation, each Terraform plan/apply, publication, migration, service activation, and qualification remain separate gates. Project IDs, billing IDs, user emails, domains, principals, credentials, plans, state, and secret payloads must not be committed. Human browser/manual accessibility/fluent-language qualification remains deferred until a controlled shared target exists.

Every later implementation boundary requires an accepted merged plan. ADR-0013 amends ADR-0012 after PR #33 and keeps remaining Gate 2 decision freezes, source/live reconciliation, each Terraform plan/apply, publication, migration, service activation, and qualification as separate gates. Do not continue from historical documentation or retired branches; always rebaseline from the exact merged integration tip.
