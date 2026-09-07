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
- `ADR-0007-phase-1-draft-employer-revision-boundary.md` — accepted and implemented boundary for revising only draft Employer `display_name` and `employer_type` with expected-version concurrency, command-bound idempotency, minimized audit authority, and localized browser recovery; PR #17 merged the implementation at `1543248`, and PR #18 merged its bounded remediation at `a4d8f90`.
- `ADR-0008-phase-1-employer-contact-authority-foundation.md` — accepted and implemented backend-only synthetic/local EmployerContact create, bounded parent query, exact read, and typed receipt/audit authority; PR #20 merged the independently reviewed implementation into protected `develop` at `6eb05d5`.
- `ADR-0009-gcp-develop-deployment-boundary.md` — accepted private, fictional-synthetic-only GCP `develop` boundary. Later ADR-0012/ADR-0013 source work, state establishment/readback, source/live adoption, ownership alignment, exact foundation apply, workload-free verification, and Gate P publication are complete. Gate S created only the bounded `synthetic-staff-id` version; database-URL versions, activation, qualification, live data, and production remain separately gated.
- `ADR-0010-pr24-terraform-remediation-boundary.md` — superseded execution boundary for the unavailable independent-review model; retained as historical evidence.
- `ADR-0011-pr24-solo-maintainer-remediation-boundary.md` — accepted successor planning boundary for a single-maintainer repository: retain the self-authorizing-CI High as open residual risk, avoid review/CODEOWNER theater, and execute only six static validate-without-apply tasks from a fresh merged-tip branch.
- `ADR-0012-solo-maintainer-consolidated-predeployment-boundary.md` — accepted permanent solo-maintainer progression boundary: retain the same-repository-CI High as open accepted residual risk, never require an unavailable second human, consolidate source-controlled pre-deployment work, and keep operational gates separate.
- `ADR-0013-post-pr33-deployment-path-remediation.md` — accepted post-PR33 staged-deployment authority amendment. Later source, foundation, publication, bounded Secret, bootstrap authority, and provisioner backend-proof gates are complete. ADR-0015 merged through PR #79 to govern the quota-authority conflict; all later operational transitions remain separate.
- `ADR-0014-workflow-scale-planning-and-delivery.md` — accepted methodology governance: plans target meaningful multi-checklist outcomes and may authorize several ordered implementation PRs; TDD remains small inside coding, material changes trigger replanning, and hazardous operational gates remain explicit.
- `ADR-0015-finops-budget-ownership-separation.md` — accepted and merged through PR #79 at `develop@e7bab147`; it separates the existing Billing Budget into an IAM-isolated billing-human FinOps root/state, uses disjoint FinOps/workload authority runners, signed one-use receipts, and interleaved import/remove/source gates. Only Implementation PR A source work is authorized next; operational gates remain separate.

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
