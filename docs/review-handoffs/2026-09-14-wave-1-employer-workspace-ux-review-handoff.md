# Review Handoff — Wave 1 Employer workspace UX implementation

**Date:** 2026-09-14
**Branch:** `feat/staff-intake-workflows`
**Target PR base:** `develop`
**Base at handoff creation:** `origin/develop@ce38fb060f2f13c0c94625ea80ca717e3e9497a9` (`docs: define staff intake workflows and reconcile source authority (#100)`)
**Review surface:** local uncommitted working tree
**Ahead commits vs `origin/develop`:** `0`
**Behind commits vs `origin/develop`:** `0`
**PR status:** no PR yet; commit, final committed-head checks, range secret scan, push, and PR creation remain outstanding

> **Fresh review update:** A fresh read-only agent review found four P2 issues. This working tree now remediates them: duplicate result names are disambiguated for assistive technology, positive search results make Review and revise the current workflow step instead of Create, confirmed revision saves update Current work to Revised only after exact refreshed detail succeeds, and real HTTP response headers are no longer collapsed before duplicate-header qualification checks. Two review test gaps were also tightened with Spanish production-toggle workflow assertions and loading-detail work-area placement coverage.

## Delivery Lock

- **Staffing:** One independent developer; fresh agent review supplies quality evidence, not independent-human authorization.
- **Human-visible outcome:** Historical v28 private fictional-synthetic develop exists at protected `develop@3414818b44d5e790f2d11c7fe4d7a48ebeb6241e`. Availability and expiring access were not rechecked for this source-only implementation candidate.
- **Gate budget:** The v28 packet is consumed. This handoff covers source, tests, build, and local UI evidence only. It grants no cloud inspection/mutation, deployment, live-data admission, public-plane work, database migration, or production authority.
- **Next executable action:** Fresh-review this working tree, remediate findings, complete final local candidate checks, then commit and run exact committed-head/range checks before opening one implementation PR to `develop`.
- **Do not regress:** Do not recreate cloud resources or credentials, restore bootstrap access, copy private URL/password material into source, admit live/client data, add fake queues/metrics/finalization/assignment, or bring back prominent synthetic/develop disclaimers in the stakeholder flow.

## Scope

This candidate implements the Wave 1 Employer workspace UX and qualification-harness follow-up package after PR #100 merged. It is the required improved-UI predecessor before the ordered staff-intake PR A-D implementation sequence.

In scope:
- production composition-root language provider repair
- intentional responsive staff workspace shell
- Employer search/create/detail/revision workflow recomposition
- bilingual workflow guide and current-session-only orientation
- selected detail presented in the Work area after search selection
- search checkpoint guidance before create
- removal of old prominent synthetic/local copy from the main stakeholder flow
- qualification-harness normalizations for header casing, generated-fictional negative probes, and Cloud Audit metadata filtering

Out of scope:
- new backend authority, schema, permissions, intake persistence, review/follow-up/finalization, queue ownership, assignments, metrics, production qualification, deployment, cloud readback, or live data

## Primary Files

Frontend:
- `apps/web/src/app/App.tsx`
- `apps/web/src/app/AppShell.tsx`
- `apps/web/src/app/App.test.tsx`
- `apps/web/src/app/AppShell.test.tsx`
- `apps/web/src/employers/EmployerCreateForm.tsx`
- `apps/web/src/employers/EmployerSearch.tsx`
- `apps/web/src/employers/EmployerWorkspace.tsx`
- `apps/web/src/employers/EmployerWorkspace.test.tsx`
- `apps/web/src/i18n/messages.ts`
- `apps/web/src/styles.css`

Qualification harness:
- `scripts/qualify_develop_deployment.py`
- `tests/unit/test_qualify_develop_deployment.py`

Living docs:
- `CURRENT_WORK.md`
- `ROADMAP.md`
- `NOTES.md`

## Current Local Evidence

Observed after the PR #100 rebase and latest selected-detail placement work:
- `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/employers/EmployerWorkspace.test.tsx --run` passed with `70 passed`.
- `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/app/App.test.tsx src/employers/EmployerWorkspace.test.tsx --run` passed with `78 passed`.
- `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/app/App.test.tsx src/app/AppShell.test.tsx src/i18n/LanguageProvider.test.tsx src/employers/EmployerWorkspace.test.tsx src/employers/EmployerRevisionForm.test.tsx --run` passed with `101 passed`; jsdom emitted the known axe-related `HTMLCanvasElement.getContext()` warnings.
- `npm --userconfig apps/web/.npmrc --prefix apps/web run lint` passed.
- `npm --userconfig apps/web/.npmrc --prefix apps/web run typecheck` passed.
- `npm --userconfig apps/web/.npmrc --prefix apps/web run build` passed.
- `npm --userconfig apps/web/.npmrc --prefix apps/web run verify` passed after review remediation: lock validation, lockfile self-tests (`24 passed`), lint, typecheck, coverage (`128 passed` across 8 files; 95.09% statements / 93.44% branches / 98.79% functions / 95.59% lines), and production build.
- `git diff --check` passed.
- Conflict-marker scan across active touched docs/source paths returned no markers.
- `python3` AST parsing of `scripts/qualify_develop_deployment.py` and `tests/unit/test_qualify_develop_deployment.py` passed (`syntax ok`).

After final review remediation, `env -u PYTHONPATH UV_CACHE_DIR=/private/tmp/golden_rose_uv_cache uv run pytest tests/unit/test_qualify_develop_deployment.py -q` passed with `47 passed`.

## Browser Evidence Boundary

Earlier loopback browser verification on this branch confirmed:
- production language toggle sets `html lang="es"` and renders Spanish workspace content
- workflow guide appears in English and Spanish
- search checkpoint and empty Current work next-step copy appear in both languages
- old synthetic/local main-flow copy is absent
- 320px viewport has no horizontal overflow
- panel/control radii compute to 8px
- no error overlay or console errors

After context compaction, local server startup escalation was rejected by the automatic approval reviewer even after explicit chat approval. Therefore selected-detail work-area placement and review remediation have fresh jsdom/DOM regression coverage and production-build evidence, but no new loopback browser evidence in this handoff. The qualifier unit test was rerun by using a tmp-local `uv` cache instead of the home cache.

## Review Focus

- Confirm `App` production composition always supplies the language provider and does not rely on test-only wrapping.
- Confirm English/Spanish parity for new workflow guide, create/search guidance, current work, and detail/revision surfaces.
- Confirm selected Employer detail is rendered inside the Work area after selecting a search result, while search retains the correct loading/failure/refresh behavior.
- Confirm loading selected-detail state also renders in the Work area and remains absent from Find an employer.
- Confirm the workflow guide and current-session panels are honest session-derived orientation only, not durable history, queue, assignment, finalization, metric, or SLA behavior.
- Confirm stakeholder-facing flow no longer foregrounds synthetic/local environment disclaimers while preserving fictional-only/server-boundary controls elsewhere.
- Confirm qualification-harness normalizations are bounded and do not weaken live-data or log-leak controls.
- Confirm no new backend authority, API route, permission, migration, deployment, credential, or cloud boundary is introduced.

## Remaining Stops Before PR

- Rerun loopback browser verification if local server permission is available.
- Commit the final candidate.
- Run exact committed-head checks, exact outgoing-range diff hygiene, and range secret scan before pushing/opening PR.
