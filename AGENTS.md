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

The accepted next-slice direction is the first local/synthetic staff Employer workspace frontend in ADR-0005 and `.hermes/plans/2026-08-06_115420-phase-1-employer-workspace-frontend-plan.md`. Beatrice accepted the independently cleared product/architecture direction on 2026-08-06, but coding still requires protected planning-PR merge, a fresh rebaseline from the merged tip, and separate implementation-operation approval. Before browser consumption the slice adds one test-first `Cache-Control: no-store` header to fresh and replayed create successes, then consumes only the existing Employer create/search/detail status/body/schema/authority contracts with English/Spanish parity, accessibility, browser privacy/no-persistence controls, and frontend quality/dependency/SBOM gates. It adds no real identity, other backend contract/schema change, contact, worksite, request, shift, export, map, cloud deployment, public route, client/live data, or legal behavior.

Every later slice requires its own reviewed and merged plan. Coding starts only from a fresh session re-baselined to the exact merged planning tip.
