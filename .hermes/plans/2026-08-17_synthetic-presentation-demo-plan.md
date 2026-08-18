# Synthetic Golden Rose Presentation Demo Implementation Plan

> **For Hermes:** Implement this plan as a deliberately isolated presentation artifact. Do not use `subagent-driven-development` against the paused Terraform remediation. Keep all work on `docs/synthetic-demo-presentation-plan` until this plan is independently reviewed and Beatrice explicitly authorizes execution.

**Goal:** Deliver a local-only, Docker-runnable, synthetic interactive demonstration that tells one end-to-end Golden Rose agency workflow story for the August 18 client presentation without connecting to product code, APIs, databases, cloud services, credentials, or client data.

**Architecture:** Create a dependency-free static site under `presentation-demo/`, isolated from `apps/web/`, `src/`, migrations, Terraform, and all deploy workflows. Browser JavaScript owns only ephemeral navigation and an explicitly fictional status transition; all mock content is stored in a local module. A tiny static-web-server container is a reproducible fallback, not a deployment artifact or product runtime.

**Tech Stack:** HTML5, CSS3, dependency-free ES modules, Node 22 built-in test runner, Python 3 local static server, Docker static-web-server image pinned by immutable digest, curl, and a manual browser walkthrough.

**Evidence posture:** All UI content is **Proposed presentation material** using fictional synthetic data. It must not claim deployment, authentication, legal approval, production readiness, client validation, live operation, automated matching/ranking, or worker/employer portal availability.

---

## Non-negotiable scope and safety contract

### In scope
- A polished, desktop-first guided workflow with four views: Agency Operations Dashboard, staff request workspace, worker opportunity view, and employer request-status view.
- One clearly non-authoritative simulated staff action: recording a fictional follow-up, which updates in-memory display state only until refresh.
- English-only demo copy for this one-night presentation artifact, with an honest script statement that production English/Spanish parity remains an affected-product requirement rather than a demonstrated completed capability.
- A static local server path and a Docker fallback, both bound to loopback only in the run instructions.

### Explicitly out of scope
- Product frontend reuse or changes in `apps/web/`; backend reuse or changes in `src/`, migrations, or `pyproject.toml`; API/database/cloud calls; auth/session simulation; forms that submit or persist; user accounts; deployment workflows; maps; uploads; messaging; legal documents; payments; matching, ranking, eligibility, hiring, referral, or worker selection decisions.
- Client-derived fixtures, personally identifying information, real worksite addresses, real employer/worker data, secrets, external fonts, analytics, telemetry, CDNs, and network calls.
- Any assertion that this artifact is a deployable release or an approved public worker/employer portal.

### Fictional data and privacy rules
- Display a persistent banner: `Concept demonstration — fictional synthetic data — local presentation only — not a production system.`
- Use a fictitious employer, `Harbor & Pine Hospitality`, a generic `Downtown service area`, and abbreviated synthetic worker name `Jordan R.`.
- Do not show addresses, email addresses, phone numbers, worker home information, protected traits, health/disability information, language as a candidate selection signal, or free-text requirements that can imply prohibited criteria.
- The worker-facing card must say `Express interest to the agency`; it must not say `Apply`, `Matched`, `Recommended`, `Eligible`, `Hire`, or equivalent decision language.
- The employer view must reveal only request/milestone/coverage information, never worker identities or private worker data.

## Presenter route and acceptance criteria

The demo must support this exact five-to-seven-minute narrative:

1. Start on the **Agency Operations Dashboard** and show separate review, coverage, and follow-up lanes plus accountable ownership.
2. Open `Harbor & Pine Hospitality` and show the staff **Request Workspace**: reviewed demand, two planned staffing needs, broad service area, controlled status, and attributable activity history.
3. Use `Preview worker-safe opportunity` to show the **Worker Opportunity** view: broad area, shift timing, approved-looking task summary, explicit agency review, no exact address, no automatic recommendation.
4. Use `Preview employer status` to show the **Employer Status** view: transparent request milestones and agency coordination without worker-private data.
5. Return to the staff workspace and use `Record fictional follow-up` to append a visual event and set an in-memory confirmation. Refreshing the browser must reset the artifact to its initial synthetic state.

Acceptance is met only when:
- The entire route works after a fresh local static-server start and after a fresh Docker image/container start.
- The page does not issue network requests other than loading local static assets.
- Keyboard operation works for primary navigation and buttons, visible focus is present, headings are hierarchical, status changes use an appropriate live region, and color is not the only carrier of status.
- A source-level test verifies the safety copy/data contract and a served-content test confirms the exact banner and four required view labels.
- A browser walkthrough verifies the five presenter actions at desktop width; it is recorded as local presentation qualification, not production accessibility/language qualification.

---

### Task 1: Establish the isolated artifact contract and presentation script

**Objective:** Create the artifact directory and an honest readme/script before creating UI code.

**Files:**
- Create: `presentation-demo/README.md`
- Create: `docs/presentation/synthetic-demo-script.md`

**Step 1: Add `presentation-demo/README.md`**

State, near the top:

```text
This is a local-only concept demonstration using fictional synthetic data.
It is not Golden Rose product code, a production deployment, an authentication implementation, or a client-data system.
```

Include exact local server, Docker build/run, stop, and reset commands. Bind local commands to `127.0.0.1`; use a non-conflicting presentation port such as `4173`. Include a `No external services` section that prohibits cloud/API/database/auth calls and client data. State that a page refresh resets mock state.

**Step 2: Add `docs/presentation/synthetic-demo-script.md`**

Write a concise presenter sequence matching the five-step route above. Begin with the exact disclaimer. For each step, provide: screen, one user action, the intended value statement, and the truthful limitation/not-a-claim. Include the closing message: the value is coordinated, privacy-conscious operational visibility with accountable human agency review—not automated placement.

**Step 3: Verify documentation content**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: this will not run yet because the test does not exist. Record this as setup-only, not behavioral RED evidence.

---

### Task 2: Build the synthetic data model and safety-contract test first

**Objective:** Make the demo’s fictional-only, no-decision language mechanically reviewable before rendering it.

**Files:**
- Create: `presentation-demo/app.js`
- Create: `presentation-demo/app.test.mjs`

**Step 1: Write the failing Node built-in test**

`app.test.mjs` imports exported `DEMO_NOTICE`, `DEMO_DATA`, `VIEWS`, and `validateDemoContract` from `app.js`. Assert all of the following:
- the notice contains `fictional synthetic data` and `not a production system`;
- the only employer name is `Harbor & Pine Hospitality`;
- the broad location is `Downtown service area` and no value contains a street-address pattern;
- the worker display name is `Jordan R.`;
- worker action text is exactly `Express interest to the agency`;
- no rendered-copy source string includes prohibited decision claims such as `matched`, `recommended`, `eligible`, or `hire` (case-insensitive);
- `validateDemoContract()` returns an empty array.

**Step 2: Run the test to verify a behavioral RED**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: FAIL because `app.js` and its exports do not yet exist.

**Step 3: Implement the minimal data and validation module**

In `app.js`, use only JSON-like constant data and pure functions. Export:
- `DEMO_NOTICE` with the persistent disclaimer;
- a frozen `VIEWS` object for `dashboard`, `workspace`, `worker`, and `employer`;
- frozen `DEMO_DATA` that includes the fictional employer, broad service area, two staffing needs, generic accountable owner, transparent milestones, and initial activity entries;
- `validateDemoContract()` that returns human-readable violations instead of mutating data.

Do not access `window`, `document`, storage, fetch, cookies, timers, or external URLs in the exported data/validation portion. Any browser boot code must be guarded so Node can import the module.

**Step 4: Re-run the test**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: PASS.

---

### Task 3: Create the accessible static shell and agency-first navigation

**Objective:** Render the persistent disclaimer, sidebar navigation, agency dashboard, and semantic landmarks with no framework or dependency.

**Files:**
- Create: `presentation-demo/index.html`
- Create: `presentation-demo/styles.css`
- Modify: `presentation-demo/app.js`

**Step 1: Extend `app.test.mjs` with a failing static-shell assertion**

Read `index.html` and assert it contains:
- one `main` landmark;
- a navigation landmark labelled `Demo views`;
- a live status region (`role="status"`); and
- a module script reference to `app.js`.

**Step 2: Run the test**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: FAIL because `index.html` is absent or lacks the required structure.

**Step 3: Implement `index.html` and first render path**

Use semantic document structure: header/banner, navigation, `main`, one `h1` per view, buttons for navigation/actions, and a persistent footer disclaimer. Set `lang="en"`. Use an inline SVG/icon-free text treatment rather than external images or fonts. Include a visibly labelled `Demo navigation only — not sign-in` control area; do not render an imitation login form.

In `app.js`, render the dashboard by default. Display three distinct lanes—not a fabricated priority score:
- Review needed
- Coverage to coordinate
- Follow-up due

Give each visible card a status word in text, a due/when label, and a `Open request workspace` button. Navigation must update the view title, document title, active navigation state, and keyboard focus to the new view heading.

**Step 4: Implement `styles.css`**

Use local CSS only. Establish restrained visual hierarchy, a readable high-contrast palette, text labels paired with status color, visible `:focus-visible`, responsive collapse for narrower displays, and `prefers-reduced-motion` handling. Optimize the initial layout for a 1440px desktop presentation while preventing horizontal scrolling at 320px.

**Step 5: Verify**

Run:

```bash
node --test presentation-demo/app.test.mjs
python3 -m http.server 4173 --bind 127.0.0.1 --directory presentation-demo
```

Expected: Node test passes; the server prints a loopback URL. Open the page and verify dashboard navigation with keyboard Tab/Enter. Stop the server after the check.

---

### Task 4: Render the staff request workspace and bounded fictional follow-up

**Objective:** Give the presenter the central operational detail screen and a truthful, reset-on-refresh interaction.

**Files:**
- Modify: `presentation-demo/app.js`
- Modify: `presentation-demo/app.test.mjs`
- Modify: `presentation-demo/styles.css`

**Step 1: Add failing behavior tests**

Export and test a pure `createInitialDemoState()` plus `recordFictionalFollowUp(state)`. Assert that:
- initial state has exactly two staffing needs and no completed follow-up;
- the operation returns a new state, does not alter `DEMO_DATA`, adds one clearly fictional activity event, and sets a visible confirmation value;
- calling the operation twice does not add a duplicate event.

**Step 2: Run the test**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: FAIL because the state helpers do not exist.

**Step 3: Implement the staff workspace**

Render employer name, a broad service-area chip, request status, two staffing-need cards, a limited activity timeline, and non-functional explanatory buttons for `Review request` and `Prepare worker-safe opportunity`. Only `Record fictional follow-up` changes state. Its result must appear in the pre-existing live status region and timeline.

Include a visible helper: `This interaction changes presentation state only and resets on refresh.` Do not provide fields accepting user-entered data. Do not use local/session storage.

**Step 4: Verify**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: PASS.

Then open the local page, activate `Record fictional follow-up`, observe one confirmation/timeline event, and refresh. Expected: confirmation/event disappears after refresh.

---

### Task 5: Add the worker-safe and employer-status perspectives

**Objective:** Complete the narrative without representing public access as a real portal, a placement decision, or an exposure of protected/private data.

**Files:**
- Modify: `presentation-demo/app.js`
- Modify: `presentation-demo/app.test.mjs`
- Modify: `presentation-demo/styles.css`

**Step 1: Add failing tests for presentation boundaries**

Test that view metadata includes exactly four view IDs. Test that the worker view source contains the agency-review notice and `Express interest to the agency`; test that employer view source contains no worker display name. Test `validateDemoContract()` still passes.

**Step 2: Run the test**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: FAIL until the two views and copy boundaries are implemented.

**Step 3: Implement worker opportunity view**

Render one reviewed fictional opportunity with role, broad service area, schedule, bounded task summary, and agency-review notice. Label the panel `Worker perspective — concept preview`, not `Worker portal`. The sole primary action is `Express interest to the agency` and produces a non-persistent explanation that interest triggers no decision or placement.

**Step 4: Implement employer status view**

Render `Employer perspective — concept preview`, request state, staffing-need summaries, and a milestone trail. Do not render individual worker identity, private profile attributes, contact details, exact location, or staffing-selection language. Its informational button returns to the staff workspace.

**Step 5: Verify**

Run:

```bash
node --test presentation-demo/app.test.mjs
```

Expected: PASS.

Perform the full presenter route manually in a browser. Verify each view title, the persistent disclaimer, back-and-forth navigation, and the absence of address/decision language.

---

### Task 6: Package the artifact as a loopback Docker fallback

**Objective:** Make the demo reproducible locally without making it part of the Golden Rose application runtime.

**Files:**
- Create: `presentation-demo/Dockerfile`
- Create: `presentation-demo/nginx.conf`
- Modify: `presentation-demo/README.md`

**Step 1: Determine an immutable static-server base-image reference**

Use the Docker registry/build tooling available at implementation time to resolve a current static-server image digest. Record the exact `image@sha256:...` reference in `presentation-demo/Dockerfile`; do not use a floating `latest` tag. The image must serve static files only and must not contain application code, Python dependencies, Node dependencies, or product environment variables.

**Step 2: Add the failing served-content verification script/test**

Extend `app.test.mjs`, or add `presentation-demo/verify-served-demo.mjs`, to request the local served root using Node `fetch` and assert HTTP 200 plus the exact persistent disclaimer and all four view labels in returned HTML/script content. The script accepts one local URL argument and rejects non-loopback hosts.

**Step 3: Run it before the container exists**

Run:

```bash
node presentation-demo/verify-served-demo.mjs http://127.0.0.1:4173
```

Expected: FAIL while no server is running. This is an environment-precondition RED, not a product test.

**Step 4: Implement hardened static serving**

Create an Nginx configuration that listens on container port `8080`, serves `/usr/share/nginx/html`, disables directory listing, sets conservative static content types, and sends `Cache-Control: no-store` for the presentation artifact. Create a Dockerfile that copies only `index.html`, `app.js`, `styles.css`, and `nginx.conf`, runs as the image’s non-root supported user when the base image supports it, exposes `8080`, and uses no secrets/build arguments/network fetches beyond the pinned base image retrieval.

Update the README with exact commands:

```bash
docker build -t golden-rose-presentation-demo:local presentation-demo
docker run --rm --name golden-rose-presentation-demo -p 127.0.0.1:4173:8080 golden-rose-presentation-demo:local
node presentation-demo/verify-served-demo.mjs http://127.0.0.1:4173
```

**Step 5: Verify image and served content**

Run the Docker build, then the container command above. In a separate terminal run the verification script and `curl -fsSI http://127.0.0.1:4173/`. Expected: HTTP 200, the correct local content, and no external requests. Stop/remove the container explicitly after browser qualification and verify no matching container remains.

---

### Task 7: Perform final local presentation qualification and handoff

**Objective:** Verify the exact artifact behavior needed tomorrow and leave a safe, concise handoff.

**Files:**
- Modify: `presentation-demo/README.md`
- Modify: `docs/presentation/synthetic-demo-script.md`
- Create: `docs/presentation/synthetic-demo-qualification.md`

**Step 1: Execute all repeatable checks**

Run:

```bash
node --test presentation-demo/app.test.mjs
python3 -m http.server 4173 --bind 127.0.0.1 --directory presentation-demo
node presentation-demo/verify-served-demo.mjs http://127.0.0.1:4173
```

Then execute the Docker path from Task 6 and repeat `verify-served-demo.mjs` against the container. Stop both servers/containers afterward.

**Step 2: Complete the browser presentation checklist**

At desktop width, verify:
- dashboard → workspace → worker preview → employer preview → workspace;
- keyboard access and visible focus for each primary action;
- live confirmation from the fictional follow-up action;
- refresh resets the in-memory interaction;
- no browser console errors or failed remote requests;
- persistent fictional/local/non-production disclaimer on every view;
- no exact location, worker identity in employer view, or automated-decision language.

**Step 3: Record minimized qualification evidence**

Write `docs/presentation/synthetic-demo-qualification.md` with date/time, local-only command outcomes, browser checklist outcomes, container teardown confirmation, and explicit limitation statement:

```text
This evidence qualifies a fictional local presentation artifact only. It does not qualify the Golden Rose application, production deployment, browser accessibility, language parity, authentication, privacy controls, or any legal/compliance behavior.
```

Do not include screenshots containing realistic-looking data, local paths beyond the artifact itself, raw browser logs, ports other than loopback commands, credentials, or client information.

**Step 4: Final hygiene verification**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors; only the planned presentation-demo/docs changes appear. Do not commit, push, open a PR, merge, authenticate to cloud, or touch the paused remediation stash without a separate explicit authorization.

---

## Expected changed-file surface

```text
.hermes/plans/2026-08-17_synthetic-presentation-demo-plan.md
presentation-demo/README.md
presentation-demo/index.html
presentation-demo/styles.css
presentation-demo/app.js
presentation-demo/app.test.mjs
presentation-demo/verify-served-demo.mjs
presentation-demo/Dockerfile
presentation-demo/nginx.conf
docs/presentation/synthetic-demo-script.md
docs/presentation/synthetic-demo-qualification.md
```

No other path is in scope. In particular, do not alter `apps/web/`, `src/`, `tests/`, `migrations/`, root `Dockerfile`, GitHub workflows, Terraform, deploy scripts, or living product-roadmap claims.

## Review checklist

Before execution approval, review this plan specifically for:
- accidental product-code coupling or ambient network calls;
- claims that could be understood as production/public availability or legal approval;
- worker/employer privacy leaks or automated-decision language;
- external font/image/CDN dependencies;
- falsified English/Spanish parity claims;
- Docker image immutability and loopback-only run instructions;
- demo artifact scope being kept separate from the paused `stash@{0}` Terraform remediation.
