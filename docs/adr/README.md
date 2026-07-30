# Architecture Decision Records

ADRs preserve material architecture, security, data-governance, delivery, and repository-governance decisions in a durable form. They complement `TECHNOLOGY_DECISIONS.md`; neither substitutes for client/counsel approval where that approval is required.

## Status values
- **Proposed:** under review; not an implementation authorization.
- **Accepted:** approved for the stated scope.
- **Superseded:** replaced by a later ADR.
- **Deferred:** intentionally postponed.

## Naming
Use `ADR-NNNN-short-title.md`, with monotonic numbers. Never renumber an existing ADR. Link superseding records both ways.

## Required sections
- Status and date
- Context/evidence posture
- Decision
- Consequences and constraints
- Alternatives considered
- Approval/owner and revisit trigger

## First records to create when decisions are ready
- First staff-pilot scope and production-data boundary.
- Public/staff identity and API boundary.
- Canonical employer-demand data model and extension approach.
- Repository governance as code policy.
- Dashboard KPI and comparison-aid decision boundaries.
- Secure document-ingestion architecture, if uploads are approved.
