import { afterEach, expect, it, vi } from 'vitest';

import { createEmployer, getEmployer, reviseEmployer, searchEmployers } from './employerClient';

const VALID_OFFSET_TIMESTAMPS = [
  '0001-01-01T00:00:00Z',
  '0099-12-31T23:59:59+00:00',
  '2026-08-05T08:00:00Z',
  '2026-08-05T08:00:00+00:00',
  '2026-08-05T08:00:00.123+00:00',
  '2026-08-05T08:00:00+05:30',
  '2026-08-05T08:00:00-04:00',
  '2028-02-29T23:59:59-05:00',
  '2026-08-05T23:30:00-02:00',
] as const;

const INVALID_TIMESTAMPS = [
  '2026-02-31T08:00:00Z',
  '2025-02-29T08:00:00Z',
  '2026-13-01T08:00:00Z',
  '2026-08-05T24:00:00Z',
  '2026-08-05T08:60:00Z',
  '2026-08-05T08:00:60Z',
  '2026-08-05T08:00:00+24:00',
  '2026-08-05T08:00:00+00:60',
  '2026-08-05T08:00:00+0:00',
  '2026-08-05T08:00:00',
  '2026-08-05',
  '2026-08-05 08:00:00Z',
  '2026-08-05T08:00:00Z trailing',
  '2026-08-05T08:00:00Z\u0007',
] as const;

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

it('accepts valid RFC3339 offsets across search detail and create payloads', async () => {
  for (const timestamp of VALID_OFFSET_TIMESTAMPS) {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                employer_id: '11111111-1111-4111-8111-111111111111',
                employer_type: 'business',
                display_name: 'Offset Search Rose',
                lifecycle_status: 'draft',
                version: 1,
                received_at: timestamp,
              },
            ],
            next_cursor: null,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    expect(await searchEmployers({ displayNameQuery: 'rose' }), timestamp).toEqual({
      ok: true,
      value: {
        items: [
          {
            employerId: '11111111-1111-4111-8111-111111111111',
            employerType: 'business',
            displayName: 'Offset Search Rose',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });

    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            employer_id: '22222222-2222-4222-8222-222222222222',
            employer_type: 'household',
            display_name: 'Offset Detail Rose',
            lifecycle_status: 'draft',
            source_channel: 'staff_entry',
            version: 1,
            received_at: timestamp,
            created_at: timestamp,
            updated_at: timestamp,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    expect(await getEmployer('22222222-2222-4222-8222-222222222222'), timestamp).toEqual({
      ok: true,
      value: {
        employerId: '22222222-2222-4222-8222-222222222222',
        employerType: 'household',
        displayName: 'Offset Detail Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 1,
        updatedAt: timestamp,
      },
    });

    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            employer_id: '33333333-3333-4333-8333-333333333333',
            employer_type: 'business',
            display_name: 'Offset Create Rose',
            lifecycle_status: 'draft',
            source_channel: 'staff_entry',
            version: 1,
            received_at: timestamp,
            created_at: timestamp,
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    expect(
      await createEmployer({
        commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        employerType: 'business',
        displayName: 'Offset Create Rose',
      }),
      timestamp,
    ).toEqual({
      ok: true,
      value: {
        employerId: '33333333-3333-4333-8333-333333333333',
        employerType: 'business',
        displayName: 'Offset Create Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });
  }
});

it('rejects invalid RFC3339 timestamps across search detail and create payloads', async () => {
  for (const timestamp of INVALID_TIMESTAMPS) {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                employer_id: '11111111-1111-4111-8111-111111111111',
                employer_type: 'business',
                display_name: 'Invalid Timestamp Rose',
                lifecycle_status: 'draft',
                version: 1,
                received_at: timestamp,
              },
            ],
            next_cursor: null,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    expect(await searchEmployers({ displayNameQuery: 'rose' }), timestamp).toEqual({ ok: false, failure: { kind: 'unexpected' } });

    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            employer_id: '22222222-2222-4222-8222-222222222222',
            employer_type: 'household',
            display_name: 'Invalid Detail Rose',
            lifecycle_status: 'draft',
            source_channel: 'staff_entry',
            version: 1,
            received_at: timestamp,
            created_at: timestamp,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    expect(await getEmployer('22222222-2222-4222-8222-222222222222'), timestamp).toEqual({ ok: false, failure: { kind: 'unexpected' } });

    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            employer_id: '33333333-3333-4333-8333-333333333333',
            employer_type: 'business',
            display_name: 'Invalid Create Rose',
            lifecycle_status: 'draft',
            source_channel: 'staff_entry',
            version: 1,
            received_at: timestamp,
            created_at: timestamp,
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    );
    expect(
      await createEmployer({
        commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
        employerType: 'business',
        displayName: 'Invalid Create Rose',
      }),
      timestamp,
    ).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
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
        updated_at: '2026-08-11T04:00:00Z',
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
      version: 1,
      updatedAt: '2026-08-11T04:00:00Z',
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

it('posts an exact revision command with frozen expected version and idempotency key', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(
      JSON.stringify({
        employer_id: '33333333-3333-4333-8333-333333333333',
        employer_type: 'business',
        display_name: 'Synthetic Revision Updated',
        lifecycle_status: 'draft',
        source_channel: 'staff_entry',
        version: 2,
        received_at: '2026-08-05T00:10:45Z',
        created_at: '2026-08-05T00:10:45Z',
        updated_at: '2026-08-11T02:50:00Z',
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Result-Version': '2',
        },
      },
    ),
  );
  vi.stubGlobal('fetch', fetchMock);

  await reviseEmployer({
    employerId: '33333333-3333-4333-8333-333333333333',
    commandId: '44444444-4444-4444-8444-444444444444',
    expectedVersion: 1,
    employerType: 'business',
    displayName: 'Synthetic Revision Updated',
  });

  expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/employers/33333333-3333-4333-8333-333333333333/revisions', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'Idempotency-Key': '44444444-4444-4444-8444-444444444444',
    },
    body: JSON.stringify({
      expected_version: 1,
      employer_type: 'business',
      display_name: 'Synthetic Revision Updated',
    }),
    cache: 'no-store',
    credentials: 'same-origin',
    mode: 'same-origin',
    redirect: 'error',
    referrerPolicy: 'no-referrer',
  });
});

it('accepts exact current-authoritative revision success and result-version metadata', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 2,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
          },
        },
      ),
    ),
  );

  const result = await reviseEmployer({
    employerId: '33333333-3333-4333-8333-333333333333',
    commandId: '44444444-4444-4444-8444-444444444444',
    expectedVersion: 1,
    employerType: 'business',
    displayName: 'Synthetic Revision Updated',
  });

  expect(result).toEqual({
    ok: true,
    value: {
      detail: {
        employerId: '33333333-3333-4333-8333-333333333333',
        employerType: 'business',
        displayName: 'Synthetic Revision Updated',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 2,
        updatedAt: '2026-08-11T02:50:00Z',
      },
      resultVersion: 2,
      replayed: false,
    },
  });
});

it('rejects actor attribution fields from routine revision and detail browser responses', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>()
      .mockResolvedValueOnce(
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
            updated_at: '2026-08-11T04:00:00Z',
            updated_by: 'staff-actor-should-not-leak',
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json; charset=utf-8' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            employer_id: '33333333-3333-4333-8333-333333333333',
            employer_type: 'business',
            display_name: 'Synthetic Revision Updated',
            lifecycle_status: 'draft',
            source_channel: 'staff_entry',
            version: 2,
            received_at: '2026-08-05T00:10:45Z',
            created_at: '2026-08-05T00:10:45Z',
            updated_at: '2026-08-11T02:50:00Z',
            updated_by: 'staff-actor-should-not-leak',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
              'Idempotency-Result-Version': '2',
            },
          },
        ),
      ),
  );

  expect(await getEmployer('22222222-2222-4222-8222-222222222222')).toEqual({
    ok: false,
    failure: { kind: 'unexpected' },
  });

  expect(
    await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    }),
  ).toEqual({
    ok: false,
    failure: { kind: 'unknown_outcome' },
  });
});

it('accepts replay after later mutation without treating the older result version as malformed', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated Again',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 3,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T03:05:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
            'Idempotency-Replayed': 'true',
          },
        },
      ),
    ),
  );

  const result = await reviseEmployer({
    employerId: '33333333-3333-4333-8333-333333333333',
    commandId: '44444444-4444-4444-8444-444444444444',
    expectedVersion: 1,
    employerType: 'business',
    displayName: 'Synthetic Revision Updated',
  });

  expect(result).toEqual({
    ok: true,
    value: {
      detail: {
        employerId: '33333333-3333-4333-8333-333333333333',
        employerType: 'business',
        displayName: 'Synthetic Revision Updated Again',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 3,
        updatedAt: '2026-08-11T03:05:00Z',
      },
      resultVersion: 2,
      replayed: true,
    },
  });
});

it('requires fresh body version to equal result version and replay body version to be at least result version', async () => {
  const invalidResponses = [
    {
      label: 'fresh body version lower than result version',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 1,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
          },
        },
      ),
    },
    {
      label: 'fresh body version higher than result version',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 3,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
          },
        },
      ),
    },
    {
      label: 'replay body version lower than result version',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 1,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
            'Idempotency-Replayed': 'true',
          },
        },
      ),
    },
  ];

  for (const invalidResponse of invalidResponses) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(invalidResponse.response));

    const result = await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    });

    expect(result, invalidResponse.label).toEqual({
      ok: false,
      failure: { kind: 'unknown_outcome' },
    });
  }
});

it('rejects missing malformed or unexpected replay and result-version headers as unknown outcome', async () => {
  const invalidResponses = [
    {
      label: 'missing result-version header',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 2,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ),
    },
    {
      label: 'malformed result-version header',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 2,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': 'abc',
          },
        },
      ),
    },
    {
      label: 'missing replay header on replay success',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated Again',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 3,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T03:05:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
          },
        },
      ),
    },
    {
      label: 'malformed replay header value',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated Again',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 3,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T03:05:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
            'Idempotency-Replayed': 'false',
          },
        },
      ),
    },
  ];

  for (const invalidResponse of invalidResponses) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(invalidResponse.response));

    const result = await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    });

    expect(result, invalidResponse.label).toEqual({
      ok: false,
      failure: { kind: 'unknown_outcome' },
    });
  }
});

it('rejects body versions lower than the command result version', async () => {
  const invalidResponses = [
    {
      label: 'fresh body version lower than result version',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 1,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
          },
        },
      ),
    },
    {
      label: 'replay body version lower than result version',
      response: new Response(
        JSON.stringify({
          employer_id: '33333333-3333-4333-8333-333333333333',
          employer_type: 'business',
          display_name: 'Synthetic Revision Updated',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 1,
          received_at: '2026-08-05T00:10:45Z',
          created_at: '2026-08-05T00:10:45Z',
          updated_at: '2026-08-11T02:50:00Z',
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Result-Version': '2',
            'Idempotency-Replayed': 'true',
          },
        },
      ),
    },
  ];

  for (const invalidResponse of invalidResponses) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(invalidResponse.response));

    const result = await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    });

    expect(result, invalidResponse.label).toEqual({
      ok: false,
      failure: { kind: 'unknown_outcome' },
    });
  }
});

it('maps 400 403 404 409 412 and 422 to definitive bounded revision failures', async () => {
  const failureStatuses = [
    { status: 400, expected: { ok: false, failure: { kind: 'validation' } } },
    { status: 403, expected: { ok: false, failure: { kind: 'forbidden' } } },
    { status: 404, expected: { ok: false, failure: { kind: 'not_found' } } },
    { status: 409, expected: { ok: false, failure: { kind: 'conflict' } } },
    { status: 412, expected: { ok: false, failure: { kind: 'stale' } } },
    { status: 422, expected: { ok: false, failure: { kind: 'validation' } } },
  ] as const;

  for (const { status, expected } of failureStatuses) {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response('secret-like-body', {
          status,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    const result = await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    });

    expect(result, `status ${String(status)}`).toEqual(expected);
  }
});

it('maps network 500 503 redirect media-type and malformed-success failures to unknown outcome', async () => {
  const failureCases = [
    {
      label: 'network failure',
      install: () => vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('network down'))),
    },
    {
      label: '500 failure',
      install: () =>
        vi.stubGlobal(
          'fetch',
          vi.fn<typeof fetch>().mockResolvedValue(
            new Response('secret-like-body', {
              status: 500,
              headers: { 'Content-Type': 'application/json' },
            }),
          ),
        ),
    },
    {
      label: '503 failure',
      install: () =>
        vi.stubGlobal(
          'fetch',
          vi.fn<typeof fetch>().mockResolvedValue(
            new Response('secret-like-body', {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            }),
          ),
        ),
    },
    {
      label: 'redirect failure',
      install: () =>
        vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('redirect blocked'))),
    },
    {
      label: 'wrong media type on success status',
      install: () =>
        vi.stubGlobal(
          'fetch',
          vi.fn<typeof fetch>().mockResolvedValue(
            new Response('<html>nope</html>', {
              status: 200,
              headers: { 'Content-Type': 'text/html' },
            }),
          ),
        ),
    },
    {
      label: 'malformed success body',
      install: () =>
        vi.stubGlobal(
          'fetch',
          vi.fn<typeof fetch>().mockResolvedValue(
            new Response('null', {
              status: 200,
              headers: {
                'Content-Type': 'application/json',
                'Idempotency-Result-Version': '2',
              },
            }),
          ),
        ),
    },
  ] as const;

  for (const failureCase of failureCases) {
    failureCase.install();

    const result = await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    });

    expect(result, failureCase.label).toEqual({
      ok: false,
      failure: { kind: 'unknown_outcome' },
    });
  }
});

it('parses each accepted revision body exactly once and disposes every other terminal response body without exposing values', async () => {
  const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
  const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
  const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {});

  function trackedResponse(options: {
    status: number;
    contentType?: string | null;
    resultVersion?: string | null;
    replayed?: string | null;
    jsonValue?: unknown;
  }) {
    const json = vi.fn(() => Promise.resolve(options.jsonValue));
    const text = vi.fn(() => Promise.resolve('secret-like-body'));
    const cancel = vi.fn(() => Promise.resolve());

    const response = {
      status: options.status,
      headers: {
        get: (name: string) => {
          switch (name.toLowerCase()) {
            case 'content-type':
              return options.contentType ?? null;
            case 'idempotency-result-version':
              return options.resultVersion ?? null;
            case 'idempotency-replayed':
              return options.replayed ?? null;
            default:
              return null;
          }
        },
      } as Headers,
      body: { cancel } as unknown as ReadableStream<Uint8Array>,
      json,
      text,
    } as unknown as Response;

    return { response, json, text, cancel };
  }

  const acceptedSuccess = trackedResponse({
    status: 200,
    contentType: 'application/json',
    resultVersion: '2',
    jsonValue: {
      employer_id: '33333333-3333-4333-8333-333333333333',
      employer_type: 'business',
      display_name: 'Synthetic Revision Updated',
      lifecycle_status: 'draft',
      source_channel: 'staff_entry',
      version: 2,
      received_at: '2026-08-05T00:10:45Z',
      created_at: '2026-08-05T00:10:45Z',
      updated_at: '2026-08-11T02:50:00Z',
    },
  });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(acceptedSuccess.response));
  expect(
    await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    }),
  ).toEqual({
    ok: true,
    value: {
      detail: {
        employerId: '33333333-3333-4333-8333-333333333333',
        employerType: 'business',
        displayName: 'Synthetic Revision Updated',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 2,
        updatedAt: '2026-08-11T02:50:00Z',
      },
      resultVersion: 2,
      replayed: false,
    },
  });
  expect(acceptedSuccess.json).toHaveBeenCalledTimes(1);
  expect(acceptedSuccess.text).not.toHaveBeenCalled();
  expect(acceptedSuccess.cancel).not.toHaveBeenCalled();

  const malformedSuccess = trackedResponse({
    status: 200,
    contentType: 'application/json',
    resultVersion: '2',
    jsonValue: null,
  });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(malformedSuccess.response));
  expect(
    await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    }),
  ).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
  expect(malformedSuccess.json).toHaveBeenCalledTimes(1);
  expect(malformedSuccess.text).not.toHaveBeenCalled();
  expect(malformedSuccess.cancel).not.toHaveBeenCalled();

  const staleResponse = trackedResponse({
    status: 412,
    contentType: 'application/json',
  });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(staleResponse.response));
  expect(
    await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    }),
  ).toEqual({ ok: false, failure: { kind: 'stale' } });
  expect(staleResponse.json).not.toHaveBeenCalled();
  expect(staleResponse.text).not.toHaveBeenCalled();
  expect(staleResponse.cancel).toHaveBeenCalledTimes(1);

  const wrongMedia = trackedResponse({
    status: 200,
    contentType: 'text/html',
  });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(wrongMedia.response));
  expect(
    await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    }),
  ).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
  expect(wrongMedia.json).not.toHaveBeenCalled();
  expect(wrongMedia.text).not.toHaveBeenCalled();
  expect(wrongMedia.cancel).toHaveBeenCalledTimes(1);

  const internalError = trackedResponse({
    status: 500,
    contentType: 'application/json',
  });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(internalError.response));
  expect(
    await reviseEmployer({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 1,
      employerType: 'business',
      displayName: 'Synthetic Revision Updated',
    }),
  ).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
  expect(internalError.json).not.toHaveBeenCalled();
  expect(internalError.text).not.toHaveBeenCalled();
  expect(internalError.cancel).toHaveBeenCalledTimes(1);

  expect(consoleError).not.toHaveBeenCalled();
  expect(consoleWarn).not.toHaveBeenCalled();
  expect(consoleLog).not.toHaveBeenCalled();
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
      label: 'search validation',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 400, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'validation' } },
    },
    {
      label: 'search forbidden',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 403, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'forbidden' } },
    },
    {
      label: 'search conflict',
      call: () => searchEmployers({ displayNameQuery: 'rose' }),
      response: mockResponse({ status: 409, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'conflict' } },
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
      label: 'detail validation',
      call: () => getEmployer('12345678-1234-4234-8234-123456789abc'),
      response: mockResponse({ status: 422, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'validation' } },
    },
    {
      label: 'detail forbidden',
      call: () => getEmployer('12345678-1234-4234-8234-123456789abc'),
      response: mockResponse({ status: 403, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'forbidden' } },
    },
    {
      label: 'detail not found',
      call: () => getEmployer('12345678-1234-4234-8234-123456789abc'),
      response: mockResponse({ status: 404, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'not_found' } },
    },
    {
      label: 'detail conflict',
      call: () => getEmployer('12345678-1234-4234-8234-123456789abc'),
      response: mockResponse({ status: 409, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'conflict' } },
    },
    {
      label: 'detail unavailable',
      call: () => getEmployer('12345678-1234-4234-8234-123456789abc'),
      response: mockResponse({ status: 503, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'unavailable' } },
    },
    {
      label: 'detail wrong media type',
      call: () => getEmployer('12345678-1234-4234-8234-123456789abc'),
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
    {
      label: 'create validation',
      call: () =>
        createEmployer({
          commandId: '88888888-8888-4888-8888-888888888888',
          employerType: 'household',
          displayName: 'Create Validation Rose',
        }),
      response: mockResponse({ status: 422, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'validation' } },
    },
    {
      label: 'create forbidden',
      call: () =>
        createEmployer({
          commandId: '99999999-9999-4999-8999-999999999999',
          employerType: 'business',
          displayName: 'Create Forbidden Rose',
        }),
      response: mockResponse({ status: 403, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'forbidden' } },
    },
    {
      label: 'create conflict',
      call: () =>
        createEmployer({
          commandId: '10101010-1010-4010-8010-101010101010',
          employerType: 'business',
          displayName: 'Create Conflict Rose',
        }),
      response: mockResponse({ status: 409, contentType: 'application/json' }),
      expected: { ok: false, failure: { kind: 'conflict' } },
    },
    {
      label: 'create unexpected 2xx',
      call: () =>
        createEmployer({
          commandId: '12121212-1212-4212-8212-121212121212',
          employerType: 'business',
          displayName: 'Create Unexpected Two Hundred Two',
        }),
      response: mockResponse({ status: 202, contentType: 'application/json', jsonValue: { detail: 'do not leak' } }),
      expected: { ok: false, failure: { kind: 'unknown_outcome' } },
    },
  ];

  for (const scenario of failureStatuses) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(scenario.response));
    const result = await scenario.call();
    expect(result, scenario.label).toEqual(scenario.expected);
  }

  expect(cancelledBodies).toEqual([
    'status:400',
    'status:403',
    'status:409',
    'status:503',
    'status:418',
    'status:200',
    'status:422',
    'status:403',
    'status:404',
    'status:409',
    'status:503',
    'status:200',
    'status:200',
    'status:201',
    'status:422',
    'status:403',
    'status:409',
    'status:202',
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

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue({ name: 'AbortError' }));
  const plainObjectAbort = await searchEmployers({ displayNameQuery: 'rose' });
  expect(plainObjectAbort).toBeNull();
});

it('classifies response-body aborts silently', async () => {
  const abortError = new DOMException('aborted', 'AbortError');
  const abortingResponse = () =>
    ({
      status: 200,
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: vi.fn().mockRejectedValue(abortError),
    }) as unknown as Response;

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(abortingResponse()));
  const searchResult = await searchEmployers({ displayNameQuery: 'rose' });

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValueOnce(abortingResponse()));
  const detailResult = await getEmployer('88888888-8888-4888-8888-888888888888');

  expect(searchResult).toBeNull();
  expect(detailResult).toBeNull();
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

it('rejects detail ID mismatch in a 200 response', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          employer_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          employer_type: 'business',
          display_name: 'Wrong Detail Rose',
          lifecycle_status: 'draft',
          source_channel: 'staff_entry',
          version: 1,
          received_at: '2026-08-05T08:00:00Z',
          created_at: '2026-08-05T08:00:00Z',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    ),
  );

  expect(await getEmployer('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')).toEqual({
    ok: false,
    failure: { kind: 'unexpected' },
  });
});
