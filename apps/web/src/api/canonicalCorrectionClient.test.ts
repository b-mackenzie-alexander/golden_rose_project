import { afterEach, expect, it, vi } from 'vitest';
import { correctCanonical, correctionPath, currentReview, reviewCanonical, validReview } from './canonicalCorrectionClient';
import type { FinalizationOutputs } from './intakeCanonicalContracts';
const id = '11111111-1111-4111-8111-111111111111', other = '22222222-2222-4222-8222-222222222222';
const ref = { id, version: 1, disposition: 'created' as const };
const outputs: FinalizationOutputs = { kind: 'worker', worker: ref, contact: ref, residence: ref, preferences: ref };
const employer: FinalizationOutputs = { kind: 'employer', employer: ref, contact: ref, contact_details: ref, worksite: ref, request: ref, business_address: ref };
const state = { review_version: 0, latest_review_id: null, status: 'unreviewed', dependencies: outputs };
const correction = { command_id: id, event_id: other, result_record_version: 2, target: { entity_type: 'worker', id, current_version: 2 } };
const reviewed = { command_id: id, review_id: other, result_record_version: 1, current: { ...state, review_version: 1, latest_review_id: other, status: 'current' } };
function reply(value: unknown, status = 200, headers: Record<string, string> = {}) {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': status === 201 ? '1' : '2', 'Idempotency-Replayed': 'false', ...headers } }));
  vi.stubGlobal('fetch', fetcher); return fetcher;
}
afterEach(() => vi.unstubAllGlobals());
it('binds correction result, original key, version and private transport', async () => {
  const fetcher = reply(correction);
  expect(await correctCanonical(`/workers/${id}/corrections`, id, { expected_version: 1 }, id)).toEqual({ ok: true, value: correction });
  expect(fetcher).toHaveBeenCalledWith(`/api/staff/v1/workers/${id}/corrections`, expect.objectContaining({ method: 'POST', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer', headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'Idempotency-Key': id } }));
});
it.each([401, 403, 404, 409, 422, 500])('classifies HTTP %i without trusting error values', async (status) => {
  reply({}, status);
  const failure = status >= 500 ? 'unknown' : status === 409 ? 'conflict' : status === 422 ? 'failed' : 'forbidden';
  expect(await correctCanonical('/workers/x/corrections', id, { expected_version: 1 }, id)).toEqual({ ok: false, failure });
  expect(await reviewCanonical(id, outputs, id, { expected_review_version: 0 })).toEqual({ ok: false, failure });
  expect((await currentReview(id, outputs)).ok).toBe(false);
});
it.each([
  null, { ...correction, command_id: other }, { ...correction, event_id: 'bad' },
  { ...correction, result_record_version: 3 }, { ...correction, extra: 'private' },
  { ...correction, target: { ...correction.target, id: other } },
  { ...correction, target: { ...correction.target, current_version: 1 } },
  { ...correction, target: { ...correction.target, entity_type: 'intake' } },
])('retains unknown outcome for malformed correction receipt', async (value) => {
  reply(value); expect(await correctCanonical('/workers/x/corrections', id, { expected_version: 1 }, id)).toEqual({ ok: false, failure: 'unknown' });
});
it('accepts current versions above original created versions, without changing IDs or disposition', () => {
  expect(validReview({ ...state, dependencies: { ...outputs, worker: { ...ref, version: 3 } } }, outputs)).toBe(true);
  for (const patch of [{ id: other }, { disposition: 'reused' }, { version: 0 }, { extra: 1 }]) expect(validReview({ ...state, dependencies: { ...outputs, worker: { ...ref, ...patch } } }, outputs)).toBe(false);
  expect(validReview({ ...state, review_version: 1 }, outputs)).toBe(false);
  expect(validReview({ ...state, latest_review_id: other }, outputs)).toBe(false);
  expect(validReview({ ...state, dependencies: { ...employer, business_address: null } }, { ...employer, business_address: null })).toBe(true);
});
it('reads current review and accepts only coherent fresh/replayed review receipts', async () => {
  reply(state); expect(await currentReview(id, outputs)).toEqual({ ok: true, value: state });
  reply(reviewed, 201); expect(await reviewCanonical(id, outputs, id, { expected_review_version: 0 })).toEqual({ ok: true, value: reviewed.current });
  reply(reviewed, 200, { 'Idempotency-Result-Version': '1', 'Idempotency-Replayed': 'true' });
  expect((await reviewCanonical(id, outputs, id, { expected_review_version: 0 })).ok).toBe(true);
  reply(reviewed, 200, { 'Idempotency-Result-Version': '1', 'Idempotency-Replayed': 'false' });
  expect((await reviewCanonical(id, outputs, id, { expected_review_version: 0 })).ok).toBe(false);
});
it('fails closed on network, malformed JSON and wrong content types', async () => {
  for (const fetcher of [vi.fn().mockRejectedValue(new Error('offline')), vi.fn().mockResolvedValue(new Response('broken', { headers: { 'Content-Type': 'application/json' } })), vi.fn().mockResolvedValue(new Response('{}'))]) {
    vi.stubGlobal('fetch', fetcher); expect((await correctCanonical('/workers/x/corrections', id, {}, id)).ok).toBe(false);
    expect((await reviewCanonical(id, outputs, id, {})).ok).toBe(false);
    expect((await currentReview(id, outputs)).ok).toBe(false);
  }
});
it('uses only the nine explicit correction sections', () => {
  for (const name of ['worker', 'contact', 'residence', 'preferences']) expect(correctionPath(outputs, name, false)).toContain('/corrections');
  for (const [name, address] of [['contact_details', false], ['contact_details', true], ['business_address', false], ['worksite', true], ['request', false]] as const) expect(correctionPath(employer, name, address)).toContain('/corrections');
  expect(correctionPath(outputs, 'employer', false)).toBeNull(); expect(correctionPath(employer, 'employer', false)).toBeNull();
  expect(correctionPath(employer, 'worksite', false)).toBeNull();
  expect(correctionPath({ ...employer, business_address: null }, 'business_address', false)).toBeNull();
});
