# Architecture Decision Records

ADRs preserve material architecture, security, data-governance, delivery, and repository-governance decisions in a durable form. They complement `TECHNOLOGY_DECISIONS.md`; neither substitutes for client/counsel approval where that approval is required.

## Status values
- **Proposed:** under review; not an implementation authorization.
- **Accepted:** approved for the stated scope.
- **Superseded:** replaced by a later ADR.
- **Deferred:** intentionally postponed.

## Naming
Use `ADR-NNNN-short-title.md`, with monotonic numbers. Never renumber an existing ADR. Link superseding records both ways.

## Records
- `ADR-0001-protected-integration-and-promotion-branches.md` — accepted protected-branch and promotion topology.
- `ADR-0002-first-phase-1-slice-and-synthetic-data-boundary.md` — accepted first tracer scope, synthetic-data boundary, and planning/coding/review handoff.
- `ADR-0003-phase-1-backend-toolchain.md` — accepted Python/FastAPI/PostgreSQL synchronous backend toolchain for the first slice.
- `ADR-0004-phase-1-employer-read-search-boundary.md` — accepted and implemented synthetic/local Employer detail and bounded-search boundary.
- `ADR-0005-phase-1-employer-workspace-frontend-boundary.md` — accepted and implemented first browser-workspace and create-response cache-hardening boundary; PR #12 merged the planning packet and PR #13 merged the bounded implementation.
- `ADR-0006-phase-1-employer-workspace-post-merge-closeout.md` — accepted and implemented post-merge closeout decision for PR #13 defects, deferred human qualification gates, and the bounded remediation lane; PR #14 merged its paired plan and PR #15 merged the exact-head-qualified closeout plus this ADR at `7ae448e`.
- `ADR-0007-phase-1-draft-employer-revision-boundary.md` — accepted and implemented boundary for revising only draft Employer `display_name` and `employer_type` with expected-version concurrency, command-bound idempotency, minimized audit authority, and localized browser recovery; PR #17 merged the implementation at `1543248`, and a bounded post-merge remediation is active for target binding and concurrent no-op/audit authority.

## Required sections
- Status and date
- Context/evidence posture
- Decision
- Consequences and constraints
- Alternatives considered
- Approval/owner and revisit trigger

## Next records to create when decisions are ready
- Public/staff identity and API boundary.
- Canonical employer-demand data model and extension approach.
- Dashboard KPI and comparison-aid decision boundaries.
- Secure document-ingestion architecture, if uploads are approved.
