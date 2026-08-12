import { afterEach, expect, it, vi } from 'vitest';

import { reviseEmployer } from './employerClient';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it('rejects revision success whose Employer ID differs from the requested target', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          employer_id: '99999999-9999-4999-8999-999999999999',
          employer_type: 'business',
          display_name: 'Synthetic Wrong Target Revision',
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
    displayName: 'Synthetic Wrong Target Revision',
  });

  expect(result).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});
