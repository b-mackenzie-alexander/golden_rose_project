import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  disposeExternalCalendarCandidate,
  getCalendarImportSummary,
} from './calendarImportClient';

const fetchMock = vi.fn<typeof fetch>();
const connection = {
  connection_id: '11111111-1111-4111-8111-111111111111',
  staff_id: '22222222-2222-4222-8222-222222222222',
  provider_name: 'google_calendar',
  calendar_alias: 'primary',
  granted_scopes: ['https://www.googleapis.com/auth/calendar.readonly'],
  connection_status: 'authorization_required',
  connected_at: null,
  disconnected_at: null,
  last_sync_status: 'configuration_required',
  last_sync_error: 'oauth_configuration_pending',
  updated_at: '2026-10-09T14:00:00Z',
  version: 1,
};
const candidate = {
  import_id: '33333333-3333-4333-8333-333333333333',
  connection_id: connection.connection_id,
  provider_event_updated_at: '2026-10-09T14:00:00Z',
  event_title: 'Owner calendar note',
  starts_at: '2026-10-12T13:30:00Z',
  ends_at: '2026-10-12T14:00:00Z',
  time_zone: 'America/New_York',
  location_review: 'Queens',
  import_status: 'candidate',
  linked_entity_type: null,
  linked_entity_id: null,
  updated_at: '2026-10-09T14:00:00Z',
  version: 1,
};

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

function problemResponse(type: string, status: number) {
  return jsonResponse(
    { type, title: 'Problem', status },
    {
      status,
      headers: { 'Content-Type': 'application/problem+json' },
    },
  );
}

function validSummary(overrides: Record<string, unknown> = {}) {
  return {
    connection,
    candidates: [candidate],
    oauth_configuration_required: true,
    ...overrides,
  };
}

function commandResponse(overrides: Record<string, unknown> = {}) {
  return {
    candidate: { ...candidate, import_status: 'ignored', version: 2 },
    event_type: 'external_calendar.candidate_ignored',
    result_version: 2,
    replayed: false,
    ...overrides,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

describe('calendarImportClient', () => {
  it('reads calendar import summary with no-store staff request handling', async () => {
    fetchMock.mockResolvedValue(jsonResponse(validSummary()));
    vi.stubGlobal('fetch', fetchMock);

    const result = await getCalendarImportSummary();

    expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/calendar-imports', {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    });
    expect(result).toEqual({
      ok: true,
      value: {
        connection: {
          connectionId: connection.connection_id,
          staffId: connection.staff_id,
          providerName: 'google_calendar',
          calendarAlias: 'primary',
          grantedScopes: ['https://www.googleapis.com/auth/calendar.readonly'],
          connectionStatus: 'authorization_required',
          connectedAt: null,
          disconnectedAt: null,
          lastSyncStatus: 'configuration_required',
          lastSyncError: 'oauth_configuration_pending',
          updatedAt: '2026-10-09T14:00:00Z',
          version: 1,
        },
        candidates: [{
          importId: candidate.import_id,
          connectionId: candidate.connection_id,
          providerEventUpdatedAt: '2026-10-09T14:00:00Z',
          eventTitle: 'Owner calendar note',
          startsAt: '2026-10-12T13:30:00Z',
          endsAt: '2026-10-12T14:00:00Z',
          timeZone: 'America/New_York',
          locationReview: 'Queens',
          importStatus: 'candidate',
          linkedEntityType: null,
          linkedEntityId: null,
          updatedAt: '2026-10-09T14:00:00Z',
          version: 1,
        }],
        oauthConfigurationRequired: true,
      },
    });
  });

  it('accepts an empty unconfigured summary', async () => {
    fetchMock.mockResolvedValue(jsonResponse(validSummary({
      connection: null,
      candidates: [],
      oauth_configuration_required: true,
    })));
    vi.stubGlobal('fetch', fetchMock);

    await expect(getCalendarImportSummary()).resolves.toEqual({
      ok: true,
      value: {
        connection: null,
        candidates: [],
        oauthConfigurationRequired: true,
      },
    });
  });

  it('disposes a calendar import candidate with idempotency and no-store headers', async () => {
    fetchMock.mockResolvedValue(jsonResponse(commandResponse()));
    vi.stubGlobal('fetch', fetchMock);

    const result = await disposeExternalCalendarCandidate(
      candidate.import_id,
      1,
      'ignored',
      'Duplicate of an existing Golden Rose item',
      '44444444-4444-4444-8444-444444444444',
    );

    expect(fetchMock).toHaveBeenCalledWith(
      `/api/staff/v1/calendar-imports/candidates/${candidate.import_id}/ignore`,
      {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'Idempotency-Key': '44444444-4444-4444-8444-444444444444',
        },
        cache: 'no-store',
        credentials: 'same-origin',
        mode: 'same-origin',
        redirect: 'error',
        referrerPolicy: 'no-referrer',
        body: JSON.stringify({
          expected_version: 1,
          reason_text: 'Duplicate of an existing Golden Rose item',
        }),
      },
    );
    expect(result).toEqual({
      ok: true,
      value: {
        candidate: {
          importId: candidate.import_id,
          connectionId: candidate.connection_id,
          providerEventUpdatedAt: '2026-10-09T14:00:00Z',
          eventTitle: 'Owner calendar note',
          startsAt: '2026-10-12T13:30:00Z',
          endsAt: '2026-10-12T14:00:00Z',
          timeZone: 'America/New_York',
          locationReview: 'Queens',
          importStatus: 'ignored',
          linkedEntityType: null,
          linkedEntityId: null,
          updatedAt: '2026-10-09T14:00:00Z',
          version: 2,
        },
        eventType: 'external_calendar.candidate_ignored',
        resultVersion: 2,
        replayed: false,
      },
    });
  });

  it('uses the mark-existing endpoint for marked-existing dispositions', async () => {
    fetchMock.mockResolvedValue(jsonResponse(commandResponse({
      candidate: { ...candidate, import_status: 'marked_existing', version: 2 },
      event_type: 'external_calendar.candidate_marked_existing',
    })));
    vi.stubGlobal('fetch', fetchMock);

    await expect(disposeExternalCalendarCandidate(
      candidate.import_id,
      1,
      'marked_existing',
      'Already represented in Golden Rose',
      '44444444-4444-4444-8444-444444444444',
    )).resolves.toEqual(expect.objectContaining({ ok: true }));
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/staff/v1/calendar-imports/candidates/${candidate.import_id}/mark-existing`,
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it.each([
    ['forbidden problem', problemResponse('https://golden-rose.local/problems/forbidden', 403), 'forbidden'],
    ['not found problem', problemResponse('https://golden-rose.local/problems/calendar-import-not-found', 404), 'not_found'],
    ['stale problem', problemResponse('https://golden-rose.local/problems/calendar-import-version-conflict', 412), 'stale'],
    ['validation problem', problemResponse('https://golden-rose.local/problems/calendar-import-invalid', 422), 'validation'],
    ['service problem', problemResponse('https://golden-rose.local/problems/service-unavailable', 503), 'unavailable'],
    ['unknown problem', problemResponse('https://golden-rose.local/problems/other', 409), 'unexpected'],
    ['non-json error', new Response('denied', { status: 403, headers: { 'Content-Type': 'text/plain' } }), 'forbidden'],
    ['unreadable problem', new Response('{', { status: 503, headers: { 'Content-Type': 'application/problem+json' } }), 'unavailable'],
  ])('maps %s into a recoverable failure kind', async (_label, response, kind) => {
    fetchMock.mockResolvedValue(response);
    vi.stubGlobal('fetch', fetchMock);

    await expect(getCalendarImportSummary()).resolves.toEqual({
      ok: false,
      failure: { kind },
    });
  });

  it('maps network failures into unavailable', async () => {
    fetchMock.mockRejectedValue(new TypeError('offline'));
    vi.stubGlobal('fetch', fetchMock);

    await expect(getCalendarImportSummary()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unavailable' },
    });
    await expect(disposeExternalCalendarCandidate(
      candidate.import_id,
      1,
      'ignored',
      'Duplicate',
      '44444444-4444-4444-8444-444444444444',
    )).resolves.toEqual({
      ok: false,
      failure: { kind: 'unavailable' },
    });
  });

  it.each([
    ['non-object summary', null],
    ['malformed connection', validSummary({ connection: { ...connection, provider_name: 'outlook' } })],
    ['bad scope', validSummary({ connection: { ...connection, granted_scopes: [''] } })],
    ['bad candidate uuid', validSummary({ candidates: [{ ...candidate, import_id: 'not-a-uuid' }] })],
    ['bad interval', validSummary({ candidates: [{ ...candidate, ends_at: candidate.starts_at }] })],
    ['bad status', validSummary({ candidates: [{ ...candidate, import_status: 'accepted' }] })],
    ['bad link uuid', validSummary({ candidates: [{ ...candidate, linked_entity_id: 'not-a-uuid' }] })],
    ['bad oauth flag', validSummary({ oauth_configuration_required: 'yes' })],
    ['malformed command event', commandResponse({ event_type: 'external_calendar.deleted' })],
    ['malformed command result version', commandResponse({ result_version: 0 })],
  ])('rejects %s', async (_label, payload) => {
    fetchMock.mockResolvedValue(jsonResponse(payload));
    vi.stubGlobal('fetch', fetchMock);

    await expect(getCalendarImportSummary()).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });

  it('rejects malformed successful command responses', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(commandResponse({ replayed: 'no' })));
    vi.stubGlobal('fetch', fetchMock);

    await expect(disposeExternalCalendarCandidate(
      candidate.import_id,
      1,
      'ignored',
      'Duplicate',
      '44444444-4444-4444-8444-444444444444',
    )).resolves.toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  });
});
