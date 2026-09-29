import { afterEach, expect, it, vi } from 'vitest';

import {
  activateStaffAccount,
  createStaffAccount,
  deprovisionStaffAccount,
  listStaffAccounts,
  recordRecoveryEvidence,
  recordSessionRevocationEvidence,
  suspendStaffAccount,
} from './staffAccountClient';

const account = {
  staff_id: '22222222-2222-4222-8222-222222222222',
  provider_subject: 'oidc:staff:123',
  display_name: 'Mariela Torres',
  role_name: 'operations_staff',
  lifecycle_status: 'suspended',
  mfa_enrolled: false,
  created_at: '2026-09-28T12:00:00Z',
  created_by: '11111111-1111-4111-8111-111111111111',
  updated_at: '2026-09-28T12:00:00Z',
  updated_by: '11111111-1111-4111-8111-111111111111',
  version: 1,
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it('lists staff accounts with no-store fetch options and strict response parsing', async () => {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({ items: [account] }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);

  const result = await listStaffAccounts();

  expect(fetchMock).toHaveBeenCalledWith('/api/staff/v1/staff-accounts', {
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
    value: [{
      staffId: account.staff_id,
      providerSubject: account.provider_subject,
      displayName: account.display_name,
      roleName: account.role_name,
      lifecycleStatus: account.lifecycle_status,
      mfaEnrolled: account.mfa_enrolled,
      createdAt: account.created_at,
      createdBy: account.created_by,
      updatedAt: account.updated_at,
      updatedBy: account.updated_by,
      version: account.version,
    }],
  });
});

it('creates and activates accounts with idempotency headers and version validation', async () => {
  const activeAccount = { ...account, lifecycle_status: 'active', mfa_enrolled: true, version: 2 };
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ account, event_type: 'staff_account.created', result_version: 1 }), {
        status: 201,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '1' },
      }),
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ account: activeAccount, event_type: 'staff_account.activated', result_version: 2 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' },
      }),
    );
  vi.stubGlobal('fetch', fetchMock);

  const created = await createStaffAccount({
    commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    displayName: 'Mariela Torres',
    mfaEnrolled: false,
    permissionNames: ['staff_account:read'],
    providerSubject: 'oidc:staff:123',
    reasonText: 'Initial onboarding',
    roleName: 'operations_staff',
  });
  const activated = await activateStaffAccount({
    commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    expectedVersion: 1,
    mfaEnrolled: true,
    reasonText: 'MFA confirmed',
    staffId: account.staff_id,
  });

  expect(created.ok).toBe(true);
  expect(activated.ok).toBe(true);
  const firstCall = fetchMock.mock.calls[0];
  expect(firstCall?.[0]).toBe('/api/staff/v1/staff-accounts');
  expect(firstCall?.[1]).toMatchObject({
    method: 'POST',
    headers: { 'Idempotency-Key': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa' },
  });
  expect(fetchMock).toHaveBeenNthCalledWith(2, `/api/staff/v1/staff-accounts/${account.staff_id}/activate`, expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({ expected_version: 1, reason_text: 'MFA confirmed', mfa_enrolled: true }),
  }));
});

it('maps version conflicts and unknown command outcomes to recoverable failures', async () => {
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(JSON.stringify({ type: 'stale' }), { status: 412, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ account, event_type: 'staff_account.sessions_revoked', result_version: 1 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '999' },
      }),
    );
  vi.stubGlobal('fetch', fetchMock);

  const stale = await activateStaffAccount({
    commandId: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    expectedVersion: 1,
    mfaEnrolled: true,
    reasonText: 'MFA confirmed',
    staffId: account.staff_id,
  });
  const unknown = await recordSessionRevocationEvidence({
    commandId: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    expectedVersion: 1,
    reasonText: 'Provider console note',
    staffId: account.staff_id,
  });

  expect(stale).toEqual({ ok: false, failure: { kind: 'stale' } });
  expect(unknown).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it('maps list and lifecycle problem responses without reading private payloads', async () => {
  const fetchMock = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'forbidden' }), { status: 403, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'invalid' }), { status: 422, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'missing' }), { status: 404, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'unavailable' }), { status: 503, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'bad request' }), { status: 400, headers: { 'Content-Type': 'application/problem+json' } }))
    .mockRejectedValueOnce(new Error('network down'));
  vi.stubGlobal('fetch', fetchMock);

  const listed = await listStaffAccounts();
  const created = await createStaffAccount({
    commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    displayName: 'Mariela Torres',
    mfaEnrolled: false,
    permissionNames: ['staff_account:read'],
    providerSubject: 'oidc:staff:123',
    reasonText: 'Initial onboarding',
    roleName: 'operations_staff',
  });
  const activated = await activateStaffAccount({
    commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    expectedVersion: 1,
    mfaEnrolled: true,
    reasonText: 'MFA confirmed',
    staffId: account.staff_id,
  });
  const suspended = await suspendStaffAccount({
    commandId: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    expectedVersion: 2,
    reasonText: 'Access review',
    staffId: account.staff_id,
  });
  const deprovisioned = await deprovisionStaffAccount({
    commandId: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    expectedVersion: 3,
    reasonText: 'Offboarding',
    staffId: account.staff_id,
  });
  const recovery = await recordRecoveryEvidence({
    commandId: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    expectedVersion: 4,
    reasonText: 'Recovery record',
    staffId: account.staff_id,
  });

  expect(listed).toEqual({ ok: false, failure: { kind: 'forbidden' } });
  expect(created).toEqual({ ok: false, failure: { kind: 'validation' } });
  expect(activated).toEqual({ ok: false, failure: { kind: 'not_found' } });
  expect(suspended).toEqual({ ok: false, failure: { kind: 'unavailable' } });
  expect(deprovisioned).toEqual({ ok: false, failure: { kind: 'validation' } });
  expect(recovery).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});

it('rejects malformed account payloads for list and command reads', async () => {
  const invalidAccounts = [
    { ...account, extra_field: 'private' },
    { ...account, staff_id: 'not-a-uuid' },
    { ...account, provider_subject: '' },
    { ...account, role_name: 'superuser' },
    { ...account, lifecycle_status: 'pending' },
    { ...account, mfa_enrolled: 'yes' },
    { ...account, created_at: 'not-a-date' },
    { ...account, created_by: 'not-a-uuid' },
    { ...account, updated_by: 'not-a-uuid' },
    { ...account, version: 0 },
  ];

  for (const invalidAccount of invalidAccounts) {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [invalidAccount] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    expect(await listStaffAccounts()).toEqual({ ok: false, failure: { kind: 'unexpected' } });
  }

  vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockResolvedValue(
    new Response(JSON.stringify({ account, event_type: 'staff_account.created', result_version: 2 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json', 'Idempotency-Result-Version': '2' },
    }),
  ));

  expect(await createStaffAccount({
    commandId: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
    displayName: 'Mariela Torres',
    mfaEnrolled: false,
    permissionNames: ['staff_account:read'],
    providerSubject: 'oidc:staff:123',
    reasonText: 'Initial onboarding',
    roleName: 'operations_staff',
  })).toEqual({ ok: false, failure: { kind: 'unknown_outcome' } });
});
