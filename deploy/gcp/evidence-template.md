# GCP deployment evidence template

Status: [passed|failed]
Mode: [read-only|qualification]
Date: [YYYY-MM-DD]
Operator: [REDACTED]
Project: [REDACTED]
Region: us-east4

## Expected operator-held inputs
- State bucket name: [REDACTED]
- Demo-access expiry/readback: [REDACTED]
- Artifact Registry writer member: [REDACTED]
- Deployer principal: [REDACTED]
- Observability viewer principal: [REDACTED]
- Recovery policy review status: [REDACTED]
- Billing account: [REDACTED]

## Read-only command posture
- No mutation mode is approved in this task.
- No cloud apply, deploy, image push, secret injection, or IAM write occurs here.
- Any future mutation path requires separate approval and a separately reviewed tool/runbook.

## Qualification posture
- Qualification must prove the temporary shared Basic boundary before synthetic writes.
- Develop mutation evidence must show that ordinary name-shaped values receive the fixed no-store `422` before persistence and that accepted employer/contact values match the generated-fictional forms documented in the runbook.
- `/health` and `/readiness` must work without credentials and return only minimized no-store status.
- Missing credentials and deliberately wrong Basic credentials must produce the same empty no-store `401` and exact challenge without reaching business responses.
- Correct credentials must use one non-argv private handoff; tracked evidence records only bounded outcomes, never the username/password, Authorization header, expiry timestamp, or service URL.
- Qualification uses newly generated fictional values only.
- Server-side develop admission rejected plausible ordinary Employer/EmployerContact names before receipt, domain, or audit writes; the successful flow used only bounded generated-fictional patterns.
- Every exercised response row, including safe generated `404`, cursor `422`, stale `412`, and changed-key `409` controls, must preserve `Cache-Control: no-store`; controlled error outcomes that are unavailable, authorization-related, or otherwise unsafe to induce remain source-controlled static contract evidence.
- Evidence must not include submitted names, UUIDs, command IDs, cursors, raw bodies, DSNs, tokens, or exception payloads.
- Cleanup must state teardown/rebuild disposition without inventing product delete semantics.
- See `deploy/gcp/qualification-status-contract.md` for the exact final status vocabulary and overclaim boundaries.
- See `deploy/gcp/human-qualification-checklist.md` and `deploy/gcp/human-feedback-template.md` for the separate manual and structured feedback gates.

## Image provenance posture
- Deploy evidence must bind to one immutable `sha256:` image digest; tags alone are not acceptable proof.
- The live migration job and service must both match that packet digest; the migration job's sole-container image and reviewed command, identity, serialization, retry/timeout, VPC, label, and environment projection must pass immediately before execution.
- Record whether signature, provenance, image SBOM, and application SBOM attestation verification all matched the exact reviewed digest.
- Record the reviewed GitHub Actions certificate identity and OIDC issuer without copying raw certificate bundles or Rekor payloads.
- Do not claim publication or attestation verification occurred unless the reviewed workflow emitted those exact evidence artifacts.

## Foundation checks
- Stage mode is recorded as foundation, migration, or service and the expected workload absence/presence is evaluated accordingly.
- Project labels and inventory match the reviewed develop posture.
- Only approved APIs are enabled.
- Budget evidence preserves raw notification-channel resource names and compares them separately from human display names.
- Service-stage Cloud Run invocation is exactly `allUsers` → `roles/run.invoker`, admitted only with the expiring Basic gate, synthetic marker, zero-to-one scaling, and private Cloud SQL.
- Public `/readiness` uptime evidence exists only in service and uses no authentication header.
- In `foundation`, Cloud SQL is absent and out of scope for the reviewed lower-layer contract.
- In `migration` and `service`, Cloud SQL remains private-path only.
- No service-account keys exist.
- `goldenRoseProvisionerQuotaUser` has the exact Terraform description, only `serviceusage.services.use`, its sole binding is the workload provisioner, and no inherited broader quota authority exists.
- Project/service-account IAM matches the reviewed effective-authority contract.
- State bucket versioning/access/recovery posture is intact.
- Budget, alert route, and logging posture are present.
- Availability alerts are provisional develop review triggers, not SLOs or client commitments.

## Violations
- [REDACTED or none]

## Qualification result
- Employer create/read/search/revision/replay: [passed|failed]
- EmployerContact create/query/read: [passed|failed]
- manual_browser: [not_run|pass|fail]
- accessibility: [not_evidenced|pass|fail]
- fluent_language: [not_evidenced|pass|fail]
- tester_access: [not_evidenced|pass|fail]
- monitoring: [not_evidenced|pass|fail]
- recovery: [not_evidenced|pass|fail]
- feedback: [not_triaged|triaged]
- final_status: [qualified_private_develop_for_human_feedback|operational_private_develop_technical_feedback_only|not_qualified|torn_down_after_failed_activation]
- Cleanup/rebuild disposition: [REDACTED]
- Log scan: [passed|failed] with no credentials, Authorization headers, submitted fictional values, identifiers, DSNs, or raw response bodies retained
- Non-mutating teardown/rebuild readiness inspection: [passed|failed] without target destruction

Do not replace the explicit `not_run`, `not_evidenced`, or `not_triaged` states with passing language unless the later separately approved human/tester/accessibility/language/feedback gate actually produced value-safe evidence.

## Value-safety notes
- Redact project IDs, principals, emails, URLs, credentials, Authorization headers, expiry timestamps, exception payloads, and raw policy blobs.
- Keep only minimized evidence needed to prove pass/fail posture.
