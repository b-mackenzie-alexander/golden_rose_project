# Post-intake next-step investigation — 2026-09-15

## Delivery position

- **Staffing:** One independent developer; automated checks and fresh agent reviews are quality evidence, not independent-human authorization.
- **Human-visible outcome:** PR #105 merged at `develop@2736c48b4835a0201a2e0a64dd6a297a375517f8`; source PRs A–D are complete. Bounded local browser qualification is recorded; the owner preview and historical shared cloud runtime were not rechecked in this investigation.
- **Gate budget:** Investigation/documentation only. Shared synthetic deployment requires one fresh bounded packet; live data and production remain separate.
- **Next executable action:** Agree the next outcome-scale source tranche around the deferred usability directions below, then write its concrete route/data/time-handling acceptance contract.
- **Do not regress:** Original finalized history, exact retries, dirty buffers, restricted field/record access, bilingual parity, applied migrations and private runtime/access custody.

## Follow-up source repair preserved for PR

After the owner’s local-preview walkthrough, the first usability blocker was repaired in source for preservation in a follow-up PR. Worker intake now has a catalog-backed common-position dropdown, repeated manual work-interest rows, stable first/middle/last name entry over the existing `full_name` contract, US phone normalization, simplified availability choices, named-day time blocks, duplicate time-block suppression, Anytime/copy controls, implicit US address country, inline red field guidance after failed worker detail saves, local 12-hour intake-history timestamps and clearer finalization matching copy.

This follow-up remains local source work until its PR is merged. It does not deploy a shared runtime, activate production permissions or complete the broader timezone/settings, ongoing Employer workspace or request/shift-demand work described below.

## Observed baseline

GitHub confirms PR #105 merged on 2026-09-15 at 20:51:16 UTC. Its final-head application, build validation, repository hygiene and branch-policy checks passed. Fresh `origin/develop` is `2736c48`; its tree matches the verified PR D feature head. No product code or runtime was changed during this investigation.

The accepted intake plan ends with PR D. Remaining human/fluent-language, assistive-technology and shared-target evidence must not be checked off merely because its source is merged. `ROADMAP.md` now closes PR D delivery and ordered A–D source implementation.

## Recommended next outcome: usable ongoing staff workspace

The owner's [deferred feedback](staff-intake-ux-polish-follow-up.md) explicitly requested reassessment after PR D. The first local-preview repair covers the entry/save blockers below; remaining broader timezone/settings, ongoing-record and request/shift-demand work still needs an accepted implementation plan.

### 0. Local preview feedback: intake entry must become savable and diagnosable

**Observed during owner walkthrough on 2026-09-15:** The Worker Entry work-interests section does not provide a usable way to select common agency placement items or manually enter a new item; it appears as a greyed-out field. The owner suspects this may be blocking backend save, and also reports that saving details is not working at all, including on the employer intake page.

**Priority outcome:** Staff must be able to enter worker interests using common agency placement options and a bounded manual entry path, then save worker and employer intake details to the backend. When save fails, the UI must identify the affected field or section and give actionable guidance instead of only reporting that changes were not saved. The follow-up source repair implements the initial worker-intake version of this outcome for local preview.

**Acceptance shape for the next plan:** Reproduce the failure against the current local preview and classify whether save failure comes from disabled controls, missing/invalid work-interest payloads, backend validation, stale readiness/schema checks, or incomplete UI validation mapping. The fix should include field-level error display, section-level status, retry behavior that preserves unsaved input, and English/Spanish parity. This is a blocker for a useful next feedback round.

**Availability feedback:** Because these are internal agency forms, availability choices should fit staff entry rather than a self-service worker form. The owner wants the primary choices simplified to Unknown, Flexible, or Specific days. "Flexible--discuss with staff" remains meaningful, but should not read as if the worker is filling out the form unaided.

**Specific-day feedback:** The current weekly entry model is too clunky for staff use. Staff should not have to enter "Monday = 1, Sunday = 7" and then manage time fields indirectly. A cleaner day/time editor should support selecting named days and adding one or more time blocks. It must also account for workers who are available irregularly or opportunistically, such as people who come in on a given day wanting work without a stable recurring Wednesday-style schedule.

**Deferred UI feedback:** Search refinement across dashboard pages is a real usability issue, but should follow the entry/save/validation work unless investigation shows search blocks the intake workflow.

### 1. Employer record navigation and ongoing maintenance

**Observed:** `apps/web/src/app/App.tsx` defaults to `/employers`; `EmployerDetail.tsx` displays name, type, lifecycle and source. Rich current-facts/correction screens use `/staff/intakes/:intakeId/outputs/:output` and resolve original finalization references in `CanonicalOutput.tsx`.

**Proposed outcome:** Intake remains onboarding/review; Employers becomes the place to find an existing employer and reach its authorized current contacts, worksite and requests, with clear access back to provenance and review history.

**Design work required:** Inventory existing canonical APIs and bounded child queries before choosing routes. Support employers created through the earlier direct-create path as well as finalized intakes; do not assume every employer has one intake or arbitrarily choose a contact/worksite. Establish how repeated intakes and multiple related records are selected. Retain restricted reveal and no-overwrite behavior. This is more than renaming navigation links.

### 2. Local-time controls and configuration

**Observed:** `IntakeFields.tsx` asks for start/end instants with a UTC offset. `IntakeWorkflow.tsx`, `IntakeWorkspace.tsx` and `IntakeHistory.tsx` render raw follow-up/history instants. No settings component was found in the inspected source tree.

**Proposed outcome:** A visible display/input timezone setting, initially `America/New_York`, normal local date/time controls, localized history and automatic conversion for absolute instants.

**Contract to settle:** Define whether the preference lasts only for the session, on one device, or across authenticated sessions. Existing privacy controls deliberately avoid browser storage; do not introduce persistence incidentally. Distinguish absolute instants, date-only values and recurring weekly local schedules. Changing display timezone must not silently rewrite drafts, original retry payloads or source schedule timezones. Reject nonexistent spring-forward times and require explicit resolution of ambiguous fall-back times. Preserve date-only semantics.

### 3. Finish deferred intake feedback

Reproduce the previously recorded issues on merged source before changing code:

- Consistent action-button, disabled, pending and keyboard-focus styles.
- English/Spanish field-level validation and completeness guidance.
- Refresh draft discovery after acknowledged creation while preserving applied filters, valid cursors and dirty buffers.

The deferred note is now included for continuity with the prior browser evidence. These observations are historical unless reproduced during the current local-preview repair or a later plan.

### Suggested implementation split

One accepted outcome-scale plan can cover: (1) savable intake entry, work-interest controls, availability/day-time controls, field-level save guidance and timezone controls, then (2) ongoing employer-record navigation and maintenance. Keep each PR independently reviewable; a bounded existing-API design is preferable where feasible. Concrete API additions, persistence policy and acceptance cases must be established before coding. This investigation does not approve a new dependency or schema.

## Next functional outcome: draft request to operational demand

**Observed:** Intake finalization creates one draft StaffingRequest and no ShiftNeed. The accepted [request/shift model](phase-1-request-shift-state-model.md) requires at least one governed shift before request submission. Intake review and current-facts re-review are not request-opening authorization.

**Proposed ordered tranche:**

1. Governed shift occurrence entry/read/correction with start/end, originating timezone and worker count; preserve request links and attribution.
2. Server-enforced request/shift review and lifecycle transitions with requiredness and permissions; handle cancellation and terminal outcomes coherently.
3. An authorization-scoped request work queue derived from authoritative records and follow-up history. Use truthful elapsed-time indicators until a validated business calendar supports stronger claims.
4. Derived calendar/coverage views once authoritative timed shifts and transitions exist; never create a parallel calendar record store.

Use the existing [queue model](phase-1-work-queue-aging-follow-up-model.md) and [calendar contract](phase-1-calendar-coverage-semantics.md) as inputs to an implementation-ready plan. Do not invent shift occurrences from an intake schedule description, infer placement, or add automated matching. This tranche materially expands the current schema/authority and is outside PR D.

## Human feedback and rollout

After the usability source tranche, create an approved current-source local feedback target and exercise both onboarding and ongoing-record journeys. Preserve the owner's existing preview until an explicit replacement/cleanup decision; its current availability is unknown.

If remote/shared testing is the next priority, prepare one fresh bounded fictional-synthetic deployment packet for the exact merged release: migration, explicit synthetic permissions, immutable artifact, access and qualification. Source merge alone neither deploys the features nor activates permissions. Manual accessibility, fluent-language and shared-target acceptance remain open.

Production identity/MFA, live-data governance and support/recovery remain prerequisites for live use. They do not need to block this bounded synthetic usability work. Maps, OCR/uploads, worker matching and broad reporting are not recommended additions to this next tranche.

## Verification of this investigation

Initial investigation used read-only GitHub merge/check readback, refreshed integration ref, source/document inspection and documentation whitespace validation. The follow-up source repair added focused and full frontend verification before PR preservation. No cloud was inspected, no shared runtime was deployed and no live/production data was used.
