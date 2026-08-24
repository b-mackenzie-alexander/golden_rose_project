# Private tester access procedure

This procedure governs named tester access to the first private fictional-synthetic GCP `develop` deployment while application authentication remains synthetic. It exists because Terraform and CI must not infer human access rosters or create broad convenience access.

Current source status: PR #37 merged the exact named-tester contract into protected `develop` at `caf96a7`. This procedure remains future operator guidance until the later explicitly approved tester-access gate.

## Scope

- named private testers only
- IAM-authenticated internet-reachable Cloud Run access for the staff tracer only
- synthetic application auth remains in place
- no public access and no broad authenticated-user shortcut

## Required posture

- every tester is individually attributable and bound as one reviewed named user principal
- every tester identity is recorded in an operator-held private record
- every access grant is service-level and bounded to the reviewed Cloud Run service
- `allUsers` and `allAuthenticatedUsers` are forbidden
- project-wide editor/owner/viewer or Secret Manager access is forbidden for testers
- tester access is temporary and reviewable

## Operator-held record

Before granting access, record outside tracked source:

- tester name
- tester principal identifier
- approving owner
- start time and expected end/review time
- reason for access
- granted service/resource scope
- removal owner
- any incident or exception notes

Do not place tester identities or emails into repo docs, Terraform vars, or PR comments.

## Grant procedure

1. Confirm the target deployment is still private, synthetic-only, and qualified for a named tester window.
2. Verify the detached Sigstore bundle for the operator-held tester-authority receipt before reading it. Derive exactly one `user:` principal and retain only the receipt SHA-256 for Terraform input; a typed principal or caller-supplied digest is not authority.
3. Confirm the derived tester has explicit owner approval and appears in the operator-held record.
4. Confirm the reviewed private access path is available for that identity.
5. Grant only the reviewed service-level Cloud Run invoker access to the exact receipt-derived named tester user principal, with its immutable tester-authority receipt SHA-256.
6. Verify no project-wide convenience role, no `allUsers`, and no `allAuthenticatedUsers` binding was introduced.
7. Deliver the private access instructions out of band. Do not paste private endpoints, receipt contents, or identity details into chat or repo artifacts.
8. Run the bounded qualification checks needed to prove access works without widening the service boundary.

## Qualification invocation boundary

- `scripts/qualify_develop_deployment.py` must not receive the private bearer token on the command line.
- Provide the token only through one of the reviewed non-echoing handoffs:
  - `--access-token-stdin` with the token piped from a protected source
  - `--access-token-env <ENV_NAME>` where the environment variable is populated outside shell history and cleared immediately after use
  - `--access-token-file <path>` where the file has restrictive local permissions and is deleted immediately after use
- Use only the reviewed IAM-authenticated Cloud Run `https://...a.run.app` authority for `--base-url`; do not add userinfo, query strings, fragments, alternate ports, or paths.
- Pass `--allow-synthetic-writes` only when the operator explicitly intends to run the synthetic create/revision/contact qualification flow.

## Verification checklist

The operator performing the later approved access ceremony must verify:

- the service ingress remains internet-reachable but IAM-authenticated and non-public
- invoker access remains limited to reviewed named user principals
- no public or convenience binding exists
- tester identities remain synthetic-workflow users only; they do not gain admin, database, or secret authority
- alerting and incident contacts for the tester window are known

## Removal procedure

Remove access when the tester window closes, the roster changes, or any exposure concern appears:

1. remove the tester principal binding from the exact Cloud Run service
2. verify the removed principal no longer has invoker access through inherited or broad bindings
3. update the private operator-held record with removal time and actor
4. if the tester handled any leaked or suspect secret material, rotate those secrets before reopening access

## Forbidden shortcuts

- `allUsers`
- `allAuthenticatedUsers`
- project-level basic roles for testers
- shared unnamed tester accounts
- direct secret disclosure to testers through chat, PRs, or screenshots
- using tester access as a substitute for application authorization design

## Accidental exposure response

If a tester URL, identity roster, or invoker binding leaks:

1. remove the exposed binding immediately
2. stop the tester window
3. rotate any affected secrets or access material
4. re-verify the IAM-authenticated ingress posture and named invoker posture
5. reopen access only after the private record reflects the corrective action
