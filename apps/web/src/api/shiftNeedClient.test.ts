import { afterEach, expect, it, vi } from 'vitest';
import { createShiftNeed, listShiftNeeds, submitShiftNeedForReview, submitStaffingRequestForReview } from './shiftNeedClient';

const employerId = '11111111-1111-4111-8111-111111111111';
const requestId = '22222222-2222-4222-8222-222222222222';
const shiftNeedId = '33333333-3333-4333-8333-333333333333';
const commandId = '44444444-4444-4444-8444-444444444444';

const shift = {
  shift_need_id: shiftNeedId,
  employer_id: employerId,
  staffing_request_id: requestId,
  request_version_at_creation: 2,
  shift_status: 'draft',
  role_title: 'Home aide',
  worker_count: 2,
  starts_at: '2026-10-01T13:00:00Z',
  ends_at: '2026-10-01T17:00:00Z',
  time_zone: 'America/New_York',
  notes: null,
  version: 1,
  created_at: '2026-09-29T12:00:00Z',
  updated_at: '2026-09-29T12:00:00Z',
};

afterEach(() => vi.unstubAllGlobals());

it('lists shift needs with no-store staff transport and strict response validation', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [shift] }), { headers: { 'Content-Type': 'application/json' } }));
  vi.stubGlobal('fetch', fetcher);

  expect(await listShiftNeeds(employerId, requestId)).toMatchObject({ ok: true, value: [{ shiftNeedId, shiftStatus: 'draft' }] });
  expect(fetcher).toHaveBeenCalledWith(
    `/api/staff/v1/employers/${employerId}/requests/${requestId}/shift-needs/query`,
    expect.objectContaining({
      cache: 'no-store',
      credentials: 'same-origin',
      method: 'POST',
      referrerPolicy: 'no-referrer',
    }),
  );
});

it('creates a shift need only when command evidence headers match', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({
    command_id: commandId,
    result_record_version: 1,
    event_type: 'shift_need.created',
    current: shift,
  }), { status: 201, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '1' } }));
  vi.stubGlobal('fetch', fetcher);

  const result = await createShiftNeed({
    employerId,
    requestId,
    expectedRequestVersion: 2,
    roleTitle: 'Home aide',
    workerCount: 2,
    startsAt: '2026-10-01T13:00:00Z',
    endsAt: '2026-10-01T17:00:00Z',
    timeZone: 'America/New_York',
    reasonText: 'Employer supplied a concrete shift',
    notes: null,
    commandId,
  });

  expect(result).toMatchObject({ ok: true, value: { commandId, resultRecordVersion: 1 } });
  const init = fetcher.mock.calls[0]?.[1] as RequestInit;
  expect(typeof init.body).toBe('string');
  expect(JSON.parse(init.body as string)).toMatchObject({
    expected_request_version: 2,
    reason_text: 'Employer supplied a concrete shift',
  });

  fetcher.mockResolvedValueOnce(new Response(JSON.stringify({
    command_id: commandId,
    result_record_version: 1,
    event_type: 'shift_need.created',
    current: shift,
  }), { status: 201, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' } }));
  expect(await createShiftNeed({
    employerId,
    requestId,
    expectedRequestVersion: 2,
    roleTitle: 'Home aide',
    workerCount: 2,
    startsAt: '2026-10-01T13:00:00Z',
    endsAt: '2026-10-01T17:00:00Z',
    timeZone: 'America/New_York',
    reasonText: 'Employer supplied a concrete shift',
    notes: null,
    commandId,
  })).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it('submits shift and request review commands with strict idempotent evidence parsing', async () => {
  const fetcher = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({
      command_id: commandId,
      result_record_version: 2,
      event_type: 'shift_need.submitted_for_review',
      current: { ...shift, shift_status: 'pending_review', version: 2, updated_at: '2026-09-29T12:05:00Z' },
    }), { status: 200, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({
      command_id: commandId,
      result_record_version: 3,
      event_type: 'staffing_request.submitted_for_review',
      current: {
        staffing_request_id: requestId,
        employer_id: employerId,
        version: 3,
        request_status: 'pending_review',
      },
    }), { status: 200, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '3' } }));
  vi.stubGlobal('fetch', fetcher);

  expect(await submitShiftNeedForReview({
    employerId,
    requestId,
    shiftNeedId,
    expectedVersion: 1,
    reasonText: 'Staff submitted shift need for review',
    commandId,
  })).toMatchObject({ ok: true, value: { eventType: 'shift_need.submitted_for_review', current: { shiftStatus: 'pending_review' } } });
  expect(await submitStaffingRequestForReview({
    employerId,
    requestId,
    expectedVersion: 2,
    reasonText: 'Staff submitted staffing request for review',
    commandId,
  })).toMatchObject({ ok: true, value: { eventType: 'staffing_request.submitted_for_review', current: { requestStatus: 'pending_review' } } });

  expect(fetcher.mock.calls[0]?.[0]).toBe(`/api/staff/v1/employers/${employerId}/requests/${requestId}/shift-needs/${shiftNeedId}/submit-review`);
  expect(fetcher.mock.calls[1]?.[0]).toBe(`/api/staff/v1/employers/${employerId}/requests/${requestId}/submit-review`);
});

it('rejects malformed lifecycle command responses', async () => {
  const fetcher = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({
      command_id: commandId,
      result_record_version: 2,
      event_type: 'shift_need.submitted_for_review',
      current: { ...shift, shift_status: 'pending_review', version: 1 },
    }), { status: 200, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({
      command_id: commandId,
      result_record_version: 3,
      event_type: 'staffing_request.submitted_for_review',
      current: {
        staffing_request_id: requestId,
        employer_id: employerId,
        version: 3,
        request_status: 'active',
      },
    }), { status: 200, headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '3' } }));
  vi.stubGlobal('fetch', fetcher);

  expect(await submitShiftNeedForReview({
    employerId,
    requestId,
    shiftNeedId,
    expectedVersion: 1,
    reasonText: 'Staff submitted shift need for review',
    commandId,
  })).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
  expect(await submitStaffingRequestForReview({
    employerId,
    requestId,
    expectedVersion: 2,
    reasonText: 'Staff submitted staffing request for review',
    commandId,
  })).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it.each([
  [403, 'forbidden'],
  [404, 'not_found'],
  [412, 'stale'],
  [422, 'validation'],
  [503, 'unavailable'],
] as const)('maps recoverable API failures %s', async (status, kind) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ type: 'about:blank' }), { status, headers: { 'Content-Type': 'application/problem+json' } })));
  expect(await listShiftNeeds(employerId, requestId)).toEqual({ ok: false, failure: { kind } });
});

it('rejects overbroad or impossible shift payloads', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
    items: [{ ...shift, ends_at: '2026-10-01T12:00:00Z' }],
  }), { headers: { 'Content-Type': 'application/json' } })));
  expect(await listShiftNeeds(employerId, requestId)).toEqual({ ok: false, failure: { kind: 'unexpected' } });
});

it('fails closed on network, HTML, malformed JSON, and non-JSON error responses', async () => {
  const input = {
    employerId,
    requestId,
    expectedRequestVersion: 2,
    roleTitle: 'Home aide',
    workerCount: 2,
    startsAt: '2026-10-01T13:00:00Z',
    endsAt: '2026-10-01T17:00:00Z',
    timeZone: 'America/New_York',
    reasonText: 'Employer supplied a concrete shift',
    notes: null,
    commandId,
  };
  const fetcher = vi.fn()
    .mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce(new Response('<html></html>', { status: 200, headers: { 'Content-Type': 'text/html' } }))
    .mockResolvedValueOnce(new Response('{', { status: 200, headers: { 'Content-Type': 'application/json' } }))
    .mockResolvedValueOnce(new Response('forbidden', { status: 403, headers: { 'Content-Type': 'text/plain' } }))
    .mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce(new Response('<html></html>', { status: 201, headers: { 'Content-Type': 'text/html' } }));
  vi.stubGlobal('fetch', fetcher);

  expect(await listShiftNeeds(employerId, requestId)).toEqual({ ok: false, failure: { kind: 'unavailable' } });
  expect(await listShiftNeeds(employerId, requestId)).toEqual({ ok: false, failure: { kind: 'unexpected' } });
  expect(await listShiftNeeds(employerId, requestId)).toEqual({ ok: false, failure: { kind: 'unexpected' } });
  expect(await listShiftNeeds(employerId, requestId)).toEqual({ ok: false, failure: { kind: 'forbidden' } });
  expect(await createShiftNeed(input)).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
  expect(await createShiftNeed(input)).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});
