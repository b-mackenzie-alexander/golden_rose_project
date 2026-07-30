# Technology Decisions — Golden Rose Operations Platform

This is the concise decision register. Detailed immutable decision records live in `docs/adr/`. Status is one of Proposed, Accepted, Superseded, or Deferred.

| ID | Decision | Status | Rationale / boundary |
|---|---|---|---|
| TD-001 | Use one modular product with explicit public/staff trust boundaries. | Proposed | Avoid premature microservices while preventing public access paths from inheriting staff credentials, sessions, APIs, or data access. |
| TD-002 | Deliver a staff-only employer-demand pilot before public portal work. | Proposed | Client priority is to reduce paper/manual operational work quickly; demand currently exceeds worker supply. |
| TD-003 | Use employer → contact → worksite → staffing request → shift need as the initial core model. | Proposed | Separates concepts co-located in the workbook/forms and supports authorized search, corrections, history, and later extensions. |
| TD-004 | Derive dashboard metrics from authoritative operational records. | Proposed | Avoids duplicate metric-collection forms and competing response stores. |
| TD-005 | Treat comparison as a staff-reviewed, explainable aid—not automated matching/ranking. | Accepted planning guardrail | Worker preferences/skills are often self-reported and legacy criteria may be discriminatory/proxy fields. |
| TD-006 | Require English/Spanish functional and accessibility parity. | Accepted | Established engagement requirement; legal/policy translations still require approved versioned content. |
| TD-007 | Use React/TypeScript frontend, FastAPI domain API, PostgreSQL, SQLAlchemy, and Alembic as the proposed V1 stack. | Proposed | Fits current engineering capability and relational/audit needs; no deployment/vendor commitment. |
| TD-008 | Use migration-managed schema evolution and append attributable corrections. | Proposed | Preserve operational/audited meaning and support rolling release safety. |
| TD-009 | Treat Google Cloud Run + Cloud SQL as the first-priced hosting reference, with AWS equivalent mapping. | Proposed | Managed services reduce small-team operations; provider, ownership, price, region, and recovery remain open. |
| TD-010 | Manage repository governance through reviewed IaC. | Accepted | `infra/github/` supplies desired policy plus apply/verify scripts. `develop` and `main` are protected with required CI checks, update-before-merge, administrator enforcement, conversation resolution, and deletion/force-push prevention. |
| TD-011 | Block document uploads until a secure ingestion boundary is designed and qualified. | Accepted planning guardrail | Untrusted files must be isolated, validated, scanned, and safely released before staff use. |

## Decision process
1. Record a proposed decision with evidence, alternatives, owner, consequences, and revisit trigger.
2. Obtain the necessary technical/client/counsel approval.
3. Create or update an ADR for material architecture, security, governance, or data-model decisions.
4. Update the status here and linked living docs.

## Non-decisions that require explicit approval
Legal/business content, fees, retention, public copy, vendor selections, cloud accounts, production data use, public release, document uploads, integrations, and any automated decision capability.
