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
- Plans operate at outcome scale: each accepted plan should normally cover multiple roadmap items and may authorize several ordered implementation PRs. RED → GREEN nodes remain small inside coding and do not each require a new planning cycle.
- Keep each PR coherent and reviewable, but return to planning only for a material architecture/trust/data/identity/vendor/schema/cloud-authority change, an assumption-invalidating Blocker/High, infeasible decomposition, or user/client feedback that changes the target workflow.
- Separate hazardous operational approvals remain mandatory even when one master plan defines the whole outcome. Cloud inventory, state adoption, each plan/apply, publication, migration, service activation, tester access, live-data admission, and production never become implicit.
- Before coding, read the living docs and re-baseline Git state with explicit approval for terminal/Git actions.
- Use a valid branch prefix: `feat/`, `fix/`, `docs/`, `chore/`, `hotfix/`, `security/`, `ci/`, `test/`, `refactor/`, or `spike/`.
- Implement narrowly, with tests first where code is introduced. Run relevant quality/security checks and `git diff --check` after changes when terminal approval is granted.
- Update `CURRENT_WORK.md`, `ROADMAP.md`, and `NOTES.md` after material planning/implementation/review milestones; update technical/security/decision docs when their contracts change.
- Never commit secrets, client personal data, raw exports, production data/backups, or unreviewed generated artifacts.

## Current implementation boundaries
The completed first implementation slice is the synthetic/local staff-only create tracer in ADR-0002 and `.hermes/plans/2026-08-04_phase-1-first-slice-plan.md`: the approved backend toolchain accepts only `employer_type` and `display_name` for one draft `Employer`, authorizes a synthetic staff principal through `employer:draft:create`, and atomically appends `employer.created` audit history.

The completed second implementation slice is the synthetic/local Employer detail and bounded-search tracer in ADR-0004 and `.hermes/plans/2026-08-04_phase-1-employer-read-search-plan.md`, merged by PR #11. It adds one `employer:read` permission, exact UUID detail, and privacy-conscious POST search requiring a bounded name fragment with optional employer type, filter-bound keyset pagination, minimized no-store responses, and no read-side domain/audit writes.

ADR-0005 and `.hermes/plans/2026-08-06_115420-phase-1-employer-workspace-frontend-plan.md` authorized the first local/synthetic staff Employer workspace frontend; PR #13 merged that implementation into `develop`.

ADR-0006 and its paired plan controlled the closeout merged by PR #15. ADR-0007 controlled draft-Employer revision merged by PR #17 and remediated by PR #18; PR #69 later merged its bounded receipt-visibility race remediation. PR #20 merged ADR-0008's EmployerContact authority implementation into protected `develop` at `6eb05d5`: backend-only contact create, bounded parent query, exact read, and typed receipt/audit authority. PR #22 merged ADR-0009 Slice B's local runtime/container contract at `f3cac4d`. PR #24 merged the validate-without-apply Terraform scaffold at `50451b3`, PR #29 merged its six-task static remediation at `08fe305`, and PR #33 merged ADR-0012's consolidated source-controlled pre-deployment implementation at `3c0118a`. PR #37/PR #42/PR #46/PR #48 closed the ADR-0013 source and verifier blockers, and PR #57 closed A1. PR #58/PR #59 plus WP-2/WP-3 completed workload binding without mutation; A2 selected new state lineage rather than prior-state adoption; E2/E3 state establishment/readback, A5, ownership alignment, exact replacement-free foundation apply, and workload-free post-apply verification are complete. PR #69 merged the Gate P commit-pinned Syft correction into protected `develop@64f4ae5`; Gate P publication verification is now the next separately approved operational boundary. Secret versions, private database/migration, service activation, tester access, qualification, live data, and production remain later separate gates. The private fictional-synthetic demo must use production-shaped application/container/database paths; temporary debt must be bounded and retired before production/handoff. Project IDs, billing IDs, user emails, domains, principals, credentials, plans, state, and secret payloads must not be committed.

Every later implementation tranche requires an accepted merged outcome-scale plan; one plan may authorize several predeclared implementation PRs under ADR-0014 without a new planning PR between them. ADR-0013 amends ADR-0012 after PR #33 and keeps private inventory/adoption, each Terraform plan/apply, publication, migration, service activation, and qualification as separate operational gates. Do not continue from historical documentation or retired branches; always rebaseline from the exact merged integration tip.
