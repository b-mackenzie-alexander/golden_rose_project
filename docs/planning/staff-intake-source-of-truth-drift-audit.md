# Staff intake source-of-truth drift audit

Status: preliminary, material drift found; NOT exhaustive clearance. Source inspection date: 2026-09-14. Independent read-only reviewer returned 11 findings. Root-document output truncation and a consent timeout prevented exhaustive coverage of ROADMAP, NOTES, SECURITY, TECHNICAL_REQUIREMENTS and ARCHITECTURE. No runtime/remote qualification was performed. No severity totals were asserted by the reviewer.

Original checkout: feat/staff-intake-workflows with uncommitted inherited Wave 1 changes. Planning worktree: docs/staff-intake-implementation-plan at a6f0791f53f9e0d4a344cd104e6237b20ad34dbb. Review covers original-checkout documents; do not infer the clean planning base includes their uncommitted status updates.

## Findings ledger
| ID | Finding / reference | Disposition |
|---|---|---|
| D01 | Active lane differs between AGENTS:10, CURRENT_WORK:4,10,84-85 and Wave 1 plan:5; intake direction not reflected | Amend current status in publication packet; retain UI closeout as predecessor and label new intake planning separately |
| D02 | Canonical field inventory:245-253 and permission matrix:7,127 exclude worker scope; durable intake aggregate is new | Required ADR and bounded worker/intake field/permission extension before coding |
| D03 | Earlier private-note alternatives conflict with later accepted finalization addenda | Latest addenda control; new identity creation requires complete current-version review plus explicit finalization, not merely identity minimums |
| D04 | Permission matrix:38-44 permits ordinary request review for Operations Staff, unlike new intake review | Add distinct intake review/finalization permissions and delegation; preserve existing request/shift rights |
| D05 | Request/shift state model:42,102-103 requires governed shift/concrete schedule; intake permits To be discussed | Intake review/finalization cannot imply submitted/open demand or fabricate a shift |
| D06 | Field inventory lacks intake save/review/finalize requiredness, worker preferences, residential/contact addresses and offer presentation | Add staged field-purpose/requiredness/disclosure matrix; retain absence and validation distinction |
| D07 | Worksite-specific precise-location rights do not authorize residential or contact addresses (permission matrix:46-47,80-86) | Add separate purpose-scoped fields and rights; do not extend calendar reveal exception |
| D08 | Follow-up due-instant question resolved by latest acceptance; unnamed draft rediscovery still absent | Preserve mandatory owner/reason/due time for explicit follow-up; specify separate bounded draft lists |
| D09 | Correction/audit contract:111-175 is compatible but lacks intake review/version/finalization authority | Extend typed events, reviewer identity history, stale-review guards and command replay contracts |
| D10 | Operational discovery register:29 and contact permission prose:61-68 still describe completed contact planning/coding | Mark bounded contact foundation complete; do not infer phone, correction or UI support |
| D11 | GIT_WORKFLOW:75-80 versus :109-111 differs on permanent solo-maintainer zero-review-quorum posture | Align active wording; no new human quorum or production-grade governance prerequisite |

## Reconciliation into implementation draft
All 11 findings are represented as publication/contract obligations in `.hermes/plans/2026-09-14-staff-intake-workflows-plan.md`. D01, D10 and D11 need active-document wording repairs. D02, D04-D09 need explicit architecture and authority amendments, not blanket supersession. D03 is resolved in intended direction through the latest private-note addenda; canonical publication remains outstanding.

These dispositions do not mean repairs are already applied. Historical logs and accepted predecessor contracts must remain intact until precise amendments are reviewed. Worker inclusion is a deliberate new direction, not proof the old employer-only implementation violated its authorized scope.

## Open verification
- Complete paginated review of root documents omitted/truncated in independent audit, distinguishing active claims from dated history.
- Verify exact cited passages before patching; line numbers refer to reviewed original checkout and may shift.
- Reconcile ADR/index, source contract, field/API and migration surfaces before marking plan executable.
- Verify live remote predecessor/planning merge state at publication/rebaseline; local tracking refs alone are insufficient.
- No clean/exhaustive source-of-truth verdict, no implemented intake claim, no deployment approval.
