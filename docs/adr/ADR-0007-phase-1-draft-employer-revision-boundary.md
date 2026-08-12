# ADR-0007: Phase 1 Draft Employer Revision Boundary

- **Status:** Accepted and implemented boundary — PR #17 merged at `1543248`; PR #18 remediation merged at `a4d8f90`
- **Date:** 2026-08-08
- **Decision owners:** Beatrice for technical delivery and security boundaries; Golden Rose client for accepted operational policy
- **Depends on:** ADR-0002, ADR-0004, ADR-0005, and merged ADR-0006
- **Implementation authority:** Historical activation gate completed: PR #16 merged this planning packet at `1c66eeb`, Beatrice authorized implementation from that exact tip, PR #17 merged the bounded implementation at `1543248`, and PR #18 merged its bounded remediation at `a4d8f90`. Any adjacent Phase 1 product slice still requires a separately reviewed and merged plan.

## Context

The merged staff Employer workspace can create one synthetic/local draft `Employer`, search authorized Employer records, and read exact Employer detail. PR #15 merged the independently rereviewed and exact-head-qualified post-merge closeout to `develop` at `7ae448e`; PR #16 merged this accepted planning packet at `1c66eeb`; and PR #17 merged the bounded draft-revision implementation at `1543248`. ADR-0006, database-authority constraints, FastAPI lifespan ownership, browser lifecycle/privacy remediation, diagnostics hardening, and SBOM validation remain predecessor authority.

The next useful Phase 1 slice is a bounded draft-Employer revision command. Staff need to correct only the existing draft `display_name` and `employer_type`. The command must not become a generic patch surface, lifecycle transition, audit timeline, contact/worksite/request workflow, or public API.

The first mutation also makes an existing create-replay ambiguity unavoidable: a valid retry of an earlier command may occur after the Employer has advanced to a later version. Reconstructing an old response by storing historical draft-name snapshots would expand retained sensitive data only to reproduce transport history. Returning the current row without metadata would conceal which version the retried command originally committed.

Claims in this ADR are classified as follows:

- **Observed:** `Employer` is the current authoritative row; `version` starts at `1`; create idempotency is actor-, command-type-, and normalized-payload-bound; audit events and command receipts are append-only; the read boundary already returns minimized no-store detail.
- **Reported/accepted:** staff may correct draft Employer data; only `display_name` and `employer_type` are in this slice.
- **Accepted decision:** the exact revision command, replay metadata, audit payload, browser authority state machine, and schema evolution below.
- **Validated:** PR #17 implemented this boundary under executable backend/frontend/migration/quality evidence. Post-merge review then found two Medium authority defects now controlled by the remediation addendum below.

## Decision

### 1. Command and authorization boundary

Add one staff-plane command endpoint:

`POST /api/staff/v1/employers/{employer_id}/revisions`

The endpoint requires:

- the distinct named permission `employer:draft:revise`;
- a valid UUIDv4 `Idempotency-Key` header;
- an exact request body containing only strict non-boolean integer `expected_version` in `1..2,147,483,646`, `display_name`, and `employer_type`;
- an existing Employer whose lifecycle status is `draft`; and
- an atomic expected-version comparison.

The endpoint does not accept actor identity, lifecycle status, source channel, timestamps, system IDs, version output, contacts, worksites, staffing requests, notes, or arbitrary patch operations from the caller.

`employer:read` does not imply revision authority. Role labels do not imply either permission. The synthetic/local principal receives the new named permission only to exercise this bounded tracer.

### 2. Normalization, no-op, and concurrency semantics

The server applies the same NFC normalization, outer-whitespace trimming, code-point bound, control-character rejection, and exact Employer-type allowlist used by create.

A fresh revision is accepted only when at least one normalized field differs from the current row. A no-op request returns a safe definitive `422` and performs no receipt, Employer, or audit write.

The authoritative write is a compare-and-swap operation equivalent to:

- exact `employer_id`;
- lifecycle status `draft`; and
- `version = expected_version`.

After authorization and normalization, an identical existing receipt is resolved before current version/no-op evaluation, so a valid retry cannot be reclassified by later state. For a fresh command, a failed compare-and-swap is classified in this order: absent Employer → `404`; lifecycle/version mismatch → `412`; matching version with unchanged normalized fields → no-op `422`. The transaction rolls back the newly reserved receipt for every fresh-command failure. Thus stale state takes precedence over apparent no-op equality.

One successful command increments the version by exactly one, assigns `updated_at` from the server clock, and assigns `updated_by` from the authenticated staff principal. Competing commands with the same expected version cannot both commit. A stale or non-draft expected-version conflict returns a safe `412` and performs no writes; `409` remains reserved for an idempotency-key conflict.

The application concurrency contract is PostgreSQL `READ COMMITTED`. Qualification must assert `SHOW transaction_isolation = 'read committed'` on each independent race-test connection. Same-key and distinct-key tests use two independent sessions/transactions plus a synchronization barrier immediately before receipt reservation/CAS. This slice does not claim `REPEATABLE READ` or `SERIALIZABLE` support and does not add implicit serialization retries.

### 3. Idempotency and replay after later mutation

Receipts remain append-only and actor-, command-type-, schema-version-, result-entity-, and normalized-payload-bound. The revision request fingerprint includes the path `employer_id`, `expected_version`, normalized `display_name`, and `employer_type`; it never includes caller-supplied actor data.

Each receipt records `result_record_version`, the Employer version committed by that command, and `result_event_type`, the one audit event type the fresh command is authorized to append. A database check binds `create_draft_employer` to `employer.created` and `revise_draft_employer` to `employer.draft_revised`; independent allowlists are insufficient. Existing create receipts are backfilled to version `1` and `employer.created`.

A valid identical replay:

- never performs another Employer or audit write;
- returns HTTP `200` for revision (`201` remains the create status);
- returns the **current authoritative minimized Employer representation**, not a stored historical draft snapshot;
- sets `Idempotency-Replayed: true`; and
- sets `Idempotency-Result-Version` to the version originally committed by that command.

Fresh create and revision responses also set `Idempotency-Result-Version`. The response body’s `version` may be greater than the header on a replay after later mutations. It must never be less. This explicitly distinguishes command-result history from current record truth without retaining historical display-name response snapshots.

Before accepting a replay, application integrity checks require: a create result version exactly `1`; a revision result version exactly `expected_version + 1`; the command-authorized result event type; the requested result entity/target; and a current Employer version at least the receipt result version. Inconsistent stored authority is a safe persistence/integrity failure, never a successful replay, `409`, or `412`.

Later-mutation replay is required for Revision itself: if revision A commits version `2` and revision B commits version `3`, replay A returns current version `3`, `Idempotency-Result-Version: 2`, and `Idempotency-Replayed: true` with no additional receipt, Employer update, or event.

#### Reconciliation with the accepted correction contract

The accepted `docs/planning/phase-1-correction-audit-event-contract.md` says an identical idempotency retry returns “the already committed result.” For this bounded Employer command family, this ADR refines that phrase to mean the immutable committed **command outcome identity**—same command, target, actor, canonical payload, and original `result_record_version`—rather than a stored historical HTTP representation. The replay transport returns that original result-version metadata together with current authoritative Employer detail. It never substitutes a later version as the command's result and never creates another write/event.

This planning publication amends the correction contract with this interpretation and forward-links ADR-0007. The accepted ADR, paired plan, and reconciled correction contract must durably merge together before implementation activation. If reviewers instead require historical response snapshots, this ADR and plan must be revised before publication; implementation may not choose semantics ad hoc.

Reuse of one key with a different actor, command type, schema version, target Employer, expected version, or normalized payload returns the existing safe idempotency `409` and performs no writes.

### 4. Current-state attribution

Add required `updated_at` and `updated_by` columns to `employers`. Existing rows are backfilled from `created_at` and `created_by`. Create assigns both created and updated attribution to the same server-controlled values.

`version` and `updated_at` are exposed and retained in the frontend exact-detail contract because the browser needs expected-version authority and current-state freshness. `updated_by` remains internal by default and is not added to routine browser responses. Search results remain minimized and do not gain either actor identifier or additional timestamp fields.

### 5. Audit evidence and database correspondence

A successful fresh revision appends exactly one `employer.draft_revised` audit event in the same transaction as the Employer update and receipt. A replay appends none.

For the bounded revision event:

- `entity_sequence` equals `new_record_version`;
- `prior_record_version = expected_version`;
- `new_record_version = expected_version + 1`;
- `actor_id` is the authenticated staff actor;
- `command_id` and correlation ID are the idempotency key;
- `changed_fields.field_names` contains only the actually changed names, in deterministic order; and
- `changed_fields` contains no display-name value, old/new row snapshot, request body, or unrestricted source text.

Receipt/event correspondence is bidirectional and exactly one-to-one over `(command_id, result/entity_id, result/new_record_version, result/event_type, actor_id)`. `command_receipts` and `audit_events` each expose an exact five-column unique target. An audit-to-receipt composite FK prevents mismatched or unauthorized events; a reverse receipt-to-audit composite FK prevents an orphan committed receipt from consuming a key without its required event. Both cyclic FKs are `DEFERRABLE INITIALLY DEFERRED`, allowing receipt and event insertion in one transaction while requiring the complete pair at commit. Database checks also enforce positive receipt versions, `event_schema_name = event_type`, `correlation_id = command_id`, one-step audit version advancement, and `entity_sequence = new_record_version` for the permitted Employer events.

This event is evidence of an explicit persisted staff save, not per-keystroke history and not a user-facing audit timeline.

### 6. API response and failure contract

Successful fresh and replayed revisions return the existing minimized Employer detail shape extended with `updated_at`. Responses and safe problem details retain `Cache-Control: no-store`.

Create `201`, revision `200`, and exact-detail `200` use `application/json` and the exact success object below; no other fields are permitted:

```json
{
  "employer_id": "UUID",
  "employer_type": "household|business",
  "display_name": "normalized string",
  "lifecycle_status": "draft",
  "source_channel": "staff_entry",
  "version": 1,
  "received_at": "RFC3339 timestamp",
  "created_at": "RFC3339 timestamp",
  "updated_at": "RFC3339 timestamp"
}
```

Fresh Create remains `201`; fresh Revision is `200`. Both set `Idempotency-Result-Version` to the committed result version and omit `Idempotency-Replayed`. Identical replay preserves the route's status, sets `Idempotency-Replayed: true`, and keeps the original result-version header while returning current authoritative body truth. Existing search remains `200` with its exact minimized page shape and receives no new mutation headers.

Search `200` uses `application/json`, `Cache-Control: no-store`, no idempotency mutation headers, and exactly this page shape; an empty `items` list and `null` cursor are valid:

```json
{
  "items": [
    {
      "employer_id": "UUID",
      "employer_type": "household|business",
      "display_name": "normalized string",
      "lifecycle_status": "draft",
      "version": 1,
      "received_at": "RFC3339 timestamp"
    }
  ],
  "next_cursor": "opaque string or null"
}
```

The bounded failure classes are:

- `400`: invalid idempotency key;
- `403`: missing revision permission;
- `404`: Employer not found;
- `409`: idempotency-key conflict, with no sensitive values;
- `412`: stale/non-draft expected-version conflict, with no sensitive values;
- `422`: invalid body or normalized no-op;
- `503`: known persistence unavailability; and
- `500`: bounded unexpected failure.

The browser does not inspect problem-detail bodies to make authority decisions. A `412` is a definitive no-commit stale result and requires canonical detail reload before a new command may be created. A `409` blocks the conflicting command identity and also requires canonical detail reload before changed authority is created.

Every problem below is `application/json`, has `Cache-Control: no-store`, and contains exactly `{type,title,detail,status}` with no dynamic value. Definitive `400`, `403`, `404`, `409`, `412`, and `422` command outcomes perform no Employer/receipt/event write. A mutation `500` or `503` remains an unknown outcome at the browser boundary; the transport response must not be used to claim no commit. Search and Detail are read-only for every status.

| Condition | Status | `type` | `title` | `detail` |
|---|---:|---|---|---|
| invalid/missing idempotency key | 400 | `https://golden-rose.local/problems/invalid-idempotency-key` | `Bad Request` | `invalid idempotency key` |
| denied revision permission | 403 | `https://golden-rose.local/problems/forbidden` | `Forbidden` | `forbidden` |
| authorized Employer absent | 404 | `https://golden-rose.local/problems/employer-not-found` | `Not Found` | `employer not found` |
| idempotency actor/type/target/version/payload conflict | 409 | `https://golden-rose.local/problems/idempotency-conflict` | `Conflict` | `idempotency conflict` |
| stale/non-draft expected-version precondition | 412 | `https://golden-rose.local/problems/employer-version-conflict` | `Precondition Failed` | `employer version conflict` |
| malformed path/body, unknown fields, or schema validation | 422 | `https://golden-rose.local/problems/request-validation` | `Unprocessable Entity` | `request validation failed` |
| normalized no-op | 422 | `https://golden-rose.local/problems/employer-revision-noop` | `Unprocessable Entity` | `employer revision requires a change` |
| known persistence failure | 503 | `https://golden-rose.local/problems/service-unavailable` | `Service Unavailable` | `service unavailable` |
| bounded unexpected failure | 500 | `https://golden-rose.local/problems/internal-error` | `Internal Server Error` | `internal server error` |

The two new domain bodies are therefore literally:

```json
{
  "type": "https://golden-rose.local/problems/employer-version-conflict",
  "title": "Precondition Failed",
  "detail": "employer version conflict",
  "status": 412
}
```

```json
{
  "type": "https://golden-rose.local/problems/employer-revision-noop",
  "title": "Unprocessable Entity",
  "detail": "employer revision requires a change",
  "status": 422
}
```

Authorization is evaluated before existence, lifecycle, version, or no-op behavior. The stale/non-draft problem intentionally does not disclose which precondition failed.

#### Literal existing-route and revision compatibility matrix

In every row, `Content-Type` is `application/json` and `Cache-Control` is `no-store`. Each named problem means the complete four-field body in the corresponding problem-table row above, not a partial body. No failure emits `Idempotency-Replayed` or `Idempotency-Result-Version`.

**Create — `POST /api/staff/v1/employers`**

| Outcome | Status/body | Mutation headers | Authority/write obligation |
|---|---|---|---|
| fresh success | `201`; exact Employer success object | `Idempotency-Result-Version: 1`; no replay header | one Employer, receipt, and `employer.created` event |
| identical replay | `201`; current exact Employer success object | `Idempotency-Replayed: true`; original `Idempotency-Result-Version` | no new write |
| invalid/missing key | `400`; exact invalid-key problem | none | definitive no-write |
| denied permission | `403`; exact forbidden problem | none | definitive no-write before record/receipt access |
| changed-key authority | `409`; exact idempotency-conflict problem | none | definitive no-write |
| malformed/unknown body | `422`; exact request-validation problem | none | definitive no-write |
| known persistence failure | `503`; exact service-unavailable problem | none | transport-unknown; application rollback is tested separately |
| bounded unexpected failure | `500`; exact internal-error problem | none | transport-unknown |

**Search — `POST /api/staff/v1/employers/search`**

| Outcome | Status/body | Mutation headers | Authority/write obligation |
|---|---|---|---|
| success | `200`; exact Search page object above | none | read-only; no domain/audit write |
| denied permission | `403`; exact forbidden problem | none | read-only |
| malformed query/cursor/body | `422`; exact request-validation problem | none | read-only |
| persistence failure | `503`; exact service-unavailable problem | none | read-only |
| bounded unexpected failure | `500`; exact internal-error problem | none | read-only |

**Detail — `GET /api/staff/v1/employers/{employer_id}`**

| Outcome | Status/body | Mutation headers | Authority/write obligation |
|---|---|---|---|
| success | `200`; exact Employer success object | none | read-only; no domain/audit write |
| malformed path UUID | `422`; exact request-validation problem | none | read-only |
| denied permission | `403`; exact forbidden problem | none | read-only; denial precedes disclosure |
| authorized Employer absent | `404`; exact employer-not-found problem | none | read-only |
| persistence failure | `503`; exact service-unavailable problem | none | read-only |
| bounded unexpected failure | `500`; exact internal-error problem | none | read-only |

**Revision — `POST /api/staff/v1/employers/{employer_id}/revisions`**

| Outcome | Status/body | Mutation headers | Authority/write obligation |
|---|---|---|---|
| fresh success | `200`; exact Employer success object | committed `Idempotency-Result-Version`; no replay header | one CAS update, one receipt, one `employer.draft_revised` event |
| identical replay | `200`; current exact Employer success object | `Idempotency-Replayed: true`; original `Idempotency-Result-Version` | no new write |
| invalid/missing key | `400`; exact invalid-key problem | none | definitive no-write |
| denied permission | `403`; exact forbidden problem | none | definitive no-write before record/receipt access |
| authorized Employer absent | `404`; exact employer-not-found problem | none | definitive no-write |
| changed-key authority | `409`; exact idempotency-conflict problem | none | definitive no-write |
| stale/non-draft | `412`; exact employer-version-conflict problem | none | definitive no-write |
| malformed path/body | `422`; exact request-validation problem | none | definitive no-write |
| normalized no-op | `422`; exact employer-revision-noop problem | none | definitive no-write; command key unconsumed |
| known persistence failure | `503`; exact service-unavailable problem | none | transport-unknown; application rollback is tested separately |
| bounded unexpected failure | `500`; exact internal-error problem | none | transport-unknown |

Compatibility tests must prove existing create/search/detail status codes, media types, exact fields, no-store behavior, and write boundaries remain unchanged except for the approved `updated_at` response field and Create's new idempotency-result-version metadata. Malformed revision path UUIDs use the exact request-validation `422` and produce no writes.

### 7. Browser authority state machine

Editing is explicit and inline from a selected exact Employer detail. The edit form starts from the authoritative detail fields and version. A new UUIDv4 command key is created only after local validation and no-op checks pass.

`EmployerWorkspace` owns one synchronous workspace-level command-owner ref and generation shared bidirectionally by Create and Revision. Both child handlers must acquire authority synchronously before dispatch, report every pending/unknown/conflict/recovery transition to the parent, and release only when their owner and generation still match. DOM disabled state is presentation, not the lock. Create and revision therefore cannot begin concurrently or bypass exclusion through same-tick handler activation. While a revision is pending or has an unknown outcome:

Search and Revision use separate sibling `<form>` elements. The search form contains only search controls; results, selected exact detail, and the revision form are outside it. Revision submit therefore cannot bubble into search submit. Every search submit, result selection, pagination, search retry, detail retry, and other read-capable handler also checks the synchronous workspace owner ref before creating an operation, so same-tick activation cannot bypass disabled-state rerendering. Acquiring Revision authority immediately retires read generations and aborts active **read** controllers before dispatching the non-abortable mutation.

- the target, expected version, normalized payload, and command key are frozen;
- competing create, search, selection, pagination, edit, retry, and abandon controls are disabled; language switching may remain enabled because authority state stores canonical enums rather than translated text;
- only one authority operation may run;
- navigation receives the existing bounded `beforeunload` warning; and
- the dispatched mutation is not aborted or sent with `keepalive`; the workspace `pagehide` listener synchronously increments the shared authority/read generation before queued completions can update state, directly retires active read controllers, and then clears visible child state; persisted restore uses the closeout’s canonical reload boundary.

A transport failure, unreadable success, unclassified status, `500`, or `503` is an unknown outcome. The operator may either retry the exact frozen command or reload canonical detail. A successful canonical reload replaces local detail and releases the frozen attempt; it does not infer whether the prior command succeeded from field equality.

Unknown and idempotency-conflict recovery retain the frozen values only in memory for same-attempt authority; submitted name/type values are removed from disabled form controls and are not echoed into recovery copy, attributes, diagnostics, URLs, or storage.

A `412` releases the stale command identity and enters stale-refreshing; editing remains disabled until exact detail reload succeeds. A `409` freezes the conflicting identity and offers canonical detail reload, not a new-key blind retry. After reload, a later edit uses the newly read version and a new command key.

A direct command `404` and an exact-detail-refresh `404` are distinct transitions but both are canonical terminal outcomes: clear selected detail, result/cursor/submitted-search authority, and the frozen attempt; release the workspace owner; announce not-found; and require a new search plus accepted exact detail before Edit can reappear. Other exact-detail refresh failures retain the applicable unknown/conflict/stale or confirmed-save recovery state.

A definitive `400`, `403`, or `422` never produces automatic retry. It synchronously invalidates the attempt generation, clears the frozen command key, releases only the matching workspace owner/generation, rejects late completion, and retains only editable values. After correction or later authorization, the next locally valid submit creates a fresh UUIDv4 key; it cannot reuse the definitively retired key. Not-found disposition remains the canonical terminal transition above. A valid `200` confirms the command but its mutation body is not rendered as the final displayed truth. In one parent-owned transition, the browser synchronously retires all active search/pagination/detail controllers and generations; clears results, cursor, pagination failure, submitted-search authority, and old selected detail; preserves only editable search inputs; then performs an exact detail `GET`. Exact detail and revision success/recovery are rendered independently from the conditional search-results tree so result invalidation cannot unmount them. Accepted refreshed detail must match the target and have a version at least as high as both the acknowledged body version and `Idempotency-Result-Version`. Every late read completion is rejected. Results must be explicitly rerun.

If the exact detail read fails after a confirmed `200`, the save is not reclassified as unknown and the command is not retried. The browser presents a localized `save confirmed; refresh failed` state, keeps editing and competing Employer authority disabled, and permits only exact-detail refresh retry until current truth is accepted.

The parent owns one explicit focus target for each transition. On successful refresh, the localized revision-success heading remains rendered and receives final focus; ordinary detail autofocus is suppressed or sequenced so it cannot steal focus. Forbidden, not-found, stale, conflict, unknown, confirmed-save refresh failure, and search-invalidated states each have bounded localized focus/live-region behavior.

All new states, instructions, controls, validation, conflict, unknown-outcome, reload, success, and focus behavior have English/Spanish functional parity and automated accessibility coverage. Human browser, manual accessibility, and fluent-language qualification remain deferred until a shared deployable `develop` environment exists and are required before promotion/client acceptance.

## Consequences

### Positive

- The first correction path is narrow, attributable, replay-safe, and concurrency-safe.
- Current record truth remains separate from command-result history.
- Historical display-name response snapshots are not retained solely for idempotency.
- Database constraints bind receipt, Employer, audit entity, and committed record version.
- Browser retries cannot silently create competing revision authority.
- Search results cannot remain presented as current after a revision changes their filter membership.

### Costs

- The first revision requires a migration, shared idempotency refactor, and explicit browser state machine.
- Existing create response and replay tests must evolve to account for `updated_at` and command-result-version metadata.
- A conservative `409` browser response requires a canonical reload even for rare idempotency-key conflicts.
- The historical planning packet was rebaselined on exact merged closeout tip `7ae448e`; PR #16 and PR #17 subsequently completed planning and implementation promotion.

## Alternatives rejected

### Store complete historical API response snapshots in command receipts

Rejected because it retains prior draft display names and response bodies solely to reproduce transport history. Current-authoritative representation plus original result-version metadata is sufficient and more privacy-conscious.

### Return the current Employer on replay without command-result metadata

Rejected because it conceals whether the replayed command originally produced the returned version.

### Use generic `PATCH /employers/{id}`

Rejected because it invites field and lifecycle expansion, weakens command semantics, and obscures idempotency/audit authority.

### Allow last-write-wins

Rejected because concurrent staff corrections could silently overwrite one another.

### Retry a conflict with a new key automatically

Rejected because it can convert an uncertain or stale operation into a second authority without deliberate canonical reload and review.

### Keep stale search results after success

Rejected because changing name or type can invalidate membership in the submitted filter and pagination set.

### Retain old and new display-name values in audit history

Rejected for this draft save because the accepted correction contract does not require every prior draft value and data minimization favors field-name evidence.

## Non-scope

This decision does not authorize:

- contacts, worksites, staffing requests, shift needs, notes, files, documents, or source-text fields;
- lifecycle submission, review, cancellation, closure, reopen, or deletion;
- audit-history read UI or export;
- public Employer or worker access;
- identity-provider, MFA, delegated-role, or production authorization integration;
- automatic matching, ranking, eligibility, hiring, referral, or assignment;
- live/client data, deployment, infrastructure, service startup, or production database roles;
- offline persistence, service workers, local/session storage, URL-carried Employer values, or client caches; or
- human browser/accessibility/fluent-language qualification before a shared deployed environment exists.

## Historical implementation activation gate

Beatrice accepted this bounded planning direction for planning-only publication. The following activation gate was completed before PR #17 implementation:

1. **Completed:** the Employer-workspace closeout was independently rereviewed, committed, exact-head qualified, exact-range scanned, merged to `develop` by PR #15, fetched, and used as this branch's exact base;
2. **Completed:** ADR-0007 and Alembic `0003` remain free, merged predecessor paths/nodes were reinspected, and contract/path drift was reconciled;
3. **Completed:** this ADR, its implementation plan, replay-contract reconciliation, ADR index, technology register, and planning-status living-document changes received independent post-rebaseline review;
4. **Completed:** every High/Blocker planning finding was remediated;
5. **Completed:** every Medium planning finding was remediated or explicitly accepted by Beatrice with rationale and owner;
6. **Completed:** PR #16 committed, qualified, scanned, reviewed, and merged the planning packet to `develop` at `1c66eeb`;
7. **Completed:** a fresh fetch verified the exact accepted packet on merged `origin/develop`; and
8. **Completed:** Beatrice authorized implementation from a fresh branch based on `1c66eeb`, and PR #17 merged the resulting bounded implementation at `1543248`.

## Post-merge remediation addendum — 2026-08-11

Independent audit of exact merged PR #17 found no Blocker or High issue and two Medium correctness/authority defects:

1. the revision browser client validated a successful response against the response's own `employer_id` rather than the Employer ID requested in the path, so a valid-shaped cross-target response could be accepted as authoritative; and
2. fresh-command no-op detection and `changed_fields` derivation occurred before receipt reservation/compare-and-swap, allowing a future-version catch-up under PostgreSQL `READ COMMITTED` to turn a semantic no-op into an extra version and inaccurate audit evidence.

The bounded remediation requires the browser parser to bind accepted success to the requested Employer ID. On the backend, fresh commands must reserve their receipt first, then lock and read the exact current draft row at `expected_version`, derive no-op and changed-field authority from that locked row, and only then perform the compare-and-swap, audit append, and commit. If the locked current values already equal the submitted normalized values, the reserved receipt must roll back and the command must remain a no-op. Known SQLAlchemy persistence failures must roll back and cross the API boundary only as value-safe service-unavailable problems.

This addendum does not alter endpoint shape, accepted fields, lifecycle scope, permission, idempotency binding, replay semantics, minimized audit payload, browser recovery contract, or any non-scope above. A fresh independent rereview and complete quality/security gate are required before this remediation may be committed, pushed, or proposed for merge. No next product slice may start before that closeout merges and the repository is rebaselined from exact protected `develop`.
