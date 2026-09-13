# First human-visible synthetic deployment runbook

## Historical status — v28 packet complete
- **Staffing:** One independent developer; fresh agent review and automated checks supply quality evidence.
- **Human-visible outcome:** Protected `develop@3414818b44d5e790f2d11c7fe4d7a48ebeb6241e` is deployed as the private fictional-synthetic `develop` service. Private SQL, application database, restricted logins, migration job, Cloud Run service, expiring Basic access, automated qualification evidence, and browser handoff evidence exist.
- **Gate budget:** The v28 one-use deployment packet is complete and consumed. This runbook remains historical evidence and procedural reference; it does not authorize repeating deployment operations.
- **Next executable action:** Use the running service for human feedback, fix the Spanish-toggle defect, and source-control the v28 qualification-harness normalizations.
- **Do not regress:** Do not recreate completed resources or credentials, restore bootstrap access, copy private URL/password material into source, admit live data, or revive production-only gates as prerequisites for feedback.

This runbook defines the single eight-hour operator packet, valid for no more than eight hours, for the first human-visible fictional-synthetic `develop` deployment. It is intentionally value-safe: project IDs, billing IDs, domains, principals, secret payloads, passwords, tokens, plans, state values, and the exact service URL stay in operator-held records rather than tracked source.

Current execution status: v28 completed the first human-visible private synthetic deployment at protected `develop@3414818b44d5e790f2d11c7fe4d7a48ebeb6241e`. The earlier V20 partial-apply recovery, SQL edition correction, native catalog correction, deletion-protection correction, migration, database verification, service activation, automated qualification, and browser handoff are historical completed stages. No status-closeout PR or repeat packet is required for ordinary feedback work.

## Historical partial-state continuations

V24 through v28 preserved successful resources through multiple bounded corrections and continuations. V28 completed the ordered bootstrap/retirement/verification/service sequence and browser handoff. Do not repeat cleanup, database, user, job, service, credential, or access creation as a prerequisite for feedback.

Job/service configuration projections use `scripts/read_cloud_run_v2.py`, a read-only authenticated v2 client. Default gcloud v1 JSON is not a v2 projection. The exact provider attribution label `goog-terraform-provisioned=true` is required along with source labels; arbitrary extra labels remain rejected. Service readiness uses a succeeded v2 terminal condition, reconciled current generation, and matching latest-created/latest-ready revision. Explicit `maxRetries=0` remains mandatory because the API retry field tracks presence and otherwise defaults to three.

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
3. Terraform credential separation is explicit: provisioner impersonation is limited to the GCS backend through the private backend configuration; the named human supplies Google provider authority for workload refresh/import/plan/apply. Do not export a provisioner token as process-wide `GOOGLE_OAUTH_ACCESS_TOKEN`, and no project provisioning role is granted to the provisioner. Set process-local `GOOGLE_CLOUD_QUOTA_PROJECT` to the bound workload project for provider/backend requests; the required quota-use permission already exists. This does not edit ADC credentials or expand IAM.
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

Run the installed migration CLI from the application working directory. The immutable image sets `WORKDIR /app` and copies `alembic.ini` and `migrations/` there; installing the Python wheel into `site-packages` must not relocate configuration lookup. Source/local CLI commands run from the repository root.

1. After the database-only targeted saved-plan apply creates private Cloud SQL and its application database, use the packet's prechecked named-human Cloud SQL user-management authority to create one temporary bootstrap built-in user. Keep its operator-selected username in the private record and supply the project, instance, generated password, and other flag values through an owner-only `--flags-file` with mode `0600`; the password is never a command-line password, terminal output, or chat value.
2. Add the temporary private database URL as the first `migration-database-url` version without displaying it. Create the migration job and its two scoped deployer bindings using the exact targeted saved plan below, then dispatch `deploy-develop.yml` at `deployment_stage=migration`. Before execution, the workflow must exact-check the stored migration job's labels, admitted image, identity, command, absent arguments, one-container/task/parallelism, zero retries, timeout, project-qualified VPC network/subnetwork, and duplicate-free environment/Secret projection. On a clean database, the explicit `develop`/`gcp-develop-private-synthetic` profile uses `SET LOCAL ROLE cloudsqlsuperuser` to create the three NOLOGIN roles and grant owner to migrator plus migrator to `SESSION_USER`, with ADMIN false and INHERIT/SET true. It resets role before transferring the schema and migrating as schema owner. The existing managed administrator must retain its observed LOGIN/INHERIT/CREATEDB/CREATEROLE and non-superuser/non-replication/non-BYPASSRLS profile. It is the durable grantor, so the temporary login can be deleted without dropping durable grants. Local superuser bootstrap stays unchanged.

3. After those roles exist, create the durable migration and runtime built-in users through separate owner-only `--flags-file` inputs. The effective Cloud SQL user contracts must equal `--database-roles=golden_rose_migrator` and `--database-roles=golden_rose_runtime`; omitting the custom role or retaining `cloudsqlsuperuser` is a stop condition.
4. Add new `migration-database-url` and `runtime-database-url` versions for those restricted logins. The migration login inherits only `golden_rose_migrator`; the runtime login inherits only `golden_rose_runtime`. Neither login may be superuser or manage roles.
5. Before any restricted migration-login rerun, disable the temporary bootstrap Secret version and delete the temporary bootstrap user so its migration-role membership is removed. Read back that the restricted URL versions remain enabled, the temporary bootstrap authority is absent, and the migration group has exactly the restricted migration login as its sole assumable direct member, alongside only the modeled managed administrator ADMIN-only creator membership. Failure to prove retirement is a stop condition; do not weaken the initialized-authority precheck or restore the temporary user automatically.
6. Perform one restricted migration-login rerun through `deploy-develop.yml` at `deployment_stage=migration`. Before `SET ROLE` or Alembic, the initialized-database path must exact-check all three NOLOGIN application-role attributes, the sole non-admin schema-owner → migrator grant, the sole non-admin migrator → current restricted-login grant, and the complete outgoing-role inventory for every application role and the current login; the managed profile additionally requires exactly three PostgreSQL-created administrator memberships (ADMIN true, INHERIT/SET false, superuser grantor) and `cloudsqlsuperuser` as the owner-to-migrator grantor. Any other incoming/outgoing membership or elevated restricted-role attribute fails closed. It must skip privileged role bootstrap, assume `golden_rose_schema_owner` only through that reviewed chain, and complete the no-op/head migration successfully.
7. After both restricted URL versions exist, complete the full untargeted migration reconciliation to create the verifier and remaining scoped bindings. Run the live foundation verifier in migration mode and require exactly the two named jobs with no extras. It must exact-check the database-authority job's labels, admitted image, identity, command, absent arguments, one-container/task/parallelism, zero retries, timeout, project-qualified VPC network/subnetwork, environment/Secret projection, complete job IAM, and exact migration/runtime Secret IAM policies. Then dispatch `deploy-develop.yml` at `deployment_stage=database-verification`; its independent projection readback must enforce the same no-override bounds before waited execution, which must pass before service planning.
8. After successful verification, read back again that the restricted URL versions remain enabled, the temporary bootstrap user and role membership remain absent, and the temporary bootstrap Secret version remains disabled.
9. Never put SQL user resources, password variables, password outputs, connection URLs, or private host values in Terraform, Git, workflow inputs, or ordinary evidence.

## Quota bootstrap and import boundary

**Current-target resumption:** Both imports are complete and v20 added resources afterward. Bind serial 45 and the exact private partial-inventory evidence; do not demand serial 41, repeat imports, or run a workload-free foundation verifier against this partial state. Use exact partial-resource readbacks before recovery and the normal migration-mode verifier after full reconciliation. Keep the budget no-op requirement.

1. Before provisioner backend initialization, the prechecked human creates—or exact-readbacks—`goldenRoseProvisionerQuotaUser` with title `Golden Rose Provisioner Quota User`, exact description `Permits only workload-project quota attribution for the provisioner.`, stage `GA`, and sole permission `serviceusage.services.use`.
2. The same human creates—or exact-readbacks—the sole binding to `golden-rose-provisioner@<control-plane-project>.iam.gserviceaccount.com`.
3. Enumerate the workload project's complete folder/organization ancestry, require exactly one project anchor matching the reviewed workload project with no duplicate ancestor, and read every ancestor IAM policy. Stop on empty/unanchored/unreadable/malformed ancestry; any direct/public/service-account-principal-set ancestor binding that can confer provisioner authority; or any group binding whose service-account membership cannot be proven absent from policy data.
4. Stop on collision, wrong title/description/stage, any additional permission/member, a broad predefined role, inherited provisioner authority, or a user-managed service-account key.
5. After propagation, the provisioner initializes the existing workload backend and imports exactly `module.develop.google_project_iam_custom_role.provisioner_quota_user` and `module.develop.google_project_iam_member.provisioner_quota_user`.
6. Read back both state objects. The first full migration plan must show zero actions for both addresses.

## One-packet execution order

Within the approved eight-hour window: exact partial-inventory/provider/backend precheck; explicitly approved failed-job cleanup and absence readback; exact-source image publication/admission; database-only saved-plan inspection/apply/readback; temporary bootstrap-user and migration-URL Secret preparation; migration-job-only saved-plan inspection/apply/readback; exact first migration projection and bootstrap execution; restricted login/URL Secret preparation; temporary bootstrap Secret/user/membership retirement with exact readback; restricted migration-login rerun; full untargeted migration reconciliation; migration-mode foundation verification and private `database-verification` execution; demo-password/expiry preparation; service plan/apply/readback; foundation/application/log qualification; non-mutating teardown/rebuild readiness inspection; private URL and credential-file-location delivery. Both jobs and the service must match the exact verifier-admitted digest before execution/readiness. Unknown mutation outcomes require readback, never blind retry. Other deletes/replacements, budget mutation, public SQL, broad IAM, extra principals, leakage, and binding drift stop the packet.

### Exceptional recovery of the first bootstrap

This is a bounded recovery from v20's observed partial apply, not routine resource targeting. [Terraform documents targeting for exceptional recovery](https://developer.hashicorp.com/terraform/tutorials/state/resource-targeting). Complete a full untargeted migration plan/apply afterward; targeted results alone do not establish convergence.

1. Bind the current partial state and exact failed `verify-database-authority` identity/generation. Reconfirm `Ready=False`, zero execution count, and an empty execution list. Only a newly approved packet explicitly naming this cleanup may delete that one failed job using the native Cloud Run API/CLI, then require absence readback. Terraform deletion protection blocks a tainted-object destroy, so do not attempt a Terraform replacement, untaint, state removal, or state editing. All successful resources remain intact.
2. With migration-stage inputs and the newly admitted digest, create/inspect/apply a saved plan with only `-target=module.develop.google_sql_database.application[0]`. Its dependency closure creates the private instance and application database; it must not create either job. Pin `settings.edition = "ENTERPRISE"` with `db-f1-micro`; PostgreSQL 16's API default is Enterprise Plus and rejects this tier. No budget update or destructive action is allowed.
3. Create the temporary bootstrap login and its real migration URL Secret version without exposing payloads. Then create/inspect/apply a saved plan targeting only `module.develop.google_cloud_run_v2_job_iam_member.deployer_jobs_executor[0]` and `module.develop.google_cloud_run_v2_job_iam_member.deployer_migration_job_viewer[0]`. Their dependency closure creates the migration job. Inspect the complete plan; do not assume targeting prevents unrelated dependency changes.
4. Execute bootstrap migration, create restricted logins and both real URL Secret versions, retire bootstrap authority, and complete the restricted migration rerun. Only then create/inspect/apply the full untargeted migration plan. Ordinary refresh must recognize the deleted failed verifier as absent and propose `create` only. Reject replacement or any other deletion. This reconciliation adds the verifier and remaining scoped bindings, including demo Secret access after metadata creation. Verify both jobs and the database before service planning.
5. Retire targeting after full reconciliation. Future source changes and production planning use the normal full-plan path. This recovery introduces no placeholder Secret versions, broad IAM, new database schema, or new deployment-stage model.

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

## Deployment workflow registration and digest discovery

Before dispatch, confirm the workflow is registered on the repository default branch (`develop` as explicitly approved during v23), and the develop environment contains the exact existing workload-identity provider, workload project, artifact-verifier identity, deployer identity, and build certificate identity. These variables reference reviewed authority; they do not grant IAM. Verify the source tag only to discover its signed digest. Re-verify the immutable reference into the signature file admitted by the repository checker; never substitute tag-produced output or relax immutable subject checks. Preserve completed database/job/credential steps on retries and confirm whether a prior attempt actually executed migration.
