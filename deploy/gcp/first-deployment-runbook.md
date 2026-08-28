# First private synthetic deployment runbook

This runbook defines the human/operator ceremony for the first private fictional-synthetic `develop` deployment after the separate cloud-read, Terraform-plan, and foundation-apply gates are complete. It is intentionally value-safe: project IDs, domains, tester identities, secret payloads, passwords, tokens, and exact private endpoints stay in operator-held records rather than tracked source.

Current source status: PR #37 merged the no-cloud deployment-path remediation at `caf96a7`; PR #42 made tester verification service-stage-only at `b2d79b5`; PR #46 made the evaluated foundation root workload-free and Cloud-SQL-free at `58aed28`; and PR #48 aligned the verifier at `5f265d8`. Private records show separately approved partial foundation work; this runbook remains future operator guidance until private inventory/adoption, foundation planning/apply, and later workload gates are explicitly approved and completed.

## Scope

- first private fictional-synthetic `develop` deployment only
- out-of-band secret payload custody and injection
- private tester access while application auth remains synthetic
- rollback/forward-recovery coordination inputs before first traffic
- deployment/readiness evidence distinct from later Gate 6 qualification evidence
- no Terraform secret payload handling
- no chat, commit, artifact, or ordinary-log secret handling

## Preconditions

1. Gate 2 read-only qualification is complete and any naming or IAM collisions are resolved.
2. Gate 3 reviewed Terraform plan exists and has explicit owner approval.
3. Gate 4 foundation apply is complete and re-verified with `scripts/verify_gcp_foundation.py`.
4. The exact immutable image digest, provenance, SBOM evidence, and vulnerability disposition are approved for deployment.
5. The migration compatibility and rollback-versus-forward-recovery decision has been reviewed for the exact image/database pair.
6. Named secret custodians, testers, alert recipients, and break-glass responders are recorded in a private operator-held record, not this repository.

## Secret custody rules

- Secret Manager secret payloads are injected out of band after foundation apply and before migration or service rollout.
- Terraform source, Terraform state, Terraform plans, workflow inputs, chat, screenshots, review artifacts, and ordinary logs must never contain secret payloads.
- Database passwords must be generated without terminal display where the tooling permits, stored only in the approved secret store, and transmitted only through an approved private channel if a second custodian must receive them.
- If any tool or command would echo a payload, stop and switch to a non-echoing method before proceeding.
- Secret identifiers may appear in value-safe evidence; secret values may not.

## Required private record before injection

Record these items outside tracked source before any payload creation:

- secret custodian name(s)
- rotation owner
- revocation owner
- recovery owner
- approved secret classes and their reviewed consumers
- creation time, last rotation time, and approved expiry/review trigger
- named testers for the first window
- accidental-exposure contact path

Do not place that private record in Git, Terraform variables, CI variables, or repo review handoffs.

## Minimum secret classes

The exact payload set must stay minimal and reviewed. For the current application/runtime contract, the operator-held deployment record must cover at least:

- runtime login connection material for `GOLDEN_ROSE_DATABASE_URL`
- migration login connection material for the later approved migration execution path together with `GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE=golden_rose_schema_owner`
- synthetic staff actor UUID for `GOLDEN_ROSE_SYNTHETIC_STAFF_ID`
- develop deployment-target marker for `GOLDEN_ROSE_DEPLOYMENT_TARGET`
- develop public-environment label for `GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL`
- deployed immutable digest marker for `GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST`

If later deployment wiring uses a different secret-to-environment mapping, update this runbook before deployment rather than improvising at the console.

## Injection ceremony

1. Confirm the reviewed secret metadata already exists and matches the intended secret classes.
2. Generate the database password and any other payload-bearing values without pasting them into chat, shell history, Terraform files, or PR comments.
3. Create new secret versions out of band for the approved payload-bearing secrets only.
4. Verify version creation through value-safe identifiers only; do not print payloads back to confirm them.
5. Update the private custody record with custodian, rotation, recovery, and revocation ownership plus the created version references.
6. Inject only reviewed secret references into the runtime/migration deployment surface at the later approved deployment gate; never convert this into inline environment literals in source-controlled IaC.
7. After rollout, validate the application through the bounded qualification tooling without emitting the injected values.

## Database password procedure

- Generate the password with a cryptographically strong local method approved for operator use.
- Do not display the password after generation if the tool supports direct write to clipboard, file descriptor, or secret-manager stdin.
- If temporary local staging is unavoidable, use an ignored local file with restrictive permissions, delete it immediately after successful secret-version creation, and do not copy it into terminal transcripts or notes.
- Never commit SQL user resources, password variables, or password outputs into Terraform.

## Database authority verification boundary

- Create authenticated database login roles out of band only; Terraform and source-controlled migrations continue to own only the non-login group roles.
- Grant the runtime login only the bounded `golden_rose_runtime` group role.
- Grant the migration login only the `golden_rose_migrator` group role and require the reviewed migration path to assume `golden_rose_schema_owner` explicitly through `GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE`.
- Before treating deployment authority as qualified, run `scripts/verify_database_authority.py` with reviewed admin/runtime/migration connection material and confirm the live login-role chain plus representative bounded-login probes pass.

## Migration-success receipt and service approval boundary

- The later service gate also requires the signed migration receipt as a separate service gate input; the migration-success receipt supplements it and never replaces it.
- A migration-success receipt is authority only after a successful waited migration execution produces the reviewed JSON plus detached Sigstore bundle.
- The later service gate must verify the migration-success receipt and its detached Sigstore bundle before cloud authentication.
- That verification must bind to the reviewed GitHub Actions certificate identity and OIDC issuer rather than trusting a blob or bundle without its reviewed signer identity.
- Service approval still requires separate database/schema/authority readback after migration completion and before service approval; a signed migration-success artifact set is necessary but not sufficient by itself.
- Do not treat a present migration-success receipt, bundle, or signature as permission to skip the separate database authority and schema readback evidence.

## Private tester access boundary

While application auth remains synthetic, platform-level access to the private Cloud Run service is the only tester gate. The private tester ceremony must therefore:

- use only reviewed named tester user identities recorded outside public evidence
- grant access only at the reviewed Cloud Run service boundary
- preserve the reviewed IAM-authenticated internet-reachable ingress posture
- avoid `allUsers` and `allAuthenticatedUsers`
- avoid broad project-level convenience bindings
- end with explicit access removal or review-triggered retention in the private operator record

See `deploy/gcp/private-tester-access.md` for the exact tester procedure.

## Stop conditions

Stop immediately if any of the following occurs:

- a secret payload appears in chat, shell output, Terraform plan/state, PR text, ticket text, screenshot, or artifact
- a command path requires `allUsers` or `allAuthenticatedUsers`
- a tester cannot be mapped to a named approved principal
- the reviewed digest, migration evidence, or foundation verification no longer matches the intended target
- a secret must be copied through an unapproved channel

## Accidental exposure cleanup

If a secret or private endpoint is exposed, or if public/broad invoker access is granted by mistake:

1. Stop the deployment or tester-access ceremony immediately.
2. Remove the broad invoker binding or other exposure path before continuing.
3. Revoke and replace every affected secret value; do not keep using a leaked value merely because the target is non-production.
4. Invalidate any temporary copies, clipboard contents, local files, and ad-hoc notes used during the failed ceremony.
5. Re-run foundation verification and bounded deployment qualification before restoring tester access.
6. Record the incident, custodian actions, and rebuilt secret references in the private operator-held record.
7. If exposure scope is uncertain, prefer teardown/rebuild over partial cleanup.

## Evidence boundary

Allowed repository evidence after the later approved deployment may include only value-safe statements such as:

- secret versions were created out of band
- named custodians/testers exist in a private record
- private invoker posture remained named and non-public
- qualification passed or failed with redacted evidence

Do not record payloads, private URLs, tester emails, password derivation material, or raw command transcripts in tracked source.
