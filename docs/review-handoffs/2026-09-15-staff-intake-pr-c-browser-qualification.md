# PR C bounded browser and bilingual accessibility qualification — 2026-09-15

- **Staffing:** One independent developer; agent-operated browser/visual/keyboard checks and fresh repair reviews provide quality evidence, not independent-human authorization or fluent-language sign-off.
- **Human-visible outcome:** The production build ran against two real loopback application processes and disposable PostgreSQL 16, using fictional records only. The exercised flows passed after two repairs. Both browsers, application processes and database are stopped; database files are removed. No continuing review target or cloud availability is claimed; historical v28 remains `not_qualified` and was not rechecked.
- **Gate budget:** The owner authorized this local browser/manual qualification; prior disposable fictional PostgreSQL authorization covered the database. Temporary principals supplied explicit PR C permissions outside source. No default-permission activation, cloud, live/client data, deployment or applied-migration changes.
- **Next executable action:** Inventory/publish the reviewed PR C source candidate and complete required remote CI. Human screen-reader/fluent-language/shared-target qualification remains separately identified; the local agent checks do not satisfy that evidence category.
- **Do not regress:** Original command/review/output references, later dirty buffers, section isolation, canonical scope/field permissions, existing Employer contracts, bilingual behavior, applied `0008` through `0008c`, private cloud protections and the separate deferred UX-polish note.

## Scope and outcome

**Validated, bounded:** Production-build Chromium browser → real HTTP handlers → restricted runtime database login → PostgreSQL → browser readback. Five intakes were created/finalized through the UI: worker creation and reuse, household creation and reuse, and business creation. English and Spanish controls, review/finalization, output navigation, restricted reads, keyboard focus and constrained-width layouts were exercised. No fabricated success endpoints or browser API stubs were used.

Two independent local application processes represented fictional staff members. Restarting both processes retained saved/finalized records. The isolated harness inherited the runtime database role, not schema-owner authority. A missing separate staffing-request read permission first produced the expected denial; adding it only to the disposable principal allowed the persisted output read after restart.

| Scenario | Observed outcome |
| --- | --- |
| Partial worker save, reload and second staff process | Name-only draft persisted; second process read completed details/address. |
| Independent address saves and explicit copy | Household/business contact and worksite sections saved separately; one-time copy still required its own worksite save. |
| Unknown committed response and later edit | Harness corrupted one response only after the real worksite transaction committed. Retry used identical key/body and original version 4 receipt, while a later line-2 edit stayed unsaved; no aggregate all-saved claim. |
| Review freshness and concurrent staff | Stale second-session save rejected. Editing a reviewed household changed status to stale; re-review preceded finalization. Unsaved navigation confirmation was exercised and intentionally accepted for the discarded test buffer. |
| Deliberate reuse | Parent search followed by explicit contact/worksite choices; incomplete selection could not save. Worker and employer candidate differences remained separate from read-only current facts. Reuse retained canonical version 1 rows. |
| Finalized outputs | Worker/household/business finalization produced read-only original references. Household reuse created one distinct new draft request. Request output remained draft and offered no demand-opening action. |
| Restricted reads | Residence and business address hidden until explicit reveal. Residence permission denial on reread cleared displayed address and reported unavailable in Spanish. |
| Worker-scope loss | Empty-scope staff could not read linked detail; list showed unnamed intake and unavailable completeness in English/Spanish, with no canonical name. |
| Bilingual history | Link/finalization history loaded after repair and displayed localized event names, attribution and versions. |
| Keyboard/visual | Tab, Space and Enter exercised review/finalization/reveal/navigation. Finalize had visible 3px focus outline. Desktop, 640px and 390px layouts were inspected; exercised layouts had no horizontal overflow. |

## Repairs discovered by the browser

1. **Unchanged selection falsely locked as concurrent conflict.** Backend correctly returns `409 no_change` for an already-unlinked create-new selection. The client now recognizes only a link command's matching problem-JSON type/code/status as a known failure, allowing discard. Other conflicts remain conflicts and original unknown retries retain their identity. The regression failed before repair, then passed; real browser repeat allowed discard and continued review. Fresh frontend review found no actionable issue.
2. **Linked history returned 503.** The response DTO omitted `intake.linked` although history queried/counts that event. Added that existing event to the strict response enum and English/Spanish linked/finalized labels. Backend schema and two bilingual UI regressions failed before repair, then passed. Restarted real application returned linked history successfully; fresh backend review passed.

No database schema, applied migration or default authorization changed. The independent-review agent results are quality reviews, not additional human authorization.

## Verification and durable evidence

- Fresh frontend: **319 tests in 20 files**, one worker; lint, typecheck and production build pass. Final single-worker coverage rerun passed all 319 tests: 95.22% statements, 90.41% branches, 97.10% functions and 96.59% lines. The first coverage attempt timed out in two existing long UI scenarios; the unchanged rerun passed, with no assertion or timeout changes. Relevant secret scans and final diff/source-manifest checks pass. Both repair reviews and the bounded closeout evidence review found no remaining actionable finding.
- Backend repair: **28 schema tests**, focused mypy and Ruff lint/format pass. Prior final integration evidence remains **1,988 backend tests / 96.06% coverage**; that full suite was not rerun for the narrow response-enum repair. Real application/database history was re-exercised.
- Axe 4.13.0, WCAG 2 A/AA and 2.1 AA tags: **10 exercised states, zero violations and zero incomplete checks**. Worker EN/ES, household ES, business EN/ES, employer reuse EN, repaired history ES, residence ES, draft request ES and business address ES. These are bounded page scans, not whole-product WCAG certification.
- Database readback: 2 finalized worker intakes, 3 finalized employer intakes; 1 worker and 2 employers, all canonical parent versions still 1; 3 requests, all draft. Exactly 1 receipt for the deliberately corrupted-response command; 0 finalized intakes missing matching final-version receipt/audit authority.
- Applied migration hashes unchanged. Source diff and relevant secret scans checked at closeout.
- Baseline: `feat/staff-intake-finalization` at `f653260d2de9a991159a1e8e5d88068631f129f0`, uncommitted candidate. Qualification source manifest covers 135 paths excluding living docs, review handoffs and the deferred polish note. Manifest SHA-256: `96eba6bc23f41622f446028d99baabb144afc27fb17953bfa92dc64bd95f45fd`.

Local evidence is retained in the disposable qualification evidence directory `golden-rose-prc-browser.0vvDGK` under the machine temporary root: screenshots, ten axe JSON results, browser network logs, database readback, migration/source manifests, test logs and application shutdown logs. These are fictional local artifacts, not shipped runtime configuration. Database data was removed after confirmed shutdown.

## Limits and follow-up

- Agent-operated visual/keyboard/language checks are complete for the listed scenarios. No human assistive-technology session, VoiceOver/NVDA speech assessment, fluent Spanish reviewer, actual browser zoom test, cross-browser matrix or shared-cloud qualification occurred. Do not relabel those rows as passed.
- Business creation and household child reuse were exercised; every mixed business-child create/reuse combination, pagination race and permission permutation was not repeated in the browser. Prior automated/source evidence covers broader combinations.
- Nonblocking usability observation: the form says incomplete without listing the missing offer requirement inline. The per-worker checkbox must be explicitly set for completeness. Record this for the separate UX work; no change to the pre-existing deferred polish note.
- Language resets to English on reload. Both languages were explicitly selected and checked; persistence across reload is not claimed.
- Tool limits: offscreen pointer activation was unreliable, so critical controls used focus/keyboard activation. A lost active tab was restored from the saved intake. An expected unsaved-changes dialog temporarily blocked automation. The benign favicon 404 and expected denial/no-change/stale responses were distinguished from the repaired history 503. No browser JavaScript exception was reported. Inherited jsdom canvas warnings occurred in component tests; real Chromium axe scans completed.

**Disposition:** Bounded local browser/durable qualification passed after repairs. Source publication and required remote CI remain; human/shared-target qualification is not implied.
