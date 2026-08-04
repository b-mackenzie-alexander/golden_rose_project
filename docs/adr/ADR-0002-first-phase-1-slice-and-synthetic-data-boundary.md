# ADR-0002: First Phase 1 Slice and Synthetic-Data Boundary

**Status:** Accepted
**Date:** 2026-08-04

## Context and evidence posture

The accepted Phase 1 direction is a staff-only employer-demand workflow. The repository currently contains planning/governance material but no application scaffold, manifest, migration environment, or application tests. Beginning with the complete employer → contact → worksite → request → shift workflow would combine too many field-requiredness, authorization, lifecycle, and audit decisions in one review surface.

The first slice must prove a real vertical path without collecting client data or implying that production identity, public access, legal behavior, cloud services, or the larger workflow is ready.

## Decision

The first implementation slice is one local/synthetic staff-API tracer:

1. bootstrap the approved Python backend toolchain, PostgreSQL migration environment, test harness, and application CI;
2. expose only `POST /api/staff/v1/employers`;
3. accept only `employer_type` (`household` or `business`) and a bounded `display_name`;
4. server-assign `draft` lifecycle state, `staff_entry` source channel, timestamps, UUIDs, actor attribution, and record version `1`;
5. authorize a synthetic staff principal through the named `employer:draft:create` permission rather than a role-name check;
6. reserve a security-internal `CommandReceipt` keyed by a non-nil UUIDv4 command/idempotency key and bound to actor plus canonical payload;
7. create the receipt, `Employer` row, and required `employer.created` `AuditEvent` atomically in one PostgreSQL transaction;
8. replay an identical committed command deterministically and reject reuse by a different actor or canonical payload without disclosing the prior result; and
9. prove denial-before-write, audit-failure rollback, concurrency/idempotency, migration, append-only event, and synthetic-auth-production-rejection behavior with tests first.

A creation command has no prior record to match. For audit/version semantics it uses prior version `0` and new version `1`; later mutations remain required to present an expected current version.

The synthetic principal is configuration/dependency supplied. No request header or body field may choose actor identity, role, or permissions. Synthetic authorization is allowed only in explicit `local` and `test` environments; the application must reject a production configuration that selects it.

`CommandReceipt` is infrastructure for transactional duplicate protection, not a business entity, public read model, event source, or authorization substitute.

Only fictional fixtures explicitly labeled synthetic may be used. No client record, raw artifact value, legacy export, production data, live provider, or live external service is admitted.

## Consequences and constraints

- This slice proves the database transaction and staff-command seam, not the complete employer-demand product.
- No frontend, contact, worksite, request, shift, queue, calendar, map, search, correction, identity-provider, MFA, export, notification, upload, cloud, or public route is included.
- `legal_name` is absent from the first command. Intake-channel and lifecycle policy are not generalized beyond server-controlled `staff_entry` and `draft` values for this tracer.
- The API does not create tables at runtime; Alembic is the only schema-management path.
- PostgreSQL is required for integration evidence. SQLite is not a substitute for PostgreSQL transaction, JSONB, constraint, or concurrency behavior.
- A local PostgreSQL service may be started only with explicit coding-session approval and synthetic credentials/data. GitHub Actions may use an ephemeral PostgreSQL service for the reviewed test workflow.
- No database or API behavior in this slice authorizes live-data admission or production activation.

## Alternatives considered

- **Bootstrap-only PR:** rejected because it would prove tooling but no domain, authorization, or audit contract.
- **Complete employer-demand aggregate:** deferred because it would force unresolved requiredness and lifecycle decisions across contacts, worksites, requests, and shifts.
- **SQLite integration tests:** rejected because they would not prove the selected PostgreSQL behavior.
- **Request-controlled synthetic actor/role headers:** rejected because they normalize a spoofable authorization shape that must never reach production.

## Approval, handoff, and revisit trigger

Beatrice explicitly selected this tracer shape and delegated the unanswered field-requiredness choice to planning judgment on 2026-08-04. The minimum `employer_type` plus `display_name` request boundary is therefore accepted for this slice, with the broader lifecycle/intake policy still open. A separate coding session may implement it only after the plan containing exact tasks and gates is reviewed and merged to `develop`. A separate review session will independently assess the resulting branch and PR evidence.

Revisit this ADR before adding any mutation beyond draft creation, real authentication, public routes, live/client data, contact/location fields, generalized lifecycle/source-channel values, corrections, exports, or production deployment behavior.