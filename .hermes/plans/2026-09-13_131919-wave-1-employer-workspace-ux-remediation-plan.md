# Wave 1 Employer Workspace UX Remediation Plan

> **For Hermes:** Implement this outcome as one cohesive coding branch and one implementation PR. Use RED → GREEN tests inside the branch, then run the complete frontend gate and one final dual-perspective review over the full package; do not open micro PRs or request independent review after each node.

**Status:** Owner-accepted direction; pending protected planning-PR merge before implementation.

**Goal:** Turn the deployed Employer tracer into a coherent, bilingual, accessible staff work surface suitable for meaningful stakeholder feedback and retire the three v28 qualification-harness normalization defects without widening product, data, identity, or cloud authority.

**Architecture:** Keep the existing React routes, API clients, command authority, privacy lifecycle, and backend contracts. Repair the production language-provider wiring, reorganize the current create/search/detail/revision capabilities into a constrained responsive workspace, add only session-derived operational orientation, and harden the existing qualification runner at its response/log normalization boundaries; do not add fake metrics, new APIs, persistence, workflow automation, or deployment authority.

**Tech stack:** React 19, TypeScript 5.9, React Router 8, Vite 8, Vitest, Testing Library, axe-core, CSS design tokens, Python 3.12/pytest, and the existing FastAPI Employer APIs/qualification runner.

**Current qualification baseline:** `not_qualified`. V28 automated qualification passed and the workspace loaded, but the Spanish-toggle defect and unrun manual accessibility/usability/fluent-language rows fall outside the narrow technical-feedback-only exception. Wave 1 repairs source behavior; it does not change that status until a separately approved deployment and human qualification rerun produces evidence.

---

## 1. Delivery shape and authority

- **Planning PR:** this plan plus the v28 source-of-truth reconciliation already prepared on `docs/wave-1-employer-workspace-remediation`.
- **Implementation PR:** one `fix/` branch from the exact merged planning-PR tip containing the full Wave 1 frontend package, tests, browser evidence, and living-doc closeout.
- Small RED → GREEN nodes and logical commits are encouraged inside the implementation branch, but there is no new plan or PR between them.
- Run final automated qualification and independent architecture/accessibility-product review once against the complete candidate. Routine findings, test fixes, CSS adjustments, and helper extraction remain in the same implementation PR.
- Replan only for a material new API/schema, data class, identity/session boundary, public exposure, vendor/dependency, cloud authority, or a Blocker/High that invalidates this approach.

## 2. Product outcome

The first rendered viewport must read as an intentional staff workspace rather than an unstyled form page:

1. A compact Golden Rose header contains the product identity, primary navigation, and working language control.
2. A constrained main column supplies a clear Employer workspace title and short operational introduction.
3. A concise **Workspace overview** or **Current work** panel explains the next available action using only current in-memory/API-derived state—no fabricated counts or analytics.
4. **Find an employer** and **Create a draft employer** are distinct, well-labeled panels with natural field labels, bounded helper text, appropriately sized actions, and clear state feedback.
5. Search results, selected detail, revision, success, empty, loading, and failure states share a consistent visual hierarchy.
6. Session-derived recent activity/next-step content may reflect successful create, selection, and revision interactions, but must be labeled as current-session context and must not imply durable workflow history, assignment, or backend support that does not exist.
7. Desktop and narrow layouts are usable without page-wide controls, excessive whitespace, overlap, horizontal scrolling, or loss of content.

## 3. Product-copy boundary

- Do **not** place a prominent private/synthetic/develop warning banner in the workspace.
- Remove repeated test-harness wording such as “staff-only synthetic search” and “fictional synthetic ... local workspace” from the main workflow copy.
- Preserve the fictional-only boundary in server validation, deployment configuration, qualification evidence, private access notes, and source-of-truth documentation.
- A subtle environment label is optional only if operator differentiation requires it; it must not compete with the task hierarchy.
- Functional UI copy remains English/Spanish and non-legal. Legal/policy translation remains outside this plan.

## 4. Implementation sequence — one implementation PR

### Task 1: Lock the production language boundary

**Objective:** Reproduce and fix the deployed Spanish-toggle failure at the real application composition root.

**Files:**
- Modify: `apps/web/src/app/App.tsx`
- Modify if composition requires it: `apps/web/src/main.tsx`
- Modify: `apps/web/src/app/App.test.tsx`
- Modify: `apps/web/src/i18n/LanguageProvider.test.tsx`

**RED → GREEN:**
1. Add `App.test.tsx::switches_the_real_app_between_complete_english_and_spanish_catalogs` that renders `<App />` without a test-only provider wrapper and asserts the shell heading, Employer heading, both form labels, toggle label, and `<html lang>` change English → Spanish → English.
2. Run `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/app/App.test.tsx`; expected RED: the English copy remains and `lang` does not change because the production tree uses the no-op default context.
3. Mount exactly one `LanguageProvider` around the production router in `App.tsx`; do not add storage, locale detection, or URL state.
4. Rerun `App.test.tsx`, `AppShell.test.tsx`, and `LanguageProvider.test.tsx`; expected GREEN with no test-only provider required for the new production-root node.

### Task 2: Establish the workspace shell and responsive visual system

**Objective:** Replace browser-default page flow with a compact, tokenized, readable staff workspace.

**Files:**
- Modify: `apps/web/src/app/AppShell.tsx`
- Modify: `apps/web/src/app/AppShell.test.tsx`
- Modify: `apps/web/src/styles.css`
- Modify: `apps/web/src/app/App.test.tsx`

**RED → GREEN:**
1. Add `AppShell.test.tsx::renders_compact_product_header_navigation_and_language_action` and `App.test.tsx::exposes_constrained_workspace_layout_hooks_without_an_environment_banner`; expected RED: required shell/container hooks and hierarchy are absent.
2. Extend `styles.css` tokens for brand accent, surfaces, borders, muted text, status states, spacing, radius, and elevation; retain the existing visible-focus and reduced-motion guarantees.
3. Implement the minimal header/navigation/main container markup and style hooks required by those tests.
4. Add `App.test.tsx::keeps_all_primary_controls_at_least_44px_and_avoids_full_viewport_actions` plus stable class/attribute assertions; expected RED before the control-system CSS lands, then GREEN after normal action widths and disabled/error/success styling are present.
5. Add source-level responsive hooks for a desktop panel grid and a single-column `@media (max-width: 48rem)` layout; browser verification later proves actual 320 CSS-pixel reflow.
6. Run `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/app/AppShell.test.tsx src/app/App.test.tsx`; expected GREEN. Do not add a dependency, decorative animation, chart, or prominent environment disclaimer.

### Task 3: Recompose Employer work into clear panels

**Objective:** Make existing Employer capabilities understandable and efficient without changing backend behavior.

**Files:**
- Modify: `apps/web/src/employers/EmployerWorkspace.tsx`
- Modify: `apps/web/src/employers/EmployerCreateForm.tsx`
- Modify: `apps/web/src/employers/EmployerSearch.tsx`
- Modify: `apps/web/src/employers/EmployerDetail.tsx`
- Modify if necessary: `apps/web/src/employers/EmployerRevisionForm.tsx`
- Modify: `apps/web/src/i18n/messages.ts`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify: `apps/web/src/employers/EmployerRevisionForm.test.tsx`

**RED → GREEN:**
1. Add `EmployerWorkspace.test.tsx::renders_overview_search_create_and_detail_regions_in_operational_order`; expected RED: the current top-level search heading wraps an interleaved create/search flow with no panel regions.
2. Add `messages.ts` keys for the new English/Spanish headings, helper copy, and distinct accessible form labels; catalog typing must fail until both catalogs are complete.
3. Implement separate overview, find, create, and results/detail/revision regions. Keep search prominent as the safe first action before duplicate creation; use a compact desktop form row and accessible mobile stack.
4. Add `EmployerWorkspace.test.tsx::uses_natural_visible_labels_and_unique_accessible_form_names`; expected RED against “Create employer type/name,” then GREEN with natural labels (`Employer type`, `Employer display name`, or localized equivalents) and unambiguous form regions.
5. Add `EmployerWorkspace.test.tsx::renders_results_as_selectable_status_rows_and_places_selected_detail_in_the_work_area`; expected RED against raw list/button paragraphs, then GREEN with visible type/status and responsive detail placement.
6. Rerun the existing create/search/detail/revision failure, idempotency, stale-response, BFCache, focus-ownership, and authority-lock tests without weakening assertions. Loading, empty, validation, unavailable, conflict, unknown-outcome, success, and retry states must remain localized, focus-managed, and value-safe.
7. Run `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/employers/EmployerWorkspace.test.tsx src/employers/EmployerRevisionForm.test.tsx`; expected GREEN.

### Task 4: Add bounded operational orientation and session residue

**Objective:** Make the surface feel like a place staff work without inventing unsupported product depth.

**Files:**
- Modify: `apps/web/src/employers/EmployerWorkspace.tsx`
- Modify callback contracts only as needed: `EmployerCreateForm.tsx`, `EmployerSearch.tsx`, `EmployerRevisionForm.tsx`
- Modify: `apps/web/src/i18n/messages.ts`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify: `apps/web/src/app/App.test.tsx`

**RED → GREEN:**
1. Add typed bilingual copy for workspace orientation, next step, draft status, and current-session activity; `LanguageProvider.test.tsx::keeps_wave_1_catalog_keys_complete_in_both_languages` must RED until both catalogs match.
2. Add `EmployerWorkspace.test.tsx::updates_current_work_and_session_activity_after_create_select_and_revision`; expected RED because no orientation/activity model exists.
3. Implement the smallest typed in-memory model derived only from existing successful create, detail-selection, and revision callbacks. Show a bounded current work item, next step, and short session activity list.
4. Add `EmployerWorkspace.test.tsx::clears_current_work_and_activity_on_pagehide`; expected RED until the new state joins the existing privacy reset, then GREEN after pagehide/BFCache clearing.
5. Add negative assertions that the panel contains no assignment, durable timeline, request queue, staffing metric, employer-contact completeness, or automatic-transition claim.
6. Run `npm --userconfig apps/web/.npmrc --prefix apps/web test -- src/i18n/LanguageProvider.test.tsx src/employers/EmployerWorkspace.test.tsx`; expected GREEN.

### Task 5: Retire v28 qualification-harness normalization debt

**Objective:** Make the source runner reproduce the bounded normalizations required during v28 so the next deployment does not depend on ad hoc evidence edits.

**Files:**
- Modify: `scripts/qualify_develop_deployment.py`
- Modify: `tests/unit/test_qualify_develop_deployment.py`
- Modify if evidence wording changes: `deploy/gcp/evidence-template.md`

**RED → GREEN:**
1. Add `test_response_normalization_canonicalizes_header_names_for_all_replay_and_cache_checks`; feed tuple, fake-response, and urllib-style case-insensitive header mappings with lowercase/mixed-case names. Expected RED: `_normalize_response` rejects non-`dict` mappings or later replay checks miss differently cased keys. Minimal GREEN: canonicalize accepted bounded header mappings once at the transport boundary and make every header lookup use the canonical representation; preserve duplicate/malformed failure behavior.
2. Add `test_live_negative_revision_probes_use_generated_fictional_allowlist_values`; expected RED: current stale/conflict payloads append ` Stale`/` Changed`, which violate the deployed generated-fictional allowlist before reaching expected `412`/`409`. Minimal GREEN: induce stale with a still-valid previously generated Employer value and induce same-key changed-payload conflict through another allowed field/value, without adding a second persisted record or weakening server validation.
3. Add `test_log_collection_excludes_cloud_audit_metadata_before_prohibited_value_scan` and a malformed/unexpected-log regression. Expected RED: raw provider audit metadata containing structural `authorization` keys trips the value scanner even when application request logs contain no prohibited values. Minimal GREEN: constrain or structurally filter the collected JSON to the reviewed Cloud Run application/request log records before scanning; never ignore prohibited values in admitted application payload/text fields, and fail closed on malformed or ambiguous input.
4. Rerun the existing log-leak, no-store, denial-probe, redaction, evidence-write, and full happy/failure-path suite.
5. Run `env -u PYTHONPATH uv run pytest tests/unit/test_qualify_develop_deployment.py -q`, then focused Ruff and mypy on the script/test; expected GREEN.

### Task 6: Complete accessibility, privacy, visual, and publication verification

**Objective:** Qualify the complete package as one review surface.

**Files:**
- Modify: `apps/web/src/app/App.test.tsx`
- Modify: `apps/web/src/employers/EmployerWorkspace.test.tsx`
- Modify if needed: `apps/web/src/test/axe.ts`
- Update: `CURRENT_WORK.md`, `ROADMAP.md`, `NOTES.md`, `SECURITY.md` only where implementation evidence changes current truth
- Create: one implementation review handoff under `docs/review-handoffs/`
- Update private Obsidian browser/feedback evidence after an approved deployed or local served walkthrough; never commit URL, credentials, raw operational values, or private screenshots

**Verification:**

Add `App.test.tsx::passes_axe_in_wave_1_initial_populated_selected_success_error_and_bilingual_states`; expected RED when new regions/copy are incomplete, then GREEN after semantic/live-region corrections. Preserve all prior axe nodes.

Run the complete candidate gates:

```text
npm --userconfig apps/web/.npmrc --prefix apps/web run verify
env -u PYTHONPATH uv run pytest tests/unit/test_qualify_develop_deployment.py tests/unit/test_terraform_hygiene.py -q
env -u PYTHONPATH uv run ruff format --check scripts/qualify_develop_deployment.py tests/unit/test_qualify_develop_deployment.py
env -u PYTHONPATH uv run ruff check scripts/qualify_develop_deployment.py tests/unit/test_qualify_develop_deployment.py
env -u PYTHONPATH uv run mypy --explicit-package-bases scripts/qualify_develop_deployment.py tests/unit/test_qualify_develop_deployment.py
env -u PYTHONPATH uv run python scripts/validate_terraform_static.py
git diff --check
```

For the loopback production-build walkthrough, run the already-built artifact with `npm --userconfig apps/web/.npmrc --prefix apps/web run preview -- --host 127.0.0.1 --port 4173`, verify the listener is loopback-only, and use the approved loopback API proxy/fixture path without live or private values. Verify at 1440×900 desktop, 320×800 narrow viewport, and 200% zoom:

- production-root English → Spanish → English switching and `lang` changes;
- desktop hierarchy, control sizing, result/detail flow, and no page-wide buttons;
- keyboard order and visible focus;
- narrow reflow without horizontal scrolling or clipped actions;
- reduced-motion behavior;
- create/search/detail/revision success and representative empty/error/recovery states;
- no browser persistence or raw-value diagnostics regression;
- axe in initial, populated, selected-detail/revision, success/error, and both-language states.

A running-`develop` walkthrough occurs only after the implementation PR merges and deployment is separately approved.

Then request two independent final reviews in parallel over the complete implementation diff:

1. architecture/security/privacy/command-authority regression review;
2. product UX/accessibility/localization/responsive review against the screenshot-derived deficiencies and this plan.

Remediate all current-target Blocker/High and substantiated Medium findings in the same implementation branch, rerun the full candidate verification, and obtain focused rereview before publication. Then stage the exact reviewed surface, run `git diff --cached --check`, commit once the complete package is final, rerun the full candidate gates on committed HEAD, verify `git diff --check origin/develop...HEAD`, verify the branch is a nonempty bounded range with `git rev-list --count origin/develop..HEAD`, and run `gitleaks git --no-banner --redact --log-opts 'origin/develop..HEAD'` before push and PR creation.

## 5. Definition of done

- The production composition root owns a working bilingual provider; the deployed Spanish defect has a regression test.
- The first viewport has deliberate header, navigation, workspace hierarchy, and bounded panels.
- Search/create flows are visually and semantically separate, with sensible control widths and natural bilingual copy.
- Existing Employer API, privacy, idempotency, focus, cache, and recovery contracts remain intact.
- Current-work/session activity is derived from real current-session interactions and resets with workspace privacy lifecycle.
- Response headers, generated-fictional negative probes, and Cloud Audit/application-log filtering are source-normalized with fail-closed regression coverage; no v28 evidence editing workaround remains necessary.
- No prominent environment disclaimer, fake dashboard metrics, unsupported queue/assignment/history claim, or new product authority appears.
- Full frontend verification and focused repository policy checks pass on the final candidate.
- Dual-perspective final review has no unresolved current-target Blocker/High/Medium.
- Living docs and private browser evidence record the result honestly; implementation is one PR to protected `develop`.

## 6. Explicit non-scope and stops

This plan does not authorize or add:

- backend/API/database schema changes;
- EmployerContact UI, staffing requests, shifts, work queue persistence, analytics, OCR/uploads, maps, worker features, matching/ranking, or integrations;
- real staff identity, MFA, sessions, production access, live/client data, or public product workflows;
- cloud/state/IAM/Secret/database mutation, image publication, deployment, credential rotation, or production promotion;
- storage of language preference, search values, selected records, or activity residue in browser persistence.

Stop and replan if the UI outcome requires any of those boundaries rather than merely reorganizing the existing Employer workflow.
