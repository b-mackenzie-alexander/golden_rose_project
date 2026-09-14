# Staff intake PR A — durable drafts and shared recovery

- **Staffing:** One independent developer; fresh agent specification and quality reviews are quality evidence, not independent-human authorization.
- **Human-visible outcome:** Wave 1 UX source merged through PR #101 at `develop@9a6b66735f7261ca705f7e8ba5b7c2afcd815f92`. PR A adds source for shared worker/employer drafts; it is not deployed. Historical v28 remains `not_qualified`, with no renewed availability/access check.
- **Gate budget:** The v28 deployment packet is consumed. The owner authorized PR A source work and disposable local PostgreSQL tests only. Browser UX verification is explicitly deferred until PR A is finished. No cloud/live/client/production authority follows.
- **Next executable action:** Finish final committed-head verification and publish the reviewed `feat/staff-intake-drafts` candidate to protected `develop`. After PR A, return to browser UX verification; PR B starts only after PR A merge and exact-tip rebaseline.
- **Do not regress:** Preserve Employer/contact contracts and merged UI, restricted fields, independent section edit buffers, exact unknown-outcome command identity, atomic typed receipts/results/audits, synthetic testing, and private operator custody. No review/link/finalization/correction placeholders or new cloud authority.

## Result

Staff can create partial worker/employer candidate drafts, recover shared drafts through bounded name/reference queries, and reopen current authoritative values. Non-address content and each authorized address have distinct Save actions. Unknown outcomes retain the submitted command key, payload, version and edit generation. A confirmed response advances the shared version only when its current version matches the command result. If another session has advanced the record, the original save is acknowledged while a persistent reconciliation barrier preserves all buffers and blocks further writes; no unseen change is silently overwritten. Reloads are bound to their section, request generation and selected record.

Migration 0006 adds intake/address tables, a deliberately unusable future link shell, typed intake authority, and reciprocal result/event/receipt integrity. Legacy receipts backfill one result and keep their existing HTTP contracts. Both old and new writers use a bounded common command-key lock, preventing the new secondary unique receipt index from racing legacy targeted conflict handling. Runtime grants allow only enumerated mutations; direct unaudited writes and populated downgrades fail closed. The verifier checks concrete constraint definitions and enabled guards, including a pinned safe function search path.

Strict request/response DTOs keep addresses out of ordinary detail/list/command responses. Restricted reveals emit only actor, intake ID, section and server timestamp to the existing restricted operator log surface. Intake permissions are added only to local/test synthetic principals; develop receives no new intake grants or admission. Process-lifetime signed cursors bind actor, permissions, record scope, filters and page size; restart requires a fresh list query, not recreation of records.

## Verification and review

- Strict contracts: 70 focused tests, including schedule offset/overflow regressions and response-projection restrictions.
- Real PostgreSQL command/query/API tests: atomic rollback, concurrent retry, current-authority replay, two-session recovery, section interleaving, cursor tampering/scope and HTTP privacy/error branches. The restricted runtime role creates and revises content/addresses successfully and cannot delete intake rows.
- Schema verification: populated 0005 upgrade/backfill, legacy compatibility, empty successor downgrade, populated refusal before DDL, exact readback and temporary-table spoof rejection.
- Frontend exact-final verification: 169 tests plus 24 lock tests; lint, typecheck, coverage and production build pass. Coverage: 94.61% statements, 90.24% branches, 98.31% functions and 95.73% lines.
- Fresh backend specification and quality review: PASS after repairing default restricted-reveal emission; focused rereview of response DTOs and common command serialization: PASS.
- Fresh frontend specification and quality review: PASS after repairing overlapping restricted-section reloads, with deferred-response regressions. Final integration review: PASS after adding the newer-current reconciliation barrier for first responses, retries, address saves and creation.
- Full backend candidate gate: **1,154 passed**, 95.80% coverage. Repository Ruff format/lint, mypy, Bandit and Terraform static policy pass; backend/frontend SBOM validation passes. Committed-head confirmation and outgoing-range secret scanning follow before publication.

No browser or live-service verification is claimed. Automated axe/jsdom coverage is not manual accessibility, fluent-language or visual evidence. No deployed migrations were run. Disposable PostgreSQL used only a local Unix socket and fictional test fixtures.

## Dependency audit disposition

Backend advisory audit found no known vulnerabilities. The required npm High-severity gate passed but reported three Moderate package entries arising from one existing Vitest 4.1.10 development-tool advisory, [GHSA-82fw-gwwq-j7x9](https://github.com/advisories/GHSA-82fw-gwwq-j7x9). The advisory concerns reachable development-server mock registration; this repository's test gate uses jsdom and does not configure its standalone mocker/interceptor plugin or browser mode. No such service was started. This is retained development-tool debt, not a claim of a clean all-severity audit; assess the pinned 4.1.11 patch in the tooling follow-up before enabling an affected server. No dependency or vendor change is included in PR A.
