import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  queryWorkInterests,
  saveWorkInterest,
  queryIntakeHistory,
  getRestrictedHistory,
  queryFollowUpOwners,
  getIntake,
  getIntakeAddress,
  queryIntakes,
  saveIntake,
} from './intakeClient';
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
  it('accepts the requested intake page size up to the API maximum', async () => {
    response({ items: Array.from({ length: 50 }, () => detail.summary), next_cursor: null });
    expect((await queryIntakes('worker', { page_size: 50 })).ok).toBe(true);
    expect(fetch).toHaveBeenCalledWith(
      '/api/staff/v1/intakes/query',
      expect.objectContaining({
        body: JSON.stringify({ kind: 'worker', lifecycle: 'draft', page_size: 50 }),
      }),
    );
    response({ items: Array.from({ length: 26 }, () => detail.summary), next_cursor: null });
    expect((await queryIntakes('worker')).ok).toBe(false);
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
    response({
      intake_id: id,
      version: 2,
      section: 'worksite_address',
      candidate: null,
      resolved: null,
    });
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
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            'Idempotency-Key': key,
          },
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

it('validates review/follow-up summaries and selected catalog versions', async () => {
  response({
    ...detail,
    summary: {
      ...detail.summary,
      review_status: 'current',
      follow_up: { owner_staff_id: id, next_follow_up_at: '2026-09-14T12:00:00Z', overdue: false },
    },
    latest_review: {
      review_id: id,
      reviewed_record_version: 1,
      reviewed_content_version: 1,
      outcome: 'intake_reviewed',
      actor_id: id,
      actor_display_name: 'Fictional',
      occurred_at: '2026-09-14T12:00:00Z',
    },
    candidate: { interests: { selections: [{ interest_id: id, catalog_version: 1 }] } },
  });
  expect((await getIntake(id)).ok).toBe(true);
  response({ ...detail, latest_review: { actor_display_name: { unexpected: true } } });
  expect((await getIntake(id)).ok).toBe(false);
  response({
    ...detail,
    candidate: { interests: { selections: [{ interest_id: id, catalog_version: 0 }] } },
  });
  expect((await getIntake(id)).ok).toBe(false);
  response({ ...detail, summary: { ...detail.summary, follow_up: { owner_staff_id: 'bad' } } });
  expect((await getIntake(id)).ok).toBe(false);
});
it('uses bounded catalog, owner and history endpoints with strict response identities', async () => {
  const entry = {
    interest_id: id,
    version: 1,
    code: 'fictional',
    label_en: 'Fictional',
    label_es: 'Ficticio',
    active: true,
  };
  response({ items: [entry], next_cursor: 'next' });
  expect((await queryWorkInterests('cursor', true)).ok).toBe(true);
  expect(fetch).toHaveBeenCalledWith(
    '/api/staff/v1/work-interests/query',
    expect.objectContaining({
      body: JSON.stringify({ page_size: 25, include_retired: true, cursor: 'cursor' }),
    }),
  );
  response({ items: [{ staff_id: id, display_name: 'Fictional owner' }], next_cursor: null });
  expect((await queryFollowUpOwners(id)).ok).toBe(true);
  response({ items: [{ staff_id: id, display_name: 'Fictional owner' }], next_cursor: null });
  expect((await queryFollowUpOwners(id, 'next')).ok).toBe(true);
  response({
    items: [
      {
        event_id: id,
        version: 2,
        content_version: 1,
        event_type: 'intake.reviewed',
        actor_id: id,
        actor_display_name: 'Fictional',
        occurred_at: '2026-09-14T12:00:00Z',
        outcome: 'intake_reviewed',
      },
    ],
    next_cursor: null,
  });
  expect((await queryIntakeHistory(id)).ok).toBe(true);
  response({ items: [], next_cursor: null });
  expect((await queryIntakeHistory(id, 'next')).ok).toBe(true);
  response({
    event_id: id,
    note: 'Fictional',
    reviewed_content: { kind: 'worker', content: {}, addresses: {} },
  });
  expect((await getRestrictedHistory(id, id)).ok).toBe(true);
  response({ event_id: 'wrong' });
  expect((await getRestrictedHistory(id, id)).ok).toBe(false);
  response({ items: [{ ...entry, active: 'yes' }], next_cursor: null });
  expect((await queryWorkInterests()).ok).toBe(false);
  response({ command_id: key, result_record_version: 1, current: entry }, 201, {
    'Idempotency-Replayed': 'false',
    'Idempotency-Result-Version': '1',
  });
  expect((await saveWorkInterest({ ...command, path: '/work-interests' })).ok).toBe(true);
  response({ command_id: key, result_record_version: 2, current: entry }, 200, {
    'Idempotency-Replayed': 'true',
    'Idempotency-Result-Version': '2',
  });
  expect((await saveWorkInterest({ ...command, path: '/work-interests' })).ok).toBe(false);
});
it('validates structured protected follow-up context and rejects extra protected fields', async () => {
  const follow_up = {
    action: 'attempt',
    reason_code: 'clarification',
    reason_text: 'Fictional',
    time_zone: 'Etc/UTC',
    method: 'phone',
    outcome: 'no_answer',
  };
  response({ event_id: id, follow_up });
  expect((await getRestrictedHistory(id, id)).ok).toBe(true);
  response({ event_id: id, follow_up: { ...follow_up, unexpected: 'hidden' } });
  expect((await getRestrictedHistory(id, id)).ok).toBe(false);
  response({
    event_id: id,
    follow_up: { action: 'needs_follow_up', reason_text: 'Fictional', time_zone: 'Etc/UTC' },
  });
  expect((await getRestrictedHistory(id, id)).ok).toBe(true);
});


it('admits unavailable linked list completeness without accepting leaked facts or unavailable detail', async () => {
  const unavailable = { ...detail.summary, complete: null, missing_fields: [] };
  response({ items: [unavailable], next_cursor: null });
  expect((await queryIntakes('worker')).ok).toBe(true);
  for (const patch of [{ display_name: 'Hidden canonical name' }, { missing_fields: ['phone'] }]) {
    response({ items: [{ ...unavailable, ...patch }], next_cursor: null });
    expect((await queryIntakes('worker')).ok).toBe(false);
  }
  response({ ...detail, summary: unavailable });
  expect((await getIntake(id)).ok).toBe(false);
});
