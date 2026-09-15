import type { DraftObject, Result } from './intakeContracts';
import type { FinalizationOutputs } from './intakeCanonicalContracts';
import { canonicalId, canonicalVersion } from './intakeCanonicalContracts';

export type CorrectionResult = { command_id: string; event_id: string; result_record_version: number; target: { entity_type: string; id: string; current_version: number } };
export type CurrentReview = { review_version: number; latest_review_id: string | null; status: 'unreviewed' | 'current' | 'stale'; dependencies: DraftObject };
const obj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const exact = (v: Record<string, unknown>, keys: string[]) => Object.keys(v).length === keys.length && keys.every((key) => Object.hasOwn(v, key));
const fetchOptions = { cache: 'no-store', credentials: 'same-origin', mode: 'same-origin', redirect: 'error', referrerPolicy: 'no-referrer' } as const;
export function correctionPath(outputs: FinalizationOutputs, output: string, address: boolean): string | null {
  if (outputs.kind === 'worker') return ['worker', 'contact', 'residence', 'preferences'].includes(output)
    ? `/workers/${outputs.worker.id}${output === 'worker' ? '' : `/${output}`}/corrections` : null;
  const prefix = `/employers/${outputs.employer.id}`;
  if (output === 'contact_details') return `${prefix}/contacts/${outputs.contact.id}/details${address ? '/address' : ''}/corrections`;
  if (output === 'business_address' && outputs.business_address) return `${prefix}/addresses/${outputs.business_address.id}/corrections`;
  if (output === 'worksite' && address) return `${prefix}/worksites/${outputs.worksite.id}/address/corrections`;
  if (output === 'request') return `${prefix}/requests/${outputs.request.id}/corrections`;
  return null;
}
export async function correctCanonical(path: string, key: string, body: DraftObject, targetId: string): Promise<Result<CorrectionResult>> {
  const expectedEntity = path.startsWith('/workers/')
    ? path.includes('/contact/') ? 'worker_contact' : path.includes('/residence/') ? 'worker_residence' : path.includes('/preferences/') ? 'worker_preferences' : 'worker'
    : path.includes('/contacts/') ? 'employer_contact_details' : path.includes('/addresses/') ? 'employer_address' : path.includes('/worksites/') ? 'worksite' : 'staffing_request';
  try {
    const response = await fetch(`/api/staff/v1${path}`, { ...fetchOptions, method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'Idempotency-Key': key }, body: JSON.stringify(body) });
    if (response.status !== 200) { await response.body?.cancel(); return { ok: false, failure: response.status >= 500 ? 'unknown' : [401, 403, 404].includes(response.status) ? 'forbidden' : response.status === 409 ? 'conflict' : 'failed' }; }
    if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) return { ok: false, failure: 'unknown' };
    const value: unknown = await response.json();
    if (!obj(value) || !exact(value, ['command_id', 'event_id', 'result_record_version', 'target']) || value.command_id !== key || !canonicalId(value.event_id) || !canonicalVersion(value.result_record_version) || value.result_record_version !== Number(body.expected_version) + 1 || !obj(value.target) || !exact(value.target, ['entity_type', 'id', 'current_version']) || value.target.id !== targetId || !canonicalVersion(value.target.current_version) || value.target.current_version < value.result_record_version || value.target.entity_type !== expectedEntity || response.headers.get('Idempotency-Result-Version') !== String(value.result_record_version) || !['true', 'false'].includes(response.headers.get('Idempotency-Replayed') ?? '')) return { ok: false, failure: 'unknown' };
    return { ok: true, value: value as CorrectionResult };
  } catch { return { ok: false, failure: 'unknown' }; }
}
export function validReview(value: unknown, outputs: FinalizationOutputs): value is CurrentReview {
  if (!obj(value) || !exact(value, ['review_version', 'latest_review_id', 'status', 'dependencies']) || !Number.isInteger(value.review_version) || Number(value.review_version) < 0 || Number(value.review_version) > 2147483647 || !['unreviewed', 'current', 'stale'].includes(String(value.status)) || !obj(value.dependencies) || !exact(value.dependencies, Object.keys(outputs)) || value.dependencies.kind !== outputs.kind) return false;
  if (value.review_version === 0 ? value.latest_review_id !== null || value.status !== 'unreviewed' : !canonicalId(value.latest_review_id) || value.status === 'unreviewed') return false;
  return Object.entries(outputs).every(([name, original]) => {
    if (name === 'kind') return true;
    const ref = value.dependencies as Record<string, unknown>, current = ref[name];
    if (original === null) return current === null;
    return obj(original) && obj(current) && exact(current, ['id', 'version', 'disposition']) && current.id === original.id && current.disposition === original.disposition && canonicalVersion(current.version) && current.version >= original.version;
  });
}
export async function currentReview(intakeId: string, outputs: FinalizationOutputs): Promise<Result<CurrentReview>> {
  try {
    const response = await fetch(`/api/staff/v1/intake-finalizations/${intakeId}/current-review`, { ...fetchOptions, headers: { Accept: 'application/json' } });
    if (response.status !== 200) { await response.body?.cancel(); return { ok: false, failure: [401, 403, 404].includes(response.status) ? 'forbidden' : 'failed' }; }
    if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) return { ok: false, failure: 'failed' };
    const value: unknown = await response.json();
    return validReview(value, outputs) ? { ok: true, value } : { ok: false, failure: 'failed' };
  } catch { return { ok: false, failure: 'failed' }; }
}
export async function reviewCanonical(intakeId: string, outputs: FinalizationOutputs, key: string, body: DraftObject): Promise<Result<CurrentReview>> {
  try {
    const response = await fetch(`/api/staff/v1/intake-finalizations/${intakeId}/current-reviews`, { ...fetchOptions, method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'Idempotency-Key': key }, body: JSON.stringify(body) });
    if (![200, 201].includes(response.status)) { await response.body?.cancel(); return { ok: false, failure: response.status >= 500 ? 'unknown' : [401, 403, 404].includes(response.status) ? 'forbidden' : response.status === 409 ? 'conflict' : 'failed' }; }
    if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) return { ok: false, failure: 'unknown' };
    const value: unknown = await response.json();
    if (!obj(value) || !exact(value, ['command_id', 'review_id', 'result_record_version', 'current']) || value.command_id !== key || !canonicalId(value.review_id) || !canonicalVersion(value.result_record_version) || value.result_record_version !== Number(body.expected_review_version) + 1 || !validReview(value.current, outputs) || value.current.review_version < value.result_record_version || (value.current.review_version === value.result_record_version && value.current.latest_review_id !== value.review_id) || response.headers.get('Idempotency-Result-Version') !== String(value.result_record_version) || response.headers.get('Idempotency-Replayed') !== String(response.status === 200)) return { ok: false, failure: 'unknown' };
    return { ok: true, value: value.current };
  } catch { return { ok: false, failure: 'unknown' }; }
}
