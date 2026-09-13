# Rollback and forward-recovery runbook

This runbook defines how the private fictional-synthetic `develop` deployment decides between rollback and forward recovery after a failed migration, failed rollout, or failed bounded qualification. V28 completed the first deployment; this remains executable guidance only after a separate recovery/deployment approval and does not authorize cloud actions from source.

Current status: protected `develop@3414818b44d5e790f2d11c7fe4d7a48ebeb6241e` is running, automated qualification passed, and formal status is `not_qualified` due to the Spanish-toggle defect and open manual rows—not a migration/service failure requiring rollback. The v28 packet is consumed. Any recovery mutation remains separately approved; ordinary Wave 1 source remediation proceeds against the existing service without invoking this runbook.

## Scope

- first private fictional-synthetic `develop` deployment and later reviewed repeats
- migration failure handling
- schema/image compatibility matrix
- rollback versus forward recovery decision
- backup/restore or rebuild evidence requirements
- no untested RTO/RPO claims

## Core rule

Choose rollback only when the reviewed schema/image compatibility matrix proves the prior digest can safely run against the post-migration database state. Otherwise use forward recovery or teardown/rebuild. Never improvise a rollback because it feels faster.

Deployment-readiness success is not Gate 6 qualification success. Treat deploy-result evidence as deployment/readiness evidence only unless the separate bounded qualification workflow explicitly ran and recorded `qualification_executed=true`.

## Preconditions

Before any later approved deployment or recovery action:

1. The exact image digest, migration evidence, and reviewed database state are identified.
2. The migration lock behavior is understood for the current failure.
3. The private operator-held secret custody record is current.
4. The latest foundation-verification and bounded qualification evidence is available.
5. Any backup/restore evidence that exists is identified as tested or untested with no inflation of confidence.

## Schema/image compatibility matrix

Classify the failure into one of these reviewed buckets before acting:

| Situation | Prior digest safe? | Preferred action |
| --- | --- | --- |
| No migration executed; rollout failed before service change | yes | rollback to prior digest or re-run reviewed rollout |
| Migration attempted but did not commit changes | usually yes after confirming lock release and unchanged schema state | rollback or rerun reviewed migration |
| Migration committed additive/backward-compatible changes and prior digest is explicitly known to tolerate them | maybe | rollback only if compatibility was reviewed; otherwise forward recovery |
| Migration committed non-backward-compatible changes or compatibility is unknown | no | forward recovery or teardown/rebuild |
| Secret or invoker exposure occurred during the same window | not by itself | rotate/restrict first, then re-evaluate rollout state |

If the exact state does not match one of these reviewed buckets, stop and prefer forward recovery over speculative rollback.

## Migration lock and failure handling

- Treat the PostgreSQL advisory lock as the authoritative serialization boundary.
- If migration failed because the lock was held, do not force concurrent retry paths; wait for the owning run to resolve or terminate through the later approved operational path.
- If migration exited unsuccessfully, determine whether the failure occurred before schema change, during schema change, or after schema change but before service rollout.
- Record only value-safe evidence in tracked notes; detailed operator findings stay in the private incident/recovery record.
- Do not let the web service start while migration state is unknown.

## Rollback procedure

Use rollback only when the reviewed schema/image compatibility matrix says the prior digest is safe.

1. Confirm the prior digest is the exact last known-good reviewed artifact.
2. Confirm secret versions and private invoker posture still match the intended rollback surface.
3. Confirm no incompatible schema change committed, or that explicit compatibility evidence exists.
4. Roll back only the service image reference; do not silently widen into unrelated IAM, secret, or network changes.
5. Re-run bounded qualification after rollback and capture value-safe evidence.
6. If rollback does not restore a healthy qualified state immediately, stop and switch to forward recovery or teardown/rebuild rather than looping.

## Forward recovery procedure

Use forward recovery when rollback is unsafe, unreviewed, or already failed.

1. Identify the smallest reviewed change that restores compatibility or service health.
2. Preserve the migration serialization boundary; no concurrent migration attempts.
3. Apply only the reviewed forward fix at the later approved operational gate.
4. Re-run health/readiness and bounded qualification.
5. If forward recovery would require unreviewed secrets, schema changes, or public access exceptions, stop and prefer teardown/rebuild.

## Backup/restore or rebuild evidence requirements

- If backup/restore has been tested and separately evidenced, cite that evidence explicitly.
- If backup/restore has not been tested, say so plainly and do not invent restore confidence.
- Untested RTO/RPO remains unknown; this runbook must not claim a recovery objective just because backups exist.
- If backup/restore confidence is missing and the environment is still fictional-synthetic-only, teardown/rebuild may be the safer reviewed path.

## Decision checklist

Before ending the incident window, confirm:

- rollback or forward recovery choice matched the reviewed compatibility matrix
- migration lock/failure handling stayed serialized
- secrets and tester access were re-verified if touched
- bounded qualification reran after the chosen recovery path
- tracked evidence stayed value-safe

## Stop conditions

Stop and escalate to teardown/rebuild if:

- schema state is uncertain
- compatibility between current schema and any candidate digest is not reviewed
- a secret exposure or public invoker exposure is still unresolved
- repeated rollback or forward recovery attempts are drifting beyond the reviewed change window
