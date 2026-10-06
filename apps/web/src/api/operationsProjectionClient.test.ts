import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { getOperationsProjection } from './operationsProjectionClient';

const fetchMock = vi.fn<typeof fetch>();
const validRequest = {
  item_type: 'staffing_request',
  source_intake_id: '11111111-1111-4111-8111-111111111111',
  employer_id: '22222222-2222-4222-8222-222222222222',
  employer_name: 'Projected Employer',
  staffing_request_id: '33333333-3333-4333-8333-333333333333',
  request_status: 'pending_review',
  role_title: 'Home aide',
  worker_count: 2,
  version: 3,
  received_at: '2026-10-01T13:00:00Z',
  updated_at: '2026-10-01T13:30:00Z',
};
const validShift = {
  item_type: 'shift_need',
  source_intake_id: null,
  employer_id: '22222222-2222-4222-8222-222222222222',
  employer_name: 'Projected Employer',
  staffing_request_id: '33333333-3333-4333-8333-333333333333',
  shift_need_id: '44444444-4444-4444-8444-444444444444',
  request_status: 'pending_review',
  shift_status: 'draft',
  role_title: 'Home aide',
  worker_count: 1,
  starts_at: '2026-10-01T14:00:00Z',
  ends_at: '2026-10-01T18:00:00Z',
  time_zone: 'America/New_York',
  version: 1,
  updated_at: '2026-10-01T13:45:00Z',
};
const validAreaSummary = [
  { area_key: 'bronx', area_label: 'Bronx', request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { area_key: 'brooklyn', area_label: 'Brooklyn', request_count: 1, shift_count: 1, worker_slots: 2, pending_review_count: 1 },
  { area_key: 'manhattan', area_label: 'Manhattan', request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { area_key: 'queens', area_label: 'Queens', request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { area_key: 'staten_island', area_label: 'Staten Island', request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
];
const validZoneSummary = [
  { zone_key: 'south_bronx', zone_label: 'South Bronx', area_key: 'bronx', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'upper_manhattan_harlem', zone_label: 'Upper Manhattan / Harlem', area_key: 'manhattan', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'midtown_lower_manhattan', zone_label: 'Midtown / Lower Manhattan', area_key: 'manhattan', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'northwest_queens', zone_label: 'Northwest Queens', area_key: 'queens', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'central_queens', zone_label: 'Central Queens', area_key: 'queens', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'northeast_queens', zone_label: 'Northeast Queens', area_key: 'queens', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'north_brooklyn', zone_label: 'North Brooklyn', area_key: 'brooklyn', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'central_brooklyn', zone_label: 'Central Brooklyn', area_key: 'brooklyn', worker_residence_count: 2, worksite_count: 1, request_count: 1, shift_count: 1, worker_slots: 2, pending_review_count: 1 },
  { zone_key: 'south_brooklyn', zone_label: 'South Brooklyn', area_key: 'brooklyn', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
  { zone_key: 'north_shore_staten_island', zone_label: 'North Shore Staten Island', area_key: 'staten_island', worker_residence_count: 0, worksite_count: 0, request_count: 0, shift_count: 0, worker_slots: 0, pending_review_count: 0 },
];
const validReportSummary = {
  request_count: 1,
  shift_count: 1,
  worker_slots: 2,
  pending_review_count: 1,
  active_area_count: 1,
  unmapped_request_count: 0,
};
const validCalendarSummary = {
  projected_shift_count: 1,
  worker_slots: 1,
  pending_review_shift_count: 0,
  coverage_day_count: 1,
  first_shift_starts_at: '2026-10-01T14:00:00Z',
  last_shift_ends_at: '2026-10-01T18:00:00Z',
};
const validQueueSummary = {
  open_item_count: 2,
  draft_count: 1,
  pending_review_count: 1,
  high_priority_count: 1,
  oldest_item_updated_at: '2026-10-01T13:30:00Z',
  newest_item_updated_at: '2026-10-01T13:45:00Z',
};

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' }, ...init });
}

function projection(
  request: Record<string, unknown> = validRequest,
  shift: Record<string, unknown> = validShift,
) {
  return {
    request_items: [request],
    shift_items: [shift],
    area_summary: validAreaSummary,
    zone_summary: validZoneSummary,
    report_summary: validReportSummary,
    calendar_summary: validCalendarSummary,
    queue_summary: validQueueSummary,
  };
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('operationsProjectionClient', () => {
  it('reads the operations projection with no-store staff request handling', async () => {
    fetchMock.mockResolvedValue(jsonResponse(projection()));

    const result = await getOperationsProjection();

    expect(result.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/operations/projection', expect.objectContaining({
      cache: 'no-store',
      credentials: 'same-origin',
      referrerPolicy: 'no-referrer',
    }));
    if (!result.ok) throw new Error('Expected projection read to succeed.');
    expect(result.value.requestItems[0]?.sourceIntakeId).toBe('11111111-1111-4111-8111-111111111111');
    expect(result.value.shiftItems[0]?.sourceIntakeId).toBeNull();
    expect(result.value.areaSummary[1]).toEqual({
      areaKey: 'brooklyn',
      areaLabel: 'Brooklyn',
      requestCount: 1,
      shiftCount: 1,
      workerSlots: 2,
      pendingReviewCount: 1,
    });
    expect(result.value.zoneSummary?.[7]).toEqual({
      zoneKey: 'central_brooklyn',
      zoneLabel: 'Central Brooklyn',
      areaKey: 'brooklyn',
      workerResidenceCount: 2,
      worksiteCount: 1,
      requestCount: 1,
      shiftCount: 1,
      workerSlots: 2,
      pendingReviewCount: 1,
    });
    expect(result.value.reportSummary).toEqual({
      requestCount: 1,
      shiftCount: 1,
      workerSlots: 2,
      pendingReviewCount: 1,
      activeAreaCount: 1,
      unmappedRequestCount: 0,
    });
    expect(result.value.calendarSummary).toEqual({
      projectedShiftCount: 1,
      workerSlots: 1,
      pendingReviewShiftCount: 0,
      coverageDayCount: 1,
      firstShiftStartsAt: '2026-10-01T14:00:00Z',
      lastShiftEndsAt: '2026-10-01T18:00:00Z',
    });
    expect(result.value.queueSummary).toEqual({
      openItemCount: 2,
      draftCount: 1,
      pendingReviewCount: 1,
      highPriorityCount: 1,
      oldestItemUpdatedAt: '2026-10-01T13:30:00Z',
      newestItemUpdatedAt: '2026-10-01T13:45:00Z',
    });
  });

  it('rejects malformed projection payloads', async () => {
    fetchMock.mockResolvedValue(jsonResponse({
      request_items: [],
      shift_items: [{ item_type: 'shift_need', starts_at: '2026-10-01T18:00:00Z', ends_at: '2026-10-01T14:00:00Z' }],
    }));

    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });

  it('maps response and network failures into recoverable failure kinds', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('offline'));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unavailable' },
    });

    fetchMock.mockResolvedValueOnce(new Response('', { status: 403 }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'forbidden' },
    });

    fetchMock.mockResolvedValueOnce(new Response('', { status: 422 }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'validation' },
    });

    fetchMock.mockResolvedValueOnce(new Response('', { status: 400 }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'validation' },
    });

    fetchMock.mockResolvedValueOnce(new Response('', { status: 503 }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unavailable' },
    });

    fetchMock.mockResolvedValueOnce(new Response('', { status: 500 }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });

  it('rejects non-json and unreadable successful responses', async () => {
    fetchMock.mockResolvedValueOnce(new Response('not json', { headers: { 'Content-Type': 'text/plain' } }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });

    fetchMock.mockResolvedValueOnce(new Response('{', { headers: { 'Content-Type': 'application/json' } }));
    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });

  it('rejects malformed request and shift identifiers', async () => {
    fetchMock.mockResolvedValue(jsonResponse({
      request_items: [{ ...validRequest, request_status: 'draft', source_intake_id: 'not-a-uuid' }],
      shift_items: [],
    }));

    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });

  it.each([
    ['non-object payload', null],
    ['missing request array', { shift_items: [] }],
    ['missing shift array', { request_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['missing area summary', { request_items: [], shift_items: [], report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['missing report summary', { request_items: [], shift_items: [], area_summary: validAreaSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['missing calendar summary', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, queue_summary: validQueueSummary }],
    ['missing queue summary', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary }],
    ['oversized request list', { request_items: Array.from({ length: 51 }, () => validRequest), shift_items: [] }],
    ['oversized shift list', { request_items: [], shift_items: Array.from({ length: 51 }, () => validShift), area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['short area summary', { request_items: [], shift_items: [], area_summary: validAreaSummary.slice(1), report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['duplicate area summary', { request_items: [], shift_items: [], area_summary: [validAreaSummary[0], ...validAreaSummary.slice(0, 4)], report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['invalid area label', { request_items: [], shift_items: [], area_summary: [{ ...validAreaSummary[0], area_label: 'Queens' }, ...validAreaSummary.slice(1)], report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['invalid area count', { request_items: [], shift_items: [], area_summary: [{ ...validAreaSummary[0], worker_slots: -1 }, ...validAreaSummary.slice(1)], report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['short zone summary', { ...projection(), zone_summary: validZoneSummary.slice(1) }],
    ['duplicate zone summary', { ...projection(), zone_summary: [validZoneSummary[0], ...validZoneSummary.slice(0, 9)] }],
    ['invalid zone label', { ...projection(), zone_summary: [{ ...validZoneSummary[0], zone_label: 'Central Queens' }, ...validZoneSummary.slice(1)] }],
    ['invalid zone count', { ...projection(), zone_summary: [{ ...validZoneSummary[0], worker_residence_count: -1 }, ...validZoneSummary.slice(1)] }],
    ['invalid report active area count', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: { ...validReportSummary, active_area_count: 6 }, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['invalid calendar day count', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: { ...validCalendarSummary, coverage_day_count: 367 }, queue_summary: validQueueSummary }],
    ['invalid calendar timestamp pairing', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: { ...validCalendarSummary, first_shift_starts_at: null }, queue_summary: validQueueSummary }],
    ['invalid calendar window', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: { ...validCalendarSummary, first_shift_starts_at: '2026-10-01T18:00:00Z', last_shift_ends_at: '2026-10-01T14:00:00Z' }, queue_summary: validQueueSummary }],
    ['invalid queue pending count', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: { ...validQueueSummary, pending_review_count: 3 } }],
    ['invalid queue high-priority count', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: { ...validQueueSummary, high_priority_count: 3 } }],
    ['invalid queue timestamp pairing', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: { ...validQueueSummary, oldest_item_updated_at: null } }],
    ['invalid queue timestamp order', { request_items: [], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: { ...validQueueSummary, oldest_item_updated_at: '2026-10-01T14:00:00Z', newest_item_updated_at: '2026-10-01T13:00:00Z' } }],
    ['non-object request', { request_items: [null], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['wrong request type', { request_items: [{ ...validRequest, item_type: 'other' }], shift_items: [], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['blank employer name', projection({ ...validRequest, employer_name: '   ' })],
    ['overlong role title', projection({ ...validRequest, role_title: 'x'.repeat(201) })],
    ['zero worker count', projection({ ...validRequest, worker_count: 0 })],
    ['unsafe version', projection({ ...validRequest, version: Number.MAX_SAFE_INTEGER + 1 })],
    ['invalid request status', projection({ ...validRequest, request_status: 'approved' })],
    ['bad received timestamp', projection({ ...validRequest, received_at: 'not-a-date' })],
    ['non-object shift', { request_items: [], shift_items: [null], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['wrong shift type', { request_items: [], shift_items: [{ ...validShift, item_type: 'other' }], area_summary: validAreaSummary, report_summary: validReportSummary, calendar_summary: validCalendarSummary, queue_summary: validQueueSummary }],
    ['invalid shift request status', projection(validRequest, { ...validShift, request_status: 'approved' })],
    ['invalid shift status', projection(validRequest, { ...validShift, shift_status: 'approved' })],
    ['same-time shift window', projection(validRequest, { ...validShift, starts_at: '2026-10-01T14:00:00Z', ends_at: '2026-10-01T14:00:00Z' })],
    ['blank time zone', projection(validRequest, { ...validShift, time_zone: '' })],
    ['bad shift update timestamp', projection(validRequest, { ...validShift, updated_at: 'not-a-date' })],
    ['bad shift identifier length', projection(validRequest, { ...validShift, shift_need_id: '44444444-4444-4444-8444-44444444444' })],
    ['bad shift identifier character', projection(validRequest, { ...validShift, shift_need_id: 'zzzzzzzz-4444-4444-8444-444444444444' })],
  ])('rejects %s', async (_caseName, body) => {
    fetchMock.mockResolvedValue(jsonResponse(body));

    await expect(getOperationsProjection()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });

  it('accepts omitted source intake identifiers as null', async () => {
    const requestWithoutSource: Record<string, unknown> = { ...validRequest };
    const shiftWithoutSource: Record<string, unknown> = { ...validShift };
    delete requestWithoutSource.source_intake_id;
    delete shiftWithoutSource.source_intake_id;
    fetchMock.mockResolvedValue(jsonResponse(projection(requestWithoutSource, shiftWithoutSource)));

    const result = await getOperationsProjection();

    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error('Expected projection read to succeed.');
    expect(result.value.requestItems[0]?.sourceIntakeId).toBeNull();
    expect(result.value.shiftItems[0]?.sourceIntakeId).toBeNull();
  });
});
