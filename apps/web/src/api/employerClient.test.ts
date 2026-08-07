import { afterEach, expect, it, vi } from 'vitest';

import { createEmployer, getEmployer, searchEmployers } from './employerClient';

afterEach(() => {
  vi.restoreAllMocks();
});

it('sends the bounded search contract', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(
      JSON.stringify({
        items: [
          {
            employer_id: '11111111-1111-4111-8111-111111111111',
            employer_type: 'business',
            display_name: 'Golden Rose Staffing',
            lifecycle_status: 'draft',
            version: 1,
            received_at: '2026-08-05T08:00:00Z',
          },
        ],
        next_cursor: 'opaque-cursor-001',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      },
    ),
  );
  vi.stubGlobal('fetch', fetchMock);

  const controller = new AbortController();
  const result = await searchEmployers({
    displayNameQuery: 'rose',
    employerType: 'business',
    cursor: 'opaque-cursor-000',
    signal: controller.signal,
  });

  expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/employers/search', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      display_name_query: 'rose',
      employer_type: 'business',
      page_size: 25,
      cursor: 'opaque-cursor-000',
    }),
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
    signal: controller.signal,
  });
  expect(result).toEqual({
    ok: true,
    value: {
      items: [
        {
          employerId: '11111111-1111-4111-8111-111111111111',
          employerType: 'business',
          displayName: 'Golden Rose Staffing',
          lifecycleStatus: 'draft',
        },
      ],
      nextCursor: 'opaque-cursor-001',
    },
  });

  fetchMock.mockResolvedValueOnce(
    new Response(JSON.stringify({ items: [], next_cursor: null }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );

  await searchEmployers({ displayNameQuery: 'lantern' });

  expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/staff/v1/employers/search', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      display_name_query: 'lantern',
      page_size: 25,
      cursor: null,
    }),
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
    signal: undefined,
  });
});

it('rejects contract-invalid search responses', async () => {
  const invalidResponses: Array<{ label: string; response: Response }> = [
    {
      label: 'missing content type',
      response: new Response(JSON.stringify({ items: [], next_cursor: null }), { status: 200 }),
    },
    {
      label: 'null page',
      response: new Response('null', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    },
    {
      label: 'non-array items',
      response: new Response(JSON.stringify({ items: {}, next_cursor: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    },
    {
      label: 'too many items',
      response: new Response(
        JSON.stringify({
          items: Array.from({ length: 26 }, (_, index) => ({
            employer_id: `11111111-1111-4111-8111-${String(index).padStart(12, '0')}`,
            employer_type: 'business',
            display_name: 'Golden Rose Staffing',
            lifecycle_status: 'draft',
            version: 1,
            received_at: '2026-08-05T08:00:00Z',
          })),
          next_cursor: null,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    },
    {
      label: 'invalid timestamp calendar',
      response: new Response(
        JSON.stringify({
          items: [
            {
              employer_id: '11111111-1111-4111-8111-111111111111',
              employer_type: 'business',
              display_name: 'Golden Rose Staffing',
              lifecycle_status: 'draft',
              version: 1,
              received_at: '2026-02-31T08:00:00Z',
            },
          ],
          next_cursor: null,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    },
    {
      label: 'empty cursor',
      response: new Response(JSON.stringify({ items: [], next_cursor: '' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    },
  ];

  for (const invalidResponse of invalidResponses) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(invalidResponse.response));

    const result = await searchEmployers({ displayNameQuery: 'rose' });

    expect(result, invalidResponse.label).toEqual({
      ok: false,
      failure: { kind: 'unexpected' },
    });
  }
});

it('sends and validates exact detail', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(
      JSON.stringify({
        employer_id: '22222222-2222-4222-8222-222222222222',
        employer_type: 'household',
        display_name: 'Golden Detail Household',
        lifecycle_status: 'draft',
        source_channel: 'staff_entry',
        version: 1,
        received_at: '2026-08-05T07:15:00Z',
        created_at: '2026-08-05T07:15:00Z',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      },
    ),
  );
  vi.stubGlobal('fetch', fetchMock);

  const requestedId = '22222222-2222-4222-8222-222222222222';
  const controller = new AbortController();
  const result = await getEmployer(requestedId, { signal: controller.signal });

  expect(fetchMock).toHaveBeenCalledWith(`/api/staff/v1/employers/${requestedId}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
    signal: controller.signal,
  });
  expect(result).toEqual({
    ok: true,
    value: {
      employerId: requestedId,
      employerType: 'household',
      displayName: 'Golden Detail Household',
      lifecycleStatus: 'draft',
      sourceChannel: 'staff_entry',
    },
  });

  const invalidIdResult = await getEmployer('not-a-uuid');
  expect(invalidIdResult).toEqual({
    ok: false,
    failure: { kind: 'validation' },
  });
});

it('sends create with caller command identity', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(
      JSON.stringify({
        employer_id: '33333333-3333-4333-8333-333333333333',
        employer_type: 'household',
        display_name: 'Synthetic Household 001',
        lifecycle_status: 'draft',
        source_channel: 'staff_entry',
        version: 1,
        received_at: '2026-08-05T00:10:45Z',
        created_at: '2026-08-05T00:10:45Z',
      }),
      {
        status: 201,
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Replayed': 'true',
        },
      },
    ),
  );
  vi.stubGlobal('fetch', fetchMock);

  const result = await createEmployer({
    commandId: '44444444-4444-4444-8444-444444444444',
    employerType: 'household',
    displayName: 'Synthetic Household 001',
  });

  expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/employers', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'Idempotency-Key': '44444444-4444-4444-8444-444444444444',
    },
    body: JSON.stringify({
      employer_type: 'household',
      display_name: 'Synthetic Household 001',
    }),
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
  });
  expect(result).toEqual({
    ok: true,
    value: {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'household',
      displayName: 'Synthetic Household 001',
      lifecycleStatus: 'draft',
      sourceChannel: 'staff_entry',
    },
  });

  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({}), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );

  const unknownOutcome = await createEmployer({
    commandId: '55555555-5555-4555-8555-555555555555',
    employerType: 'business',
    displayName: 'Synthetic Replay API 001',
  });

  expect(unknownOutcome).toEqual({
    ok: false,
    failure: { kind: 'unknown_outcome' },
  });
});

it('maps create transport and invalid-success-body failures to unknown outcome', async () => {
  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('network down')));
  const transportFailure = await createEmployer({
    commandId: '99999999-9999-4999-8999-999999999999',
    employerType: 'business',
    displayName: 'Synthetic Network Failure 001',
  });

  expect(transportFailure).toEqual({
    ok: false,
    failure: { kind: 'unknown_outcome' },
  });

  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValue(
      new Response('null', {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );

  const invalidBody = await createEmployer({
    commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    employerType: 'household',
    displayName: 'Synthetic Invalid Body 001',
  });

  expect(invalidBody).toEqual({
    ok: false,
    failure: { kind: 'unknown_outcome' },
  });
});

it('maps failures and disposes unread bodies without reflection', async () => {
  const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
  const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
  const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {});

  const cancelledBodies: string[] = [];

  function mockResponse(options: {
    status: number;
    contentType?: string | null;
    jsonValue?: unknown;
    cancelRejects?: boolean;
  }): Response {
    const json = vi.fn(() => Promise.resolve(options.jsonValue));
    const text = vi.fn(() => Promise.resolve('secret-like-body'));
    const cancel = vi.fn(() => {
      cancelledBodies.push(`status:${String(options.status)}`);
      if (options.cancelRejects) {
        return Promise.reject(new Error('cancel failed'));
      }
      return Promise.resolve();
    });

    return {
      status: options.status,
      headers: {
        get: (name: string) =>
          name.toLowerCase() === 'content-type' ? (options.contentType ?? null) : null,
      } as Headers,
      body: { cancel } as unknown as ReadableStream<Uint8Array>,
      json,
      text,
    } as unknown as Response;
  }

  const failureStatuses = [
    {
      label: 'search forbidden',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 403, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'forbidden' } },
    },
    {
      label: 'search unavailable',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 503, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'unavailable' } },
    },
    {
      label: 'search unexpected status',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 418, contentType: 'application/json', cancelRejects: true }),
      expected: { ok: false, failure: { kind: 'unexpected' } },
    },
    {
      label: 'search wrong media type',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 200, contentType: 'text/html', jsonValue: { secret: 'nope' } }),
      expected: { ok: false, failure: { kind: 'unexpected' } },
    },
    {
      label: 'create 200 unknown outcome',
      call: () =>
        createEmployer({
          commandId: '66666666-6666-4666-8666-666666666666',
          employerType: 'business',
          displayName: 'Synthetic Replay API 001',
        }),
      response: mockResponse({ status: 200, contentType: 'application/json', jsonValue: { detail: 'do not leak' } }),
      expected: { ok: false, failure: { kind: 'unknown_outcome' } },
    },
    {
      label: 'create invalid 201 media type',
      call: () =>
        createEmployer({
          commandId: '77777777-7777-4777-8777-777777777777',
          employerType: 'household',
          displayName: 'Synthetic Household 001',
        }),
      response: mockResponse({ status: 201, contentType: 'text/plain', jsonValue: { detail: 'do not leak' } }),
      expected: { ok: false, failure: { kind: 'unknown_outcome' } },
    },
  ];

  for (const scenario of failureStatuses) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(scenario.response));
    const result = await scenario.call();
    expect(result, scenario.label).toEqual(scenario.expected);
  }

  expect(cancelledBodies).toEqual([
    'status:403',
    'status:503',
    'status:418',
    'status:200',
    'status:200',
    'status:201',
  ]);
  expect(consoleError).not.toHaveBeenCalled();
  expect(consoleWarn).not.toHaveBeenCalled();
  expect(consoleLog).not.toHaveBeenCalled();
});

it('classifies aborted reads silently', async () => {
  const abortError = new DOMException('aborted', 'AbortError');
  const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(abortError));
  const searchResult = await searchEmployers({ displayNameQuery: 'rose' });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(abortError));
  const detailResult = await getEmployer('88888888-8888-4888-8888-888888888888');

  expect(searchResult).toBeNull();
  expect(detailResult).toBeNull();
  expect(consoleError).not.toHaveBeenCalled();
});

it('maps non-abort read transport failures to unavailable', async () => {
  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('offline')));
  const searchResult = await searchEmployers({ displayNameQuery: 'rose' });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('offline')));
  const detailResult = await getEmployer('88888888-8888-4888-8888-888888888888');

  expect(searchResult).toEqual({ ok: false, failure: { kind: 'unavailable' } });
  expect(detailResult).toEqual({ ok: false, failure: { kind: 'unavailable' } });
});

it('maps detail and create unreadable success payloads to bounded failures', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValueOnce(
      new Response('not-json', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );

  const detailUnreadable = await getEmployer('12345678-1234-4234-8234-123456789abc');
  expect(detailUnreadable).toEqual({ ok: false, failure: { kind: 'unexpected' } });

  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValueOnce(
      new Response('not-json', {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );

  const createUnreadable = await createEmployer({
    commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    employerType: 'business',
    displayName: 'Synthetic Invalid JSON 001',
  });
  expect(createUnreadable).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});
