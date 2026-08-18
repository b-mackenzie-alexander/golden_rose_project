# Synthetic Demo Qualification Log

Date: 2026-08-17 (agent-run verification)

## Scope

Validates the concept-only local demo artifact at `presentation-demo/` against the implementation plan and the stakeholder-review remediation pass:

- Concept-only synthetic workflow artifact
- Agency-first dashboard with actionable request cards and concrete due times
- Manual synthetic worker/employer intake from paper into a shared staff queue preview
- Connected request detail, worker view, and employer view interactions
- No API/db/auth/tooling integrations
- Reusable local proof artifacts and scripted verification

## Execution summary

Executed:

- `node --test presentation-demo/app.test.mjs`
- `node presentation-demo/verify-served-demo.mjs http://127.0.0.1:4174` with Python static server on loopback
- Browser walkthrough on `http://127.0.0.1:4174/` proving top navigation, manual intake actions, and worker/employer preview actions
- `docker build -t golden-rose-presentation-demo:local presentation-demo`
- `docker run --rm --name gr-demo-serving-test4 -p 127.0.0.1:8081:8080 golden-rose-presentation-demo:local`
- `node presentation-demo/verify-served-demo.mjs http://127.0.0.1:8081`

## Verification outcomes

- PASS: 8/8 unit/invariant tests
- PASS: static served validation against loopback `index.html` and `app.js`
- PASS: browser interaction validation for top navigation, manual worker/employer intake, worker interest preview, and employer update preview
- PASS: synthetic-data contract checks (single concise disclaimer, bounded actors, concrete due times, no real API/auth/db references)
- PASS: local artifact builds successfully into a pinned nginx image and serves from loopback

## Known caveats

- The artifact is intentionally disconnected from product backend/runtime and has reset-on-refresh behavior.
- An older local container may still be serving an earlier demo on `127.0.0.1:4173`; rebuild/restart that container before using port 4173 for the updated walkthrough.

## Acceptance alignment

This artifact is suitable for the synthetic concept presentation demonstration lane when run locally on loopback for tomorrow’s walkthrough, provided it is introduced verbally as concept/non-production before stakeholders review it.
