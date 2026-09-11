# First human-visible synthetic deployment runbook

This runbook defines the single eight-hour operator packet for the first human-visible fictional-synthetic `develop` deployment. It is intentionally value-safe: project IDs, billing IDs, domains, principals, secret payloads, passwords, tokens, plans, state values, and the exact service URL stay in operator-held records rather than tracked source.

Current source status: PR #88 merged the PR #87 closeout into protected `develop@4b678d1c2b6b5eb13c1031bd2cd4be16a2da5302`. A fresh successor packet was approved; A00/A01 and exact A02 readback passed, but the mandatory foundation verifier stopped on incomplete managed-service-agent allowlisting and exact same-provider redundant-role handling. That packet is consumed and performed no mutation. Bounded source correction is active; after protected merge and final-tip rebind, one fresh explicitly approved packet may resume the one ordered transaction for no more than eight hours.

## Scope

- first private fictional-synthetic `develop` deployment only
- out-of-band secret payload custody and injection
- temporary `allUsers` Cloud Run invocation behind the expiring application Basic gate
- rollback/forward-recovery coordination inputs before first traffic
- deployment/readiness evidence distinct from later Gate 6 qualification evidence
- no Terraform secret payload handling
- no chat, commit, artifact, or ordinary-log secret handling

## Preconditions

1. The source PR is merged and the packet is bound to its exact protected `develop` SHA, repository, publication workflow identity, Terraform/provider locks, state generations, non-secret inputs, and action allowlists.
2. Beatrice's selected named human identity has custom-role create/read plus project-IAM policy get/set authority for the narrow quota bootstrap, read-only access to enumerate the workload project's folder/organization ancestry and each ancestor IAM policy, and the existing project permissions required to read/plan/apply the reviewed Terraform-managed workload graph. Bind that exact named `user:` as `--provider-operator-principal` on every live foundation-verifier call. The verifier may accept `roles/owner` only when its complete direct membership is exactly that one provider operator; any other basic role or additional member stops the packet. The provider authority precheck must prove effective scope before packet execution; missing ancestor or managed-resource visibility stops the packet and is not treated as absence.
3. Terraform credential separation is explicit: provisioner impersonation is limited to the GCS backend through the private backend configuration; the named human supplies Google provider authority for workload refresh/import/plan/apply. Do not export a provisioner token as process-wide `GOOGLE_OAUTH_ACCESS_TOKEN`, and no project provisioning role is granted to the provisioner.
4. Current state, IAM, resources, budget, labels, service-account keys, and collision posture have been read back without mutation.
5. The exact immutable image digest is either already admitted for the source SHA or is declared as the exact publication workflow's designated packet output.
6. Private custody locations, alert recipients, and the accidental-exposure path are recorded outside Git and chat.

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
- browser credential recipient for the first window
- accidental-exposure contact path

Do not place that private record in Git, Terraform variables, CI variables, or repo review handoffs.

## Minimum Secret Manager payload classes

The executable Secret Manager references are limited to:

- runtime login connection material for `GOLDEN_ROSE_DATABASE_URL` in `runtime-database-url`
- migration login connection material for the later approved migration execution path in `migration-database-url`, together with the non-secret `GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE=golden_rose_schema_owner` configuration
- synthetic staff actor UUID for `GOLDEN_ROSE_SYNTHETIC_STAFF_ID` in `synthetic-staff-id`
- at least 32 random bytes encoded as canonical unpadded base64url for `GOLDEN_ROSE_DEMO_ACCESS_PASSWORD` in `demo-access-password`

`GOLDEN_ROSE_DEPLOYMENT_TARGET`, `GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL`, and `GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST` are reviewed non-secret Terraform configuration, not Secret Manager payload classes. The metadata-only `deployment-posture` container has no current runtime or migration secret reference and receives no version merely to satisfy historical wording.

If later deployment wiring uses a different secret-to-environment mapping, update and review the source contract before deployment rather than improvising at the console.

## Injection ceremony

1. Confirm the reviewed secret metadata already exists and matches the four executable Secret Manager references.
2. Read back the already completed bounded `synthetic-staff-id` version through value-safe metadata only; do not create a placeholder or duplicate version merely for this packet.
3. Do not create runtime or migration database-URL versions until migration-stage Cloud SQL/database creation and the packet's login-role step provide real connection material; placeholders and guessed URLs are prohibited.
4. Generate database passwords and other payload-bearing values without pasting them into chat, shell history, Terraform files, or PR comments.
5. Create new database-URL Secret versions out of band for the packet-authorized payload-bearing secrets only after the database and login roles are ready; this is an internal packet step, not a fresh approval.
6. Verify every version creation through value-safe identifiers only; do not print payloads back to confirm them.
7. Update the private custody record with custodian, rotation, recovery, and revocation ownership plus the created version references.
8. Generate the demo password directly into Secret Manager stdin and an owner-held `0600` file outside the repository; never place it in argv, Terraform state, workflow inputs, logs, or chat.
9. Set the strict UTC RFC 3339 expiry no later than seven days after the service revision creation boundary and keep the timestamp out of public evidence.
10. Inject only reviewed secret references into the runtime/migration deployment surface; never convert payloads into inline Terraform values.
11. After rollout, invoke `scripts/qualify_develop_deployment.py` with `--demo-password-file`, `--demo-password-env`, or `--demo-password-stdin`, then clear the handoff.

The develop application accepts persisted mutation values only in generated fictional forms: `Synthetic Qual Employer <8 lowercase hex>`, `Synthetic Demo Employer <8 lowercase hex>` with optional ` Revised`, and `Synthetic Contact <8 lowercase hex>` or `Synthetic Demo Contact <8 lowercase hex>`. Plausible ordinary names fail with a fixed no-store `422` before receipt, domain, or audit access. Do not paste real/client-derived values behind a synthetic prefix.

## Database password procedure

- Generate the password with a cryptographically strong local method approved for operator use.
- Do not display the password after generation if the tool supports direct write to clipboard, file descriptor, or secret-manager stdin.
- If temporary local staging is unavoidable, use an ignored local file with restrictive permissions, delete it immediately after successful secret-version creation, and do not copy it into terminal transcripts or notes.
- Never commit SQL user resources, password variables, or password outputs into Terraform.

## Database bootstrap and authority verification boundary

1. After the migration-stage Terraform apply creates private Cloud SQL and both bounded jobs, use the packet's prechecked named-human Cloud SQL user-management authority to create one temporary bootstrap built-in user. Keep its operator-selected username in the private record and supply the project, instance, generated password, and other flag values through an owner-only `--flags-file` with mode `0600`; the password is never a command-line password, terminal output, or chat value.
2. Add the temporary private database URL as the first `migration-database-url` version without displaying it, then dispatch `deploy-develop.yml` at `deployment_stage=migration`. Before execution, the workflow must exact-check the stored migration job's labels, admitted image, identity, command, absent arguments, one-container/task/parallelism, zero retries, timeout, project-qualified VPC network/subnetwork, and duplicate-free environment/Secret projection. On a clean database, `golden-rose-migrate` may then bootstrap the three NOLOGIN authority roles and migrate the schema under that temporary Cloud SQL bootstrap authority.
3. After those roles exist, create the durable migration and runtime built-in users through separate owner-only `--flags-file` inputs. The effective Cloud SQL user contracts must equal `--database-roles=golden_rose_migrator` and `--database-roles=golden_rose_runtime`; omitting the custom role or retaining `cloudsqlsuperuser` is a stop condition.
4. Add new `migration-database-url` and `runtime-database-url` versions for those restricted logins. The migration login inherits only `golden_rose_migrator`; the runtime login inherits only `golden_rose_runtime`. Neither login may be superuser or manage roles.
5. Before any restricted migration-login rerun, disable the temporary bootstrap Secret version and delete the temporary bootstrap user so its migration-role membership is removed. Read back that the restricted URL versions remain enabled, the temporary bootstrap authority is absent, and the migration group has exactly the restricted migration login as its sole direct member. Failure to prove retirement is a stop condition; do not weaken the initialized-authority precheck or restore the temporary user automatically.
6. Perform one restricted migration-login rerun through `deploy-develop.yml` at `deployment_stage=migration`. Before `SET ROLE` or Alembic, the initialized-database path must exact-check all three NOLOGIN application-role attributes, the sole non-admin schema-owner → migrator grant, the sole non-admin migrator → current restricted-login grant, and the complete outgoing-role inventory for every application role and the current login; any extra incoming or outgoing membership or elevated role attribute fails closed. It must skip privileged role bootstrap, assume `golden_rose_schema_owner` only through that reviewed chain, and complete the no-op/head migration successfully.
7. Run the live foundation verifier in migration mode and require exactly the two named jobs with no extras. It must exact-check the database-authority job's labels, admitted image, identity, command, absent arguments, one-container/task/parallelism, zero retries, timeout, project-qualified VPC network/subnetwork, environment/Secret projection, complete job IAM, and exact migration/runtime Secret IAM policies. Then dispatch `deploy-develop.yml` at `deployment_stage=database-verification`; its independent projection readback must enforce the same no-override bounds before waited execution, which must pass before service planning.
8. After successful verification, read back again that the restricted URL versions remain enabled, the temporary bootstrap user and role membership remain absent, and the temporary bootstrap Secret version remains disabled.
9. Never put SQL user resources, password variables, password outputs, connection URLs, or private host values in Terraform, Git, workflow inputs, or ordinary evidence.

## Quota bootstrap and import boundary

1. Before provisioner backend initialization, the prechecked human creates—or exact-readbacks—`goldenRoseProvisionerQuotaUser` with title `Golden Rose Provisioner Quota User`, exact description `Permits only workload-project quota attribution for the provisioner.`, stage `GA`, and sole permission `serviceusage.services.use`.
2. The same human creates—or exact-readbacks—the sole binding to `golden-rose-provisioner@<control-plane-project>.iam.gserviceaccount.com`.
3. Enumerate the workload project's complete folder/organization ancestry, require exactly one project anchor matching the reviewed workload project with no duplicate ancestor, and read every ancestor IAM policy. Stop on empty/unanchored/unreadable/malformed ancestry; any direct/public/service-account-principal-set ancestor binding that can confer provisioner authority; or any group binding whose service-account membership cannot be proven absent from policy data.
4. Stop on collision, wrong title/description/stage, any additional permission/member, a broad predefined role, inherited provisioner authority, or a user-managed service-account key.
5. After propagation, the provisioner initializes the existing workload backend and imports exactly `module.develop.google_project_iam_custom_role.provisioner_quota_user` and `module.develop.google_project_iam_member.provisioner_quota_user`.
6. Read back both state objects. The first full migration plan must show zero actions for both addresses.

## One-packet execution order

Within the approved eight-hour window: precheck named-human provider authority plus backend-only provisioner impersonation; exact quota bootstrap/readback; backend initialization/import/readback; exact-source image publication if needed; migration plan inspection/apply/readback creating private Cloud SQL, the migration job, and the database-authority job; temporary bootstrap-user and first migration-URL version preparation through owner-only non-argv files; exact first migration-job projection/image readback and bootstrap migration execution; restricted migration/runtime login creation and URL-secret version preparation; temporary bootstrap Secret/user/membership retirement with exact readback; restricted migration-login rerun; private `database-verification` job execution and retirement recheck; demo-password/expiry preparation; service plan inspection/apply/readback; foundation/application/log qualification; non-mutating teardown/rebuild readiness inspection; private URL and credential-file-location delivery. Both jobs and the service must equal the packet's exact verifier-admitted digest before execution/readiness. Unknown mutation outcomes require readback before retry. Deletes, replacements, budget mutation, public database access, broad IAM, extra principals, secret leakage, source/image/state drift, or out-of-allowlist actions stop the packet.

## Human access boundary

For this fictional-synthetic target only, Cloud Run has exactly `allUsers` → `roles/run.invoker`; the application Basic middleware is the shared browser boundary. `/health` and `/readiness` remain public and minimized. Every business, environment, and static route is protected. Cloud Run remains capped at zero-to-one instances and Cloud SQL remains private. The password and URL are delivered privately; only the owner-held credential-file location may be returned in ordinary chat. `allAuthenticatedUsers`, named tester invokers, project-wide convenience roles, sessions, and cookies remain absent.

See `deploy/gcp/private-tester-access.md` for the exact tester procedure.

## Stop conditions

Stop immediately if any of the following occurs:

- a secret payload appears in chat, shell output, Terraform plan/state, PR text, ticket text, screenshot, or artifact
- a command path requires `allAuthenticatedUsers`, an additional invoker, or any project-wide convenience role
- the application Basic gate, expiry, or one-instance cap cannot be verified
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
- private credential custody exists in an owner-held record
- the exact temporary public invoker remained protected by the expiring Basic gate
- qualification passed or failed with redacted evidence

Do not record payloads, private URLs, tester emails, password derivation material, or raw command transcripts in tracked source.
