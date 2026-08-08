# ADR-0006: Phase 1 Employer Workspace Post-Merge Closeout

**Status:** Accepted
**Date:** 2026-08-07

## Context and evidence posture

PR #13 merged the first local/synthetic staff Employer workspace implementation into protected `develop` at `f8236e6`. That merge preserved the approved Phase 1 boundary: one local/test-only browser workspace over the existing Employer create, exact-detail, and bounded-search contracts, with synthetic-only data, no real identity, no deployment, no public routes, and no adjacent domain expansion.

Independent post-merge review then found closeout defects that are immediate source-level issues rather than later product-scope candidates. The observed defect classes are:

- production BFCache canonical reload is not wired through the real route surface;
- late asynchronous create completions can repopulate state after page reset/pagehide;
- unknown-outcome retry and abandonment authority can race or regress authoritative success;
- definitive create and bounded read failures are incompletely rendered in the localized browser UX;
- valid RFC 3339 timestamps with numeric offsets are rejected at the client boundary;
- `CommandReceipt`, `Employer`, and creation-event correspondence is not fully database-enforced;
- SQLAlchemy engine ownership is request-scoped rather than application-lifespan-scoped;
- SBOM validation remains a structural stub rather than strict identity/schema/graph/tool validation with a recorded dependency disposition;
- frontend test diagnostics still depend on DOM serialization and sentinel-style redaction instead of value-independent failure output.

At the same time, the review clarified that some earlier wording overstated what has been qualified. Automated jsdom/axe/catalog-parity/build/CI evidence exists locally, but **human browser walkthrough, manual accessibility, contrast/zoom/reflow/reduced-motion checks, and fluent English/Spanish review have not occurred against a shared deployed target**. Runtime-role immutability, production connection-pool sizing, and load behavior also remain later deployment-readiness work rather than current closeout evidence.

## Decision

Treat the next lane as a bounded **post-merge closeout** for PR #13 only.

This lane may change browser behavior, FastAPI lifecycle ownership, SQLAlchemy metadata/migrations, CI SBOM validation, and review-facing documentation **only** to remediate the evidence-backed issues above. It must preserve the existing synthetic/local create/search/detail product boundary and must not widen into draft-Employer revision, adjacent entities, real identity, deployment, public routes, client/live data, or other next-slice scope.

Human browser/manual accessibility/fluent-language qualification is explicitly deferred until a shared deployed `develop` environment exists. Those human gates block later promotion and client acceptance, but they are not to be misrepresented as completed now. Likewise, runtime-role immutability, pool sizing, and load qualification remain deferred deployment-readiness work.

## Consequences and constraints

- The active branch after rebaseline is a remediation lane, not a new product slice.
- Repository and handoff documents must be corrected before more implementation proceeds, because stale workflow-state claims are themselves evidence defects.
- The closeout branch must not start draft-Employer revision work. That remains the next recommended planning candidate only after this closeout merges.
- Final evidence must distinguish automated local verification from deferred human/deployed-target qualification.
- Any High/Blocker finding in implementation or rereview blocks PR preparation.

## Alternatives considered

- **Proceed directly to draft Employer revision:** rejected because the merged workspace still has evidence-backed post-merge defects and stale workflow-state claims.
- **Treat human browser/manual accessibility/fluent-language review as a pre-merge requirement for this closeout lane:** rejected because there is no shared deployed `develop` target yet; claiming it occurred locally would overstate evidence.
- **Expand closeout into deployment/runtime-role/load work:** rejected because those are later readiness gates and would widen scope beyond the merged workspace defects.

## Approval, owner, and revisit trigger

Beatrice accepted the closeout direction after independent review of the planning packet. PR #14 merged only the paired closeout plan into `develop` at `b0a459b`; PR #15 then merged the independently rereviewed and exact-head-qualified implementation closeout plus this ADR into `develop` at `7ae448e`. The closeout lane is complete. ADR-0007 and its paired plan are a separate planning-publication boundary and do not authorize draft-revision implementation.

Revisit this ADR before any of the following:

- starting draft-Employer revision implementation or planning from the same branch,
- introducing new domain entities or permissions,
- claiming human browser/manual accessibility/fluent-language qualification,
- beginning deployment/runtime-role/load work,
- or widening beyond the existing synthetic/local Employer create/search/detail boundary.
