# GCP deployment evidence template

Status: [passed|failed]
Mode: [read-only|qualification]
Date: [YYYY-MM-DD]
Operator: [REDACTED]
Project: [REDACTED]
Region: us-east4

## Expected operator-held inputs
- State bucket name: [REDACTED]
- Private invoker principal: [REDACTED]
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
- Qualification must use approved authenticated private access only.
- The approved and unapproved tokens use separate non-argv handoffs; tracked evidence records only bounded outcomes, never token values.
- The authenticated-but-unapproved denial probe requires cryptographic verification of the actual valid Google identity token (issuer, exact service audience, subject, issued-at/expiry/not-before claims) plus a fresh IAM Policy Troubleshooter `NOT_GRANTED` result for that verified subject, exact Cloud Run service resource, and `run.routes.invoke`; this proves the subject has no direct, inherited, group/domain, public, or broad invocation path; operator-authored JSON assertions are not evidence.
- `/health` and `/readiness` remain non-mutating probes and are not substitutes for bounded workflow qualification.
- Qualification uses newly generated fictional values only.
- Every exercised response row, including safe generated `404`, cursor `422`, stale `412`, and changed-key `409` controls, must preserve `Cache-Control: no-store`; controlled error outcomes that are unavailable, authorization-related, or otherwise unsafe to induce remain source-controlled static contract evidence.
- Evidence must not include submitted names, UUIDs, command IDs, cursors, raw bodies, DSNs, tokens, or exception payloads.
- Cleanup must state teardown/rebuild disposition without inventing product delete semantics.
- See `deploy/gcp/qualification-status-contract.md` for the exact final status vocabulary and overclaim boundaries.
- See `deploy/gcp/human-qualification-checklist.md` and `deploy/gcp/human-feedback-template.md` for the separate manual and structured feedback gates.

## Image provenance posture
- Deploy evidence must bind to one immutable `sha256:` image digest; tags alone are not acceptable proof.
- Record whether signature, provenance, image SBOM, and application SBOM attestation verification all matched the exact reviewed digest.
- Record the reviewed GitHub Actions certificate identity and OIDC issuer without copying raw certificate bundles or Rekor payloads.
- Do not claim publication or attestation verification occurred unless the reviewed workflow emitted those exact evidence artifacts.

## Foundation checks
- Stage mode is recorded as foundation, migration, or service and the expected workload absence/presence is evaluated accordingly.
- Project labels and inventory match the reviewed develop posture.
- Only approved APIs are enabled.
- Budget evidence preserves raw notification-channel resource names and compares them separately from human display names.
- Cloud Run invoker access remains private and named only when a later stage brings the service into scope.
- Authenticated `/readiness` uptime evidence exists only in service and uses the reviewed monitoring service-agent path.
- In `foundation`, Cloud SQL is absent and out of scope for the reviewed lower-layer contract.
- In `migration` and `service`, Cloud SQL remains private-path only.
- No service-account keys exist.
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

Do not replace the explicit `not_run`, `not_evidenced`, or `not_triaged` states with passing language unless the later separately approved human/tester/accessibility/language/feedback gate actually produced value-safe evidence.

## Value-safety notes
- Redact project IDs, principals, emails, URLs, tokens, exception payloads, and raw policy blobs.
- Keep only minimized evidence needed to prove pass/fail posture.
