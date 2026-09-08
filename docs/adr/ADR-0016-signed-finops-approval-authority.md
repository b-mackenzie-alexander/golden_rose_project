# ADR-0016: Require signed one-use authority for FinOps transactions

- **Status:** Accepted; protected publication pending
- **Date:** 2026-09-07
- **Owner:** Beatrice Alexander (engagement owner and sole repository maintainer)
- **Amends:** ADR-0015 transaction-approval authority and Implementation PR A
- **Related:** ADR-0011, ADR-0012, ADR-0014, `.hermes/plans/2026-09-07_signed-finops-approval-authority-amendment-plan.md`

## Context and evidence posture

ADR-0015 and its outcome-scale plan merged through PR #79 and authorized Implementation PR A source work only. PR #80 then merged the post-status closeout at protected `develop@c933bfc934d2f61e4c08e077e92cc82af7e017dc`. Implementation PR A began from that exact tip and remained uncommitted, unpushed, source-only, and no-cloud.

Independent review of the uncommitted candidate found that its local runner interfaces could receive both a policy or approval artifact and a caller-computed digest. Recomputing the named source, input, backend, plan, and approval bytes detects later drift, but it does not distinguish a previously reviewed approval from a fresh self-authored packet when the same caller supplies the artifact, path, and expected digest. That invalidates ADR-0015's assumption that a digest-bound local file alone is an executable approval claim.

The same review also identified command-path, exact saved-plan, and descriptor/pathname gaps. Those are bounded implementation defects under the existing intent. The missing independent approval trust anchor is different: it changes the transaction-authority architecture and therefore triggers ADR-0014 replanning.

Evidence is classified as follows:

- **Observed:** the original PR A candidate stayed local and uncommitted; no GCP authentication, real backend initialization, state operation, plan/apply, import/removal, workflow dispatch, or cloud mutation occurred.
- **Validated:** unsigned local policy-plus-digest input is self-asserted; exact byte recomputation alone cannot prove that the protected approval ceremony authorized those bytes.
- **Validated:** a detached Sigstore bundle with an exact protected workflow identity can authenticate a value-safe approval envelope without exposing private identifiers or granting the signer GCP authority.
- **Accepted prerequisite:** ADR-0011/ADR-0012 retain the same-repository, sole-maintainer CI/approval concentration as a High/open residual risk. This amendment must not describe a protected workflow as an independent second human.
- **Not yet validated:** exact signed-approval schema, workflow/static contract, offline verifier, replay claim, runner integration, and clean reimplementation after amendment merge.

## Decision

### 1. Suspend the existing PR A implementation authority

The source authority granted by merged ADR-0015 is suspended for executable transaction-runner completion because its approval trust assumption proved incomplete. The local uncommitted candidate is preserved as review evidence only. It must not be committed, pushed, opened as a PR, or used as authority.

Implementation resumes only after this ADR and its paired amendment plan are independently reviewed, explicitly accepted, and merged through protected `develop`. The implementation branch must then be recreated from that exact merged tip. Existing local code may be consulted, but only changes expressly authorized by the merged amendment may be replayed and every affected test must run again with honest RED/GREEN classification.

### 2. Use a separate protected signer for value-safe transaction approvals

Add a dedicated `.github/workflows/sign-finops-approval.yml` workflow. It is separate from `.github/workflows/sign-finops-receipt.yml`; receipt signatures and transaction approvals are not interchangeable.

The approval signer:

- runs only by `workflow_dispatch` on exact protected `refs/heads/develop`;
- uses the separately governed `finops-approval` GitHub environment so environment approval is part of the ceremony;
- accepts only a base64-encoded value-safe approval envelope and its exact SHA-256;
- requires the envelope `source_sha` to equal the signer's exact `GITHUB_SHA`;
- validates the complete exact schema, digest grammar, canonical UUIDv4 nonce, domain/operation allowlist, and maximum 30-minute validity window before signing;
- uses keyless Sigstore OIDC through one exact workflow identity and issuer with immutable action pins;
- has no GCP authentication, GCP secrets, repository write, cloud credential, state, plan/apply, or arbitrary artifact-download authority; and
- publishes only the value-safe envelope and detached Sigstore bundle with bounded retention.

The exact executable workflow contract is normative in the paired amendment plan: filename, workflow/job names, job ID, runner, `if`, timeout, concurrency, environment, complete input objects, permissions, ordered step inventory, 40-character action pins, every `with`/`env`/`if`/`shell` field, canonical run body, artifact name/path/file inventory, retention, and failure behavior. Implementation and static allowlists must match that contract bidirectionally; the implementer has no discretion to invent adjacent workflow authority.

The signer establishes cryptographic workflow provenance for the approval ceremony. It does not remove ADR-0011/ADR-0012's accepted High/open sole-maintainer concentration: Beatrice still controls the repository and approval environment. Required checks and delegated review remain quality evidence, not a fictional independent human.

### 3. Define one exact value-safe approval envelope

The envelope is one UTF-8 JSON object with no duplicate keys, no JSON constants, and exactly the following string-valued fields:

- schema `golden-rose.finops-transaction-approval-envelope/v1`;
- canonical UUIDv4 `approval_nonce`;
- `issued_at` and `expires_at`, with a maximum 30-minute window;
- exact protected `source_sha`;
- exact `domain`: `finops`, `workload-state`, `bootstrap`, or `workload-plan`;
- the domain-specific operation enum;
- canonical `transaction_manifest_sha256`;
- exact `policy_sha256`;
- exact `source_artifact_sha256`;
- exact `operation_input_sha256`;
- exact `backend_artifact_sha256`;
- exact `private_approval_record_sha256`; and
- exact `claim_root_fingerprint` derived from the pre-existing owner-only replay root's canonical identity contract.

`source_sha` is exactly 40 lowercase hexadecimal characters. Every `*_sha256` and `claim_root_fingerprint` is exactly 64 lowercase hexadecimal characters. Timestamps use exact UTC RFC 3339 `YYYY-MM-DDTHH:MM:SSZ` form. `approval_nonce` is a lowercase canonical UUIDv4. Strict base64 input is ASCII with no whitespace, has canonical padding/re-encoding, is at most 10,924 encoded bytes, and decodes to 1..8,192 bytes. JSON must be an object; malformed, non-object, missing, extra, duplicate, boolean/null/number/array/object-instead-of-string, receipt-schema, and unknown-schema inputs fail closed.

The exact domain/operation map is:

- `finops`: `collect`, `readback`, `init_import`, `plan`, `apply`;
- `workload-state`: `readback`, `state_remove`;
- `bootstrap`: `plan`, `apply`, `readback`; and
- `workload-plan`: `migration_plan`.

At signer and verifier time, `issued_at` may be at most 60 seconds in the future and at most five minutes old, `expires_at` must be strictly after the current instant, and `0 < expires_at - issued_at <= 30 minutes`. The exact 60-second and five-minute boundaries are accepted; one second beyond either boundary is rejected. There is no implicit local-time or offset-timestamp normalization.

It contains no project, billing account, bucket, principal, email, backend value, path, state, plan body, credential, token, command output, or raw approval text. The signed manifest and policy digests bind the complete domain, identity, operation, ordered primary/finally graph, cwd, argv, environment schema, private artifact paths and hashes, output destinations/schema/limits, expiry, and transaction nonce without exposing those values to GitHub.

For an `apply` transaction, `operation_input_sha256` is the exact saved-plan byte digest, and the policy binds the sole apply argv path to that same artifact. For backend initialization, the policy binds the sole `-backend-config=<path>` argument to the exact backend artifact. The signed policy digest prevents a caller from substituting another `.tfplan`, backend file, command, output path, or artifact map while keeping locally self-consistent hashes.

### 4. Verify and consume signed authority before credentials or commands

Add credential-free `scripts/verify_finops_transaction_approval.py`. All four domain runners must invoke its library boundary before token acquisition or subprocess execution.

The verifier follows this exact order:

1. opens only the value-safe approval envelope and Sigstore bundle through held no-follow regular-file descriptors;
2. verifies the raw envelope bytes through descriptor-backed `/dev/fd/<n>` arguments against the exact approval-workflow certificate identity and GitHub OIDC issuer;
3. only after signature success, parses the envelope with duplicate-key/constant rejection and validates source SHA, domain, operation, time window, nonce, and digest grammar;
4. only then opens the owner-only private claim root and exact policy, manifest, source, operation input, backend, and private approval artifacts through held no-follow descriptors;
5. validates the signed replay-root fingerprint and hashes each private artifact once from its held descriptor;
6. compares the complete manifest/policy graph and exact plan/backend argv bindings;
7. under a verifier-owned exclusive `flock`, creates the nonce claim with `O_CREAT|O_EXCL`, fsyncs the claim and directories, and never overwrites or removes it; and
8. returns a typed verified authority object that the runner must present unchanged to execution.

The typed verified authority object owns the held operation-input and backend descriptors through subprocess completion. Terraform receives descriptor paths—not re-openable private pathnames—using `terraform apply /dev/fd/<saved-plan-fd>` and `terraform init ... -backend-config=/dev/fd/<backend-fd>` with only those exact descriptors inherited through `pass_fds`. Immediately before launch, the runner rechecks descriptor identity, mode, owner, link count, size, offset, and digest; it closes the descriptors only after the child exits. Replacement or rename of the original pathname therefore cannot change the bytes Terraform executes. Equivalent descriptor-bound handling applies to any collector/private operation input.

The runner does not accept raw policy plus caller-supplied digest as authority. Caller paths merely locate candidate artifacts; only the signed envelope, fixed signer identity, exact digest graph, bound replay-root fingerprint, held descriptors, and durable one-use claim admit execution. A failure after claim consumption requires a newly reviewed and newly signed approval.

Each trust domain remains separate. A FinOps approval cannot authorize workload state removal; a workload approval cannot authorize billing collection/import/plan/apply; a receipt signature cannot authorize a transaction; and an approval signature cannot substitute for the final FinOps budget receipt.

### 5. Complete the related command and filesystem hardening in revised PR A

The revised implementation must also:

- dispatch the dedicated collector by repository-relative absolute script path, never ambient `PATH` resolution;
- exact-match state readback, import, backend init, plan, and apply argv;
- bind apply to the exact signed saved-plan digest and init to the exact signed backend artifact;
- verify both human and provisioner process-memory token identity before command execution;
- attempt every pre-authorized mandatory finally readback while retaining the first failure;
- open each command output once with `O_NOFOLLOW`, validate and parse/hash the held descriptor bytes, and never reopen by pathname;
- pass held envelope/bundle descriptors to Cosign rather than reconstructed pathnames;
- retain descriptor-relative, owner-only, inode-revalidated receipt publication and verifier-owned receipt replay consumption; and
- keep the signer workflows, static policy, and authority manifest exact and non-interchangeable.

### 6. Keep every operational gate closed

This planning amendment authorizes no workflow dispatch, GitHub environment creation, cloud authentication, IAM/bucket creation, backend initialization, state read/write, import/removal, Terraform plan/apply, budget mutation, database/Secret operation, migration, service activation, tester access, qualification, live data, or production action.

Revised PR A adds exact enforcing boundaries for all four domains: `run_finops_operator_packet.py`, `run_workload_state_packet.py`, new `run_bootstrap_operator_packet.py` for B1, and new `run_workload_plan_packet.py` for M1. Each accepts only its domain/operation map and the typed verified authority object. B1 plan, apply, and readback are separate signed transactions; M1 is one signed `workload-plan/migration_plan` transaction that consumes the independently signed FinOps budget receipt before workload token acquisition. No generic runner or cross-domain operation is admitted.

After amendment merge and revised PR A merge, **Gate E0** separately configures and reads back the `finops-approval` GitHub environment before any signer dispatch. The exact source-controlled runbook requires protected-branch-only deployment policy, no custom branch/tag policy, no environment secrets or variables, no admin bypass where the API supports that setting, the exact private owner reviewer configuration, and truthful `prevent_self_review = false` under the sole-maintainer residual. E0 requires its own one-use approval; mismatch or unavailable readback stops. Source merge does not create or configure the environment.

Every signing/operational transaction remains a later separate explicit gate. No historical envelope, bundle, policy, nonce, token, plan, receipt, or approval may be reused.

## Consequences and constraints

### Positive

- Converts a self-asserted local digest into cryptographically authenticated, schema-bound, one-use workflow authority.
- Keeps private paths and infrastructure values outside GitHub while letting the signer see only digests and safe metadata.
- Makes policy/manifest/plan/backend substitution detectable before credentials or commands.
- Preserves distinct approval, execution, and final-receipt trust domains.

### Costs and risks

- Adds another protected workflow, Sigstore identity, environment gate, envelope schema, verifier, replay ledger, and failure-recovery path.
- Requires an online GitHub/Sigstore approval ceremony before each domain transaction.
- A consumed approval remains consumed after downstream failure, increasing ceremony cost but avoiding ambiguous reuse.
- The sole maintainer still controls repository and environment policy. This amendment narrows unsigned local forgery but does not claim independent-human separation or close the accepted same-repository-CI High.

### Hard constraints

- No caller-supplied boolean, unsigned JSON, matching local artifact/digest pair, receipt signature, or workflow-success flag is transaction authority.
- Approval and receipt workflows use different filenames, schemas, identities, tests, static contracts, artifacts, and replay ledgers.
- Signer workflows receive no private artifact and no GCP/secret authority.
- Private identifiers, paths, state, plans, receipts, tokens, and raw evidence remain outside Git and ordinary chat.
- Revised PR A remains source/local-validation only and preserves `infra/gcp/develop/budgets.tf`, its dependencies, and billing inputs unchanged.

## Alternatives considered

### Retain the named human caller as approval authority

Rejected for this amendment. It would document the current behavior as a procedural residual but would not satisfy ADR-0015's claim that the runner validates and atomically consumes an approval claim distinct from arbitrary caller input.

### Use an OS-owned local approval store

Rejected as the primary contract. It introduces host-specific user/UID/provisioning assumptions, complicates portability and recovery, and still needs an authority that populates the store. Filesystem ownership remains a defense-in-depth requirement, not the cryptographic trust anchor.

### Reuse the FinOps budget receipt signer

Rejected. Transaction authorization and post-transfer budget evidence have different schemas, timing, replay meaning, and consumers. Sharing one workflow identity would make cross-purpose substitution harder to audit and easier to misconfigure.

### Commit approval digests to Git

Rejected. Per-operation approvals and private artifact relationships do not belong in ordinary source history, and a commit-based ceremony would couple operational authority to a new code publication cycle.

## Approval and revisit triggers

This ADR is accepted after independent architecture/security, workflow/static-policy, plan-executability, and final acceptance-transition review. It still requires protected merge, exact-tip rebaseline, and separate implementation authorization before revised PR A implementation authority resumes.

Revisit if the protected signer cannot remain value-safe and no-GCP, the exact approval envelope cannot bind all private artifacts without exposing them, descriptor-backed Sigstore verification is not portable across the approved runners, the replay-root fingerprint cannot be made stable and non-copyable, environment protection cannot enforce the intended ceremony, or a non-human/multi-party approval authority becomes required.
