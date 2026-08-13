# ADR-0008 — Phase 1 EmployerContact authority foundation

- **Status:** Accepted
- **Date:** 2026-08-12
- **Decision owner:** Beatrice, technical delivery owner
- **Scope:** Accepted synthetic/local backend-only EmployerContact create, bounded parent collection-query, and exact-read planning slice after PR #18
- **Acceptance:** Beatrice formally accepted this independently reviewed boundary on 2026-08-12. PR #19 merged the exact planning packet through protected `develop` at `745f9e8`, and a separately authorized coding lane then rebaselined from that merge tip onto `feat/employer-contact-authority-foundation`.

## Context and evidence posture

PR #18 merged the bounded draft-Employer revision remediation into protected `develop` at `a4d8f90`. Fresh review at that exact merged tip found the current Employer create/search/detail/revision tracer technically healthy: the complete local application-quality sequence passed, the exact PR #18 range was secret-clean, and no adjacent product entity is yet implemented.

The accepted Phase 1 structure requires `EmployerContact`, but field requiredness, contact lifecycle, named permissions, and the existing Employer-only receipt/audit foreign-key model must be resolved before code. Worksite, StaffingRequest, queue, calendar, map, and real identity work have more unresolved policy, privacy, or deployment dependencies and should not be bundled into this first adjacent-entity migration.

This record is an accepted implementation boundary. Exact-artifact API/security/privacy and persistence/migration/TDD closure reviews passed with no residual Blocker, High, or Medium findings, PR #19 merged the planning packet into protected `develop` at `745f9e8`, and the separately approved coding lane rebaselined from that exact integration tip before implementation began.

## Accepted planning decision

### Product and API boundary

Add one backend-only, synthetic/local EmployerContact identity tracer nested under an existing draft Employer:

- `POST /api/staff/v1/employers/{employer_id}/contacts`
- `POST /api/staff/v1/employers/{employer_id}/contacts/query`
- `GET /api/staff/v1/employers/{employer_id}/contacts/{employer_contact_id}`

The collection query is the minimum authoritative rediscovery seam after tab-memory loss: it accepts only bounded `page_size` and an optional opaque parent-bound keyset cursor in the POST body, orders by `created_at DESC, employer_contact_id DESC`, returns minimized contact representations, and exposes no total count. It is not a global contact list or name search.

No browser, name/global search, unbounded list, count, update, delete, notification, export, or public route is included.

### First persisted fields

The request supplies only bounded `full_name`. The server supplies:

- `employer_contact_id`;
- `employer_id` from the authorized path;
- `created_at` / `created_by`;
- `updated_at` / `updated_by`; and
- record `version = 1`.

`full_name` is required only to create this bounded identity record. It is attributable staff entry, not proof of the person's authority, identity, contactability, or consent. Phone, email, relationship/title, preferred language, preferred contact method, contact status, consent, and communication delivery are deferred. This deliberately avoids inventing phone/email normalization, contactability, consent, or lifecycle policy. A later workflow may require a contact method before request review/open without rewriting this draft-stage decision.

### Lifecycle boundary

The first contact record has no independent client-controlled lifecycle/status field. Creation is allowed only beneath an existing draft Employer. Contact supersession, correction, subsequent change, cancellation, deletion, and review-state behavior require a later accepted contract.

### Permission boundary

Add two server-enforced permissions:

- `employer_contact:draft:create`; and
- `employer_contact:read`.

All three routes also require `employer:read` for the parent. Framework transport parsing may reject a malformed path UUID, missing header, wrong body type, or extra/missing field before application authorization; those value-safe failures perform no SQL or writes. Once transport shape is valid, authorization occurs before UUIDv4 idempotency semantics, contact-name normalization, cursor decoding/binding, parent/contact lookup, response derivation, or writes. Route/body/header role claims cannot grant authority. Platform Administrator receives neither permission.

### Generalized receipt/audit authority

Migration `0004` must remove the current Employer-only polymorphism trap without weakening receipt/event correspondence:

1. Add a security-internal two-entity authority registry keyed by `(entity_type, entity_id)`. It has mutually exclusive `employer_id` and `employer_contact_id` foreign keys to the concrete domain tables plus checks that the selected concrete ID equals `entity_id`; a registry row therefore cannot authorize a nonexistent domain row.
2. Backfill all existing Employers into the registry before replacing Employer-only receipt/audit foreign keys.
3. Register each new Employer or EmployerContact atomically with its domain row; the existing Employer create command must be updated and regression-tested as part of this migration.
4. Bind `CommandReceipt(result_entity_type, result_entity_id)` and `AuditEvent(entity_type, entity_id)` to the registry.
5. Extend the bidirectional receipt/event authority foreign keys and unique keys to include entity type as well as command, entity ID, result version, event type, and actor.
6. Preserve command-specific checks that bind each command type to its exact result entity type, event type/schema, and version; likewise bind each audit event type/schema to its exact entity type.
7. Keep the registry, receipt, and audit rows guarded against ordinary row `UPDATE` and `DELETE`, and keep all domain/registry/receipt/event writes in one transaction. The current synthetic/local database-owner role can still bypass row triggers through `TRUNCATE`, DDL, or trigger changes; non-owner runtime grants remain a separately qualified deployment gate.

The registry is an internal relational-integrity mechanism, not a public domain entity, search index, event store, or generic metadata facility.

### Command and replay contract

EmployerContact creation requires a UUIDv4 idempotency key. Its normalized fingerprint includes command schema/type, parent Employer ID, and normalized `full_name`.

A fresh accepted command atomically creates:

- one entity-authority registry row;
- one EmployerContact row;
- one `CommandReceipt`; and
- one minimized `employer_contact.created` `AuditEvent` at version/sequence 1.

Identical replay returns the current minimized contact representation with immutable original result-version metadata and no writes. Changed actor, parent, schema, command type, or normalized payload returns a bounded conflict without disclosing another result. Audit changed-field evidence names `employer_id` and `full_name`, may include the internal parent Employer ID, and never stores the contact name as an approved value or ordinary log field.

### Read and privacy contract

Collection query and exact read are parent-scoped. A contact under another Employer is indistinguishable from an absent contact. The collection query is bounded to 1–50 records per page, has no name filter or total count, and binds each canonical cursor to the parent Employer and page-size contract; cursors are transport state, not authorization or durable authority. Each approved contact operation and every explicitly enumerated operation error uses `Cache-Control: no-store`; unmatched routes and unsupported methods retain the merged application-level router behavior and are not claimed as contact-operation responses. Routine responses omit actor IDs and unrestricted audit data. Reads create no domain, receipt, or audit writes.

Only wholly fictional synthetic contact names may be used. No client/live-derived, transformed, hashed, or de-identified records are allowed.

### Migration reversal contract

Migration tests must prove three states separately:

1. empty upgrade and downgrade succeeds;
2. populated Employer-only predecessor-compatible state downgrades successfully with rows, constraints, correspondence, and ordinary-row update/delete guards preserved; and
3. any EmployerContact/related successor authority causes downgrade to fail closed without altering schema, data, or guards.

Upgrade and downgrade run in one transaction under a fixed writer-compatible lock order. Upgrade takes `SHARE ROW EXCLUSIVE` locks on `command_receipts`, `employers`, then `audit_events` before preflight/backfill and holds them through new-constraint validation and commit. Downgrade takes the same lock mode on `command_receipts`, `employers`, `employer_contacts`, `entity_authorities`, then `audit_events` before its refusal query or DDL; a refused downgrade mutates nothing. Allowed reversal drops successor references in dependency order, restores exact revision-0003 keys/checks/Employer-only foreign keys, and only then removes successor constraints and tables while preserving ordinary row update/delete guards.

## Consequences and constraints

- This advances the canonical Employer → EmployerContact chain and generalizes the authority spine once, before requests/worksites depend on it.
- It adds contact PII even in synthetic form, so strict response/log/audit minimization is mandatory.
- It does not complete the roadmap’s broad employer/contact/worksite/request/shift persistence item; it records measurable partial progress only.
- It does not implement real authentication, staff accounts, MFA, production roles, live data, deployment, GCP, queue/calendar/map behavior, household/general-labor extensions, or communications.
- The planning packet and ADR must merge before implementation begins from a fresh branch.

## Alternatives considered

- **Implement many unchecked roadmap rows together:** rejected because those rows mix product epics, production gates, client/counsel decisions, and infrastructure authorization.
- **Implement real staff authentication next:** deferred until provider/session/recovery/runtime boundaries are selected and qualified; synthetic/local domain progress need not invent that production contract.
- **Implement Worksite next:** deferred because exact-address collection/reveal, geocoding, zone/CDTA, correction, and disposal boundaries add materially greater privacy scope.
- **Implement StaffingRequest/queue/calendar together:** deferred because contacts/worksites, request extensions/requiredness, lifecycle commands, and time/ownership configuration must exist first.
- **Keep receipt/audit tables Employer-only or record contact creation as an Employer event:** rejected because it would misstate the affected authoritative entity and create a second redesign immediately afterward.
- **Drop relational result-entity checks and rely only on application code:** rejected because it weakens the reviewed authority spine.
- **Collect phone/email now:** deferred because normalization, requiredness, correction, restricted-history, and communication/consent semantics are not yet accepted.
- **Expose only create plus exact read:** rejected because the returned contact UUID would not be authoritatively rediscoverable after in-memory state clears. The bounded parent collection query closes that gap without authorizing a browser, global search, name filter, count, or export.

## Publication and revisit trigger

The accepted ADR and paired plan merged through protected `develop` in PR #19 at `745f9e8`, and the fresh implementation branch now treats them as the controlling authority. Revisit before adding contact methods, contact status, correction/supersession, browser behavior, name/global search, unbounded list/count, request opening rules, communications, public access, live data, or another authoritative entity type.
