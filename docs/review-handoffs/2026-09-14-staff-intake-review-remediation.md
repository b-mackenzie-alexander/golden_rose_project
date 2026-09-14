# Staff-intake semantic review remediation — 2026-09-14

## Delivery lock
- **Staffing:** One independent developer; fresh agent review supplies quality evidence, not independent-human authorization. Accepted solo-maintainer High remains.
- **Human-visible outcome:** Historical v28 private fictional-synthetic develop/browser evidence remains; availability/access expiry was not rechecked. Last recorded formal status is `not_qualified`. Improved UI is a preserved unmerged predecessor; intake/corrections are not implemented or deployed.
- **Gate budget:** V28 approval is consumed. Docs-only edits grant no service start, database execution, cloud inspection/mutation, live-data admission, public-plane or production authority.
- **Next executable action:** Publish the semantically reviewed documents-only packet after final staged/outgoing-range checks and secret scanning. Renewed mechanical-check approval was received and candidate scope, Markdown links and whitespace checks passed. Docs publication is independent of UI merge; accepted protected planning merge AND preserved improved-UI merge must both precede separately authorized coding from the exact merged tip.
- **Do not regress:** Preserve original dirty UI checkout, immutable finalization/review history, restricted field rights, typed receipt/audit authority, bilingual/accessibility behavior and existing deployment protections. No prominent synthetic disclaimers, identity merging, intake overwrite, fictional human quorum or restarted deployment gates.

## Current verification closeout
Fresh focused semantic rereview returned PASS with H1, M1, M2 and L1 closed and no new substantive inconsistency in the inspected scope. This is documentation-contract evidence, not implementation or exhaustive historical review. After renewed tool approval, the parent verified 23 candidate Markdown documents, 30 relative Markdown links with no missing targets, and no trailing whitespace; tracked `git diff --check` also passed. Final staged/range checks and redacted secret scanning remain publication steps. The status-only closeout changes no technical contract.

## Historical pre-rereview surface and evidence boundary
Local documentation edits in `/Users/genie/Desktop/golden_rose_intake_planning`, not a committed or published candidate. Git state, outgoing scope, paths/links, whitespace/diff hygiene and tests were deliberately not checked: mechanical verification is approval-blocked. File reads and successful documentation patches establish authored disposition only. Earlier planning verification does not cover this edit set. No clean verdict, independent acceptance or executed test evidence is asserted.

## H1 — High: post-finalization correction excluded from accepted recover/correct workflow
**Finding:** Contract/plan/ADR made new canonical outputs read-only and deferred all corrections except existing Employer revision, contradicting recover/correct and making finalized worker/contact/address/preferences/request facts unusable for normal error recovery.

**Authored disposition:** Contract §9 and plan PR D include bounded canonical correction and separate current-facts re-review. Exact API routes/DTOs, target expected versions, review-head/dependency versions, delegated permissions, restricted read plus write checks, reason, protected before/after audit, same-key replay, migration/grants and files are specified. Worker name/phone/residence/interests/availability, current employer representative/phone/household or business address, worksite address and request role/duties/count/offer/schedule descriptions are covered. Legacy EmployerContact remains unchanged; versioned ContactDetails owns the corrected current representative name. No missing-child upsert, identity merge, parent reassignment, lifecycle/reclassification, shift/open demand or pay agreement is introduced.

Original finalized intake content, original review IDs/payloads, finalization output identities/dispositions/original versions and receipts never change. Canonical detail has explicit correction controls; selected references remain read-only inside intake. Draft links must refresh/re-review after dependency changes; finalized output screens separately re-review current facts without rewriting original intake review.

**Proposed proof:** Plan PR D names unit/integration/API/migration/UI/browser nodes for every correction section, mandatory reason, exact versions, atomic audit/result/receipt, unknown retry, revoked/restricted permission, immutable originals, legacy contact compatibility, current-review staleness/re-review, concurrent correction, direct-SQL denial and populated upgrade/downgrade stops. Real app/PostgreSQL bilingual browser journey: finalize → correct → re-review → reopen and compare unchanged originals. None executed.

## M1 — Medium: one form Save versus separate section commands ambiguous
**Finding:** Ordinary content and restricted address mutations use distinct commands but the form-wide Save language could falsely report success, replace another section's dirty data on version refresh, or change command identity after an unknown outcome.

**Authored disposition:** Contract §8 explicitly requires section-local Save controls, status, immutable key/payload and edit generation. One atomic initial create is distinguished from later section saves. Pending/unknown commands serialize per intake; users may keep editing in memory. Exact original retry precedes the next command. Updated server version changes only the baseline, never another section's unsaved buffer. Aggregate all-saved is forbidden with any dirty/pending/failed/unknown section. Restricted denial is unavailable, not empty/saved; concealed values never round-trip. Canonical correction forms inherit the same rule for shared target versions.

**Proposed proof:** `tests/integration/test_intake_commands.py::test_section_success_then_unknown_retry_preserves_other_section_and_versions`; `IntakeWorkspace.test.tsx` title `keeps aggregate unsaved after one section succeeds and the next is unknown with later edits`; proposed browser `apps/web/tests/browser/staffIntakeRecovery.spec.ts` title `section success then unknown with later dirty edits never reports all saved`. Content succeeds, address commits with dropped response, content gets later edits, exact address retry creates no second event and cannot erase dirty content, only its later explicit Save clears aggregate unsaved. Verify second-session persisted facts and restricted denial in both languages. None executed.

## M2 — Medium: publication dependency contradicted active lane
**Finding:** Plan/ADR required UI merge before docs publication, whereas CURRENT_WORK allowed planning publication first.

**Authored disposition:** Plan/ADR delivery locks and active root summaries now make docs-only publication independent of UI merge. Both accepted protected planning merge and preserved improved-UI merge remain hard pre-coding dependencies. No original-checkout work, publication or coding performed.

**Proposed proof:** Fresh semantic rereview of delivery locks and next actions; later approved mechanical/reference verification. No runtime test needed to prove documentation ordering; code rebaseline remains future evidence.

## L1 — Low: EmployerContact foundation incorrectly scheduled again
**Finding:** Operational discovery register row still told staff to publish the accepted ADR-0008 plan and begin coding, despite completed foundation.

**Authored disposition:** Row now records PR #20 at `6eb05d5` as completed backend authority, preserves its regressions, and points genuine remaining current contact methods/address/correction UI/API scope to ADR-0017 ContactDetails and PRs C/D. The canonical-correction discovery row no longer defers the bounded outcome.

**Proposed proof:** Semantic comparison with existing source milestone records; remote history was not rechecked. Later implementation must retain legacy contact DTO/version/create/read/receipt regressions. None executed here.

## Modified and created documentation
- Modified contract: `docs/planning/staff-intake-contract.md`.
- Modified plan: `.hermes/plans/2026-09-14-staff-intake-workflows-plan.md` (ordered A–D; exact PR D files/tests and M1 scenarios).
- Modified decision: `docs/adr/ADR-0017-staff-intake-workflows.md`.
- Modified amendments: `docs/planning/phase-1-operational-discovery-register.md`, `docs/planning/phase-1-correction-audit-event-contract.md`, `docs/planning/phase-1-staff-permission-matrix.md`.
- Modified active roots: `AGENTS.md`, `CURRENT_WORK.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `TECHNICAL_REQUIREMENTS.md`, `SECURITY.md`, `TECHNOLOGY_DECISIONS.md`, `README.md`.
- Appended dated `NOTES.md` entry without rewriting older evidence.
- Created this handoff.

## Remaining risks / acceptance stops
- Fresh independent semantic review is required, particularly PR D's mutable current-row/immutable history migration, correction/review authority, legacy contact/current-details presentation and concurrency semantics. Author disposition is not reviewer closure.
- Mechanical scope/link/diff/Git checks were not run; no exhaustive repository-wide clearance is claimed. File paths and test symbols newly proposed here must be reconciled after both predecessors merge.
- Real PostgreSQL migrations/atomicity/replay and production-build browser accessibility/language/section-state tests remain unimplemented and unrun. No durability, runtime qualification or clean verdict follows from this handoff.
- Live catalog/terminology, named permissions, retention/legal approval and broader identity/lifecycle maintenance remain genuine later boundaries. No new cloud/live authority has been granted.
