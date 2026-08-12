# Phase 1 EmployerContact Next-Session Plan

> **For Hermes:** Treat this as the next-session planning artifact after the PR #17 post-merge remediation closeout. Do not start coding from this file until the remediation PR merges to `develop`, the exact merged tip is rebaselined locally, and the prerequisite decisions below are recorded in the controlling ADR/living docs.

**Goal:** Prepare the smallest honest next coding lane after the draft-Employer revision remediation: a synthetic/local, backend-only `EmployerContact` create + exact-read tracer nested under an existing draft Employer.

**Architecture:** Keep the next product slice backend/API only. Reuse the existing authority spine pattern—permission gate, strict request contract, idempotent command receipt, current-row authority, and minimized audit evidence—but stop before implementation if the repo has not yet approved multi-entity receipt/audit authority or draft-stage contact requiredness. This plan is intentionally split into a short decision/preflight phase and a bounded implementation phase so the next session can halt honestly if governance inputs are still missing.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, pytest, Ruff, mypy, Bandit; no browser work in this slice.

---

## Current truth

- PR #17 is merged at `1543248`.
- The draft-Employer revision post-merge remediation is separately prepared on `fix/draft-employer-revision-post-merge` and must merge before this plan becomes executable.
- The best next product candidate, after that closeout, is a nested `EmployerContact` tracer rather than Worksite, StaffingRequest, or auth expansion.
- This slice is **not executable yet** unless the next session confirms the decision gates below.

## Decision gates — must pass before Task 1

1. **Closeout merged:** the post-merge remediation PR from `fix/draft-employer-revision-post-merge` is merged to `develop`, fetched locally, and the next coding branch is created from that exact merged tip.
2. **Field-requiredness decision recorded:** the controlling docs explicitly state the first allowed client-supplied contact fields and requiredness. At minimum, decide whether:
   - `full_name` alone is allowed;
   - phone and email are both optional;
   - at least one contact method is required; and
   - title/role belongs in the first tracer or is deferred.
3. **Draft contact lifecycle decision recorded:** either define the initial contact lifecycle/status contract or explicitly exclude contact status from the first tracer.
4. **Permission decision recorded:** define the exact named permissions for contact create and contact read, and whether parent `employer:read` is sufficient for nested exact-read.
5. **Multi-entity authority decision recorded:** approve how receipts/audit authority expand beyond `Employer`-only constraints. Do not invent this inside migration `0004`.
6. **New ADR accepted:** a reviewed ADR for the first `EmployerContact` slice exists and is merged or accepted per the repo’s current planning gate.

If any gate is unresolved, the next session should stop after updating docs/plan status rather than guessing and coding.

## Exact non-scope

- Worksites, exact addresses, CDTA/service zones, maps, or reveal permissions.
- Staffing requests, shifts, assignment/referral behavior, queue/calendar logic.
- Browser routes, React forms, frontend API clients, localization, or accessibility work.
- Contact search/list/export, contact editing, deletion, supersession, or post-submission correction.
- Messaging vendors, notifications, consent, outreach, or communications delivery.
- Public access, real identity-provider/MFA/session work.
- Live/client data, deployment, GCP, imports/migrations from legacy systems, documents/files.
- Audit-history UI or unrestricted raw contact values in ordinary audit/log output.

## Proposed bounded product contract

### Create command

- `POST /api/staff/v1/employers/{employer_id}/contacts`
- Parent Employer must exist, be authorized, and remain in `draft` status.
- Strict request body with only the approved first-tracer fields.
- Idempotency key required.
- Server owns IDs, attribution, timestamps, and version.
- One atomic write of:
  - nested `EmployerContact`
  - `CommandReceipt`
  - minimized `employer_contact.created` audit event
- Strict `Cache-Control: no-store`.

### Exact read

- `GET /api/staff/v1/employers/{employer_id}/contacts/{contact_id}`
- Parent-scoped lookup only; no global contact detail endpoint.
- Authorization checked before read.
- Fixed response shape; reject leaked fields at API contract tests.
- No list/search/pagination in this first tracer.

## Likely files

### New / modified production files

- `migrations/versions/0004_*.py`
- `src/golden_rose/persistence/models.py`
- `src/golden_rose/persistence/command_receipts.py`
- `src/golden_rose/persistence/audit_events.py`
- `src/golden_rose/persistence/employers.py`
- `src/golden_rose/persistence/employer_contacts.py` (new)
- `src/golden_rose/application/create_employer_contact.py` (new)
- `src/golden_rose/application/get_employer_contact.py` (new)
- `src/golden_rose/auth/permissions.py`
- `src/golden_rose/api/dependencies.py`
- `src/golden_rose/api/staff/schemas.py`
- `src/golden_rose/api/staff/employer_contacts.py` (new, preferred)
- `src/golden_rose/main.py`

### Required tests

- `tests/integration/test_initial_migration.py`
- `tests/integration/application/test_create_employer_contact.py` (new)
- `tests/integration/application/test_get_employer_contact.py` (new)
- `tests/integration/api/test_staff_employer_contacts.py` (new)
- `tests/unit/api/test_employer_contact_schemas.py` (new if needed)
- `tests/unit/application/test_create_employer_contact.py` (new if needed for normalization/decision logic)

## Next-session task list

### Task 0: Rebaseline and decision audit

**Objective:** Prove the closeout merged and that the contact slice is actually authorized to start.

**Files:**
- Read: `CURRENT_WORK.md`
- Read: `ROADMAP.md`
- Read: `TECHNICAL_REQUIREMENTS.md`
- Read: `TECHNOLOGY_DECISIONS.md`
- Read: `docs/planning/phase-1-operational-discovery-register.md`
- Read: `docs/planning/phase-1-correction-audit-event-contract.md`
- Read: the new contact ADR if present

**Steps:**
1. Fetch and verify exact merged `origin/develop` tip.
2. Confirm the remediation PR merged and create a fresh branch from that exact tip.
3. Check every decision gate above.
4. If any gate is unresolved, stop and write a small planning/status update rather than coding.

### Task 1: Write/merge the controlling ADR if still missing

**Objective:** Land the exact `EmployerContact` boundary before product code.

**Files:**
- Create or update: `docs/adr/ADR-0008-phase-1-employer-contact-boundary.md`
- Modify: `docs/adr/README.md`
- Modify: `TECHNOLOGY_DECISIONS.md`
- Modify: `CURRENT_WORK.md`
- Modify: `ROADMAP.md`
- Modify: `NOTES.md`

**Required ADR content:**
- exact accepted contact fields and requiredness
- permission model
- whether contact status exists in slice 1
- multi-entity receipt/audit authority shape
- minimized audit payload
- exact non-scope
- migration identifier reservation

### Task 2: Migration RED for multi-entity authority

**Objective:** Prove the repo can safely support a second entity without widening past the approved boundary.

**Files:**
- Create: `migrations/versions/0004_*.py`
- Modify: `tests/integration/test_initial_migration.py`

**TDD shape:**
1. Add failing migration/integrity tests for the chosen multi-entity authority model.
2. Run only those tests to capture RED.
3. Implement the minimal migration and metadata changes.
4. Re-run focused migration tests to GREEN.

### Task 3: Persistence + application create command

**Objective:** Add one idempotent nested create command under a draft Employer.

**Files:**
- Create: `src/golden_rose/persistence/employer_contacts.py`
- Create: `src/golden_rose/application/create_employer_contact.py`
- Modify: `src/golden_rose/persistence/models.py`
- Modify: `src/golden_rose/persistence/command_receipts.py`
- Modify: `src/golden_rose/persistence/audit_events.py`
- Test: `tests/integration/application/test_create_employer_contact.py`

**Required behavior:**
- parent draft-only gate
- strict normalization/validation
- idempotency conflict on changed payload/authority
- atomic contact + receipt + audit event
- no leaked contact values in ordinary error diagnostics

### Task 4: Exact parent-scoped read

**Objective:** Add one exact nested read and nothing more.

**Files:**
- Create: `src/golden_rose/application/get_employer_contact.py`
- Test: `tests/integration/application/test_get_employer_contact.py`

**Required behavior:**
- parent-scoped exact lookup only
- authorization before lookup
- no list/search route or pagination side effects

### Task 5: API boundary

**Objective:** Expose only the accepted create and exact-read routes.

**Files:**
- Create: `src/golden_rose/api/staff/employer_contacts.py`
- Modify: `src/golden_rose/api/staff/schemas.py`
- Modify: `src/golden_rose/api/dependencies.py`
- Modify: `src/golden_rose/auth/permissions.py`
- Modify: `src/golden_rose/main.py`
- Test: `tests/integration/api/test_staff_employer_contacts.py`

**Required API coverage:**
- success contracts
- strict validation failures
- parent not found vs contact not found
- permission failure
- stale/idempotency conflict if applicable
- no-store headers
- OpenAPI route surface exactness

### Task 6: Quality/security closeout

**Objective:** Prove the new slice cleanly under the repo gate.

**Minimum commands:**
- `env -u PYTHONPATH uv run ruff format --check .`
- `env -u PYTHONPATH uv run ruff check .`
- `env -u PYTHONPATH uv run mypy src tests`
- `env -u PYTHONPATH uv run bandit -q -r src`
- `env -u PYTHONPATH uv run alembic upgrade head`
- `env -u PYTHONPATH uv run pytest --cov=golden_rose --cov-report=term-missing --cov-fail-under=95`
- `env -u PYTHONPATH uv run alembic downgrade base`
- `env -u PYTHONPATH uv run alembic upgrade head`
- `env -u PYTHONPATH uv run pip-audit --skip-editable`
- frontend verification only if any frontend file was intentionally touched; otherwise do not widen the lane.

### Task 7: Documentation + handoff

**Objective:** Reconcile the authoritative packet and prepare the next review handoff.

**Files:**
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`
- `README.md`
- `ARCHITECTURE.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `docs/adr/README.md`
- `docs/review-handoffs/<dated-employer-contact-handoff>.md`

**Must preserve:**
- deferred human browser/manual accessibility/fluent-language gates
- synthetic/local-only truth
- no implied browser or deployment work
- exact non-scope

## Stop conditions

Stop immediately if any of the following occurs:
- multi-entity receipt/audit authority is still undecided;
- requiredness or permission decisions are missing;
- the slice starts requiring browser work, search/list behavior, or contact lifecycle transitions;
- migration `0004` begins carrying unreviewed architecture decisions;
- the next session cannot prove it is based on the exact merged remediation tip.

## Expected next-session deliverable

If all decision gates are satisfied, the next coding session should end with:
- one merged controlling ADR,
- one merged implementation plan/handoff if the repo still requires it,
- or one bounded backend/API EmployerContact tracer branch ready for independent review.

If the gates are not satisfied, the honest deliverable is a planning/decision closeout rather than partial product code.
