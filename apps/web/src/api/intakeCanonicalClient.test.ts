import { afterEach, expect, it, vi } from 'vitest';
import { getCanonicalIntake, getIntake, saveCanonicalIntake, saveIntake } from './intakeClient';
import type { Command } from '../intakes/saveState';

const id = '11111111-1111-4111-8111-111111111111';
const key = '22222222-2222-4222-8222-222222222222';
const ref = { id, version: 1 };
const output = { ...ref, disposition: 'reused' };
const outputs = { kind: 'worker', worker: output, contact: output, residence: output, preferences: output };
const detail = {
  summary: { intake_id: id, kind: 'worker', version: 4, lifecycle: 'finalized', complete: true,
    missing_fields: [], review_status: 'current', updated_at: '2026-09-15T12:00:00Z' },
  content_version: 2, candidate: { full_name: 'Fictional candidate' },
  resolved: { full_name: 'Fictional canonical' },
  links: { worker: ref, worker_contact: ref, worker_residence: ref, worker_preferences: ref },
  dependency_stale: false, finalization: outputs,
};
function response(value: unknown, status = 200, headers: Record<string, string> = {}) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(value), {
    status, headers: { 'Content-Type': 'application/json', ...headers },
  })));
}
const command = { key, path: `/intakes/${id}/finalizations`, generation: 0,
  body: { expected_version: 3, review_id: id } };
const receipt = { command_id: key, result_record_version: 4, current: detail, finalization: outputs };
const headers = { 'Idempotency-Replayed': 'false', 'Idempotency-Result-Version': '4' };
afterEach(() => vi.unstubAllGlobals());

it('reads finalized records only through the new explicit reader', async () => {
  response(detail);
  expect((await getCanonicalIntake(id)).ok).toBe(true);
  expect((await getIntake(id)).ok).toBe(false);
});

it.each(['worker', 'employer'] as const)('validates %s original finalization outputs', async (kind) => {
  const employer = { kind: 'employer', employer: output, contact: output, contact_details: output,
    worksite: output, request: { ...ref, disposition: 'created' }, business_address: null };
  const current = kind === 'worker' ? detail : { ...detail,
    summary: { ...detail.summary, kind }, candidate: { display_name: 'Candidate' },
    resolved: { display_name: 'Canonical', employer_type: 'household' }, links: { employer: ref },
    finalization: employer };
  response({ ...receipt, current, finalization: current.finalization }, 201, headers);
  expect((await saveCanonicalIntake(command)).ok).toBe(true);
  expect(fetch).toHaveBeenCalledWith(`/api/staff/v1/intakes/${id}/finalizations`, expect.objectContaining({
    body: JSON.stringify(command.body), cache: 'no-store', credentials: 'same-origin',
    redirect: 'error', referrerPolicy: 'no-referrer',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': key },
  }));
});

it('retains exact retry identity after an unknown outcome and accepts later current version', async () => {
  response({}, 503);
  expect(await saveCanonicalIntake(command)).toEqual({ ok: false, failure: 'unknown' });
  response({ ...receipt, current: { ...detail, summary: { ...detail.summary, version: 5 } } }, 200,
    { ...headers, 'Idempotency-Replayed': 'true' });
  expect((await saveCanonicalIntake(command)).ok).toBe(true);
  expect(fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({
    body: JSON.stringify(command.body),
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': key },
  }));
});

it.each([
  { resolved: { line1: 'Private address' } },
  { links: { worker: ref } },
  { links: { ...detail.links, worker: { ...ref, version: true } } },
  { links: { ...detail.links, worker: { ...ref, line1: 'Private' } } },
  { finalization: undefined },
  { finalization: { ...outputs, contact: { ...output, disposition: 'created' } } },
  { finalization: { ...outputs, worker: { ...output, version: 2147483648 } } },
  { finalization: { ...outputs, private: 'address' } },
  { private_address: 'Private' },
])('rejects malformed or sensitive current detail %#', async (patch) => {
  response({ ...detail, ...patch });
  expect(await getCanonicalIntake(id)).toEqual({ ok: false, failure: 'failed' });
});

it.each([
  { finalization: { ...outputs, worker: { ...output, id: key } } },
  { current: { ...detail, summary: { ...detail.summary, intake_id: key } } },
  { command_id: id },
  { finalization: undefined },
])('treats an inconsistent finalization receipt as unknown %#', async (patch) => {
  response({ ...receipt, ...patch }, 200, headers);
  expect(await saveCanonicalIntake(command)).toEqual({ ok: false, failure: 'unknown' });
});

it.each([
  [200, 'false', 4], [201, 'true', 4], [201, 'false', 3],
] as const)('rejects incorrect status/replay/result combinations %s %s %s', async (status, replay, version) => {
  response({ ...receipt, result_record_version: version }, status,
    { 'Idempotency-Replayed': replay, 'Idempotency-Result-Version': String(version) });
  expect(await saveCanonicalIntake(command)).toEqual({ ok: false, failure: 'unknown' });
});

it.each([403, 409])('preserves authorization/conflict outcomes %s', async (status) => {
  response({}, status);
  expect(await saveCanonicalIntake(command)).toEqual({ ok: false,
    failure: status === 403 ? 'forbidden' : 'conflict' });
});

it('keeps an unchanged link selection recoverable without a false version conflict', async () => {
  response({ type: 'urn:golden-rose:intake:no_change', status: 409, code: 'no_change' }, 409,
    { 'Content-Type': 'application/problem+json' });
  expect(await saveCanonicalIntake({ ...command, path: `/intakes/${id}/links`,
    body: { expected_version: 3, party: null } })).toEqual({ ok: false, failure: 'failed' });
});

it('accepts link replay after finalization without requiring historical output echo', async () => {
  response({ command_id: key, result_record_version: 2, current: detail }, 200,
    { 'Idempotency-Replayed': 'true', 'Idempotency-Result-Version': '2' });
  expect((await saveCanonicalIntake({ ...command, path: `/intakes/${id}/links`,
    body: { expected_version: 1, party: ref } })).ok).toBe(true);
});

it.each([
  { path: '/intakes' }, { path: `/intakes/${id}/revisions` },
  { body: { expected_version: true, review_id: id } },
  { body: { expected_version: 3, review_id: id, phone: 'Private' } },
  { key: 'bad' },
] as Partial<Command>[])('rejects invalid command before fetching %#', async (patch) => {
  response(receipt, 200, headers);
  // Exercise untrusted runtime inputs beyond compile-time command types.
  expect(await saveCanonicalIntake({ ...command, ...patch })).toEqual({ ok: false, failure: 'failed' });
  expect(fetch).not.toHaveBeenCalled();
});


it.each(['', '/revisions', '/addresses/worker_residence/revisions', '/reviews', '/follow-ups'])(
  'resolves original legacy %s receipt with strictly validated finalized current detail', async (suffix) => {
    const original = { ...command, path: suffix ? `/intakes/${id}${suffix}` : '/intakes' };
    response({ command_id: key, result_record_version: 2, current: detail }, 200,
      { 'Idempotency-Replayed': 'true', 'Idempotency-Result-Version': '2' });
    expect((await saveIntake(original)).ok).toBe(true);
    response({ command_id: key, result_record_version: 2, current: { ...detail, finalization: undefined } },
      200, { 'Idempotency-Replayed': 'true', 'Idempotency-Result-Version': '2' });
    expect(await saveIntake(original)).toEqual({ ok: false, failure: 'unknown' });
  });
