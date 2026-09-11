# Temporary shared browser-access procedure

This procedure governs Beatrice's temporary browser access to the first human-visible fictional-synthetic GCP `develop` deployment while application authentication remains synthetic. Cloud Run invocation is temporarily public, but every business/static route is protected by the expiring shared HTTP Basic gate.

Current source status: the successor packet stopped read-only at A02 on managed-IAM verifier modeling and is consumed. No service, invoker, password, URL, access grant, or qualification action occurred. Bounded source correction is active from `develop@4b678d1c2b6b5eb13c1031bd2cd4be16a2da5302`; this procedure requires a fresh final-tip packet and approval.

## Scope

- Beatrice's browser and bounded API qualification only
- exact service-stage `allUsers` → `roles/run.invoker`
- synthetic application auth remains in place
- expiring high-entropy HTTP Basic gate before every non-probe route

## Required posture

- `/health` and `/readiness` are public, no-store, and minimized to status only
- `/`, static assets, `/api/staff/v1/environment`, and every staff API require the fixed username `golden-rose-demo` plus the shared password
- the password is at least 32 random bytes encoded as canonical unpadded base64url, stored only in Secret Manager and an owner-held `0600` file
- expiry is strict UTC RFC 3339, unexpired, and no later than seven days after revision creation
- Cloud Run is capped at zero-to-one instances and Cloud SQL remains private
- `allAuthenticatedUsers`, named tester invokers, extra public members, project-wide tester roles, sessions, and cookies are absent

## Operator-held record

Before granting access, record outside tracked source:

- credential file location and `0600` mode
- secret version reference without payload
- revision creation and credential-expiry evidence
- approving owner and packet expiry
- service-level public-invoker readback
- rotation/removal owner
- any incident or exception notes

Do not place tester identities or emails into repo docs, Terraform vars, or PR comments.

## Enablement procedure

1. Verify exact source/image, private Cloud SQL, one-instance cap, synthetic labels, budget alerts, and runtime-only access to `demo-access-password`.
2. Generate the password directly into Secret Manager stdin and the owner-held file; do not display or pass it in argv.
3. Configure the strict bounded expiry and apply the exact service plan only after migration success.
4. Read back exactly one `roles/run.invoker` member: `allUsers`. Stop on any other invoker or broad project role.
5. Prove unauthenticated and wrong-Basic business requests return the same fixed no-store `401`, while public probes remain minimized.
6. Run the synthetic workflow qualification with the correct password through a non-argv handoff.
7. Let the qualification command collect the exact service's last 15 minutes of Cloud Run revision logs after every synthetic request with `--log-project-id <workload-project>`; the fixed no-shell query scans in memory for Authorization, Basic credentials, password material, submitted fictional values, UUIDs, cursors, DSNs, and raw bodies. `--log-export-file` is reserved for a separately synchronized `0600` post-request export.
8. Deliver the URL and credential-file location privately; never return the password in chat.

For manual browser mutations, use only server-admitted generated fictional shapes: `Synthetic Demo Employer <8 lowercase hex>` with optional ` Revised`, and `Synthetic Demo Contact <8 lowercase hex>`. Ordinary plausible names are intentionally rejected before persistence. Never disguise real/client-derived data by adding a synthetic prefix.

## Qualification invocation boundary

- `scripts/qualify_develop_deployment.py` must not receive the password on the command line.
- Use exactly one non-argv handoff: `--demo-password-stdin`, `--demo-password-env <ENV_NAME>`, or `--demo-password-file <path>`.
- Use `--log-project-id <workload-project>` so the fixed log query runs only after every HTTP qualification request. Do not substitute a pre-request export as post-qualification evidence.
- Use only the reviewed Cloud Run `https://...a.run.app` authority for `--base-url`; do not add userinfo, query strings, fragments, alternate ports, or paths.
- Pass `--allow-synthetic-writes` only when the operator explicitly intends to run the synthetic create/revision/contact qualification flow.
- The tracked output must preserve the schema-stable `manual_browser`, `accessibility`, `fluent_language`, `tester_access`, `monitoring`, `recovery`, and `feedback` fields as `not_run`, `not_evidenced`, or `not_triaged` until those separate gates run.
- The automated evidence must require `Cache-Control: no-store` for exercised responses, including safe generated not-found/cursor/stale/idempotency controls; it may use source-controlled static contract evidence only for unavailable, authorization, and other unsafe-to-induce outcomes.
- Reconcile the final status through `deploy/gcp/qualification-status-contract.md`, `deploy/gcp/human-qualification-checklist.md`, and `deploy/gcp/human-feedback-template.md`; the only tracked status labels are `qualified_private_develop_for_human_feedback`, `operational_private_develop_technical_feedback_only`, `not_qualified`, and `torn_down_after_failed_activation`.

## Verification checklist

The operator performing the later approved access ceremony must verify:

- the service ingress remains internet-reachable and has exactly the accepted temporary `allUsers` invoker
- the Basic gate and expiry protect every non-probe route
- no second invoker model or convenience binding exists
- only the runtime service account can access the demo-password secret
- alerting and incident contacts for the tester window are known

## Removal procedure

Remove access when the credential expires, the synthetic feedback window closes, or any exposure concern appears:

1. remove `allUsers` from the exact Cloud Run service
2. disable/destroy the demo-password version and remove the Basic configuration
3. verify no inherited or broad invocation remains
4. update the private operator-held record with removal time and actor

## Forbidden shortcuts

- `allAuthenticatedUsers`
- project-level basic roles for testers
- any additional or named invoker retained beside `allUsers`
- direct secret disclosure to testers through chat, PRs, or screenshots
- using tester access as a substitute for application authorization design

## Accidental exposure response

If the service URL, credential material, or invoker posture leaks:

1. remove the exact `allUsers` invoker binding when needed for immediate containment
2. stop the browser-access window
3. rotate any affected secrets or access material
4. re-verify the exact service-level `allUsers` invoker set, expiring Basic-gate posture, and fixed unauthorized denials before restoring access
5. reopen access only after the private record reflects the corrective action
