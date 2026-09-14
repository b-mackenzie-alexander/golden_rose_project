# PR B — Staff intake review, history and follow-up

- **Staffing:** One independent developer; fresh specification and code-quality agent reviews supply evidence, not independent-human authorization.
- **Human-visible outcome:** PR #102 merged durable intake drafts at `develop@2783415dd19027428bf2036730b6c0d83f23ab3c`. Bounded local browser verification followed on the separate evidence branch. PR B is a source candidate on `feat/staff-intake-review`; it has no new running browser target or deployment. Historical v28 remains `not_qualified` and its availability was not rechecked.
- **Gate budget:** The v28 packet is consumed. The owner authorized PR B source work and disposable local PostgreSQL validation with fictional data. Future synthetic deployment requires one fresh bounded packet; live data, production and materially different authority remain separate.
- **Next executable action:** Publish this verified PR B candidate to `develop` and complete required CI before the owner merges. Fresh backend/frontend specification and quality reviews and final integration review approved source publication. Rebaseline PR C only after the PR B merge.
- **Do not regress:** Preserve Employer APIs/UX, explicit original-key retries, dirty section isolation, restricted addresses/history, immutable reviews and audit authority, bilingual functionality, synthetic-only testing and private access custody. Keep C/D linking/finalization/corrections out of this PR.

## Source outcome

Both intake kinds have saved completeness/missing-field summaries, explicit version-bound review and attributable shared follow-up. Review/follow-up advance the aggregate version; only fact/address changes advance content version. A later disposition supersedes the previous one, and fact/catalog changes stale reviewed content without modifying the original protected snapshot.

The governed work-interest catalog retains bilingual version history. Worker selections record concrete catalog IDs/versions; active current selections must be explicitly chosen before review. Other text satisfies the minimum-interest requirement but never hides invalid existing selections. Catalog maintenance has separate read/manage rights.

Owners come from an injected trusted directory. The bounded owner-choice route returns only active, eligible members within record scope and revalidates assignment at command time. This is no directory administration or production identity provider. Structured protected follow-up context preserves the original reason, optional note, attempt method/outcome and zone; ordinary history contains minimized attribution/version/deadline metadata only.

The UI serializes workflow commands with existing section saves, binds confirmation to the displayed saved version, preserves exact unknown command identity and later dirty buffers, and keeps selected catalog/owner metadata visible across pagination. Unknown catalog metadata is distinguished from confirmed stale/retired versions. Controlled history enums are localized; supplied text stays verbatim.

## Migration and authority

`0007_intake_review_follow_up` follows merged `0006_intake_drafts`; earlier migrations are unchanged. It adds review/payload, follow-up/payload and catalog/version tables with bounded fields, concrete FKs, append-only guards and exact runtime column rights. Every successful workflow/catalog command binds one receipt, typed result, event and domain transition atomically.

Direct SQL checks reject absent/forged payloads, invented snapshots, extra catalog audit events and reviews attached to standalone follow-up events. Cleared all-null address rows normalize exactly like absent address values in the writer; restricted projection explicitly represents absence as null. Populated upgrades preserve existing draft/legacy data; populated downgrade stops before destructive DDL. Empty disposable downgrade still reaches the inherited operator-reviewed role-handoff refusal.

## Verification and review evidence

Full backend gate: 1,253 tests / 95.64% combined coverage. Exact final frontend pass: 202 tests / 95.12% statements, 90.32% branches, 98.55% functions and 96.36% lines; full lock/lint/typecheck/build gate passed.

Real PostgreSQL tests cover both employer kinds and workers, incomplete/cleared addresses, original-result replay with current state, same-key and competing-key concurrency, transaction rollback, scope/permission revocation, owner eligibility/reassignment, protected disclosure, keyset cursor bindings and catalog retirement/completeness. Strict input tests cover attribution injection, field bounds, offset/zone mismatch, DST gaps/overlaps and concrete unique catalog selections.

Review findings were remediated with explicit RED/GREEN regressions: standalone-follow-up review authority, Other plus stale selections, locked/current-row permission checks, cleared-address snapshots, version-bound UI confirmation, catalog/owner pagination bilingual protected enums and consistent 200-character staff-name bounds. Specification review precedes code-quality review. All review labels mean fresh agent evidence, never human authorization.

Ruff format/lint, mypy, lock validation, dependency tree and both generated CycloneDX SBOM validations passed. Bandit identified an assertion used as a workflow invariant; it was replaced with an explicit safe validation error. Final Bandit passed; the fresh final integration review approved source publication without actionable findings. Python audit found no known vulnerabilities. The npm High-severity gate passed after explicit metadata-transmission approval; it retains the existing Moderate development-tool advisory GHSA-82fw-gwwq-j7x9 across Vitest/mocker/coverage packages. Dependencies are unchanged; no affected browser-mode/mocker service was started. This is not an all-severity audit pass.

The approved disposable PostgreSQL 16 service was stopped; only its exact temporary cluster/socket were removed after validation. Candidate snapshot secret scanning passed, and the final staged/outgoing range is scanned before publication. No application/browser or cloud service was started for PR B.

## Deferred and separate work

The owner-requested polish note `docs/planning/staff-intake-ux-polish-follow-up.md` stays untracked and excluded from PR B. The next docs PR should bring it together with browser evidence commit `ee82615` on `test/staff-intake-browser-ux`. Do not fold the browser docs commit into this feature branch or silently implement the deferred polish here.

PR C adds deliberate canonical links/finalization after this PR merges; PR D adds canonical corrections and current-facts re-review. PR B does not complete the full intake outcome. New browser UX verification, full manual accessibility/fluent-language review and any deployed runtime qualification remain separately identifiable evidence rather than claimed by unit/component tests.
