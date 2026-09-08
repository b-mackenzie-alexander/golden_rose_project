# Signed FinOps Approval Authority Planning Review Handoff

**Status:** ACCEPTED and CLEAN; uncommitted planning-only publication handoff with exact stage/commit/final-range verification/push/PR/readback/CI authority approved
**Base:** protected `develop@c933bfc934d2f61e4c08e077e92cc82af7e017dc`
**Branch:** `docs/finops-approval-authority-amendment`
**Separate paused implementation:** `/Users/genie/Desktop/golden_rose_project` on `feat/finops-budget-ownership-foundation`; preserved dirty and unpublished as evidence only

## Trigger

ADR-0015 Implementation PR A review proved a material trust-boundary defect: local runners could receive both a policy or approval artifact and the caller's matching digest. Byte recomputation detects drift but cannot prove a separate protected approval ceremony authorized those bytes. Beatrice selected a separately protected, cryptographically signed, one-use approval envelope and explicitly paused PR A for replanning.

The completed Terraform/static rereview was `CLEAN`. Architecture/security remained `CHANGES_REQUIRED` until approval authority has an independent cryptographic trust anchor. Bounded collector-path, exact-plan/backend, descriptor-backed Cosign, and output-open defects are carried into revised implementation TDD; they are not implemented in this planning worktree.

## Accepted decision awaiting protected publication

ADR-0016 and its paired plan require:

- a separate `.github/workflows/sign-finops-approval.yml` identity, distinct from receipt signing;
- direct value-safe envelope bytes plus SHA-256 only, protected `develop` source binding, a separately governed `finops-approval` environment, keyless Sigstore, immutable actions, and no GCP/secret/repository-write authority;
- an exact envelope binding source SHA, domain/operation, policy, complete manifest, source, operation input/saved plan, backend, private approval record, claim-root fingerprint, expiry, and one-use nonce by digest;
- a credential-free verifier that authenticates the signer and every private artifact through held descriptors before token access, then atomically consumes the approval under verifier-owned `flock`/`O_CREAT|O_EXCL`;
- strict separation among FinOps, workload-state, bootstrap, and workload-plan approvals plus final FinOps budget receipts;
- revised PR A TDD for unsigned/self-authored rejection, replay/root binding, exact plan/backend/collector commands, output/Cosign descriptors, workflow/static contracts, and no-cloud closeout; and
- truthful retention of ADR-0011/ADR-0012's same-repository sole-maintainer High instead of claiming independent-human separation.

## Pre-acceptance technical-review hashes

- `docs/adr/ADR-0016-signed-finops-approval-authority.md`: `eb2ca30b409d01895b62191e7a7812bb5a0f0e6969ee8259265c4357cc03315c`
- `.hermes/plans/2026-09-07_signed-finops-approval-authority-amendment-plan.md`: `833946a314a523b16aa301fb9ad7c513f2cbefbb5b23ba8de377043bc932d77a`
- `docs/planning/templates/sign-finops-approval.yml`: `6b18814f94c1f3fcac3097c02cc640d610e739ccc6d86d487a9f6a0a1340e6be`
- canonical stripped signer run body: `ecb7f5e5f038c929bf6240af807e198d09daaeef91d4780806cb72758cf71344`
- `docs/planning/finops-signed-approval-tdd-ledger.md`: `68e85c56a2cea12e3f55e6235649d0c41c3c0008cb1464c3693514c800bc5889`
- `docs/planning/finops-signed-approval-negative-fixture-ledger.md`: `da5e7b643a64990bda2cf94914c7505c77fee2b9e4b79b0f8c2ef13ff2f1b5d1`
- `docs/planning/finops-pr-a-replay-disposition.md`: `b58d7cc23effd605892ef012b3924808e3c966bd1da2190eb446362227f4519f`
- `deploy/github/finops-approval-environment-runbook.md`: `e8918513bf5edc98960c275ed7d57219c95164e780c41ee307d2e92f29ddd8c3`

These hashes identify the final independently CLEAN Proposed-state technical surface. The owner-acceptance transition changed only status, completed-gate, and publication-boundary wording in the hash-bound planning artifacts.

## Accepted publication hashes

- `docs/adr/ADR-0016-signed-finops-approval-authority.md`: `87dc8e27150ae2f9adaa9df3a5a067b9864bc3fec9abd59385740e929aa4a592`
- `.hermes/plans/2026-09-07_signed-finops-approval-authority-amendment-plan.md`: `f0f7e22c71df062a46173948d31e95cb03656225ead6b71283dfb8cde6109703`
- `docs/planning/templates/sign-finops-approval.yml`: `6b18814f94c1f3fcac3097c02cc640d610e739ccc6d86d487a9f6a0a1340e6be`
- canonical stripped signer run body: `ecb7f5e5f038c929bf6240af807e198d09daaeef91d4780806cb72758cf71344`
- `docs/planning/finops-signed-approval-tdd-ledger.md`: `f28fcbdcce32f620ecd8d988b6eb3a46271ae30305156f26070a00b8fe1418ac`
- `docs/planning/finops-signed-approval-negative-fixture-ledger.md`: `6a4855a8d3ac1c822fdcbf6f823d7dde169ce465fd54adf09e8a1f6c680c8e4b`
- `docs/planning/finops-pr-a-replay-disposition.md`: `a2e2ede36edb29017a1fe88b6d024de11c1d238eafa6856cb23fca161d6a169a`
- `deploy/github/finops-approval-environment-runbook.md`: `8bc4335ef33e79ce134d29aacbbc31a8b05f783297b7ac7dd31ffdcfdc171764`

The accepted hashes are the publication controls. Any later substantive technical change requires renewed technical review; publication-status updates after commit/PR must remain bounded and separately verified.

## Exact planning surface

The remediated review surface is 23 paths:

- `.hermes/plans/2026-09-07_finops-budget-ownership-separation-plan.md`
- `.hermes/plans/2026-09-07_signed-finops-approval-authority-amendment-plan.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `CURRENT_WORK.md`
- `README.md`
- `NOTES.md`
- `ROADMAP.md`
- `SECURITY.md`
- `TECHNICAL_REQUIREMENTS.md`
- `TECHNOLOGY_DECISIONS.md`
- `docs/adr/ADR-0015-finops-budget-ownership-separation.md`
- `docs/adr/ADR-0016-signed-finops-approval-authority.md`
- `docs/adr/README.md`
- `deploy/gcp/bootstrap-state-runbook.md`
- `deploy/gcp/staged-plan-approval.md`
- `deploy/github/finops-approval-environment-runbook.md`
- `docs/planning/finops-pr-a-replay-disposition.md`
- `docs/planning/finops-signed-approval-negative-fixture-ledger.md`
- `docs/planning/finops-signed-approval-tdd-ledger.md`
- `docs/planning/templates/sign-finops-approval.yml`
- `docs/review-handoffs/2026-09-07-signed-finops-approval-authority-plan-review-handoff.md`
- `infra/gcp/README.md`

No `scripts/`, `tests/`, `infra/gcp/`, or `.github/workflows/` implementation path is modified in this planning worktree.

## Initial review findings and remediation

Architecture/security returned `CLEAN`. Workflow/static-policy returned two High and two Medium findings; plan-executability/governance returned two Blocker, five High, and one Medium finding.

The remediated packet now:

- keeps verified saved-plan, backend, and operation-input descriptors alive through Terraform child completion and passes only `/dev/fd/<n>` with explicit `pass_fds`, with prelaunch replacement races in the exact TDD ledger;
- defines four enforcing domains and runners, including exact bootstrap B1 and workload-plan M1 boundaries;
- makes raw approval-envelope signature verification precede every private root/artifact open and adds a zero-private-open failure node;
- binds implementation to the byte-exact signer template and its complete/run-body hashes, with exact job/input/permission/step/action/artifact fields;
- defines the complete 14-string-field parser grammar, strict base64/JSON/digest/UUID/timestamp boundaries, four-domain operation map, and isolated rejection selectors;
- replaces horizontal cycle wording with 44 primary vertical selectors plus a 30-node isolated-negative ledger, each with its own RED/classification/minimal-GREEN contract, including explicit import and plan substitutions;
- adds exact manifest bidirectional equality plus separate exact test/template path inventories and authority-family escape fixtures;
- adds Gate E0's exact environment configuration/readback runbook and stop behavior;
- aligns `README.md`, `infra/gcp/README.md`, bootstrap and staged-plan runbooks to the PR A suspension;
- defines the exact final source/review/commit/final-HEAD/range/push/CI/merge/rebaseline order; and
- adds a 41-path REBUILD/REWRITE/DROP replay ledger, maps all 15 post-A3 remediation selectors, prohibits wholesale replay/historical evidence reuse, and names the fresh revised-PR-A handoff.

The first focused rereview closed most of the twelve original findings but found or retained four contract defects: contradictory two-domain wording, timestamp parsing without exact lexical round-trip enforcement, aggregate parser/authority-family RED nodes that could pass for the wrong reason, and four stale active-status claims. The remediated packet now uses the same exact four domains everywhere; the signer requires an exact timestamp regex and canonical round trip; a separate 30-node ledger isolates every parser/schema and signer-authority mutation before aggregate regressions; and the active status surfaces suspend original PR A consistently.

## Final independent rereview

- Workflow/static-policy rereview closed H1, H2, M1, and M2 with zero new Blocker, High, or Medium findings.
- Plan-executability/governance rereview closed all eight original findings. Its one new High identified two remaining two-runner summaries in `CURRENT_WORK.md` and `docs/adr/README.md`.
- Architecture/security delta rereview identified the same summaries as its sole Medium.
- Both summaries now explicitly name `finops`, `workload-state`, `bootstrap`, and `workload-plan`. Two independent final delta rereviews closed the High and Medium, with zero residual or new Blocker, High, or Medium findings.
- Final verdict across the required review lanes: **CLEAN**.

## Review lanes

### Architecture and security

Verify that the signed envelope—not caller-supplied matching artifacts/digests—is the executable trust anchor; signer identity and approval/receipt separation are exact; private values remain excluded; replay-root and one-use semantics are complete; signature/artifact verification precedes credentials; failure remains consumed; and the sole-maintainer residual is stated honestly.

### Workflow and static policy

Verify that the proposed signer can remain direct-input, value-safe, environment-protected, immutable, exact-source-bound, and no-GCP/no-secret; that static-policy nodes cover triggers, inputs, environment, permissions, step structure/order, action pins, run body, schema, and cross-signer substitution; and that no existing workflow/resource authority is silently widened by planning.

### Plan executability and governance

Verify that R1-R6 can execute from a fresh post-merge branch under strict TDD, exact proposed node names are coherent, paused-source replay is controlled, all files are named, planning/implementation/operational gates remain separate, and no step requires private values in Git or a cloud/state action during implementation.

## Local planning checks

- Worktree started clean from exact `origin/develop@c933bfc934d2f61e4c08e077e92cc82af7e017dc`.
- `git diff --check` passed on the remediated 23-file surface.
- Mechanical inventory matched exactly `23/23`; search found no implementation path in the planning diff.
- TDD/replay ledgers passed mechanical checks: 44 ordered primary selectors plus 30 ordered isolated negative selectors (`74` unique total), 41 unique paused paths, and 15 unique post-A3 selector dispositions.
- The normative signer template parses as YAML and its embedded Python compiles; its exact template and canonical run-body hashes match the plan.
- `env -u PYTHONPATH uv run python scripts/validate_terraform_static.py` passed.
- `env -u PYTHONPATH uv run pytest tests/unit/test_terraform_hygiene.py -q` passed (`299 passed`).
- Independent workflow/static-policy, plan-executability/governance, architecture/security, and final two-line delta rereviews are CLEAN with zero residual Blocker, High, or Medium findings.
- No commit, push, PR, signer/environment action, GCP authentication, backend/state operation, plan/apply, import/removal, or cloud mutation occurred.

## Current stop

The planning packet is accepted and CLEAN. The exact 23-file stage/commit/final-range verification/Gitleaks/push/PR-to-`develop`/remote-readback/CI sequence is approved. Merge remains separately withheld. Planning acceptance or publication does not authorize revised PR A implementation, signer/environment action, GCP authentication, backend/state access, plan/apply, import/removal, migration, or any downstream operation.
