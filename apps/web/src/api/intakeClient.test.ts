import { afterEach, describe, expect, it, vi } from 'vitest';
import { getIntake, getIntakeAddress, queryIntakes, saveIntake } from './intakeClient';
const id = 'bda61d25-4021-4d8a-9f5d-9b77ad6c351f';
const key = '22222222-2222-4222-8222-222222222222';
const detail = {
  summary: {
    intake_id: id,
    kind: 'worker',
    version: 2,
    lifecycle: 'draft',
    complete: false,
    missing_fields: ['phone'],
    review_status: 'unreviewed',
    updated_at: '2026-09-14T12:00:00Z',
  },
  content_version: 2,
  candidate: { full_name: 'Fictional' },
  resolved: {},
  links: {},
  dependency_stale: false,
};
const command = {
  key,
  path: '/intakes',
  body: { kind: 'worker', content: { full_name: 'Fictional' } },
  generation: 1,
};
function response(body: unknown, status = 200, headers: Record<string, string> = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json', ...headers },
      }),
    ),
  );
}
afterEach(() => vi.unstubAllGlobals());
describe('intake transport', () => {
  it('sends bounded shared query and exact detail with privacy options', async () => {
    response({ items: [detail.summary], next_cursor: null });
    expect((await queryIntakes('worker')).ok).toBe(true);
    expect(fetch).toHaveBeenCalledWith(
      '/api/staff/v1/intakes/query',
      expect.objectContaining({
        cache: 'no-store',
        mode: 'same-origin',
        credentials: 'same-origin',
        redirect: 'error',
        referrerPolicy: 'no-referrer',
        body: JSON.stringify({ kind: 'worker', lifecycle: 'draft', page_size: 25 }),
      }),
    );
    response(detail);
    expect((await getIntake(id)).ok).toBe(true);
    expect(await getIntake('not-an-id')).toEqual({ ok: false, failure: 'failed' });
  });
  it('validates restricted address reads', async () => {
    response({
      intake_id: id,
      version: 2,
      section: 'worker_residence',
      candidate: { line1: 'Fictional' },
      resolved: null,
    });
    expect((await getIntakeAddress(id, 'worker_residence')).ok).toBe(true);
    response({ intake_id: id, version: 2, section: 'worksite_address', candidate: null, resolved: null });
    expect((await getIntakeAddress(id, 'worker_residence')).ok).toBe(false);
  });
  it('accepts exact command receipt and replay current version', async () => {
    for (const replay of ['true', 'false']) {
      response({ command_id: key, result_record_version: 2, current: detail }, 200, {
        'Idempotency-Replayed': replay,
        'Idempotency-Result-Version': '2',
      });
      expect((await saveIntake(command)).ok).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        '/api/staff/v1/intakes',
        expect.objectContaining({
          headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'Idempotency-Key': key },
          body: JSON.stringify(command.body),
        }),
      );
    }
  });
  it.each([400, 404, 413, 422])('classifies %s as a known rejection', async (status) => {
    response({}, status);
    expect(await saveIntake(command)).toEqual({ ok: false, failure: 'failed' });
  });
  it.each([
    [403, 'forbidden'],
    [409, 'conflict'],
    [503, 'unknown'],
    [500, 'unknown'],
  ] as const)('classifies %s safely', async (status, failure) => {
    response({}, status);
    expect(await saveIntake(command)).toEqual({ ok: false, failure });
  });
  it('treats transport, malformed receipt and truncated JSON as unknown', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('private response never displayed')));
    expect(await saveIntake(command)).toEqual({ ok: false, failure: 'unknown' });
    expect(await getIntake(id)).toEqual({ ok: false, failure: 'failed' });
    response({ command_id: key, result_record_version: 2, current: detail });
    expect((await saveIntake(command)).ok).toBe(false);
    response({ command_id: 'wrong', result_record_version: 2, current: detail }, 201, {
      'Idempotency-Replayed': 'false',
      'Idempotency-Result-Version': '2',
    });
    expect((await saveIntake(command)).ok).toBe(false);
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('{', { headers: { 'Content-Type': 'application/json' } })),
    );
    expect((await saveIntake(command)).ok).toBe(false);
  });
  it('rejects mixed restricted projections, malformed lists, and non-json success', async () => {
    response({ ...detail, candidate: { residential_address: {} } });
    expect((await getIntake(id)).ok).toBe(false);
    response({ items: [null], next_cursor: null });
    expect((await queryIntakes('worker')).ok).toBe(false);
    response({}, 200, { 'Content-Type': 'text/html' });
    expect((await getIntake(id)).ok).toBe(false);
    expect((await saveIntake(command)).ok).toBe(false);
    response({}, 503);
    expect((await queryIntakes('worker')).ok).toBe(false);
  });
  it('accepts typed partial content and rejects concealed nested replacement data', async () => {
    const worker = {
      ...detail,
      candidate: {
        full_name: 'Fictional',
        phone: '555 555 0100',
        interests: { other_description: 'Fictional' },
        availability: {
          mode: 'weekly',
          time_zone: 'Etc/UTC',
          ranges: [{ weekday: 1, start_local: '08:00', end_local: '16:00', end_day_offset: 0 }],
        },
      },
    };
    response(worker);
    expect((await getIntake(id)).ok).toBe(true);
    response({ ...worker, candidate: { interests: { residential_address: 'concealed' } } });
    expect((await getIntake(id)).ok).toBe(false);
    response({
      ...detail,
      summary: { ...detail.summary, kind: 'employer' },
      candidate: {
        display_name: 'Fictional',
        worker_count: 2,
        schedule: { mode: 'to_be_discussed' },
        offer: { minimum: '12.34', negotiable: true, per_worker: true },
      },
    });
    expect((await getIntake(id)).ok).toBe(true);
    response({ ...detail, candidate: { availability: { mode: 'flexible', unexpected: 'concealed' } } });
    expect((await getIntake(id)).ok).toBe(false);
    response({ ...detail, candidate: { full_name: null, interests: null } });
    expect((await getIntake(id)).ok).toBe(true);
  });
});
