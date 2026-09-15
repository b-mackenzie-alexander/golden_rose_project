# PR C — Final integration review

- **Staffing:** One independent developer; three fresh agent reviews provide quality evidence, not independent-human authorization.
- **Human-visible outcome:** PR C is an uncommitted source candidate on `feat/staff-intake-finalization`, based on `develop@f653260d2de9a991159a1e8e5d88068631f129f0`. No application/browser runtime or deployment was started for this review. Historical v28 remains `not_qualified` and was not rechecked.
- **Gate budget:** Existing source and disposable fictional local PostgreSQL approval covered review remediation and tests. No cloud, live/client data, default permission activation or applied migration change.
- **Next executable action:** Proceed to production-build browser/manual language/accessibility and durable end-to-end qualification. Publication and required remote CI remain separate unfinished steps.
- **Do not regress:** Original command identity and output/review references, independent dirty buffers, selected canonical field/record permissions, restricted addresses, legacy Employer revision behavior, applied `0008` through `0008c`, bilingual parity and private cloud protections. Preserve the separate UX-polish note.

## Review outcome

**Source review: no remaining actionable findings after remediation and fresh rereview.** Final automated verification also passes; browser/manual evidence remains separate.

Reviews covered backend command/API projection and replay, frontend/backend DTO and endpoint alignment, and persistence/migration/verifier authority. Checks included parent-first lock ordering, review/dependency freshness, created versus reused outputs, atomic receipt/result/audit cardinality, original retries, dirty-buffer preservation, restricted reveals, bilingual controls, query pagination and legacy Employer compatibility. The React Best Practices checklist informed the affected UI review. No browser walkthrough or independent-human authorization is claimed.

### Resolved findings

1. **P2 — Legacy original retries rejected finalized current detail.** A save/review/follow-up could commit, lose its response, and then be finalized by another session. `saveIntake` now accepts strictly validated finalized current detail while retaining the original receipt and retry identity. Missing/malformed finalization outputs remain unknown outcomes. Workspace recovery confirms the old save without discarding later local edits or silently adopting a newer baseline.
2. **P2 — Allowed Employer type changes broke historical intake reads.** An existing business Employer can become a household through the preserved legacy revision contract. Original selected business-address and finalization references remain immutable; current detail now reports the stale dependency and current type, without counting the historical business address as current household completeness. The real two-session race regression now verifies subsequent GET and original finalization replay, unchanged original outputs and unchanged audit counts after reads/replay.
3. **P2 — Linked recovery lists used candidate names/completeness.** Recovery summaries now share effective linked projection with detail. Canonical names participate in search only under the required selected-field permissions and worker scope, before keyset pagination; cursors bind worker scope. Unauthorized linked facts produce `complete:null, missing_fields:[]` with no name, retaining intake identity/lifecycle/review/follow-up metadata. Both languages display completeness unavailable. Full detail still requires authorized boolean completeness. Shared predecessor mappings remain unchanged; search uses a separate successor-column mapping.

The query repair initially referenced link columns absent from the intentionally minimal predecessor mappings; fresh rereview and regressions caught this, and the separate mapping resolves it. Test setup corrections enforced substantive drafts, exclusive name/reference filters and a migrated base database. No test exclusion or weakened typing policy was introduced.

## Verification

- Frontend: **316 tests passed in 20 files**, one worker; coverage **95.25% statements, 90.44% branches, 97.10% functions, 96.63% lines**. Lint, typecheck and production build pass. New bilingual unavailable-list tests include automated accessibility checks; inherited jsdom canvas warnings remain.
- Focused backend: **17 query regressions passed**, covering linked worker/employer names, pagination, permission denial, worker scope/cursor binding and unlinked recovery; **4 parent-ordering/concurrency tests passed**, including historical reads/replay after type change; **43 focused projection/schema tests passed**. The persistence reviewer separately ran 67 unit checks successfully before remediation.
- Full backend verification: **1988 tests passed**, **96.06% coverage**, 7 inherited warnings in 629.01s. The whole run is green, superseding the prior full-plus-focused evidence.
- Ruff formatting/lint, mypy across 202 source/test files, Bandit and `git diff --check` pass. Bandit retains the inherited unused `nosec` notice. Source, tests and frontend-source secret scans are clear. All four applied migration hashes match the start of this review.
- Disposable PostgreSQL cleanup: The Unix-socket-only PostgreSQL 16 cluster was stopped and its data removed. No application/browser service was started.

## Reviewed source boundary

The reviewed working-tree scope contains 133 modified/untracked source, test, configuration and contract paths, excluding the three living status documents, this report and the separate UX-polish note. Sorted `sha256(file) + two spaces + relative path + newline` manifest digest: `060ded6038b5e4e3c63d0d91daae44ed2c42102af7b2f17fe62c37167db46752`.

The source verdict does not close browser/manual or durable application-process qualification, required remote CI, source publication, protected merge, PR D canonical corrections, production identity, or deployment.
