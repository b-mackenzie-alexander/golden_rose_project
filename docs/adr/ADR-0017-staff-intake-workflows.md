# ADR-0017 — Staff intake workflows

## 2026-09-14 — PR A source activation

PR #100 merged this intake planning contract at `ce38fb0`; PR #101 merged the Wave 1 UX predecessor at `9a6b66735f7261ca705f7e8ba5b7c2afcd815f92`. The owner subsequently authorized PR A implementation and disposable local PostgreSQL tests. The active branch is `feat/staff-intake-drafts` from that exact integration tip. Older docs-only/unmerged-predecessor statements below describe the planning snapshot and are superseded for this source lane. Browser UX verification is deferred until PR A is finished at the owner's request.

PR A adds only durable candidate drafts, separately authorized address sections, bounded shared recovery and typed atomic receipt/result/audit authority. Review/follow-up, links, canonical finalization and corrections remain PRs B–D. The v28 runtime is historical and remains `not_qualified`; no deployment, cloud inspection/mutation, live data or production is authorized or claimed.


**Status:** Proposed — finalized for approved docs-only publication; pending fresh review and accepted protected planning merge.
**Date:** 2026-09-14
**Owner:** Beatrice, technical delivery owner. Conversational workflow acceptance is distinct from technical approval and client/counsel/live-use acceptance.

## Delivery lock
- One independent developer; fresh agent review supplies quality evidence, not a fictional human quorum.
- v28 private fictional-synthetic develop is human-visible. The improved Wave 1 UI remains an uncommitted predecessor in the original checkout; this planning worktree neither includes nor deploys it.
- v28's one-packet approval is consumed. No cloud/database mutation, service starts, live data or production authority is granted here; future synthetic deployment needs one fresh bounded packet.
- Next: fresh-review and publish this docs-only packet independently of UI merge; both accepted protected planning merge AND preserved improved-UI merge are required before separately authorized coding from the exact merged tip.
- Do not regress existing Employer/contact APIs, ordinary demand review rights, typed authority, restricted addresses, bilingual/accessibility behavior, private SQL or deployment protections. No prominent environment disclaimers reintroduced.

## Context and evidence posture
**Observed locally:** planning HEAD `a6f0791f53f9e0d4a344cd104e6237b20ad34dbb`; existing source has Employer/contact typed authority, legacy single-primary receipt/result binding, committing creation services and migrations through `0005_database_authority.py`. Local tracking refs are not independent remote verification.

**Accepted conversational direction:** shared durable incomplete manual intake, explicit saves/resume, review/follow-up, existing identity links without silent overwrite and complete current-reviewed explicit finalization. **Proposed technical choices:** exact fields, permissions, DTOs, migration and output sets in `../planning/staff-intake-contract.md`. No implementation, deployed intake, fluent-language acceptance or counsel policy is asserted.

## Decision
Adopt one separate Intake aggregate per manual worker/employer intake, not a second editable customer master. Freeze the normative technical contract in `../planning/staff-intake-contract.md` §§2–9 and ordered implementation PRs A–D in `../../.hermes/plans/2026-09-14-staff-intake-workflows-plan.md`.

Incomplete draft Save never creates canonical records. Review binds exact content and linked dependency versions; candidate/link changes invalidate it. Distinct `intake:review` and `intake:finalize` rights apply to Owner or explicitly delegated Manager/Operations Staff; self-review is allowed. Ordinary Operations Staff request/shift review stays Allow. Restricted residence/party/worksite fields retain independent rights and protected history.

Finalization is one atomic typed operation after current authorized completeness/review/version checks. New worker emits the four §5 profile records; employer emits the precise new/reused contact/address/worksite set and one new draft request. Existing links are versioned, read-only references; no silent overwrite, automatic duplicate merge, reopening or invented child data. No ShiftNeed, open demand, assignment, referral, verification or agreed compensation is produced. Existing Employer/contact commands keep their old requiredness, DTOs, permissions and result semantics.

Implement the typed multi-result authority migration from contract §7 rather than weaken the old receipt/audit bijection or compose committing services. Reciprocal concrete event/result authority, exact cardinality, rollback, bounded concurrency/replay and least-privilege grants are mandatory source requirements. No runtime DDL is authorized by this ADR.

## Narrow supersession map
The dated staff-intake amendments in the following files supersede only their named intake omissions/deferrals upon accepted publication:
- `../planning/phase-1-canonical-field-purpose-inventory.md`: worker profile and intake candidate fields/requiredness; no assignment/payment scope.
- `../planning/phase-1-staff-permission-matrix.md`: intake review/finalize and restricted worker/party fields; no change to ordinary request review or legacy API permissions.
- `../planning/phase-1-request-shift-state-model.md`: separate intake lifecycle; no change to demand/shift guards.
- `../planning/phase-1-correction-audit-event-contract.md`: protected intake review history and exact typed multi-result finalization; legacy single-result commands preserved.
- `../planning/phase-1-work-queue-aging-follow-up-model.md`: intake-specific mandatory owner/reason/due and shared visibility; ordinary request policy preserved.
- `../planning/phase-1-operational-discovery-register.md`: manual durable intake separated from deferred scan/OCR; business/live-use questions remain open.

ADR-0002/0004/0007/0008 API boundaries are not globally superseded. ADR-0014 outcome-scale delivery and ADR-0016/v28 deployment protections remain in force. This ADR does not supersede calendar, map, service-zone, legal, public-plane or identity-provider contracts.

## Consequences and constraints
- Improves recoverable shared staff intake without inventing absent names/contact data or coupling drafts to public/customer records.
- Adds sensitive field and migration complexity; test against real disposable PostgreSQL, permission revocation and concurrent commands before claims of durability/atomicity.
- PR D includes bounded canonical corrections and current-facts re-review under contract §9; original finalized intake/review/output links remain immutable. Separate expected-version/permission/reason/audit/retry commands correct worker contact/address/preferences, current employer contact/address, worksite and request descriptions, never via intake overwrite. Broader identity/lifecycle/customer-maintenance expansion remains separate.
- Saves are section-local with immutable command identity and independent status; aggregate all-saved requires no dirty/pending/failed/unknown section. Version refresh cannot replace another section's unsaved edits. Contract §8 and plan PR A require the success-then-unknown-with-later-edits integration/browser regression.
- Real catalog, locale ergonomics, named access, retention/disposal, legal translations and operational follow-up policy remain discovery items. Synthetic technical defaults are not client policy.
- Improved dirty UI must be preserved and merged before coding, not before docs-only publication; planning publication is independent. Both merges gate coding. Do not reproduce it from a stale planning checkout. No code, deployment, live data, commit/push or automatic PR action follows this docs-only task.

## Alternatives considered
- Weaken Employer name/type or create canonical partial identities on Save: rejected; breaks existing authority and confuses candidate facts with canonical records.
- Browser-only drafts or fixture-backed durability: rejected; cannot prove shared resume or persistent finalization.
- Let linking patch existing records: rejected; silent competing authority and unaudited correction.
- Compose current committing services or store untyped output UUIDs: rejected; non-atomic publication and broken audit/result integrity.
- Combine intake review with existing demand review: rejected; falsely opens demand and changes ordinary staff rights.

## Approval, evidence and revisit triggers
Docs-only publication preparation is approved; technical acceptance/merge and independent whole-packet review remain outstanding. Local path/source and whitespace checks are planning evidence only. Root-document coverage/drift repair is owned by the parent lane, not claimed here.

Revisit for material trust/data/schema/identity/vendor changes, a Blocker/High contradicting this contract, infeasible PR decomposition, or client feedback changing workflow meaning. Routine RED/GREEN fixes do not require a new plan. Live data, public/legal features, canonical correction beyond §9 and future cloud actions keep their separate gates.
