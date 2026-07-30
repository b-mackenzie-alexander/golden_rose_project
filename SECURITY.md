# Security — Golden Rose Operations Platform

**Status:** Planning baseline. This document records security posture and open controls; it does not claim production compliance or completed implementation.

## Security objectives
- Protect worker, employer, household/worksite, document, and operational data using least privilege and data minimization.
- Preserve attributable, reviewable operational history without making originals silently editable.
- Keep public workflow traffic materially separate from higher-trust agency administration.
- Make security controls testable before real data or production use.

## Trust boundaries
1. **Public plane:** eventual worker/employer browser/API flows. Public accounts never gain staff access by role selection or token reuse.
2. **Staff plane:** agency-member administration, operational search, data entry, review, and reporting. Requires separate identity client/session/token audience, endpoints, credentials, authorization checks, MFA, and account lifecycle.
3. **Controlled crossing:** narrow, authorized, audited staff actions on public-workflow records.
4. **Data stores:** transactional records, documents, logs, backups, exports, and secrets have distinct access and retention controls.

## Baseline controls required before live data
- Server-enforced, role/record/field authorization; no UI-only authorization.
- Staff MFA, least-privilege roles, attributable privileged actions, controlled access recovery, and prompt deprovisioning.
- TLS/HTTPS in transit; encryption at rest; secrets outside source code and client-facing builds.
- Separate development/test and production accounts, databases, buckets, identity clients, and credentials.
- Structured application audit events separated from operational logs; redact secrets and unnecessary personal data from logs.
- Backup/restore evidence, forward-recovery plans, and incident/support ownership.
- Dependency, secret, static-analysis, migration, authorization, and deployment review gates in CI/CD.

## Data-protection rules
- Treat precise household/worksite address, proximity, household composition, worker contact data, résumés, and free-text notes as sensitive operational data.
- Use least-precise location for routine worker-facing/public views; disclose precise location only in approved need-to-know workflows.
- Do not make protected traits, nationality/religion/community labels, language inference, disability/health proxies, caregiving preferences, or legacy free-text requirements default filters, comparison signals, or decisions.
- Employer assertions about conditions, pay, safety, language, physical demands, transportation, and supervision require agency review; they do not automatically become worker-facing facts.
- Treat all legal text, consents, notices, communication preferences, retention rules, and fee/payment behavior as versioned, approved content—not hardcoded form copy.

## Document ingestion: blocked until qualified
If worker résumé upload is approved, the system must establish:
- authenticated/authorized initiation;
- strict PDF-first allowlisting, signature/content validation, bounded sizes, and rate limits;
- isolated, non-executable private quarantine storage;
- malware scanning before release to staff or downstream processing;
- safe preview/download behavior and authorization checks;
- audit events, failure/retry process, retention/deletion, and user-visible outcomes.

Unscanned/rejected artifacts must not be served, rendered, indexed, or available to staff/public users.

## Security workflow
1. Classify the observation as Observed, Reported, Proposed, or Validated.
2. Record risk, affected boundary/data, owner, mitigation, evidence, and approval state.
3. Treat High/Blocker security findings as release blockers until resolved or explicitly accepted by the authorized owner.
4. Require security review escalation for auth, public/staff boundaries, data access, documents, payments, exports, logging/audit, dependencies, infrastructure, and database migrations.
5. Record correction/exception paths; do not erase operational history to correct it.

## Current open security decisions
- Staff role/permission matrix, MFA provider, recovery, and support/incident owners.
- Production data classification, retention/deletion/export rules, and migration governance.
- Identity, messaging, signature, payment, screening, and other vendor selection/data processing.
- Backup RTO/RPO, test cadence, key-management details, security-edge/WAF needs, and monitoring/alert ownership.
- Upload scope and secure-ingestion implementation acceptance criteria.

## Incident handling baseline
Do not improvise with client records. Preserve minimum necessary evidence, protect access, notify the designated client/security owner through the approved path, assess containment and recovery, and document attributable remediation. Formal incident notification obligations require approved legal/business policy.
